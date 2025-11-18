import os
from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, status
from dotenv import load_dotenv
from typing import List

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, select
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from passlib.context import CryptContext

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories.sql import SQLChatMessageHistory
from fastapi.middleware.cors import CORSMiddleware 



load_dotenv()


DATABASE_URL = "sqlite:///./chat_app.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["scrypt", "bcrypt"], deprecated="auto")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)





class User(Base):
    """Modelo de Usuário para o banco de dados."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False) 
    hashed_password = Column(String, nullable=False)
    
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    """Modelo para agrupar mensagens de uma mesma sessão de chat (histórico)."""
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, index=True) 
    title = Column(String, nullable=False, default="Nova Conversa")
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="conversations")


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserBase(BaseModel):
    username: str
    email: EmailStr 

class UserCreate(UserBase):
    password: str
    password_confirm: str

    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        """Verifica se a senha e a confirmação são iguais."""
        if 'password' in values and v != values['password']:
            raise ValueError('As senhas não coincidem.')
        return v

class UserLogin(UserBase):
    password: str

class UserLogin(BaseModel): 
    username: str
    password: str

class ConversationTitleUpdate(BaseModel):
    title: str

class ChatMessage(BaseModel):
    """Schema para o corpo da requisição de chat."""
    conversationId: str
    message: str
    #userId: int # Adicione esta informação, idealmente obtida via token JWT após login

class ConversationItem(BaseModel):
    id: str
    title: str
    
    class Config:
        from_attributes = True

class HistoryMessage(BaseModel):
    role: str
    content: str

class HistoryResponse(BaseModel):
    sessionId: str
    history: List[HistoryMessage]


prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente útil e responde de forma clara."),
    ("human", "{input}")
])

chain = prompt | llm

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria um novo token de acesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais inválidas ou token expirado",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Decodifica o token JWT e retorna o objeto User autenticado."""
    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
 
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
 
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user 

def get_history(session_id: str):
    """Retorna ou cria memória para a sessão no banco de dados."""
    
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string=DATABASE_URL,
        table_name="message_history", 
    )

chat_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history=get_history,
    input_messages_key="input",
)


app = FastAPI() 

 
origins = [
    "*", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)


@app.post("/register", response_model=UserBase)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Rota para cadastro de novo usuário, agora com email e validação."""
    
 
    db_user_name = db.execute(select(User).where(User.username == user.username)).scalar_one_or_none()
    if db_user_name:
        raise HTTPException(status_code=400, detail="Nome de usuário já registrado")


    db_user_email = db.execute(select(User).where(User.email == user.email)).scalar_one_or_none()
    if db_user_email:
        raise HTTPException(status_code=400, detail="E-mail já registrado")
    

    hashed_password = pwd_context.hash(user.password) 
    

    db_user = User(
        username=user.username, 
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Rota para login. Gera e retorna um JWT (access token)."""
    db_user = db.execute(select(User).where(User.username == user.username)).scalar_one_or_none()
    

    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")


    access_token = create_access_token(
        data={"sub": str(db_user.id)} 
    )
    

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": db_user.id, 
        "username": db_user.username
    }



@app.post("/session")
def create_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cria uma nova conversa (sessão) associada ao usuário autenticado."""
 
    import uuid
    session_id = str(uuid.uuid4())
    new_conversation = Conversation(id=session_id, user_id=user.id) 
    
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    return {"sessionId": session_id, "title": new_conversation.title}

@app.post("/chat")
def chat(msg: ChatMessage, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rota principal do chat. Verifica a permissão usando o JWT e o userId do token."""
    

    user_id = user.id 


    conversation = db.execute(select(Conversation).where(
        (Conversation.id == msg.conversationId) & (Conversation.user_id == user_id)
    )).scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=400, detail="Conversa inválida ou não pertence ao usuário.")


    response = chat_with_memory.invoke(
        {"input": msg.message},
        config={"configurable": {"session_id": msg.conversationId}}
    )
    
    return {"answer": response.content}


@app.get("/history/{user_id}", response_model=List[ConversationItem])
def get_user_conversations(user_id: int, db: Session = Depends(get_db)):
    """Obtém a lista de conversas de um usuário para exibição na sidebar."""
    conversations = db.execute(select(Conversation).where(Conversation.user_id == user_id)).scalars().all()
    
    return conversations


@app.get("/conversation/{session_id}", response_model=HistoryResponse)
def get_conversation_history(session_id: str, db: Session = Depends(get_db)):
    """Obtém o histórico de mensagens de uma conversa específica."""
    

    history_obj = get_history(session_id)


    history_list = [
        {"role": msg.type, "content": msg.content}
        for msg in history_obj.messages
    ]

    return {
        "sessionId": session_id,
        "history": history_list
    }

@app.put("/conversation/{session_id}")
def update_conversation_title(session_id: str, title_update: ConversationTitleUpdate, db: Session = Depends(get_db)):
    """Atualiza o título de uma conversa."""
    conversation = db.execute(select(Conversation).where(Conversation.id == session_id)).scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    conversation.title = title_update.title
    db.commit()
    db.refresh(conversation)
    
    return {"message": "Título atualizado", "title": conversation.title}
