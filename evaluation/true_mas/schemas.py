from typing import Any, Literal
from typing_extensions import TypeAliasType
from pydantic import BaseModel, Field

# PLANNER OUTPUT

class PlannerResource(BaseModel):
    node_id: str = Field(
        description=(
            "Short logical identifier for this resource. "
            "Must be unique within the plan."
        )
    )

    kind: str = Field(
        description=(
            "Brief semantic name for the required infrastructure resource, "
            "independent of exact Terraform naming."
        )
    )

    resource_type_candidate: str | None = Field(
        default=None,
        description=(
            "Possible exact Terraform AWS resource type when strongly supported "
            "by the prompt or retrieved documentation. Use null if uncertain."
        )
    )

    keywords: list[str] = Field(
        default=[],
        description=(
            "AWS service and resource terms useful for provider-schema retrieval."
            "Use short keywords that would likely appear in the exact Terraform resource name."
        )
    )

    properties: dict[str, Any] = Field(
        default={},
        description=(
            "Concrete semantic configuration required for the resource. "
            "Keys need not match exact Terraform attributes."
        )
    )

    constraints: list[str] = Field(
        default=[],
        description=(
            "Resource-specific requirements not clearly represented as individual properties."
        )
    )


class PlannerRelation(BaseModel):
    source: str = Field(
        description=(
            "node_id of the source resource."
        )
    )

    target: str = Field(
        description=(
            "node_id of the target resource."
        )
    )

    relation: str = Field(
        description=(
            "Semantic relationship between the source and target resources. "
            "Do not use Terraform syntax."
        )
    )

    source_attribute_hint: str | None = Field(
        default=None,
        description=(
            "Possible Terraform attribute on the source that implements the relation. "
            "Use null if unknown."
        )
    )

    target_attribute_hint: str | None = Field(
        default=None,
        description=(
            "Possible readable Terraform attribute on the target used by the source. "
            "Use null if unknown."
        )
    )


class PlannerPlan(BaseModel):
    resources: list[PlannerResource] = Field(
        description=(
            "All infrastructure resources required by the user request."
        )
    )

    relations: list[PlannerRelation] = Field(
        default=[],
        description=(
            "Semantic relationships between resources."
        )
    )

    global_constraints: list[str] = Field(
        default=[],
        description=(
            "Requirements that apply to the infrastructure plan as a whole."
        )
    )




# HARMONIZER OUTPUT

class IIRReference(BaseModel):
    node_id: str = Field(
        description=(
            "node_id of the referenced resource or data source."
        )
    )

    attribute: str = Field(
        description=(
            "Exact readable provider attribute of the referenced node."
        )
    )


IIRValue = TypeAliasType(
    "IIRValue",
    str
    | int
    | float
    | bool
    | None
    | IIRReference
    | list["IIRValue"]
    | dict[str, "IIRValue"],
)


class IIRBlock(BaseModel):
    attributes: dict[str, IIRValue] = Field(
        default={},
        description=(
            "Exact provider attributes and values inside this nested Terraform block."
        )
    )

    blocks: dict[str, list["IIRBlock"]] = Field(
        default={},
        description=(
            "Nested block types inside this block, keyed by exact provider block name."
        )
    )


class IIRResource(BaseModel):
    node_id: str = Field(
        description=(
            "Unique logical identifier for this node. "
            "Used by references and as the Terraform label."
        )
    )

    mode: Literal["resource", "data"] = Field(
        default="resource",
        description=(
            "Use 'resource' for managed infrastructure and 'data' for provider data sources."
        )
    )

    resource_type: str = Field(
        description=(
            "Exact Terraform AWS resource or data-source type verified against "
            "the provider schema."
        )
    )

    region: str | None = Field(
        default=None,
        description=(
            "Required AWS region when this node needs a specific region. "
            "Use null otherwise."
        )
    )

    attributes: dict[str, IIRValue] = Field(
        default={},
        description=(
            "Exact configurable provider attributes and their values."
        )
    )

    blocks: dict[str, list[IIRBlock]] = Field(
        default={},
        description=(
            "Exact nested provider blocks required by this node."
        )
    )

    # This might be duplicate information if constraints are already expressed in attributes or blocks.
    # However, reviewer for example may benefit from these when repairing the code.
    constraints: list[str] = Field(
        default=[],
        description=(
            "Resource-specific requirements that cannot be represented as single attributes or blocks."
        )
    )


class IIRDependency(BaseModel):
    source: str = Field(
        description=(
            "node_id of the resource requiring the explicit dependency."
        )
    )

    target: str = Field(
        description=(
            "node_id of the required resource. Use only when no value reference "
            "already establishes the dependency."
        )
    )


class IIRPlan(BaseModel):
    resources: list[IIRResource] = Field(
        description=(
            "All fully harmonized Terraform resources and data sources."
        )
    )

    dependencies: list[IIRDependency] = Field(
        default=[],
        description=(
            "Explicit dependencies not already represented by value references."
        )
    )

    global_constraints: list[str] = Field(
        default=[],
        description=(
            "Requirements that must remain true for the infrastructure plan as a whole."
        )
    )