# Detetive do Presente AI

Chatbot em Python que usa a API do Google Gemini para sugerir presentes personalizados com base em perfil, idade, interesses, orçamento, ocasião e restrições.

O projeto possui dois modos de interação:

1. **Perguntas passo a passo (estilo detetive)**
2. **Mensagem única com todas as informações**

## Requisitos

- Python 3
- Chave da API do Google Gemini

## Instalação

1. Entre na pasta do projeto:

```bash
cd gift_chatbot
```

2. (Opcional, recomendado) Crie e ative um ambiente virtual.

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configurar a chave da API Gemini

1. Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell, você pode usar:

```powershell
Copy-Item .env.example .env
```

2. Edite o arquivo `.env` e adicione sua chave:

```env
GEMINI_API_KEY=sua_chave_aqui
```

## Como executar

Na pasta `gift_chatbot`, execute:

```bash
python main.py
```

## Versão web (entrega por link)

Se o professor pediu um link direto para funcionalidade, use a interface web com Streamlit:

```bash
streamlit run app.py
```

### Publicar no Streamlit Community Cloud

1. Suba este projeto para um repositório no GitHub.
2. Acesse [https://share.streamlit.io](https://share.streamlit.io).
3. Clique em **New app** e selecione seu repositório.
4. Defina o arquivo principal como `gift_chatbot/app.py`.
5. Em **Advanced settings > Secrets**, adicione:

```toml
GEMINI_API_KEY="sua_chave_aqui"
```

6. Clique em **Deploy**.

Ao final, você recebe um link público para entregar (ex.: `https://seu-app.streamlit.app`).

Ao iniciar, o chatbot mostra:

```text
Detetive do Presente AI

How would you like to interact?

1 - Answer questions step by step
2 - Write everything in one message
```

Depois disso, ele conversa com você e usa o Gemini para gerar **3 a 5 sugestões personalizadas** de presente.

> Observação: o projeto seleciona automaticamente um modelo Gemini compatível com sua API key (priorizando versões Flash).