from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage,AIMessage,HumanMessage
from pydantic import BaseModel
import hello as Base

load_dotenv()

query = "Explain python for Ai scuffolding in 100 words"

client = ChatOpenAI(
    base_url= Base.BASE_URL,
    model=Base.MODEL,
    api_key=Base.API_KEY
) 

message = [HumanMessage(query)]

print(client.invoke(message).content)