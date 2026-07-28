import os
from dotenv import load_dotenv
from azure.identity import AzureCliCredential, get_bearer_token_provider
from openai import AzureOpenAI

load_dotenv()

AOAI_ENDPOINT = "https://hello-foundry-muthu.openai.azure.com/"

token_provider = get_bearer_token_provider(
    AzureCliCredential(),
    "https://cognitiveservices.azure.com/.default",
)

client = AzureOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
)

resp = client.embeddings.create(
    model=os.environ["EMBEDDING_DEPLOYMENT"],
    input=["hello world"],
)
print("SUCCESS! Vector length:", len(resp.data[0].embedding))