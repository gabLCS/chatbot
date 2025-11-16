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

---

## Estrutura do Projeto

/

|- main.py

|- requirements.txt

|- start.sh

|- README.md


---

# 1. Instalação Local

## 1.1 Clone o repositório
git clone https://github.com/SEU-USUARIO/chatbot.git
cd chatbot

## 1.2 Criar ambiente virtual

python3 -m venv venv

source venv/bin/activate  # Linux/Mac

venv\Scripts\activate     # Windows

## 1.3 Instalar dependências
pip install -r requirements.txt

## 1.4 Criar arquivo .env
GEMINI_API_KEY=SUA_CHAVE_AQUI

## 1.5 Rodar a API
uvicorn main:app --host 0.0.0.0 --port 8000

---

#  2. Endpoints

## Criar sessão
GET /session

Resposta:
{ "sessionId": "UUID" }

## Enviar mensagem
POST /chat

Body:
{
  "sessionId": "ID_DA_SESSAO",
  "message": "sua mensagem"
}

Resposta:
{
  "answer": "resposta do modelo"
}

---

#  3. Configurar servidor

## 3.1 Atualizar servidor
sudo apt update && sudo apt upgrade -y

## 3.2 Instalar dependências
sudo apt install python3 python3-venv python3-pip git -y

## 3.3 Clonar repositório

git clone https://github.com/SEU-USUARIO/chatbot-multiuser.git

cd chatbot-multiuser

## 3.4 Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

## 3.5 Instalar dependências
pip install -r requirements.txt

## 3.6 Criar .env
echo "GEMINI_API_KEY=SUA_CHAVE" > .env

---

# ▶ 4. start.sh (script para iniciar a API)

Conteúdo do start.sh:

#!/bin/bash

cd /home/ubuntu/chatbot-multiuser

source venv/bin/activate

uvicorn main:app --host 0.0.0.0 --port 8000


Tornar executável:
chmod +x start.sh

---

# 5. Iniciar automaticamente com systemd

## Criar serviço

sudo nano /etc/systemd/system/chatbot.service


Conteúdo:

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

## Ver logs
journalctl -u chatbot -f

---

# 6. Acesso público

Após iniciar a API, acesse:

http://SEU_IP_PUBLICO:8000/session

ou via POST:

http://SEU_IP_PUBLICO:8000/chat

---







