import streamlit as st
import requests
import os
import time
import datetime
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from tavily import TavilyClient

load_dotenv()

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="City Intel — Dawn Edition",
    page_icon="🌅",
    layout="wide"
)

# ─────────────────────────────────────────
# SUNRISE CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    background-color: #fdf6ee !important;
    color: #2a1a08 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Keyframes ── */
@keyframes sunRise {
    from { transform: translateY(70px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
}
@keyframes skyFade {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes rayPulse {
    0%,100% { opacity: 0.18; transform: translateX(-50%) scale(1);   }
    50%      { opacity: 0.32; transform: translateX(-50%) scale(1.08);}
}
@keyframes cloudDrift {
    0%   { transform: translateX(0px);  }
    50%  { transform: translateX(10px); }
    100% { transform: translateX(0px);  }
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0);    }
}
@keyframes slideL {
    from { opacity: 0; transform: translateX(-20px); }
    to   { opacity: 1; transform: translateX(0);     }
}
@keyframes slideR {
    from { opacity: 0; transform: translateX(20px); }
    to   { opacity: 1; transform: translateX(0);    }
}
@keyframes tempPop {
    from { opacity: 0; transform: scale(0.5); }
    to   { opacity: 1; transform: scale(1);   }
}
@keyframes barIn {
    from { width: 0; }
}
@keyframes breathe {
    0%,100% { transform: scale(1);    }
    50%      { transform: scale(1.05); }
}
@keyframes msgPop {
    from { opacity: 0; transform: scale(0.88) translateY(8px); }
    to   { opacity: 1; transform: scale(1)    translateY(0);   }
}
@keyframes shimmer {
    0%,100% { opacity: 0.25; }
    50%      { opacity: 1;    }
}
@keyframes sunGlow {
    0%,100% { box-shadow: 0 0 24px 8px rgba(245,166,35,0.35);  }
    50%      { box-shadow: 0 0 48px 18px rgba(245,166,35,0.55); }
}

/* ── Sky banner ── */
.sky-banner {
    background: linear-gradient(180deg,#0d0825 0%,#1a1035 25%,#3d1c5c 50%,#c2522a 75%,#f0a84a 100%);
    border-radius: 20px;
    position: relative;
    overflow: hidden;
    height: 200px;
    margin-bottom: 20px;
    animation: skyFade 1s ease both;
}
.sky-sun {
    position: absolute;
    bottom: -22px; left: 50%;
    transform: translateX(-50%);
    width: 88px; height: 88px;
    border-radius: 50%;
    background: radial-gradient(circle,#ffe87a 28%,#f5a623 62%,#e05a00 100%);
    animation: sunRise 1.5s 0.3s cubic-bezier(0.22,1,0.36,1) both, sunGlow 3s 1.8s ease-in-out infinite;
    z-index: 3;
}
.sky-ray {
    position: absolute;
    bottom: -22px; left: 50%;
    width: 240px; height: 240px;
    border-radius: 50%;
    background: radial-gradient(circle,rgba(245,166,35,0.22) 0%,transparent 70%);
    animation: sunRise 1.5s 0.3s cubic-bezier(0.22,1,0.36,1) both,
               rayPulse 3.5s 1.8s ease-in-out infinite;
    z-index: 2;
}
.sky-cloud {
    position: absolute;
    border-radius: 40px;
    background: rgba(255,255,255,0.07);
}
.sky-cloud-1 { width:100px;height:24px;bottom:78px;left:10%; animation:cloudDrift 7s ease-in-out infinite; }
.sky-cloud-2 { width:66px; height:18px;bottom:90px;right:16%;animation:cloudDrift 9s ease-in-out infinite 1s; }
.sky-cloud-3 { width:48px; height:13px;bottom:98px;left:58%;animation:cloudDrift 6s ease-in-out infinite 2s; }
.sky-horizon {
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg,transparent,#f0a84a,transparent);
    z-index: 4;
}
.sky-cityline {
    position: absolute; bottom: 0; left: 0; right: 0; height: 64px;
    z-index: 4;
}
.sky-title {
    position: absolute; top: 20px; left: 24px; z-index: 10;
    font-family: 'Playfair Display', serif;
    font-size: 2rem; font-weight: 700;
    color: #ffecd0;
    text-shadow: 0 2px 14px rgba(0,0,0,0.55);
    animation: fadeUp 0.8s 0.5s ease both; opacity: 0; animation-fill-mode: forwards;
}
.sky-sub {
    position: absolute; top: 58px; left: 26px; z-index: 10;
    font-size: 0.68rem; color: #ffcf8a;
    letter-spacing: 0.2em; text-transform: uppercase;
    animation: fadeUp 0.8s 0.7s ease both; opacity: 0; animation-fill-mode: forwards;
}
.sky-clock {
    position: absolute; top: 18px; right: 22px; z-index: 10;
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem; color: #ffecd0; letter-spacing: 0.06em;
    animation: fadeUp 0.8s 0.9s ease both; opacity: 0; animation-fill-mode: forwards;
}

/* ── Search bar ── */
.search-wrap { animation: fadeUp 0.5s 0.15s ease both; }
div[data-testid="stTextInput"] input {
    background: #fff8f0 !important;
    border: 1.5px solid #f0c080 !important;
    border-radius: 40px !important;
    color: #2a1a08 !important;
    font-size: 1rem !important;
    padding: 0.7rem 1.3rem !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: border-color 0.22s, box-shadow 0.22s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #e05a00 !important;
    box-shadow: 0 0 0 3px rgba(224,90,0,0.12) !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #c09060 !important; }

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: #e05a00 !important;
    color: #fff8f0 !important;
    border: none !important;
    border-radius: 40px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.62rem 1.6rem !important;
    letter-spacing: 0.03em !important;
    transition: background 0.2s, transform 0.15s !important;
    cursor: pointer !important;
}
div[data-testid="stButton"] > button:hover {
    background: #c24800 !important;
    transform: translateY(-2px) !important;
}
div[data-testid="stButton"] > button:active {
    transform: scale(0.97) !important;
}

/* ── Sidebar buttons ── */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: #fff8f0 !important;
    color: #7a3a00 !important;
    border: 1.5px solid #f0c080 !important;
    border-radius: 40px !important;
    font-weight: 400 !important;
    font-size: 0.85rem !important;
    transition: all 0.18s !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: #e05a00 !important;
    color: #fff8f0 !important;
    border-color: #e05a00 !important;
    transform: translateX(5px) !important;
}

/* ── Weather card ── */
.wcard {
    background: #fff8f0;
    border: 1.5px solid #f0c080;
    border-radius: 18px;
    padding: 1.5rem;
    position: relative; overflow: hidden;
    animation: slideL 0.55s 0.3s ease both; opacity: 0; animation-fill-mode: forwards;
    transition: transform 0.22s, box-shadow 0.22s;
}
.wcard:hover {
    transform: translateY(-5px);
    box-shadow: 0 14px 40px rgba(224,90,0,0.13);
}
.wcard::after {
    content: '';
    position: absolute; top: -40px; right: -40px;
    width: 140px; height: 140px; border-radius: 50%;
    background: radial-gradient(circle,rgba(245,166,35,0.16) 0%,transparent 70%);
    pointer-events: none;
}
.wcard-lbl {
    font-size: 0.6rem; letter-spacing: 0.18em;
    text-transform: uppercase; color: #c09060; margin-bottom: 4px;
}
.wcard-city {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem; color: #2a1a08; margin-bottom: 6px;
}
.wcard-icon {
    font-size: 3.4rem; line-height: 1;
    display: inline-block;
    animation: breathe 4s ease-in-out infinite;
    margin-bottom: 4px;
}
.wcard-temp {
    font-family: 'Playfair Display', serif;
    font-size: 4.5rem; font-weight: 700; color: #c24800;
    line-height: 1;
    animation: tempPop 0.6s 0.5s ease both; opacity: 0; animation-fill-mode: forwards;
}
.wcard-unit { font-size: 1.6rem; color: #e08030; vertical-align: super; }
.wcard-desc { font-size: 0.82rem; color: #a07040; text-transform: capitalize; margin-top: 6px; margin-bottom: 16px; }
.wcard-stats { display: flex; gap: 8px; }
.wstat {
    background: #feeee0; border-radius: 10px;
    padding: 9px 10px; flex: 1;
    transition: transform 0.15s;
}
.wstat:hover { transform: translateY(-3px); }
.wstat-lbl { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; color: #c09060; margin-bottom: 2px; }
.wstat-val { font-family: 'Playfair Display', serif; font-size: 1rem; color: #2a1a08; }

/* ── News cards ── */
.news-wrap { animation: slideR 0.55s 0.35s ease both; opacity: 0; animation-fill-mode: forwards; }
.news-lbl { font-size: 0.6rem; letter-spacing: 0.18em; text-transform: uppercase; color: #c09060; margin-bottom: 10px; }
.ncard {
    background: #fff8f0; border: 1.5px solid #f0c080;
    border-left: 3px solid #e05a00; border-radius: 0 13px 13px 0;
    padding: 11px 15px; margin-bottom: 10px;
    transition: border-left-color 0.2s, transform 0.18s, background 0.18s;
    cursor: pointer;
}
.ncard:hover { border-left-color: #f5a623; transform: translateX(6px); background: #fef3e8; }
.ntag { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.12em; color: #c09060; margin-bottom: 3px; }
.ntitle {
    font-family: 'Playfair Display', serif;
    font-size: 0.9rem; color: #2a1a08; line-height: 1.4; margin-bottom: 3px;
}
.nsnip { font-size: 0.77rem; color: #a07040; line-height: 1.5; }
.nlink { font-size: 0.72rem; color: #e05a00; display: inline-block; margin-top: 5px; text-decoration: none; }

/* ── Forecast ── */
.fc-wrap {
    background: #fff8f0; border: 1.5px solid #f0c080; border-radius: 18px;
    padding: 1.4rem;
    animation: fadeUp 0.55s 0.44s ease both; opacity: 0; animation-fill-mode: forwards;
}
.fc-title {
    font-size: 0.6rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: #c09060; margin-bottom: 16px;
}
.fc-row { display: flex; align-items: center; gap: 10px; margin-bottom: 9px; }
.fc-day { font-size: 0.7rem; color: #a07040; width: 42px; text-transform: uppercase; letter-spacing: 0.06em; flex-shrink: 0; }
.fc-track { flex: 1; background: #feeee0; border-radius: 20px; height: 7px; overflow: hidden; }
.fc-fill { height: 100%; border-radius: 20px; animation: barIn 0.9s ease both; min-width: 8px; }
.fc-temp { font-family: 'Playfair Display', serif; font-size: 0.82rem; color: #2a1a08; width: 40px; text-align: right; flex-shrink: 0; }

/* ── Chat ── */
.chat-wrap {
    background: #fff8f0; border: 1.5px solid #f0c080; border-radius: 18px; overflow: hidden;
    animation: fadeUp 0.55s 0.52s ease both; opacity: 0; animation-fill-mode: forwards;
}
.chat-hdr {
    padding: 12px 16px; border-bottom: 1.5px solid #f0c080;
    font-size: 0.6rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: #c09060; display: flex; align-items: center; gap: 8px;
}
.sun-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #f5a623;
    display: inline-block; animation: breathe 2s ease-in-out infinite;
}
.chat-body { padding: 13px 15px; display: flex; flex-direction: column; gap: 9px; min-height: 110px; }
.msg-u {
    align-self: flex-end;
    background: #e05a00; color: #fff8f0;
    border-radius: 16px 16px 3px 16px;
    padding: 8px 14px; font-size: 0.87rem; max-width: 72%;
    animation: msgPop 0.25s ease both;
    font-family: 'DM Sans', sans-serif;
}
.msg-b {
    align-self: flex-start;
    background: #feeee0; border: 1px solid #f0c080; color: #2a1a08;
    border-radius: 16px 16px 16px 3px;
    padding: 8px 14px; font-size: 0.87rem; max-width: 84%; line-height: 1.55;
    animation: msgPop 0.25s ease both;
    font-family: 'DM Sans', sans-serif;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #fef3e8 !important;
    border-right: 1.5px solid #f0c080 !important;
}
section[data-testid="stSidebar"] * { color: #2a1a08 !important; }
section[data-testid="stSidebar"] h3 {
    font-family: 'Playfair Display', serif !important;
    color: #c24800 !important;
}

/* ── Misc ── */
hr { border-color: #f0c080 !important; }
div[data-testid="stSpinner"] > div { border-top-color: #e05a00 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# STATIC DATA
# ─────────────────────────────────────────
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

FORECAST_DATA = {
    "Mumbai":    [29, 31, 33, 30, 28, 31, 32],
    "Delhi":     [37, 38, 40, 39, 36, 38, 41],
    "Bangalore": [23, 24, 22, 21, 24, 25, 23],
    "Kolkata":   [32, 33, 34, 33, 31, 32, 33],
    "Chennai":   [33, 34, 35, 32, 34, 35, 33],
}


# ─────────────────────────────────────────
# LANGCHAIN TOOLS
# ─────────────────────────────────────────
@tool
def get_weather(city: str) -> str:
    """Get current weather of a city"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"
    data = requests.get(url).json()
    if str(data.get("cod")) != "200":
        return f"Error: {data.get('message')}"
    return (f"{data['weather'][0]['description']}|{data['main']['temp']}|"
            f"{data['main']['humidity']}|{data['wind']['speed']}")


def get_weather_raw(city: str) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"
    data = requests.get(url).json()
    if str(data.get("cod")) != "200":
        return {"error": data.get("message", "Not found")}
    return {
        "city":       data["name"],
        "temp":       round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "humidity":   data["main"]["humidity"],
        "wind":       data["wind"]["speed"],
        "desc":       data["weather"][0]["description"],
        "icon":       data["weather"][0]["icon"],
    }


@tool
def get_news(city: str) -> str:
    """Get latest news about a city"""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    results = client.search(
        query=f"latest news in {city}", max_results=3
    ).get("results", [])
    if not results:
        return f"No news found for {city}"
    return "\n\n".join(
        [f"- {r['title']}\n  {r['url']}\n  {r.get('content','')[:120]}" for r in results]
    )


def get_news_raw(city: str) -> list:
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        return client.search(
            query=f"latest news in {city}", max_results=4
        ).get("results", [])
    except Exception:
        return []


# ─────────────────────────────────────────
# RUNNABLE AGENT
# ─────────────────────────────────────────
@st.cache_resource
def get_agent():
    llm = ChatMistralAI(
        model="mistral-small-2506",
        api_key=os.getenv("MISTRAL_API_KEY")
    )
    tools    = [get_weather, get_news]
    tool_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    def format_input(data):
        return [
            SystemMessage(content="You are a helpful and friendly city assistant. Be concise."),
            HumanMessage(content=data["input"])
        ]

    def call_llm(messages):
        response = llm_with_tools.invoke(messages)
        return {"messages": messages, "response": response}

    def handle_tools(data):
        messages = data["messages"]
        response = data["response"]
        messages.append(response)
        if not response.tool_calls:
            return {"messages": messages, "final": True}
        for tc in response.tool_calls:
            result = tool_map[tc["name"]].invoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        return {"messages": messages, "final": False}

    def get_answer(data):
        if data["final"]:
            return data["messages"][-1].content
        return llm_with_tools.invoke(data["messages"]).content

    return (
        RunnableLambda(format_input)
        | RunnableLambda(call_llm)
        | RunnableLambda(handle_tools)
        | RunnableLambda(get_answer)
    )


# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
for key, val in [
    ("chat_history", []),
    ("weather_data", None),
    ("news_data",    []),
    ("current_city", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = val


# ─────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────
def weather_icon(icon_code: str) -> str:
    mapping = {
        "01": "☀️", "02": "🌤", "03": "☁️", "04": "☁️",
        "09": "🌧", "10": "🌦", "11": "⛈", "13": "❄️", "50": "🌫",
    }
    return mapping.get(icon_code[:2], "🌡")


def bar_color(temp: int) -> str:
    if temp >= 36:   return "#c24800"
    elif temp >= 30: return "#e05a00"
    elif temp >= 24: return "#f5a623"
    else:            return "#5b9bd5"


def render_sky_banner():
    current_time = time.strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="sky-banner">
        <div class="sky-ray"></div>
        <div class="sky-sun"></div>
        <div class="sky-cloud sky-cloud-1"></div>
        <div class="sky-cloud sky-cloud-2"></div>
        <div class="sky-cloud sky-cloud-3"></div>
        <svg class="sky-cityline" viewBox="0 0 800 64" preserveAspectRatio="none">
          <path d="M0,64 L0,44 L30,44 L30,30 L42,30 L42,20 L52,20 L52,30 L72,30
                   L72,36 L92,36 L92,18 L102,18 L102,10 L106,10 L106,18 L114,18
                   L114,36 L134,36 L134,42 L154,42 L154,26 L168,26 L168,14 L174,14
                   L174,26 L188,26 L188,40 L214,40 L214,22 L228,22 L228,12 L234,12
                   L234,22 L248,22 L248,40 L274,40 L274,44 L304,44 L304,32 L318,32
                   L318,20 L325,20 L325,32 L342,32 L342,44 L374,44 L374,36 L394,36
                   L394,20 L404,20 L404,13 L408,13 L408,20 L418,20 L418,36 L444,36
                   L444,42 L464,42 L464,28 L478,28 L478,18 L484,18 L484,28 L498,28
                   L498,42 L524,42 L524,33 L542,33 L542,44 L574,44 L574,38 L592,38
                   L592,24 L602,24 L602,16 L607,16 L607,24 L618,24 L618,38 L642,38
                   L642,44 L674,44 L674,36 L702,36 L702,44 L734,44 L734,30 L752,30
                   L752,44 L800,44 L800,64 Z" fill="#1a1035"/>
        </svg>
        <div class="sky-horizon"></div>
        <div class="sky-title">City Intel</div>
        <div class="sky-sub">dawn · weather · news · ai assistant</div>
        <div class="sky-clock">{current_time}</div>
    </div>
    """, unsafe_allow_html=True)


def render_weather_card(w: dict):
    icon = weather_icon(w.get("icon", "01"))
    st.markdown(
        '<div class="wcard">'
        '<div class="wcard-lbl">Current Weather</div>'
        f'<div class="wcard-city">{w["city"]}, IN</div>'
        f'<div class="wcard-icon">{icon}</div>'
        f'<div><span class="wcard-temp">{w["temp"]}</span>'
        '<span class="wcard-unit">°C</span></div>'
        f'<div class="wcard-desc">{w["desc"]}</div>'
        '<div class="wcard-stats">'
        '<div class="wstat"><div class="wstat-lbl">Feels like</div>'
        f'<div class="wstat-val">{w["feels_like"]}°</div></div>'
        '<div class="wstat"><div class="wstat-lbl">Humidity</div>'
        f'<div class="wstat-val">{w["humidity"]}%</div></div>'
        '<div class="wstat"><div class="wstat-lbl">Wind</div>'
        f'<div class="wstat-val">{w["wind"]} m/s</div></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def render_news_cards(news: list, city: str):
    tags = ["Business", "Local", "Weather", "Tech", "Health", "Politics"]
    cards = '<div class="news-lbl">Latest News — ' + city + '</div>'
    for i, item in enumerate(news):
        title   = item.get("title", "No title")
        url     = item.get("url", "#")
        snippet = item.get("content", "")[:130]
        tag     = tags[i % len(tags)]
        delay   = f"{0.06 + i * 0.09:.2f}s"
        cards += (
            f'<div class="ncard" style="animation:slideR 0.4s {delay} ease both;'
            'opacity:0;animation-fill-mode:forwards">'
            f'<div class="ntag">{tag}</div>'
            f'<div class="ntitle">{title}</div>'
            f'<div class="nsnip">{snippet}...</div>'
            f'<a href="{url}" target="_blank" class="nlink">↗ Read full article</a>'
            '</div>'
        )
    st.markdown('<div class="news-wrap">' + cards + '</div>', unsafe_allow_html=True)


def render_forecast(city: str):
    fc      = FORECAST_DATA.get(city, [30] * 7)
    min_t   = min(fc)
    max_t   = max(fc)
    today_i = datetime.datetime.now().weekday()
    rows    = ""
    for i, temp in enumerate(fc):
        pct   = int(((temp - min_t) / max(max_t - min_t, 1)) * 100)
        color = bar_color(temp)
        day   = "Today" if i == 0 else DAYS[(today_i + i) % 7]
        rows += (
            '<div class="fc-row">'
            f'<span class="fc-day">{day}</span>'
            '<div class="fc-track">'
            f'<div class="fc-fill" style="width:{max(pct,8)}%;background:{color}"></div>'
            '</div>'
            f'<span class="fc-temp">{temp}°C</span>'
            '</div>'
        )
    st.markdown(
        '<div class="fc-wrap">'
        '<div class="fc-title">7-Day Forecast</div>'
        + rows +
        '</div>',
        unsafe_allow_html=True,
    )


def render_chat():
    msgs = "".join([
        f'<div class="{"msg-u" if m["role"] == "user" else "msg-b"}">{m["content"]}</div>'
        for m in st.session_state.chat_history
    ]) or '<div class="msg-b">Good morning! Ask me anything about a city — weather, news or forecasts.</div>'

    st.markdown(
        '<div class="chat-wrap">'
        '<div class="chat-hdr">'
        '<span class="sun-dot"></span>'
        'AI City Assistant'
        '</div>'
        f'<div class="chat-body">{msgs}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌅 City Intel")
    st.markdown(
        "<div style='color:#c09060;font-size:0.75rem;margin-bottom:1.2rem;'>"
        "Mistral · LangChain · Tavily · OpenWeather"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("**Quick Cities**")
    for qc in ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai"]:
        if st.button(qc, key=f"q_{qc}", use_container_width=True):
            st.session_state.current_city = qc
            with st.spinner(f"Loading {qc}..."):
                st.session_state.weather_data = get_weather_raw(qc)
                st.session_state.news_data    = get_news_raw(qc)
            st.rerun()

    st.markdown("---")
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ─────────────────────────────────────────
# SKY BANNER
# ─────────────────────────────────────────
render_sky_banner()

# ─────────────────────────────────────────
# SEARCH BAR
# ─────────────────────────────────────────
st.markdown("<div class='search-wrap'>", unsafe_allow_html=True)
s_col, b_col = st.columns([5, 1])
with s_col:
    city_input = st.text_input(
        "", placeholder="Search any city...",
        label_visibility="collapsed"
    )
with b_col:
    search_clicked = st.button("Search", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if search_clicked and city_input.strip():
    city = city_input.strip()
    st.session_state.current_city = city
    with st.spinner(f"Fetching data for {city}..."):
        st.session_state.weather_data = get_weather_raw(city)
        st.session_state.news_data    = get_news_raw(city)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# WEATHER + NEWS
# ─────────────────────────────────────────
if st.session_state.weather_data or st.session_state.news_data:
    w_col, n_col = st.columns([1, 1.8], gap="large")

    with w_col:
        w = st.session_state.weather_data
        if w and "error" not in w:
            render_weather_card(w)
        elif w:
            st.error(f"Weather error: {w['error']}")

    with n_col:
        if st.session_state.news_data:
            render_news_cards(st.session_state.news_data, st.session_state.current_city)
        else:
            st.markdown(
                '<div style="color:#c09060;font-size:0.9rem;">No news found.</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.current_city in FORECAST_DATA:
        render_forecast(st.session_state.current_city)
        st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────
render_chat()
st.markdown("<br>", unsafe_allow_html=True)

c_col, s_col = st.columns([5, 1])
with c_col:
    user_msg = st.text_input(
        "", placeholder="Ask about weather, news, forecasts...",
        key="chat_input", label_visibility="collapsed"
    )
with s_col:
    send_clicked = st.button("Send ↗", use_container_width=True, key="send_btn")

if send_clicked and user_msg.strip():
    st.session_state.chat_history.append({"role": "user", "content": user_msg})
    with st.spinner("Thinking..."):
        try:
            agent    = get_agent()
            response = agent.invoke({"input": user_msg})
            st.session_state.chat_history.append({"role": "bot", "content": response})
        except Exception as e:
            st.session_state.chat_history.append(
                {"role": "bot", "content": f"⚠️ Error: {str(e)}"}
            )
    st.rerun()