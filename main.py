from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

load_dotenv()

app = FastAPI()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

store = {}  # Armazena histórico de todas as sessões


def get_history(session_id: str):
    """Retorna ou cria memória para a sessão."""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente útil e responde de forma clara."),
    ("human", "{input}")
])

chain = prompt | llm

chat_with_memory = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history"
)


class Message(BaseModel):
    sessionId: str
    message: str


@app.get("/session")
def create_session():
    session_id = str(uuid4())
    store[session_id] = InMemoryChatMessageHistory()
    return {"sessionId": session_id}


@app.post("/chat")
def chat(msg: Message):

    if msg.sessionId not in store:
        raise HTTPException(status_code=400, detail="Sessão inválida")

    response = chat_with_memory.invoke(
        {"input": msg.message},
        config={"configurable": {"session_id": msg.sessionId}}
    )

    return {"answer": response.content}



@app.get("/history/{session_id}")
def get_session_history(session_id: str):

    if session_id not in store:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    history_obj = store[session_id]

    history_list = [
        {"role": msg.type, "content": msg.content}
        for msg in history_obj.messages
    ]

    return {
        "sessionId": session_id,
        "history": history_list
    }

