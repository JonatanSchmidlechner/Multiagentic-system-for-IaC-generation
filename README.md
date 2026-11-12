
# Multi-Agent Code-Orchestrated Generation for Reliable Infrastructure-as-Code (IaC‑Eval)

This repository evaluates our multi-agent approach that turns natural language intents into reliable Terraform HCL using IaC‑Eval. IaC-Eval is a comprehensive framework for quantitatively evaluating the capabilities of large language models in cloud IaC code generation. Infrastructure-as-Code (IaC) is an important component of cloud computing, that allows the definition of cloud infrastructure in high-level programs. Our framework targets Terraform specifically for now.

IaC-Eval also provides the first human-curated and challenging Infrastructure-as-Code (IaC) dataset containing 458 questions ranging from simple to difficult across various cloud services (targeting AWS for now), which can be found in our [HuggingFace repository](https://huggingface.co/datasets/autoiac-project/iac-eval).

## My contribution
This repository is based on an existing benchmark. My primary contribution was implementing TRUE-MAS configuration for the benchmark. I also made it possible to run multiple configurations using 1 command. Additionally, I changed the benchmark to run the language models locally (or to run in our own cloud servers) instead of in 3rd party cloud providers' servers.

## Architecture

TRUE-MAS generates and validates Terraform configurations from natural language prompts using a four-agent pipeline paired with deterministic verification tools. Instead of generating code in a single pass, the system separates planning, schema checking, code generation, and error repair into distinct steps.

### Agents

* **Planner:** Breaks down the prompt into a structured infrastructure plan, identifying the required AWS resources and dependencies.
* **Provider Harmonizer:** Maps the planned resources against official AWS provider schemas so invalid arguments or resource types are caught before code generation.
* **IaC Generator:** Writes the Terraform HCL code from the validated plan, and applies targeted fixes during repair iterations.
* **Reviewer:** Inspects Terraform and policy error messages when validation fails, diagnoses the issue, and produces a fix plan for the Generator.

### Tools

* **LlamaIndex RAG:** Retrieves relevant chunks from indexed AWS Terraform documentation to give the Planner accurate resource context.
* **AWS Provider Schema Lookup:** Queries the Terraform AWS provider schema (`v5.75.0`) to supply valid resource attributes and block definitions to the Harmonizer.
* **Terraform CLI (`plan`):** Validates HCL syntax, provider versions, and resource references, compiling an execution plan (`plan.json`).
* **Open Policy Agent (OPA):** Evaluates `plan.json` against Rego policies to verify that the generated infrastructure satisfies functional and compliance rules.

### Execution Flow

1. **Plan & Ground:** The **Planner** drafts the resource layout using **LlamaIndex RAG**, and the **Provider Harmonizer** verifies the resources against the **AWS Provider Schema**.
2. **Generate:** The **IaC Generator** produces the Terraform HCL code.
3. **Verify & Repair:** **Terraform** and **OPA** validate the code. If either check fails, the **Reviewer** diagnoses the error and sends a fix plan back to the **IaC Generator** (up to 3 repair attempts).

## TRUE-MAS INSTALLATION AND USAGE GUIDE

Here are the instructions what is needed to run the local models. A lot of the instructions below are required for LLMs but not needed for local SLMs. If something does not work, then refer to the other instructions as I may have forgot something.

1. The environment does not work on Winodws. Use Linux (I have used Ubuntu with WSL).
2. Install Terraform
3. Install Opa. The latest versions don't work. I have version 0.70.0. Add OPA to path.
4. Install Anaconda
5. Create the conda environment:
Use the following command in project root:
```shell
   conda env create -f environment-py311.yml
   ```
Note: before `conda activate` you might need to do `conda init SHELL_NAME` on your preferred shell (e.g. `conda init bash`). If you run into problems initializing the shell session, try referring to [this GitHub issue](https://github.com/conda/conda/issues/13423#issuecomment-2113968807) for a fix.

6. Preconfigure the retriever database: refer to instructions in `retriever/README.md`.
7. Create .env file to repository root and add the API_KEY and BASE_URL according to the .env_example

## TRUE-MAS USAGE GUIDE
See more instructions in `evaluation/README.md` for more details about scripts.
All commands assume you are in the `evaluation` directory, and that you have activated the env:

1. Script to run true-MAS using a medium sized subset of the dataset. Remove --sampled to use the whole dataset.
```shell
python3 eval.py --config=config.json -e true-MAS --sampled
   ```
Use --quick-test to test the pipeline with 2 dataset rows.
```shell
python3 eval.py --config=config.json -e true-MAS --quick-test
   ```
config.json contains the used model name and sample size.

NOTE: The pipeline can not be run if there are existing evaluation results for the same model in tmp/ or in results/.

2. Get evaluation results by running the following script:
```shell
python3 misc/ablation/ablation-iac-eval-pipeline.py
   ```
3. See the TRUE-MAS specific logs in true_mas/true_mas_debug.log.

## Run Experiment with multiple models and methods
You can use a single command to run a multi-run experiment testing multiple models with each of the specified methods. The ablation script for showing final results is run automatically here after the experiment is finished.

Below is an example command, which uses the whole dataset. Use --sampled for a smaller subset or use --quick-test for a subset of 2 rows for each model + method run.
```shell
python3 run_experiment.py \
  --models 'llama3.1:8b,llama3.2:latest,deepseek-r1:7b,qwen2.5-coder:7b,starcoder2:7b' \
  --methods 'RAW,RAG,COT,FSP,multi-turn,multi-agent,true-MAS' \
  --samples 1
   ```

Each experiment automatically gets an unique based on timestamp. The results are stored in results/<experiment id>. If your experiment gets interrupted, you can continue the experiment by adding the correct id with --experiment-id <id> to the run_experiment command. You can also add new models to the experiment later the same way.

run_experiment.py automatically checks that each specified model can be reached before starting the main benchmark. However, It is still suggested to use quick-test to check that new models work properly. Check that the final results look ok in quick-test.
## Acknowledgments

<https://github.com/openai/human-eval/tree/master>
