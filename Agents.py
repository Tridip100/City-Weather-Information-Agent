from langchain_mistralai import ChatMistralAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv
import requests, os

load_dotenv()

# =========================
# 🌦️ Weather Tool
# =========================
@tool
def get_weather(city: str) -> str:
    """Get current weather of a city"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"
    data = requests.get(url).json()
    if str(data.get("cod")) != "200":
        return f"Error: {data.get('message')}"
    return f"Weather in {city}: {data['weather'][0]['description']}, {data['main']['temp']}°C"

# =========================
# 📰 News Tool
# =========================
@tool
def get_news(city: str) -> str:
    """Get latest news about a city"""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    results = client.search(query=f"latest news in {city}", max_results=3).get("results", [])
    if not results:
        return f"No news found for {city}"
    return "\n\n".join([f"- {r['title']}\n  🔗 {r['url']}" for r in results])

# =========================
# 🧠 LLM + Tools
# =========================
llm = ChatMistralAI(model="mistral-small-2506")
tools = [get_weather, get_news]
tool_map = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)

# =========================
# 🔧 Runnable Steps
# =========================

# Step 1 — Format input into messages
def format_input(data: dict) -> list:
    return [
        SystemMessage(content="You are a helpful city assistant."),
        HumanMessage(content=data["input"])
    ]

# Step 2 — Call LLM
def call_llm(messages: list) -> dict:
    response = llm_with_tools.invoke(messages)
    return {"messages": messages, "response": response}

# Step 3 — Human approval + tool execution
def handle_tools(data: dict) -> dict:
    messages = data["messages"]
    response = data["response"]
    messages.append(response)

    if not response.tool_calls:
        return {"messages": messages, "final": True}

    for tc in response.tool_calls:
        confirm = input(f"\n🔔 Agent wants to call '{tc['name']}' with {tc['args']}. Approve? (yes/no): ")

        if confirm.lower() != "yes":
            result = "Tool call denied by user."
        else:
            result = tool_map[tc["name"]].invoke(tc["args"])

        messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return {"messages": messages, "final": False}

# Step 4 — Extract final answer or loop back
def get_answer(data: dict) -> str:
    if data["final"]:
        return data["messages"][-1].content

    # Loop: call LLM again after tool results
    response = llm_with_tools.invoke(data["messages"])
    return response.content

# =========================
# ⛓️ Build Runnable Chain
# =========================
chain = (
    RunnableLambda(format_input)   # dict → messages
    | RunnableLambda(call_llm)     # messages → {messages, response}
    | RunnableLambda(handle_tools) # handles approval + tool calls
    | RunnableLambda(get_answer)   # → final string
)

# =========================
# 🚀 Run the Agent
# =========================
print("City Agent | type 'exit' to quit\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    answer = chain.invoke({"input": user_input})
    print(f"Bot: {answer}\n")
