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