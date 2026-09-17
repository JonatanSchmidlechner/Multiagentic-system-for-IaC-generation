from .schemas import IIRPlan

from .agents.planner import planner
from .agents.providerHarmonizer import provider_harmonizer
from .agents.generator import iac_generator
from .agents.reviewer import reviewer

def run_true_mas(model, task_prompt, policy_file, aws_docs_context, evaluator, uuid_1):
    print("Retrieved AWS docs context for Planner:")
    print(aws_docs_context)
    planner_response = planner(model, task_prompt, aws_docs=aws_docs_context)
    print("Planner response:")
    print(planner_response.text)
    initial_iir_json = IIRPlan.model_validate_json(planner_response.text)

    provider_harmonizer_response = provider_harmonizer(
        model,
        initial_iir_json,
        schemas={}
    )
    print("Final I-IR after provider harmonization:")
    print(provider_harmonizer_response.text)

    final_iir_json = IIRPlan.model_validate_json(provider_harmonizer_response.text)

    iac_generator_response = iac_generator(
        model,
        final_iir_json
    )
    terraform_code = iac_generator_response.text
    print("Initial Terraform code generated:")
    print(terraform_code)

    MAX_REPAIR_ATTEMPTS = 3
    for attempt in range(MAX_REPAIR_ATTEMPTS):
        validation = evaluator(
            terraform_code,
            policy_file,
            task_prompt,
            uuid_1,
        )
        terraform_success = validation["terraform_plan_success"]
        opa_success = (
            validation["opa_evaluation_result"] == "Success"
        )

        if terraform_success and opa_success:
            break

        fix_plan = reviewer(
            model,
            terraform_code,
            validation,
        )

        iac_generator_response = iac_generator(
            model,
            final_iir_json,
            previous_code=terraform_code,
            fix_plan=fix_plan,
        )
        terraform_code = iac_generator_response.text
    return {
        "terraform_code": terraform_code,
        "evaluation_result": validation,
    }