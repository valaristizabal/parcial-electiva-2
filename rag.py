from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnableLambda, RunnableSequence
from dotenv import load_dotenv
import os

load_dotenv()

PDF_FOLDER = "./pdfs"

# se crea la vecrorstore a partir de los pdfs, 
# se guarda en cache para no tener que volver a cargarlo cada vez
def create_vectorstore():

    docs = []

    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            print(f"Cargando PDF: {file}")
            #carganos los pdfs y lo convertimos a ttexto
            loader = PyPDFLoader(os.path.join(PDF_FOLDER, file))
            docs.extend(loader.load())

    #el texto lo dividmos en trozos pequeños para que la IA lo procese mejor
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)

    print(f"Total chunks generados: {len(chunks)}")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001"
    )

    #se crea la base de datos vectorial a partir de los chunks y sus embeddings
    vectorstore = FAISS.from_documents(chunks, embeddings)

    print("Vectorstore listo")

    return vectorstore

_vectorstore = None
#se crea una única vez para no tener que recalcular cada que se haga una pregunta
def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = create_vectorstore()
    return _vectorstore

#El runnable 0 limpia la pregunta del usuario
def step0(data):
    print("\n Runnable 0: Limpiando pregunta")

    data["question"] = data["question"].strip().lower()

    return data

runnable0 = RunnableLambda(step0)
#el primer runnable recibe la pregunta
def step1(data):
    print("\n Runnable 1: Recibiendo pregunta")
    print(f"Pregunta: {data['question']}")
    return data

runnable1 = RunnableLambda(step1)

#el segundo runnable recupera los documentos relevantes para la pregunta del vectorstore
def step2(data):
    print("\n Runnable 2: Recuperando documentos")

    vectorstore = get_vectorstore()

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 2}
    )

    docs = retriever.invoke(data["question"])

    print(f"Documentos encontrados: {len(docs)}")

    return {
        "question": data["question"],
        "modo": data["modo"],
        "docs": docs
    }
runnable2 = RunnableLambda(step2)

# el tercer runnable construye el prompt para la IA usanso la pregunta y los documentos recuperados
def step3(data):
    print("\n Runnable 3: Construyendo prompt")

    context = "\n\n".join([doc.page_content for doc in data["docs"]]) #aquí juntamos todos los documentos en uno solo

    prompt = f"""
        Responde la pregunta basándote en el contexto.

        Modo de respuesta: {data['modo']}

        Contexto:
        {context}

        Pregunta: {data['question']}
    """

    return prompt

runnable3 = RunnableLambda(step3)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2 #la temperatura para que sea más preciso
)

#el cuarto runnable genera la respuesta usando el prompt construido y el modelo de lenguaje
def step4(prompt):
    print("\nRunnable 4: Generando respuesta con LLM")

    response = llm.invoke(prompt) #se genera la respuests

    print("Respuesta generada (primeros 200 caracteres):")
    print(response.content[:200])

    return response.content

runnable4 = RunnableLambda(step4)

#se crea el pipeline que encadena los 4 runnables
pipeline = RunnableSequence(
    runnable0,
    runnable1,
    runnable2,
    runnable3,
    runnable4
)

#se llama desde app para hacer la pregunta y tener la respuesta
def ask_question(question, modo):
    print(" EJECUTANDO PIPELINE COMPLETO")

    data = {
        "question": question,
        "modo": modo
    }

    respuesta = pipeline.invoke(data)

    # reutilizamos el mismo flujo para obtener docs
    data_with_docs = step2(data)

    return respuesta, data_with_docs["docs"]