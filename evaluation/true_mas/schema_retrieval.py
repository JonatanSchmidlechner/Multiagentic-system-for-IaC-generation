import re

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

def keyword_score(resource_type: str, keywords: list[str]) -> int:
    resource_tokens = set(normalize(resource_type).split("_"))

    score = 0

    for keyword in keywords:
        keyword_tokens = normalize(keyword).split("_")

        matched_tokens = 0

        for token in keyword_tokens:
            if token in resource_tokens:
                matched_tokens += 1

        score += matched_tokens

        # Small bonus if every part of a multi-token keyword matches.
        if len(keyword_tokens) > 1 and matched_tokens == len(keyword_tokens):
            score += 1

    return score

def retrieve_provider_schemas_object(
    planner_plan,
    provider_schemas: dict
):
    MAX_CANDIDATES = 1
    schemas_object = {}

    for resource in planner_plan.resources:
        candidates = {}

        resource_type = resource.resource_type_candidate

        # 1. Exact resource type exists.
        if resource_type and resource_type in provider_schemas:
            candidates[resource_type] = trim_resource_schema(provider_schemas[resource_type])

        # 2. Exact type missing or invalid -> keyword retrieval.
        else:
            matches = []

            for schema_type, schema in provider_schemas.items():
                score = keyword_score(
                    schema_type,
                    resource.keywords,
                )

                if score > 0:
                    matches.append(
                        (score, schema_type, schema)
                    )

            # Highest scoring schemas first.
            matches.sort(
                key=lambda match: match[0],
                reverse=True,
            )

            for _, schema_type, schema in matches[:MAX_CANDIDATES]:
                candidates[schema_type] = trim_resource_schema(schema)

        schemas_object[resource.node_id] = candidates

    return schemas_object

def trim_block(block):
    trimmed = {
        "attributes": {},
        "block_types": {},
    }

    # Preserve block-level description if present
    if block.get("description"):
        trimmed["description"] = block["description"]

    # Attributes
    for name, attr in block.get("attributes", {}).items():
        trimmed_attr = {
            "type": attr.get("type"),
            "required": attr.get("required", False),
            "optional": attr.get("optional", False),
            "computed": attr.get("computed", False),
            "sensitive": attr.get("sensitive", False),
        }

        if attr.get("description"):
            trimmed_attr["description"] = attr["description"]

        trimmed["attributes"][name] = trimmed_attr

    # Nested blocks
    for name, block_type in block.get("block_types", {}).items():
        nested = {
            "nesting_mode": block_type.get("nesting_mode"),
            "block": trim_block(block_type.get("block", {})),
        }

        # Preserve description directly on the block_type if it exists
        if block_type.get("description"):
            nested["description"] = block_type["description"]

        if "min_items" in block_type:
            nested["min_items"] = block_type["min_items"]

        if "max_items" in block_type:
            nested["max_items"] = block_type["max_items"]

        trimmed["block_types"][name] = nested

    return trimmed


def trim_resource_schema(resource_schema):
    return trim_block(resource_schema.get("block", {}))