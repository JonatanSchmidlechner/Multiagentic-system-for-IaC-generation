from .schemas import IIRPlan, PlannerPlan

from .agents.planner import planner
from .agents.providerHarmonizer import provider_harmonizer
from .agents.generator import iac_generator
from .agents.reviewer import reviewer
from .schema_retrieval import retrieve_provider_schemas_object

def run_true_mas(model, task_prompt, policy_file, aws_docs_context, evaluator, uuid_1, aws_provider_schemas):
    print("Retrieved AWS docs context for Planner:")
    print(aws_docs_context)
    planner_response = planner(model, task_prompt, aws_docs=aws_docs_context)
    print("Planner response:")
    print(planner_response.text)
    planner_plan = PlannerPlan.model_validate_json(planner_response.text)
    planner_plan_text = planner_plan.model_dump_json()

    provider_candidate_schemas_object = retrieve_provider_schemas_object(planner_plan, aws_provider_schemas)
    provider_harmonizer_response = provider_harmonizer(
        model,
        planner_plan_text,
        provider_candidate_schemas_object
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