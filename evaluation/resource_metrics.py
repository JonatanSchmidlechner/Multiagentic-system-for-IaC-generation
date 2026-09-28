"""Names of per-sample resource metrics recorded during evaluation."""

RESOURCE_METRICS = (
    "prompt_tokens", "completion_tokens", "total_tokens", "model_request_attempts", "retries",
    "request_failures", "timeouts", "output_limit_hits", "duration_seconds",
    "peak_vram_mib", "energy_wh", "estimated_co2e_g",
)
