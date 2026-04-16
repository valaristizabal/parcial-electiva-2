import streamlit as st
from rag import ask_question

st.set_page_config(
    page_title="Asistente de Estudio",
    page_icon="📚"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "modo" not in st.session_state:
    st.session_state.modo = "Detallada"

# sidebar
with st.sidebar:
    st.title("Configuración")

    modo = st.selectbox(
        "Tipo de respuesta",
        ["Corta", "Detallada", "Resumen"],
        index=["Corta", "Detallada", "Resumen"].index(st.session_state.modo)
    )

    st.session_state.modo = modo


st.title("Asistente de estudio")

#muestra el historial de mensajes
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# muestra el input
prompt = st.chat_input("Haz una pregunta...")

if prompt:
    # guarda el mensaje del usuario
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    # myestra la respuesta del asistente
    with st.chat_message("assistant"):
        respuesta, docs = ask_question(prompt, st.session_state.modo)

        st.write(respuesta)

        # muestra que documentos fueron usados
        with st.expander("📄 Ver fuentes usadas"):
            for i, doc in enumerate(docs):
                st.markdown(f"**Documento {i+1}:**")
                st.write(doc.page_content[:200] + "...")
                st.write(f"Fuente: {doc.metadata.get('source', 'Desconocido')}")
                st.write("---")

    # se guarda la respuesta
    st.session_state.messages.append({
        "role": "assistant",
        "content": respuesta
    })