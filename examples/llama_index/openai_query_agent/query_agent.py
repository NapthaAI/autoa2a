import os
import asyncio
from typing import Dict, Any
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, AgentStream
from llama_index.core.tools import QueryEngineTool
from llama_index.core.query_engine import NLSQLTableQueryEngine, RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.vector_stores import MetadataInfo, VectorStoreInfo
from llama_index.readers.wikipedia import WikipediaReader
from llama_index.core.workflow import Context
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from llama_index.core import SQLDatabase
from dotenv import load_dotenv
import time

load_dotenv()

class QueryAgent:
    def __init__(self, openai_model: str = "gpt-4o-mini"):
        Settings.llm = OpenAI(model=openai_model)
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        Settings.node_parser = TokenTextSplitter(chunk_size=1024)

        self.pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        self._setup_pinecone_index()
        self._setup_sql_database()
        self._setup_vector_store()
        self._setup_query_engines()
        
        self.agent = FunctionAgent(
            tools=[self.sql_tool, self.vector_tool],
            llm=OpenAI(model="gpt-4o-mini"),
        )
        self.ctx = Context(self.agent)

    def _setup_pinecone_index(self):
        """Set up Pinecone index for vector storage."""
        if "quickstart-sql" not in self.pc.list_indexes().names():
            self.pc.create_index(
                name="quickstart-sql",
                dimension=1536,
                metric="euclidean",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            time.sleep(10)
        
        self.index = self.pc.Index("quickstart-sql")

    def _setup_sql_database(self):
        """Set up SQL database with city statistics."""
        engine = create_engine("sqlite:///:memory:", future=True)
        metadata_obj = MetaData()
        
        # Create city SQL table
        city_stats_table = Table(
            "city_stats",
            metadata_obj,
            Column("city_name", String(16), primary_key=True),
            Column("population", Integer),
            Column("country", String(16), nullable=False),
        )
        metadata_obj.create_all(engine)
        
        # Insert sample data
        rows = [
            {"city_name": "Toronto", "population": 2930000, "country": "Canada"},
            {"city_name": "Tokyo", "population": 13960000, "country": "Japan"},
            {"city_name": "Berlin", "population": 3645000, "country": "Germany"},
        ]
        for row in rows:
            with engine.begin() as connection:
                connection.execute(city_stats_table.insert().values(**row))
        
        self.sql_database = SQLDatabase(engine, include_tables=["city_stats"])

    def _setup_vector_store(self):
        """Set up vector store with city information from Wikipedia."""
        vector_store = PineconeVectorStore(
            pinecone_index=self.index, 
            namespace="wiki_cities"
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        self.vector_index = VectorStoreIndex([], storage_context=storage_context)
        
        # Check if we already have data in Pinecone
        try:
            stats = self.index.describe_index_stats()
            if stats['total_vector_count'] > 0:
                return
        except Exception as e:
            print(f"Error checking Pinecone data: {e}")
        
        # Load and index city information from Wikipedia
        cities = ["Toronto", "Berlin", "Tokyo"]
        wiki_docs = WikipediaReader().load_data(pages=cities)
        
        for city, wiki_doc in zip(cities, wiki_docs):
            nodes = Settings.node_parser.get_nodes_from_documents([wiki_doc])
            for node in nodes:
                node.metadata = {"title": city}
            self.vector_index.insert_nodes(nodes)

    def _setup_query_engines(self):
        """Set up SQL and vector query engines with their respective tools."""
        # SQL query engine
        self.sql_query_engine = NLSQLTableQueryEngine(
            sql_database=self.sql_database,
            tables=["city_stats"],
        )
        
        # Vector query engine
        vector_store_info = VectorStoreInfo(
            content_info="articles about different cities",
            metadata_info=[
                MetadataInfo(
                    name="title", 
                    type="str", 
                    description="The name of the city"
                ),
            ],
        )
        vector_auto_retriever = VectorIndexAutoRetriever(
            self.vector_index, 
            vector_store_info=vector_store_info
        )
        self.retriever_query_engine = RetrieverQueryEngine.from_args(
            vector_auto_retriever,
        )
        
        # Create tools
        self.sql_tool = QueryEngineTool.from_defaults(
            query_engine=self.sql_query_engine,
            name="sql_tool",
            description=(
                "Useful for translating a natural language query into a SQL query over"
                " a table containing: city_stats, containing the population/country of"
                " each city"
            ),
        )
        self.vector_tool = QueryEngineTool.from_defaults(
            query_engine=self.retriever_query_engine,
            name="vector_tool",
            description=(
                "Useful for answering semantic questions about different cities"
            ),
        )

    def get_agent(self):
        return self.agent

async def main():
    agent = QueryAgent().get_agent()
    
    # Example queries
    queries = [
        "Tell me about the arts and culture of the city with the highest population.",
        "Tell me about the history of Berlin",
        "Can you give me the country corresponding to each city you know?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        handler = agent.run(query, ctx=Context(agent))
        response = await handler
        print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())