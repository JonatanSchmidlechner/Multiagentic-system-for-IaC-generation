import time

from effgen import GenerationConfig, load_model

from ..config import (
    STRUCTURED_GENERATION_MAX_TOKENS,
    TEXT_GENERATION_MAX_TOKENS,
    TEMPERATURE,
)
from ..logger import mas_logger


temperature = TEMPERATURE

MAX_TIMEOUT_RETRIES = 2
RETRY_DELAY_SECONDS = 5


timeout_stats = {
    "timeout_events": 0,
    "recovered_calls": 0,
    "failed_calls": 0,
    "failed_tasks": 0,
    "by_agent": {},
}


class ModelTimeoutError(RuntimeError):
    pass


def is_timeout_error(error):
    message = str(error).lower()
    return "timed out" in message or "timeout" in message


def record_timeout(agent_name):
    timeout_stats["timeout_events"] += 1

    timeout_stats["by_agent"][agent_name] = (
        timeout_stats["by_agent"].get(agent_name, 0) + 1
    )


def generate_structured(
    model,
    prompt,
    system_prompt,
    schema,
    schema_name,
    agent_name,
):
    max_tokens = STRUCTURED_GENERATION_MAX_TOKENS

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True,
        },
    }

    config = GenerationConfig(
        temperature=temperature,
        max_tokens=max_tokens,
    )

    for attempt in range(MAX_TIMEOUT_RETRIES + 1):
        try:
            result = model.generate_structured(
                prompt,
                response_format=response_format,
                system_prompt=system_prompt,
                config=config,
            )

            if attempt > 0:
                timeout_stats["recovered_calls"] += 1

                mas_logger.info(
                    "%s recovered after timeout retry",
                    agent_name,
                )

            return result

        except RuntimeError as e:
            if not is_timeout_error(e):
                raise

            record_timeout(agent_name)

            if attempt == MAX_TIMEOUT_RETRIES:
                timeout_stats["failed_calls"] += 1

                mas_logger.error(
                    "%s failed after %d timeout retries",
                    agent_name,
                    MAX_TIMEOUT_RETRIES,
                )

                raise ModelTimeoutError(
                    f"{agent_name} timed out after "
                    f"{MAX_TIMEOUT_RETRIES + 1} attempts"
                ) from e

            mas_logger.warning(
                "%s timed out. Retrying %d/%d",
                agent_name,
                attempt + 1,
                MAX_TIMEOUT_RETRIES,
            )

            time.sleep(RETRY_DELAY_SECONDS)


def generate(
    model,
    prompt,
    agent_name,
):
    max_tokens = TEXT_GENERATION_MAX_TOKENS

    config = GenerationConfig(
        temperature=temperature,
        max_tokens=max_tokens,
    )

    for attempt in range(MAX_TIMEOUT_RETRIES + 1):
        try:
            result = model.generate(
                prompt,
                config=config,
            )

            if attempt > 0:
                timeout_stats["recovered_calls"] += 1

                mas_logger.info(
                    "%s recovered after timeout retry",
                    agent_name,
                )

            return result

        except RuntimeError as e:
            if not is_timeout_error(e):
                raise

            record_timeout(agent_name)

            if attempt == MAX_TIMEOUT_RETRIES:
                timeout_stats["failed_calls"] += 1

                mas_logger.error(
                    "%s failed after %d timeout retries",
                    agent_name,
                    MAX_TIMEOUT_RETRIES,
                )

                raise ModelTimeoutError(
                    f"{agent_name} timed out after "
                    f"{MAX_TIMEOUT_RETRIES + 1} attempts"
                ) from e

            mas_logger.warning(
                "%s timed out. Retrying %d/%d",
                agent_name,
                attempt + 1,
                MAX_TIMEOUT_RETRIES,
            )

            time.sleep(RETRY_DELAY_SECONDS)


def load_effgen_model(model_name, base_url, api_key):
    return load_model(
        model_name,
        provider="openai_compatible",
        base_url=base_url,
        api_key=api_key
        timeout=480, #8min
        max_retries=0
    )