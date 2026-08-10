import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AZURE_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]              # <-- add: bare host for embeddings
BASE_URL = os.environ["AZURE_OPENAI_ENDPOINT"] + "openai/v1/"
MODEL = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
EMBEDDING_MODEL = os.environ["AZURE_EMBEDDING_DEPLOYMENT"]
EMBEDDING_API_VERSION = "2024-10-21"

LANGSMITH_TRACING=os.environ["LANGSMITH_TRACING"]
LANGSMITH_API_KEY=os.environ["LANGSMITH_API_KEY"]
LANGSMITH_PROJECT=os.environ["LANGSMITH_PROJECT"]