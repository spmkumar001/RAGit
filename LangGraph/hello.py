import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

query = "Who is messi? Describe in one word"
API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
BASE_URL = os.environ["AZURE_OPENAI_ENDPOINT"] + "openai/v1/"
MODEL = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]

client = OpenAI(
    api_key= os.environ["AZURE_OPENAI_API_KEY"],
    base_url= os.environ["AZURE_OPENAI_ENDPOINT"] + "openai/v1/"
)

resp = client.chat.completions.create(
    model= os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
    messages=[
        {"role":"system","content":"Answer like a hater"},
        {"role":"user","content":query}
    ]
)

if __name__ == "__main__":
    print(resp.choices[0].message.content)
