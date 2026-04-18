import requests
import streamlit as st

API_KEY = st.secrets["GEMINI_API_KEY"]
DEFAULT_MODEL = "gemini-1.5-mini"

if "GEMINI_API_KEY" not in st.secrets:
    st.error(
        "A chave da API Gemini não foi encontrada. Configure a chave nos secrets do Streamlit (Arquivo .streamlit/secrets.toml)."
    )
    st.stop()

st.set_page_config(page_title="Chat com IA Gemini", page_icon="🤖", layout="wide")

st.title("Chat IA Gemini")
st.markdown("Um chat com IA generativa no estilo ChatGPT usando a API Gemini.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Eu sou um assistente de IA. Pergunte qualquer coisa."}
    ]

model = st.sidebar.selectbox(
    "Modelo Gemini",
    ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
    index=0,
)

max_tokens = st.sidebar.slider("Máximo de tokens de resposta", 128, 1024, 512, step=64)
temperature = st.sidebar.slider("Temperatura", 0.0, 1.0, 0.7, step=0.1)

with st.expander("Instruções", expanded=False):
    st.write(
        "Digite sua pergunta no chat e pressione Enter. O histórico de conversas será mantido enquanto a sessão estiver aberta."
    )

for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

def call_gemini(prompt_text: str, model_name: str, max_tokens: int, temperature: float) -> str:
    endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
    params = {"key": API_KEY}
    contents = []
    for msg in prompt_text.split("\n"):
        if msg.startswith("user: ") or msg.startswith("assistant: "):
            role = "user" if msg.startswith("user: ") else "model"
            parts = [{"text": msg.split(": ", 1)[1] if ": " in msg else msg}]
            contents.append({"role": role, "parts": parts})
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }

    response = requests.post(endpoint, params=params, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "candidates" in data and len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        if "content" in candidate and "parts" in candidate["content"]:
            return candidate["content"]["parts"][0].get("text", "")

    return "Desculpe, não foi possível gerar uma resposta no momento."

user_input = st.chat_input("Escreva sua mensagem...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        st.write("Escrevendo...")

    try:
        prompt = "\n".join(
            [f"{m['role']}: {m['content']}" for m in st.session_state.messages if m["role"] in ["user", "assistant"]]
        )
        assistant_response = call_gemini(prompt, model, max_tokens, temperature)
    except requests.exceptions.RequestException as error:
        assistant_response = f"Erro na requisição à API Gemini: {error}"

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.chat_message("assistant").write(assistant_response)
