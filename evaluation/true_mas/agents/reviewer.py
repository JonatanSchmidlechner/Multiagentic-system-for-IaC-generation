from .agent_utils import generate_structured
from ..schemas import FixPlan


def reviewer(model, terraform_code, tool_feedback):
    system_prompt = """
You are a Terraform repair reviewer.

You receive Terraform code and deterministic feedback from tools such as:
- terraform validate;
- terraform plan;
- OPA policy checks.

If the tools report failure, produce a small targeted repair plan for the
Terraform generator.

Do not rewrite the Terraform yourself.
Prefer fixing the concrete reported error rather than redesigning the whole
infrastructure.
""".strip()
    prompt = f"""TERRAFORM CODE:
{terraform_code}
TOOL FEEDBACK:
{tool_feedback}
Create a targeted repair plan.
""".strip()
    
    return generate_structured(
        model,
        prompt,
        system_prompt,
        FixPlan.model_json_schema(),
        "FixPlan",
    )