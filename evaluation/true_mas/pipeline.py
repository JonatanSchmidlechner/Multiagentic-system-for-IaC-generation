from .schemas import IIRPlan, PlannerPlan, FixPlan

from .agents.planner import planner
from .agents.providerHarmonizer import provider_harmonizer
from .agents.generator import iac_generator
from .agents.reviewer import reviewer
from .schema_retrieval import retrieve_provider_schemas_object
from output_utils import separate_answer_and_code, DELIMITERS
import json
from .logger import mas_logger

def run_true_mas(model, task_prompt, policy_file, aws_docs_context, evaluator, uuid_1, aws_provider_schemas):
    planner_response = planner(model, task_prompt, aws_docs=aws_docs_context)
    planner_plan = PlannerPlan.model_validate_json(planner_response.text)
    planner_plan_text = planner_plan.model_dump_json()
    planner_plan_debug = json.dumps(
        planner_plan.model_dump(),
        indent=2
    )
    mas_logger.debug("Task prompt:\n%s", task_prompt)
    mas_logger.debug("Retrieved AWS docs:\n%s", aws_docs_context)
    mas_logger.debug("PlannerPlan:\n%s", planner_plan_debug)
    provider_candidate_schemas_object = retrieve_provider_schemas_object(planner_plan, aws_provider_schemas)
    provider_harmonizer_response = provider_harmonizer(
        model,
        planner_plan_text,
        provider_candidate_schemas_object
    )

    final_iir = IIRPlan.model_validate_json(provider_harmonizer_response.text)
    final_iir_text = final_iir.model_dump_json()
    final_iir_debug = json.dumps(
        final_iir.model_dump(),
        indent=2
    )

    selected_schema_names = {
        node_id: list(candidates.keys())
        for node_id, candidates in provider_candidate_schemas_object.items()
    }
    mas_logger.debug("Selected provider schemas: %s", selected_schema_names)
    mas_logger.debug("Final IIR:\n%s", final_iir_debug)
    iac_generator_response = iac_generator(
        model,
        final_iir_text
    )
    terraform_raw_code = iac_generator_response.text
    answer, terraform_code = separate_answer_and_code(terraform_raw_code, DELIMITERS)
    mas_logger.debug("Generated Terraform:\n%s", terraform_code)
    validation = evaluator(
        terraform_code,
        policy_file,
        task_prompt,
        uuid_1,
    )
    MAX_REPAIR_ATTEMPTS = 3
    for attempt in range(MAX_REPAIR_ATTEMPTS):
        terraform_success = validation["terraform_plan_success"]
        opa_success = (
            validation["opa_evaluation_result"] == "Success"
        )
        validation_error = None
        if not terraform_success:
            validation_error = validation["terraform_plan_error"]
            mas_logger.info(
                "Terraform validation failed on repair attempt %d",
                attempt
            )
        elif not opa_success:
            validation_error = validation["opa_evaluation_error"]
            mas_logger.info(
                "OPA validation failed on repair attempt %d",
                attempt
            )
        else:
            break
        mas_logger.debug("Validation error:\n%s", validation_error)
        reviewer_response  = reviewer(
            model,
            terraform_code,
            validation_error,
            final_iir_text
        )
        fix_plan = FixPlan.model_validate_json(
            reviewer_response.text
        )
        fix_plan_text = fix_plan.model_dump_json()
        fix_plan_debug = json.dumps(
            fix_plan.model_dump(),
            indent=2
        )
        mas_logger.debug("FixPlan:\n%s", fix_plan_debug)

        iac_generator_response = iac_generator(
            model,
            final_iir,
            previous_code=terraform_code,
            fix_plan=fix_plan_text,
        )
        terraform_raw_code = iac_generator_response.text
        answer, terraform_code = separate_answer_and_code(terraform_raw_code, DELIMITERS)
        validation = evaluator(
                terraform_code,
                policy_file,
                task_prompt,
                uuid_1,
        )
        mas_logger.debug("Generated Terraform:\n%s", terraform_code)

    mas_logger.info(
        "Final result: terraform_success=%s, opa_result=%s",
        validation["terraform_plan_success"],
        validation["opa_evaluation_result"],
    )
    return {
        "terraform_code": terraform_code,
        "evaluation_result": validation,
        "raw_answer": terraform_raw_code
    }