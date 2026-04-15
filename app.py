import streamlit as st
from rag import ask_question

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Asistente de Estudio",
    page_icon="📚"
)

# ESTADO INICIAL
if "messages" not in st.session_state:
    st.session_state.messages = []

if "modo" not in st.session_state:
    st.session_state.modo = "Detallada"

# SIDEBAR (CONFIGURACIÓN)
with st.sidebar:
    st.title("Configuración")

    modo = st.selectbox(
        "Tipo de respuesta",
        ["Corta", "Detallada", "Resumen"],
        index=["Corta", "Detallada", "Resumen"].index(st.session_state.modo)
    )

    st.session_state.modo = modo


# TÍTULO PRINCIPAL
st.title("Asistente de estudio")

# MOSTRAR HISTORIAL
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# INPUT DEL USUARIO
prompt = st.chat_input("Haz una pregunta...")

if prompt:
    # GUARDAR MENSAJE USUARIO
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    # RESPUESTA DEL SISTEMA
    with st.chat_message("assistant"):
        respuesta, docs = ask_question(prompt, st.session_state.modo)

        st.write(respuesta)

        # MOSTRAR DOCUMENTOS USADOS
        with st.expander("📄 Ver fuentes usadas"):
            for i, doc in enumerate(docs):
                st.markdown(f"**Documento {i+1}:**")
                st.write(doc.page_content[:200] + "...")
                st.write(f"Fuente: {doc.metadata.get('source', 'Desconocido')}")
                st.write("---")

    # GUARDAR RESPUESTA
    st.session_state.messages.append({
        "role": "assistant",
        "content": respuesta
    })