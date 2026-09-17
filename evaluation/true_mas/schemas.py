from typing import Any
from pydantic import BaseModel


class IIRReference(BaseModel):
    attribute: str
    resource_id: str
    resource_attribute: str

class IIRResource(BaseModel):
    id: str
    kind: str
    keywords: list[str] = []

    service_hint: str | None = None
    resource_type: str | None = None

    attributes: dict[str, Any] = {}
    references: list[IIRReference] = []

    constraints: list[str] = []

class IIRDependency(BaseModel):
    source: str
    target: str
    relation: str = "depends_on"


class IIRPlan(BaseModel):
    resources: list[IIRResource]
    dependencies: list[IIRDependency] = []
    global_constraints: list[str] = []


class HarmonizationCandidate(BaseModel):
    resource_type: str
    schema: dict[str, Any] = {}


class HarmonizationInput(BaseModel):
    plan: IIRPlan
    candidates: dict[str, list[HarmonizationCandidate]] = {}


class ToolFeedback(BaseModel):
    success: bool
    terraform_validate: str = ""
    terraform_plan: str = ""
    opa: str = ""


class FixPlan(BaseModel):
    summary: str
    changes: list[str] = []
