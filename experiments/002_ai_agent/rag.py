from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

import os

load_dotenv()

# --- Embeddings & LLM ---
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)

# --- PDF Loading ---
pdf_path = "Stock_Market_Performance_2024.pdf"
if not os.path.exists(pdf_path):
    raise FileNotFoundError(f"PDF file not found: {pdf_path}")

pages = PyPDFLoader(pdf_path).load()
print(f"Loaded PDF with {len(pages)} pages")

pages_split = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200
).split_documents(pages)

# --- Vector Store (load if exists, create if not) ---
persist_directory = "./chroma_db"
collection_name = "stock_market"

if os.path.exists(persist_directory) and os.listdir(persist_directory):
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name
    )
    print("Loaded existing vector store")
else:
    os.makedirs(persist_directory, exist_ok=True)
    vectorstore = Chroma.from_documents(
        documents=pages_split,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    print("Created new vector store")

# --- Retriever with MMR ---
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 10, "lambda_mult": 0.7}
)

# --- Tool ---
@tool
def retriever_tool(query: str) -> str:
    """This tool Ssarches the Stock Market Performance 2024 document."""
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant information found."
    return "\n\n".join(f"Document {i+1}:\n{doc.page_content}" 
                       for i, doc in enumerate(docs))

tools = [retriever_tool]
llm_with_tools = llm.bind_tools(tools)

# --- State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

system_prompt = """You are an AI assistant answering questions about Stock Market 
Performance in 2024. Use the retriever tool to find relevant information.
Always cite the specific document sections you use."""

def call_llm(state: AgentState) -> AgentState:
    messages = [SystemMessage(content=system_prompt)] + list(state['messages'])
    return {"messages": [llm_with_tools.invoke(messages)]}

# --- Graph ---
graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("retriever_agent", ToolNode(tools))  

graph.set_entry_point("llm")
graph.add_conditional_edges(
    "llm",
    tools_condition,
    {"tools": "retriever_agent", END: END}  # map its default output to your node name
)
graph.add_edge("retriever_agent", "llm")

rag_agent = graph.compile()

# --- Run ---
def running_agent():
    print("\n=== RAG AGENT ===")
    while True:
        user_input = input("\nYour question (or 'exit'): ")
        if user_input.lower() in ['exit', 'quit']:
            break
        result = rag_agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"recursion_limit": 10}
        )
        print("\n=== ANSWER ===")
        print(result['messages'][-1].content)

running_agent()