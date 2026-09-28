"""Request counters and resource measurements for one task/sample."""
from contextlib import contextmanager
import logging
import os
import time
from threading import Event, Thread

from codecarbon import OfflineEmissionsTracker

from true_mas import config
from resource_metrics import RESOURCE_METRICS

if config.MEASURE_VRAM:
    import pynvml

stats = {}


@contextmanager
def monitor_emissions():
    """Estimate CPU/RAM and selected GPU emissions for one sample."""
    country = config.CODECARBON_COUNTRY_ISO_CODE
    tracker = None
    try:
        if not country:
            raise ValueError("Set CODECARBON_COUNTRY_ISO_CODE in true_mas/config.py to the server's three-letter country code")
        tracker = OfflineEmissionsTracker(
            country_iso_code=country,
            gpu_ids=str(config.GPU_METRICS_DEVICE),
            tracking_mode="machine", measure_power_secs=1,
            save_to_file=False, save_to_api=False, save_to_logger=False, pue=1.0,
            log_level="warning",
        )
        tracker.start()
    except Exception as error:
        logging.warning("Emissions tracking unavailable: %s", error)
        if tracker is not None:
            try:
                tracker.stop()
            except Exception:
                pass
        tracker = None
    try:
        yield
    finally:
        if tracker is not None:
            try:
                emissions = tracker.stop()
                data = tracker.final_emissions_data
                if emissions is None or data is None:
                    raise RuntimeError("CodeCarbon returned no emissions data")
                stats.update(
                    estimated_co2e_g=emissions * 1000,
                    energy_wh=data.energy_consumed * 1000,
                )
            except Exception as error:
                logging.warning("Emissions tracking failed: %s", error)


@contextmanager
def monitor_vram():
    """Track observed peak device VRAM; use null if monitoring fails."""
    if not config.MEASURE_VRAM:
        yield
        return

    stopped = Event()

    def sample():
        try:
            pynvml.nvmlInit()
            try:
                device = str(config.GPU_METRICS_DEVICE)
                handle = (pynvml.nvmlDeviceGetHandleByIndex(int(device)) if device.isdigit()
                          else pynvml.nvmlDeviceGetHandleByUUID(device))
                peak = 0
                while True:
                    peak = max(peak, pynvml.nvmlDeviceGetMemoryInfo(handle).used)
                    stats['peak_vram_mib'] = peak / (1024 ** 2)
                    if stopped.wait(0.5):
                        break
            finally:
                pynvml.nvmlShutdown()
        except Exception as error:
            stats['peak_vram_mib'] = None
            logging.warning("VRAM monitoring failed: %s", error)

    thread = Thread(target=sample, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stopped.set()
        thread.join()


METRICS = RESOURCE_METRICS


def reset():
    stats.clear()
    stats.update({key: 0 for key in METRICS})
    stats.update(peak_vram_mib=None, energy_wh=None, estimated_co2e_g=None)


def attempt(retry=False):
    stats['model_request_attempts'] += 1
    stats['retries'] += int(retry)


def response(prompt_tokens, completion_tokens, finish_reason):
    for key, value in (("prompt_tokens", prompt_tokens), ("completion_tokens", completion_tokens)):
        if value is None:
            stats[key] = None
        elif stats[key] is not None:
            stats[key] += value
    if finish_reason is None:
        stats['output_limit_hits'] = None
    elif stats['output_limit_hits'] is not None:
        stats['output_limit_hits'] += int(finish_reason in ('length', 'MAX_TOKENS'))


def failure(error):
    stats['request_failures'] += 1
    message = str(error).lower()
    stats['timeouts'] += int(isinstance(error, TimeoutError) or 'timeout' in message or 'timed out' in message)
    # A failed request may have consumed tokens before its response was lost.
    stats['prompt_tokens'] = stats['completion_tokens'] = None
    stats['output_limit_hits'] = None


@contextmanager
def measure_sample(df, index, sample, checkpoint=None):
    reset()
    with monitor_emissions(), monitor_vram():
        started = time.monotonic()
        try:
            yield
        finally:
            stats['duration_seconds'] = time.monotonic() - started
    stats['total_tokens'] = (None if stats['prompt_tokens'] is None or stats['completion_tokens'] is None
                             else stats['prompt_tokens'] + stats['completion_tokens'])
    for key in METRICS:
        df.at[index, f"{key} #{sample}"] = stats[key]
    if checkpoint is not None:
        temporary = str(checkpoint) + ".tmp"
        df.to_csv(temporary, index=False, encoding="utf-8")
        os.replace(temporary, checkpoint)


reset()
