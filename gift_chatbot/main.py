"""Detetive do Presente AI - chatbot de recomendação de presentes com Gemini."""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
import google.generativeai as genai


SYSTEM_INSTRUCTIONS = """
Você é o Detetive do Presente AI, um especialista criativo em recomendação de presentes.

Regras de comportamento:
- Tom amigável, conversacional e com tema de detetive.
- Se faltarem dados para boas sugestões, faça apenas UMA pergunta por vez.
- Se já houver dados suficientes, gere sugestões imediatamente.
- Sempre forneça entre 3 e 5 sugestões personalizadas.
- Para cada sugestão, inclua:
  1) Nome do presente
  2) Explicação curta de por que combina com a pessoa
  3) Preço aproximado (na moeda do usuário quando possível)
- Considere perfil da pessoa, idade, interesses, orçamento, ocasião e restrições.
- Evite sugestões fora do orçamento, a menos que ofereça alternativa semelhante mais barata.
- Estruture a resposta de forma clara e fácil de ler.
""".strip()


STEP_BY_STEP_QUESTIONS = [
    "Para quem é o presente?",
    "Qual a idade da pessoa?",
    "Quais são os interesses ou hobbies dela?",
    "Qual é o seu orçamento aproximado?",
    "Qual é a ocasião?",
    "Existe alguma restrição? (ex.: alergias, estilo, nada tecnológico, etc.)",
]


PREFERRED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
]


def choose_supported_model_name() -> str:
    """Escolhe automaticamente um modelo compatível com generateContent."""
    available_names: List[str] = []

    for model in genai.list_models():
        methods = getattr(model, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            model_name = getattr(model, "name", "")
            if model_name.startswith("models/"):
                model_name = model_name.replace("models/", "", 1)
            if model_name:
                available_names.append(model_name)

    for preferred in PREFERRED_MODELS:
        if preferred in available_names:
            return preferred

    if available_names:
        return available_names[0]

    raise RuntimeError(
        "Nenhum modelo compatível com generateContent foi encontrado para esta API key."
    )


def configure_model() -> genai.GenerativeModel:
    """Carrega .env, valida a chave e retorna o modelo Gemini configurado."""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada. Crie um arquivo .env com sua chave da API."
        )

    genai.configure(api_key=api_key)
    selected_model = choose_supported_model_name()
    print(f"\n🔧 Modelo Gemini selecionado: {selected_model}")
    return genai.GenerativeModel(model_name=selected_model)


def print_header() -> None:
    """Mostra o cabeçalho e o menu inicial."""
    print("Detetive do Presente AI\n")
    print("Como você gostaria de interagir?\n")
    print("1 - Responder perguntas passo a passo")
    print("2 - Escrever tudo em uma única mensagem")


def build_initial_history() -> List[dict]:
    """Cria histórico de conversa com instruções de sistema para o modelo."""
    return [
        {
            "role": "user",
            "parts": [f"Instruções do sistema:\n{SYSTEM_INSTRUCTIONS}"],
        },
        {
            "role": "model",
            "parts": [
                "Entendido. Vou agir como Detetive do Presente AI seguindo todas as regras."
            ],
        },
    ]


def ask_mode() -> str:
    """Lê e valida o modo de interação."""
    while True:
        mode = input("\nEscolha 1 ou 2: ").strip()
        if mode in {"1", "2"}:
            return mode
        print("⚠️ Opção inválida. Digite 1 ou 2.")


def run_step_by_step_mode(model: genai.GenerativeModel) -> None:
    """Executa o fluxo com perguntas sequenciais e gera sugestões ao final."""
    print("\n🕵️ Bem-vindo ao Detetive do Presente AI!")
    print("Vamos investigar o presente perfeito.\n")

    answers: List[str] = []
    conversation_history = build_initial_history()

    for question in STEP_BY_STEP_QUESTIONS:
        user_answer = input(f"🕵️ {question}\n> ").strip()
        answers.append(f"- {question} {user_answer if user_answer else '(não informado)'}")
        conversation_history.append({"role": "user", "parts": [f"{question} {user_answer}"]})

    summary = "\n".join(answers)
    prompt = (
        "Com base no perfil abaixo, gere agora 3 a 5 sugestões personalizadas de presente.\n"
        "Inclua nome do presente, explicação curta e preço aproximado em cada item.\n"
        "\nPerfil coletado:\n"
        f"{summary}"
    )

    conversation_history.append({"role": "user", "parts": [prompt]})
    response = model.generate_content(conversation_history)

    print("\n🧩 Caso resolvido! Aqui estão as pistas de presentes:\n")
    print(response.text)


def run_single_message_mode(model: genai.GenerativeModel) -> None:
    """Recebe uma mensagem única do usuário e pede sugestões ao Gemini."""
    print("\n🕵️ Bem-vindo ao Detetive do Presente AI!")
    print("Compartilhe todas as pistas em uma única mensagem e eu investigo.\n")

    user_message = input("> ").strip()
    conversation_history = build_initial_history()

    prompt = (
        "Mensagem do usuário com os detalhes para sugestão de presente:\n"
        f"{user_message}\n\n"
        "Se houver informações suficientes, gere 3 a 5 sugestões agora. "
        "Se faltar algo essencial, faça apenas uma pergunta objetiva."
    )
    conversation_history.append({"role": "user", "parts": [prompt]})

    response = model.generate_content(conversation_history)
    print("\n🔎 Resultado da investigação:\n")
    print(response.text)


def main() -> None:
    """Ponto de entrada do programa."""
    try:
        model = configure_model()
    except Exception as error:
        print(f"\n❌ Erro ao configurar Gemini: {error}")
        return

    print_header()
    mode = ask_mode()

    try:
        if mode == "1":
            run_step_by_step_mode(model)
        else:
            run_single_message_mode(model)
    except Exception as error:
        error_message = str(error)
        if "API_KEY_INVALID" in error_message or "API key not valid" in error_message:
            print("\n❌ Chave da API Gemini inválida.")
            print("Verifique o arquivo .env e gere uma nova chave no Google AI Studio.")
            print("Formato esperado: GEMINI_API_KEY=AIza...")
            return

        print(f"\n❌ Ocorreu um erro durante a conversa: {error}")


if __name__ == "__main__":
    main()