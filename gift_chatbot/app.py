"""Interface web (Streamlit) do Detetive do Presente AI."""

import os
from pathlib import Path
from typing import List

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv


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


def build_initial_history() -> List[dict]:
    """Cria histórico inicial com instruções de comportamento."""
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


@st.cache_resource
def configure_model() -> genai.GenerativeModel:
    """Configura Gemini usando variável de ambiente e retorna modelo."""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    secret_key = ""
    try:
        secret_key = str(st.secrets.get("GEMINI_API_KEY", ""))
    except Exception:
        secret_key = ""

    api_key = (secret_key or os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada. Crie um arquivo .env com sua chave da API."
        )

    genai.configure(api_key=api_key)
    model_name = choose_supported_model_name()
    st.session_state["selected_model"] = model_name
    return genai.GenerativeModel(model_name=model_name)


def generate_suggestions_from_profile(model: genai.GenerativeModel, answers: List[str]) -> str:
    """Gera recomendações com base nas respostas coletadas."""
    lines = [f"- {question} {answer}" for question, answer in zip(STEP_BY_STEP_QUESTIONS, answers)]
    summary = "\n".join(lines)

    prompt = (
        "Com base no perfil abaixo, gere agora 3 a 5 sugestões personalizadas de presente.\n"
        "Inclua nome do presente, explicação curta e preço aproximado em cada item.\n"
        "\nPerfil coletado:\n"
        f"{summary}"
    )

    history = build_initial_history()
    history.append({"role": "user", "parts": [prompt]})
    response = model.generate_content(history)
    return response.text


def generate_suggestions_from_message(model: genai.GenerativeModel, message: str) -> str:
    """Gera recomendações a partir de uma mensagem única do usuário."""
    prompt = (
        "Mensagem do usuário com os detalhes para sugestão de presente:\n"
        f"{message}\n\n"
        "Se houver informações suficientes, gere 3 a 5 sugestões agora. "
        "Se faltar algo essencial, faça apenas uma pergunta objetiva."
    )

    history = build_initial_history()
    history.append({"role": "user", "parts": [prompt]})
    response = model.generate_content(history)
    return response.text


def reset_step_mode_state() -> None:
    """Reinicia o estado do modo passo a passo."""
    st.session_state["step_index"] = 0
    st.session_state["step_answers"] = [""] * len(STEP_BY_STEP_QUESTIONS)


def render_step_by_step_mode(model: genai.GenerativeModel) -> None:
    """Renderiza o fluxo investigativo de perguntas sequenciais."""
    if "step_index" not in st.session_state or "step_answers" not in st.session_state:
        reset_step_mode_state()

    step_index = st.session_state["step_index"]
    step_answers: List[str] = st.session_state["step_answers"]

    if step_index < len(STEP_BY_STEP_QUESTIONS):
        question = STEP_BY_STEP_QUESTIONS[step_index]
        st.write(f"🕵️ Pista {step_index + 1}/{len(STEP_BY_STEP_QUESTIONS)}")
        answer = st.text_input(question, key=f"question_{step_index}")

        if st.button("Salvar resposta e próxima pergunta", use_container_width=True):
            cleaned = answer.strip() if answer.strip() else "(não informado)"
            step_answers[step_index] = cleaned
            st.session_state["step_answers"] = step_answers
            st.session_state["step_index"] = step_index + 1
            st.rerun()
    else:
        st.success("✅ Informações coletadas. Pronto para gerar sugestões!")
        with st.expander("Ver resumo das pistas"):
            for question, answer in zip(STEP_BY_STEP_QUESTIONS, step_answers):
                st.write(f"- **{question}** {answer}")

        col1, col2 = st.columns(2)
        with col1:
            generate_clicked = st.button("Gerar sugestões de presente", use_container_width=True)
        with col2:
            restart_clicked = st.button("Reiniciar investigação", use_container_width=True)

        if restart_clicked:
            reset_step_mode_state()
            st.rerun()

        if generate_clicked:
            with st.spinner("Investigando ideias perfeitas..."):
                result = generate_suggestions_from_profile(model, step_answers)
            st.markdown("### 🧩 Caso resolvido! Aqui estão as pistas de presentes:")
            st.write(result)


def render_single_message_mode(model: genai.GenerativeModel) -> None:
    """Renderiza o modo de mensagem única."""
    st.write("Digite todos os detalhes em uma mensagem e o detetive gera as sugestões.")
    user_message = st.text_area(
        "Mensagem",
        placeholder=(
            "Ex.: Preciso de um presente para minha amiga de 20 anos que ama astronomia. "
            "Meu orçamento é de 100 reais."
        ),
        height=120,
    )

    if st.button("Investigar e sugerir presentes", use_container_width=True):
        if not user_message.strip():
            st.warning("Digite uma mensagem com os detalhes para continuar.")
            return

        with st.spinner("Investigando ideias perfeitas..."):
            result = generate_suggestions_from_message(model, user_message.strip())
        st.markdown("### 🔎 Resultado da investigação:")
        st.write(result)


def main() -> None:
    """Ponto de entrada da aplicação web."""
    st.set_page_config(page_title="Detetive do Presente AI", page_icon="🕵️", layout="centered")

    st.title("🕵️ Detetive do Presente AI")
    st.write("Vamos investigar o presente ideal com IA Generativa.")

    try:
        model = configure_model()
    except Exception as error:
        st.error(f"Erro ao configurar Gemini: {error}")
        return

    selected_model = st.session_state.get("selected_model", "(desconhecido)")
    st.caption(f"Modelo Gemini em uso: {selected_model}")

    mode = st.radio(
        "How would you like to interact?",
        ["1 - Answer questions step by step", "2 - Write everything in one message"],
    )

    if mode.startswith("1"):
        render_step_by_step_mode(model)
    else:
        render_single_message_mode(model)


if __name__ == "__main__":
    main()