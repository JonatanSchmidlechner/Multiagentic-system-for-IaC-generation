import os
import logging
import sys
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from effgen import load_model

class Retriever:
    def __init__(self, stored_index = None, path = None, llm=None):
        self.llm = llm
        self.embed_model = HuggingFaceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B"
        )
        self.index = self.retrieve_documents(stored_index, path)

    def retrieve_documents(self, stored_index = None, path = None):
        Settings.embed_model = self.embed_model
        if os.path.exists(stored_index):
            print("Loading index from storage")
            storage_context = StorageContext.from_defaults(persist_dir=stored_index)
            index = load_index_from_storage(storage_context)
        else: 
            print("Building index from scratch")
            nodes = self.read_docs(path)
            index = self.build_index(nodes)
            index.storage_context.persist(persist_dir=stored_index)
        return index 

    def read_docs(self, path = "terraform-provider-aws/website/docs/r"):
        
        documents = SimpleDirectoryReader(
            path
        ).load_data()

        # parser = MarkdownNodeParser()
        
        splitter = TokenTextSplitter(
            chunk_size=400,
            chunk_overlap=20,
            separator=" ",
        )
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"Read {len(documents)} documents")
        print(f"Extracted {len(nodes)} nodes")
        return nodes

    def build_index(self, nodes):
        index = VectorStoreIndex(nodes, show_progress=True)
        return index

    def generate_prompt_for_index(self, query, num_queries=10):
        # The prompt is not necessary 
        QUERY_GEN_PROMPT = (
            "You are a helpful assistant that generates multiple search queries based on a "
            "single input query. Generate {num_queries} search queries, one on each line, "
            "related to the following input query:\n"
            "Query: {query}\n"
        )
        formatted_prompt = QUERY_GEN_PROMPT.format(num_queries=num_queries, query=query)

        response = self.llm.generate(formatted_prompt)
        questions = response.text.split('\n')

        print(questions) 
        return questions
 
    def query_documents(self, questions):
        retriever = self.index.as_retriever()

        context = set()
        for q in questions:
            if not isinstance(q, str) or q == "":
                continue
            nodes = retriever.retrieve(q)
            context.add(nodes[0].text)
        return context

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ["API_KEY"]
    base_url = os.environ["BASE_URL"]
    effgen_model = load_model(
        model_name="llama3.1:8b",
        provider="openai_compatible",
        api_key=api_key,
        base_url=base_url,
        timeout=480,
        max_retries=0,
    )

    retriever = Retriever(stored_index='aws-index', path='terraform-provider-aws/website/docs/r', llm=effgen_model)
    query = '''sets up a VPC with public and private subnets, multiple security groups for different components like master, worker, alert, API, standalone, and database services within an AWS region specified as "cn-north-1". It includes a 5.7, 50GB MySQL database instance within the VPC, accessible and secured by a designated security group.''' 
    questions = retriever.generate_prompt_for_index(query)
    # questions = ['defines an AWS RDS option group named "option-group-pike" with major engine version 11, and use the sqlserver-ee engine. It should have options for "SQLSERVER_AUDIT" and "TDE" ', '', '1. How to create an AWS RDS option group with major engine version 11 and sqlserver-ee engine?', '2. What are the available options for an AWS RDS option group with major engine version 11 and sqlserver-ee engine?', '3. How to add the "SQLSERVER_AUDIT" option to an AWS RDS option group?', '4. How to add the "TDE" option to an AWS RDS option group?', '5. What is the option group description for an AWS RDS option group named "option-group-pike"?', '6. How to set the timezone option for an AWS RDS option group?', '7. How to set the IAM role ARN for the "SQLSERVER_BACKUP_RESTORE" option in an AWS RDS option group?', '8. What are the MariaDB options available for an AWS RDS option group?', '9. What are the Microsoft SQL Server options available for an AWS RDS option group?', '10. What are the MySQL options available for an AWS RDS option group?'] # this caused an error
    context = retriever.query_documents(questions)
    for i, c in enumerate(context):
        print(f'Context {i}:')
        print(c)

    