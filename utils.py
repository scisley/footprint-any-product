from dotenv import load_dotenv
from pathlib import Path
import os
from psycopg_pool import ConnectionPool
# from langchain_openai import OpenAIEmbeddings
# from langchain_postgres import PGVector

def load_env(dir='.'):
    # Load environment variables from .env.local file
    env_path = Path(dir) / '.env.local'
    load_dotenv(dotenv_path=env_path)

load_env()

DB_URI = os.environ['DB_DEV_CONNECTION']
# embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
# vector_store = PGVector(
#     embeddings=embeddings,
#     collection_name="my_docs",
#     connection=DB_URI.replace("postgresql","postgresql+psycopg"),
# )
pool = ConnectionPool(
        conninfo=DB_URI,
        max_size=20,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
        }
    )
