
# Multi-Agent Code-Orchestrated Generation for Reliable Infrastructure-as-Code (IaC‑Eval)

This repository evaluates our multi-agent approach that turns natural language intents into reliable Terraform HCL using IaC‑Eval. IaC-Eval is a comprehensive framework for quantitatively evaluating the capabilities of large language models in cloud IaC code generation. Infrastructure-as-Code (IaC) is an important component of cloud computing, that allows the definition of cloud infrastructure in high-level programs. Our framework targets Terraform specifically for now. We leave integration of other IaC tools as future work. 

IaC-Eval also provides the first human-curated and challenging Infrastructure-as-Code (IaC) dataset containing 458 questions ranging from simple to difficult across various cloud services (targeting AWS for now), which can be found in our [HuggingFace repository](https://huggingface.co/datasets/autoiac-project/iac-eval).

**We are actively developing and patching the project. However, as of now, IaC-Eval is not production-ready.** 

## TRUE-MAS INSTALLATION AND USAGE GUIDE

Here are the instructions what is needed to run the local models. A lot of the instructions below are required for LLMs but not needed for local SLMs. If something does not work, then refer to the other instructions as I may have forgot something.

1. The environment does not work on Winodws. Use Linux (I have used Ubuntu with WSL).
2. Install Terraform
3. Install Opa. The latest versions don't work. I have version 0.70.0. Add OPA to path.
4. Install Anaconda
5. Create the conda environment: (This environment is specifically for true-MAS. True-MAS required a python version upgrade, which caused dependency problems. I think MACOG with local SLMs still work, but I had to remove some dependencies, which may have broken the use of the LLMs.)
Use the following command in project root:
```shell
   conda env create -f environment-py311.yml
   ```
Note: before `conda activate` you might need to do `conda init SHELL_NAME` on your preferred shell (e.g. `conda init bash`). If you run into problems initializing the shell session, try referring to [this GitHub issue](https://github.com/conda/conda/issues/13423#issuecomment-2113968807) for a fix.
6. Preconfigure the retriever database: refer to instructions in `retriever/README.md`.
7. Create .env file to repository root and add the API_KEY and BASE_URL according to the .env_example

# TRUE-MAS USAGE GUIDE
See more instructions in `evaluation/README.md` for more details about scripts.
All commands assume you are in the `evaluation` directory, and that you have activated the env:

1. Script to run true-MAS using a medium sized subset of the dataset. Remove --sampled to use the whole dataset.
python3 eval.py --config=config.json -e true-MAS --sampled

Use --quick-test to test the pipeline with 2 dataset rows.
python3 eval.py --config=config.json -e true-MAS --quick-test

config.json contains the used model name and sample size.

NOTE: The pipeline can not be ran if there are existing evaluation results for the same model in tmp/ or in results/.

2. Get evaluation results by running the following script:
python3 misc/ablation/ablation-iac-eval-pipeline.py

3. See the TRUE-MAS specific logs in true_mas/true_mas_debug.log.
## Installation

1. Install Terraform (also [install AWS CLI and setup credentials](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-build#prerequisites))
2. Install [Opa](https://www.openpolicyagent.org/docs/latest/#1-download-opa) (make sure to add opa to path and we used opa version: 0.46.0).
3. <sup>*</sup>Obtain the following LLM model inference API keys as appropriate, depending on which of our currently supported models you want to perform evaluation on:
- [OpenAI API token](https://platform.openai.com/docs/quickstart/account-setup): for GPT-3.5-Turbo and GPT-4
- [Google API token](https://ai.google.dev/gemini-api/docs/quickstart?lang=python#set-up-api-key): for Gemini-1.0-Pro
- [Replicate API token](https://replicate.com/): for CodeLlama and WizardCoder variants

<sup>*</sup> Our evaluation against MagiCoder was performed on a manually deployed AWS SageMaker instance inference endpoint. We provide more details on our setup script, see `evaluation/README.md`, if that is of interest.  

### Using the Evaluation Pipeline

To access and utilize the evaluation pipeline, you need to switch to a specific branch of this repository and set up the environment. Follow these steps:

1. Ensure you have the `main` branch of the project checked out.

2. Install the Conda environment by running:

   ```shell
   conda env create -f environment.yml
   ```

3. Activate the newly created Conda environment named `iac-eval`:

   ```shell
   conda activate iac-eval
   ```

   Note: before `conda activate` you might need to do `conda init SHELL_NAME` on your preferred shell (e.g. `conda init bash`). If you run into problems initializing the shell session, try referring to [this GitHub issue](https://github.com/conda/conda/issues/13423#issuecomment-2113968807) for a fix.
 
4. (Optional) Preconfigure the retriever database (if you would like to use the RAG strategy): refer to instructions in `retriever/README.md`.

5. See instructions in `evaluation/README.md` for details on how to use the main pipeline: `eval.py`, and other scripts.

Note: You can run `./setup.sh` to check if you have Terraform and OPA installed. It will also create and activate the necessary conda environment. The shell script assumes you are using `bash`, change `#!/bin/SHELL` to your preferred shell in the script.




## Acknowledgments

<https://github.com/openai/human-eval/tree/master>
