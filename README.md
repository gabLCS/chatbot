# Chatbot Multiusuário com Memória (FastAPI + LangChain + Gemini)

API Python simples para chatbot com múltiplas sessões independentes, usando Google Gemini via LangChain e memória por sessão.
Este projeto é uma aplicação completa de chat com memória contínua, construída utilizando FastAPI no backend e React no frontend.
A API utiliza o modelo Gemini 2.5 Flash, da Google, integrado através do LangChain 1.x totalmente atualizado — garantindo alta performance, compatibilidade total e suporte às features mais modernas do ecossistema.

Cada usuário recebe um sessionId único, permitindo que o assistente mantenha um histórico de conversa individual. A memória é gerenciada utilizando RunnableWithMessageHistory, garantindo persistência de contexto e respostas mais naturais a cada interação.

O projeto inicial visava a utilização da api do OpenAI. Mas houve essa necessidade de troca pelo modelo 2.5-flash do Gemini da Google. A troca do OpenAI pelos modelos Gemini ocorreu por uma combinação de fatores técnicos e práticos. O Gemini 2.5 Flash oferece excelente desempenho, sendo ideal para aplicações de chat em tempo real. A integração com a API da Google é direta e funcionou perfeitamente com memória conversacional e pipelines. Para continuar usando a API da OpenAI é necessário ter créditos pagos obrigatórios, mesmo para testes simples.
Isso torna o processo mais limitado para desenvolvimento inicial, prototipação e testes rápidos.
O Gemini, por outro lado, oferece uma camada gratuita mais generosa, facilitando o desenvolvimento sem custos imediatos.

---

## Funcionalidades
- Criar sessões independentes para vários usuários
- Manter histórico separado para cada sessão
- Responder perguntas usando Gemini 2.5 Flash
- Hospedar em AWS EC2
- Iniciar automaticamente como serviço systemd
- Endpoint público acessível pela internet
- Autenticação JWT Segura: Gerencia sessões de usuário utilizando JSON Web Tokens (JWT).
- Registro Completo: Inclui validação de Nome de Usuário, Email e Confirmação de Senha.
- Hashing Moderno: Senhas armazenadas com hashing SCrypt (via passlib), sem o limite de 72 bytes do Bcrypt.
- Persistência SQL: Usuários e Metadados de Conversa (título, user_id) persistidos em banco de dados SQLite (via SQLAlchemy).
- Memória por Usuário/Sessão: Histórico de chat isolado e persistente usando SQLChatMessageHistory.
- CORS: Configuração de middleware CORS para permitir comunicação com o Frontend.

---

## Estrutura do Projeto

/

|- main.py

|- requirements.txt

|- start.sh

|- README.md

|- frontend/
    |- index.html
    |- style.css



---

# 1. Instalação Local

## 1.1 Clone o repositório
```bash
git clone https://github.com/gabLCS/chatbot.git
cd chatbot
```



## 1.2 Criar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

## 1.3 Instalar dependências
```bash
pip install -r requirements.txt
```


## 1.4 Criar arquivo .env
GEMINI_API_KEY=SUA_CHAVE_AQUI

## 1.5 Rodar a API
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```


---

#  2. Endpoints

## Cadastro de Usuário
```bash
POST /register
```


Body:
```bash
{
  "username": "usuario",
  "email": "email@dominio.com",
  "password": "senha_forte",
  "password_confirm": "senha_forte"
}
```

## Login e Geração de Token

```bash
{
POST /login
}
```
Body:
```bash

{
  "username": "usuario",
  "password": "senha_forte"
}

```



Resposta:
```bash

{
  "access_token": "eyJhbGciOiJIUzI1Ni...", 
  "token_type": "bearer",
  "user_id": 1,
  "username": "usuario"
}

```


Criar Nova Sessão
```bash
POST /session
```



Resposta:
```bash
{ "sessionId": "UUID_DA_NOVA_SESSAO", "title": "Novo Chat" }
```


Enviar Mensagem (Autenticado)


```bash
POST /chat
```

Body:
```bash
{
  "conversationId": "ID_DA_SESSAO",
  "message": "sua mensagem"
}
```



Resposta:
```bash
{ "answer": "resposta do modelo" }
```


---

#  3. Configurar servidor

## 3.1 Atualizar servidor
```bash
sudo apt update && sudo apt upgrade -y
```


## 3.2 Instalar dependências
```bash
sudo apt update
sudo apt install python3 python3-pip git nginx -y
pip install gunicorn
```


## 3.3 Clonar repositório
```bash
git clone https://github.com/gabLCS/chatbot.git
cd chatbot
```




## 3.4 Criar ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate
```



## 3.5 Instalar dependências
```bash
pip install -r requirements.txt
```


## 3.6 Criar .env
```bash
echo "GEMINI_API_KEY=SUA_CHAVE" > .env
```

## 3.7 Configurar Nginx (Proxy Reverso)
Crie o arquivo de configuração Nginx:
```bash
sudo nano /etc/nginx/sites-available/chat_app
```
Conteúdo (Ajuste o caminho e o nome do servidor):
```bash
server {
    listen 80;
    server_name _; # Usa wildcard para capturar o IP dinâmico da EC2

    # Servir arquivos estáticos (Frontend)
    location / {
        root /home/ubuntu/seu_projeto/frontend;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # Proxy Reverso para a API FastAPI (Porta 8000)
    location /login {
        proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000);
        proxy_set_header Host $host;
    }

    location /register {
        proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000);
        proxy_set_header Host $host;
    }

    # Rotas autenticadas
    location /chat {
        proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000);
        proxy_set_header Host $host;
    }
    
    location /session {
        proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000);
        proxy_set_header Host $host;
    }
    
    location /history {
        proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000);
        proxy_set_header Host $host;
    }
}

```

Ative e reinicie o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/chat_app /etc/nginx/sites-enabled/
sudo unlink /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

# 4. start.sh (script para iniciar a API)

Conteúdo do start.sh:
```bash
#!/bin/bash

PROJECT_DIR="/home/ubuntu/chatbot-multiuser"

cd $PROJECT_DIR

source venv/bin/activate

gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```




Tornar executável:
```bash
chmod +x start.sh
```


---

# 5. Iniciar automaticamente com systemd

## Criar serviço
```bash
sudo nano /etc/systemd/system/chatbot.service
```




Conteúdo:
```bash
[Unit]

Description=Chatbot Multiuser API

After=network.target


[Service]

User=ubuntu

WorkingDirectory=/home/ubuntu/chatbot-multiuser

ExecStart=/home/ubuntu/chatbot-multiuser/start.sh

Restart=always


[Install]
WantedBy=multi-user.target

## Ativar serviço

sudo systemctl daemon-reload

sudo systemctl enable chatbot

sudo systemctl start chatbot
```



## Ver logs
```bash
journalctl -u chatbot -f
```


---

# 6. Acesso público

4. Acesso Público

Após a configuração do Nginx, acesse sua aplicação web pelo navegador sem especificar a porta:

```bash
http://SEU_IP_PUBLICO
```




---











