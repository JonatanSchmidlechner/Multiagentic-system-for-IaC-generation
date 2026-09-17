from effgen import GenerationConfig, load_model
from ..config import STRUCTURED_GENERATION_MAX_TOKENS, TEXT_GENERATION_MAX_TOKENS, TEMPERATURE


temperature = TEMPERATURE

def generate_structured(
    model,
    prompt,
    system_prompt,
    schema,
    schema_name,
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

    result = model.generate_structured(
        prompt,
        response_format=response_format,
        system_prompt=system_prompt,
        config=config,
    )

    return result


def generate(
    model,
    prompt,
    ):
    max_tokens = TEXT_GENERATION_MAX_TOKENS
    
    config = GenerationConfig(
        temperature=temperature,
        max_tokens=max_tokens,
    )

    result = model.generate(
        prompt,
        config=config,
    )

    return result

def load_effgen_model(model_name, base_url):
    model = load_model(
            model_name,
            provider="openai_compatible",
            base_url=base_url,
        )
    return model