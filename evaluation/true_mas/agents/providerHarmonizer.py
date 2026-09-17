from ..schemas import HarmonizationInput, IIRPlan
from .agent_utils import generate_structured

def provider_harmonizer(model, initial_plan, schemas=None):
    harmonization_input = HarmonizationInput(
        plan=initial_plan,
        schemas=schemas or {},
    )

    system_prompt = """
You are a Terraform AWS provider harmonization agent.

You receive:
1. an abstract I-IR infrastructure plan;
2. zero or more candidate Terraform resource types and schemas for
   each abstract resource.

Your job is to produce a provider-specific final I-IR plan.

For every resource:
- select the most appropriate Terraform AWS resource_type from the supplied
  candidates when possible;
- use the supplied provider schema to correct and refine attributes;
- preserve the resource's original intent and constraints;
- add provider-specific supporting resources when necessary;
- preserve or update dependencies;
- do not use attributes that conflict with the supplied schema.

Do not generate HCL. Return only the final I-IR plan.
""".strip()
    
    prompt = f"""
HARMONIZATION INPUT:
{harmonization_input.model_dump_json(indent=2)}

Produce the final provider-specific I-IR plan.
""".strip()
    
    return generate_structured(
        model,
        prompt,
        system_prompt,
        IIRPlan.model_json_schema(),
        "IIRPlan",
    )