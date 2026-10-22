import streamlit as st
import pandas as pd

from pln import responder

st.set_page_config(
    page_title="UniBot",
    page_icon="🎓",
    layout="wide",
)

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "consultas" not in st.session_state:
    st.session_state.consultas = []

st.title("chatbot escolar")
st.caption("Asistente universitario inteligente ")

total = len(st.session_state.consultas)
resueltas = sum(
    c["resuelta"] for c in st.session_state.consultas
)

col1, col2, col3 = st.columns(3)
col1.metric("Consultas", total)
col2.metric("Resueltas", resueltas)
col3.metric(
    "Sin respuesta",
    total - resueltas,
)

tab1, tab2, tab3 = st.tabs([
    "Chatbot",
    "Estadísticas",
    "Base de conocimiento",
])

with tab1:
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["rol"]):
            st.write(mensaje["texto"])

    pregunta = st.chat_input("Escribe tu pregunta universitaria...")

    if pregunta:
        st.session_state.mensajes.append({
            "rol": "user",
            "texto": pregunta,
        })

        resultado = responder(pregunta)

        st.session_state.mensajes.append({
            "rol": "assistant",
            "texto": resultado["respuesta"],
        })

        st.session_state.consultas.append({
            "pregunta": pregunta,
            "categoria": resultado["categoria"],
            "confianza": resultado["confianza"],
            "resuelta": resultado["resuelta"],
        })

        st.rerun()

with tab2:
    if st.session_state.consultas:
        df = pd.DataFrame(st.session_state.consultas)

        st.subheader("Consultas por categoría")
        st.bar_chart(df["categoria"].value_counts())

        st.subheader("Historial de consultas")
        st.dataframe(df, use_container_width=True)

    else:
        st.info("Aún no hay consultas. Prueba el chatbot.")

with tab3:
    st.subheader("Preguntas frecuentes")

    from pln import FAQ

    df_faq = pd.DataFrame(FAQ)
    st.dataframe(df_faq, use_container_width=True)