import hello as Base    

query1 = "What is 2 + 5"
query2 = "what numbers did i ask the ans for?"
queries = [query1,query2,"who is messi","who is cristiano ronaldo","who has a worldcup between them?","who has more goals?"]

messages = [{"role": "system", "content": "You are a helpful assistant."}]


def call_LLm(query) -> str:
    print(f"Query: {query}")
    messages.append({"role":"user","content":query})
    res = Base.client.chat.completions.create(
        model = Base.MODEL,
        messages = messages
    )
    messages.append({"role":"assistant", "content":res.choices[0].message.content})
    print(f"Message Length So Far {len(messages)}")
    return res.choices[0].message.content

for str in queries:
    ress = call_LLm(str)
    print(ress)