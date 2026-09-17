from .agent_utils import generate_structured
from ..schemas import IIRPlan

def planner(model, task_prompt, aws_docs=""):
  system_prompt = """
  You are an Infrastructure-as-Code planning agent.

Convert the user's AWS infrastructure request into a structured
Infrastructure Intermediate Representation (I-IR).

Your plan must:
- identify all infrastructure resources that are needed;
- include supporting resources even when the user did not explicitly mention
  them, when they are required to make the infrastructure work;
- identify important attributes and constraints;
- identify dependencies between resources;
- preserve useful AWS service hints such as EFS, S3, Lambda, RDS, etc.;
- provide useful keywords for later Terraform resource-schema retrieval;
- NOT invent exact Terraform resource_type names unless they are obvious.
  Provider-specific Terraform naming is mainly the Harmonizer's job.

Use the supplied AWS documentation context when relevant.
""".strip()

  prompt = f"""
USER TASK:
{task_prompt}
AWS DOCUMENTATION CONTEXT:
{aws_docs if aws_docs else "(No RAG context supplied yet.)"}
Create the initial I-IR plan.
""".strip()
  
  return generate_structured(
      model,
      prompt,
      system_prompt,
      IIRPlan.model_json_schema(),
      "IIRPlan",
  )