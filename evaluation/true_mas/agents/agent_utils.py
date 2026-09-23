import time

from effgen import GenerationConfig, load_model

from ..config import (
    STRUCTURED_GENERATION_MAX_TOKENS,
    TEXT_GENERATION_MAX_TOKENS,
    TEMPERATURE,
)
from ..logger import mas_logger


MAX_TIMEOUT_RETRIES = 2
RETRY_DELAY_SECONDS = 5


timeout_stats = {
    "timeout_events": 0, 
    "recovered_calls": 0, # How many recovered after having a timeout error
    "failed_calls": 0, # How many tasks failed cause of timeout
    "by_agent": {},
}


class ModelTimeoutError(RuntimeError):
    pass


class ModelOutputError(RuntimeError):
    """Generation stopped at the output token limit."""


def is_timeout_error(error):
    # effgen may wrap a provider timeout in a RuntimeError.
    message = str(error).lower()
    return isinstance(error, TimeoutError) or "timed out" in message or "timeout" in message


def record_timeout(agent_name):
    timeout_stats["timeout_events"] += 1

    timeout_stats["by_agent"][agent_name] = (
        timeout_stats["by_agent"].get(agent_name, 0) + 1
    )


def generate_structured(model, prompt, system_prompt, schema, schema_name, agent_name):
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True,
        },
    }
    return _generate_with_retries(
        model, prompt, agent_name, STRUCTURED_GENERATION_MAX_TOKENS,
        system_prompt=system_prompt, response_format=response_format,
    )


def generate(model, prompt, agent_name):
    return _generate_with_retries(
        model, prompt, agent_name, TEXT_GENERATION_MAX_TOKENS,
    )


def _generate_with_retries(
    model, prompt, agent_name, max_tokens, system_prompt=None, response_format=None,
):
    """Retry timeouts only. Let eval.py handle all other failures."""
    config = GenerationConfig(temperature=TEMPERATURE, max_tokens=max_tokens)

    for attempt in range(MAX_TIMEOUT_RETRIES + 1):
        try:
            if response_format is None:
                result = model.generate(
                    prompt,
                    config=config,
                    extra_body={"max_tokens": max_tokens},  # Ollama token cap
                )
            else:
                result = model.generate_structured(
                    prompt,
                    system_prompt=system_prompt,
                    response_format=response_format,
                    config=config,
                    extra_body={"max_tokens": max_tokens},
                )
        except Exception as error:
            if not is_timeout_error(error):
                raise

            record_timeout(agent_name)
            if attempt == MAX_TIMEOUT_RETRIES:
                timeout_stats["failed_calls"] += 1
                raise ModelTimeoutError(
                    f"{agent_name} timed out after {attempt + 1} attempts"
                ) from error

            mas_logger.warning(
                "%s timed out. Retrying %d/%d",
                agent_name, attempt + 1, MAX_TIMEOUT_RETRIES,
            )
            time.sleep(RETRY_DELAY_SECONDS)
            continue

        if result.finish_reason == "length":
            raise ModelOutputError(
                f"{agent_name} reached its output limit of {max_tokens} tokens"
            )

        if attempt > 0:
            timeout_stats["recovered_calls"] += 1
            mas_logger.info("%s recovered after timeout retry", agent_name)

        return result


def load_effgen_model(model_name, base_url, api_key):
    return load_model(
        model_name,
        provider="openai_compatible",
        base_url=base_url,
        api_key=api_key,
        timeout=480, #8min
        max_retries=0
    )