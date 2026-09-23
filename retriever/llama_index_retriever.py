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
    def __init__(self, max_tokens=2000, stored_index = None, path = None, llm=None, generate_fn=None):
        self.llm = llm
        self.generate_fn = generate_fn
        self.max_tokens = max_tokens
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

        response = self.generate_fn(
            self.llm,
            formatted_prompt,
            agent_name="retriever",
                                     )
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
    retriever = Retriever(stored_index='aws-index', path='terraform-provider-aws/website/docs/r', llm=effgen_model)