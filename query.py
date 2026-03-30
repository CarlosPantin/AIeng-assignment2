import os
from dotenv import load_dotenv
from swarm import Swarm, Agent
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("PROXY_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY") 
)
swarm_client = Swarm(client=client)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

def search_literature(query: str):
    docs = vectorstore.similarity_search(query, k=3)
    results = []
    for d in docs:
        source = os.path.basename(d.metadata.get('source', 'Unknown'))
        page = d.metadata.get('page', 'Unknown')
        results.append(f"Content: {d.page_content}\nSource: {source}, Page: {page}\n---")
    return "\n".join(results)

def transfer_to_methods(): return methods_agent
def transfer_to_results(): return results_agent
def transfer_to_skeptical(): return skeptical_agent
def transfer_to_general(): return general_agent

router_agent = Agent(
    name="Router",
    instructions=(
        "You are a routing system. You do not have access to files directly. "
        "Your ONLY job is to delegate the user's question to a specialist by calling a transfer function. "
        "Do not answer the question yourself. "
        "Transfer to 'Methods Analyst' for methods, setup, datasets, or metrics. "
        "Transfer to 'Results Extractor' for results, numbers, or comparisons. "
        "Transfer to 'Skeptical Reviewer' for limitations or critiques. "
        "Transfer to 'General Synthesizer' for everything else."
    ),
    functions=[transfer_to_methods, transfer_to_results, transfer_to_skeptical, transfer_to_general],
    model="openai/gpt-4.1-mini"
)

methods_agent = Agent(
    name="Methods Analyst",
    instructions="You MUST use the 'search_literature' tool to answer questions about methods and setup. Do not ask the user to upload files. Always cite document and page number.",
    functions=[search_literature],
    model="openai/gpt-4.1-mini"
)

results_agent = Agent(
    name="Results Extractor",
    instructions="You MUST use the 'search_literature' tool to answer questions about results and numbers. Do not ask the user to upload files. Always cite document and page number.",
    functions=[search_literature],
    model="openai/gpt-4.1-mini"
)

skeptical_agent = Agent(
    name="Skeptical Reviewer",
    instructions="You MUST use the 'search_literature' tool to answer questions about limitations and threats. Do not ask the user to upload files. Always cite document and page number.",
    functions=[search_literature],
    model="openai/gpt-4.1-mini"
)

general_agent = Agent(
    name="General Synthesizer",
    instructions="You MUST use the 'search_literature' tool to answer general questions. Do not ask the user to upload files. Always cite document and page number.",
    functions=[search_literature],
    model="openai/gpt-4.1-mini"
)

def main():
    print("--- Literature Assistant Ready ---")
    print("(Type 'exit' to stop)\n")
    
    messages = []
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = swarm_client.run(
                agent=router_agent,
                messages=messages
            )
            
            messages = response.messages
            last_message = response.messages[-1]
            
            print(f"\n[{response.agent.name}]: {last_message['content']}\n")
        except Exception:
            messages = []
            print("\n[System]: Error encountered. Session reset. Please ask your question again.\n")

if __name__ == "__main__":
    main()