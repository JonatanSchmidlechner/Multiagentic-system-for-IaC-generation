from .agent_utils import generate

def iac_generator(model, final_plan, previous_code=None, fix_plan=None):
    system_prompt = """
You are a Terraform code generation agent.

Generate one complete Terraform configuration from the supplied final I-IR plan.

Requirements:
- output Terraform HCL only;
- include all resources from the plan;
- respect dependencies and constraints;
- use only provider-specific resource types and attributes from the plan;
- make references between resources correctly;
- include provider configuration when needed;
- do not wrap the answer in Markdown fences.
""".strip()

    prompt = f"""
FINAL I-IR PLAN:
{final_plan}
"""

    if previous_code is not None and fix_plan is not None:
        prompt += f"""

PREVIOUS TERRAFORM CODE:
{previous_code}

TARGETED FIX PLAN:
{fix_plan}

Correct the previous Terraform configuration.
Make only the changes needed to address the fix plan.
Return the complete corrected Terraform configuration.
"""
    else:
        prompt += """

Generate the complete Terraform configuration.
"""

    full_prompt = f"""
SYSTEM INSTRUCTIONS:
{system_prompt}

USER INPUT:
{prompt}
""".strip()

    return generate(
        model=model,
        prompt=full_prompt
    )