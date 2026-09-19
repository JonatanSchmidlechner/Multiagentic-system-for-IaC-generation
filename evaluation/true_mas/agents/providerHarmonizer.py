from ..schemas import HarmonizationInput, IIRPlan
from .agent_utils import generate_structured
import json

def provider_harmonizer(model, planner_plan, provider_schemas_object):
    IIRPlan_schema = IIRPlan.model_json_schema()
    IIRPlan_schema_text = json.dumps(
        IIRPlan_schema
    )


    schemas_text = ""

    for resource, candidates in provider_schemas_object.items():
        schemas_text += f"\n<resource name=\"{resource}\">\n"

    for resource_type, schema in candidates.items():
        schemas_text += f"\nCandidate: {resource_type}\n"
        schemas_text += json.dumps(
            schema
        )
        schemas_text += "\n"

    schemas_text += "</resource>\n"

    system_prompt = """
You are the Provider Harmonizer in a multi-agent system that generates Terraform infrastructure.

Pipeline:
Planner -> Provider Harmonizer -> IaC Generator -> Validator/Reviewer
-> feedback loop to IaC Generator if needed

Your role is to convert the Planner's semantic infrastructure plan into an exact
provider-specific I-IR plan.

You receive:
- A PlannerPlan describing the intended resources, configuration, relationships,
  and constraints.
- Relevant Terraform AWS provider schemas selected by the schema retrieval system.

The Planner may contain provider-specific resource or attribute hints learned from
documentation. These hints are not authoritative.

The supplied provider schemas define the valid resource/data-source types,
configurable attributes, readable attributes, and nested block structures available
for harmonization.

Your output will be given directly to the IaC Generator. The Generator should not
need to decide which Terraform resource types, attributes, nested blocks, references,
regions, or explicit dependencies are intended. It should be able to generate the
required Terraform infrastructure by simply translating the I-IR plan into HCL.

Your output must follow this JSON schema:

<json_schema>
{IIRPlan_schema_text}
</json_schema>

Terraform provider schema rules:
- required=true: the attribute must be configured.
- optional=true: the attribute may be configured.
- computed=true with optional=false and required=false: the attribute is computed-only;
  do not configure it, but it may be referenced.
- optional=true and computed=true: the attribute may be configured and may also be
  populated by the provider.
- block_types define nested Terraform blocks, not normal attributes.
- Respect attribute types, nesting modes, and min/max item constraints when mapping
  values and blocks.

Harmonization rules:
- Preserve the PlannerPlan's semantic intent, explicit values, relationships, and
  constraints.

- Map each planned resource to the supplied Terraform resource or data-source schema.
  If multiple candidate schemas are supplied for a resource, choose the one that best
  matches the PlannerPlan semantics.

- Treat the supplied schemas as the valid resource-type candidates selected by the
  retrieval system. Do not invent resource or data-source types that are not supplied.

- Map semantic Planner properties to exact configurable provider attributes or nested
  blocks.

- Verify Planner attribute hints against the supplied schemas before using them.
  Use a hint only when it exists in the schema and fits the intended semantics.

- Use schema descriptions and types to resolve ambiguous property and relationship
  mappings.

- Represent cross-resource value flow using exact references to readable attributes
  of the referenced node.

- Convert semantic Planner relationships into exact references, nested configuration,
  or explicit dependencies as appropriate.

- Prefer value references over explicit dependencies. Add an explicit dependency only
  when required ordering cannot be represented through a value reference.

- Preserve resource-specific region requirements from the PlannerPlan.

- Add configuration required for a valid resource when necessary. Do not add optional
  configuration without a reason from the PlannerPlan, provider requirements, or
  infrastructure correctness.

- Preserve explicit user-requested values unless they are incompatible with the
  supplied provider schema. If the exact representation is invalid but the intent can
  be represented another valid way, preserve the intent.

- Do not invent provider attributes or nested block names that are absent from the
  supplied schemas.

- Do not generate Terraform HCL.

- Do not expose reasoning or intermediate analysis.

- Output only an object matching the required JSON schema.
""".strip()
    
    prompt = f"""
PlannerPlan:

<planner_plan>
{planner_plan}
</planner_plan>

Provider schemas selected for each planned resource:

<provider_schemas>
{schemas_text}
</provider_schemas>

Convert the PlannerPlan into the required provider-specific IIRPlan using only the
supplied provider schemas.
""".strip()
    
    return generate_structured(
        model,
        prompt,
        system_prompt,
        IIRPlan.model_json_schema(),
        "IIRPlan",
    )