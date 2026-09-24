import streamlit as st
import chromadb
from pypdf import PdfReader
from openai import OpenAI
from anthropic import Anthropic
import json
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Evaluador de Informes IA", layout="wide")

# --- INICIALIZACIÓN DE LA BASE DE DATOS VECTORIAL (RAG) ---
@st.cache_resource
def init_chroma():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="base_conocimiento")
    return collection

collection = init_chroma()

# --- FUNCIONES AUXILIARES ---
def extraer_texto_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    texto = ""
    for page in reader.pages:
        if page.extract_text():
            texto += page.extract_text() + "\n"
    return texto

# --- BARRA LATERAL: CONFIGURACIÓN DEL PROFESOR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    st.info("Elige el motor de IA. En la nube usarás tu API Key. En local (Ollama) el proceso es privado y gratuito.")
    
    proveedor = st.selectbox(
        "Proveedor de Inteligencia Artificial",
        ["Google Gemini", "OpenAI (ChatGPT)", "Anthropic (Claude)", "Groq", "Ollama (Local)"]
    )
    
    api_key_usuario = ""
    modelo_local = ""
    
    if proveedor == "Ollama (Local)":
        opcion_modelo = st.selectbox(
            "Selecciona el modelo descargado:",
            ["qwen2.5", "llama3.1", "mistral-nemo", "Otro (Escribir manualmente)"]
        )
        if opcion_modelo == "Otro (Escribir manualmente)":
            modelo_local = st.text_input("Escribe el nombre exacto del modelo:", value="llama3.2")
        else:
            modelo_local = opcion_modelo
            
        st.caption("Asegúrate de tener la app Ollama abierta en tu PC.")
    
    elif proveedor == "OpenAI (ChatGPT)":
        api_key_usuario = st.text_input("API Key de OpenAI:", type="password")
        modelo_nube = st.selectbox("Modelo:", ["gpt-4o", "gpt-4o-mini"])
    
    elif proveedor == "Anthropic (Claude)":
        api_key_usuario = st.text_input("API Key de Anthropic:", type="password")
        modelo_nube = st.selectbox("Modelo:", ["claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"])
        
    elif proveedor == "Google Gemini":
        api_key_usuario = st.text_input("API Key de Gemini:", type="password")
        modelo_nube = st.selectbox("Modelo:", ["gemini-1.5-flash", "gemini-1.5-pro"])
        st.caption("🔑 [Conseguir clave de Gemini Gratis](https://aistudio.google.com/app/apikey)")
        
    elif proveedor == "Groq":
        api_key_usuario = st.text_input("API Key de Groq:", type="password")
        modelo_nube = "openai/gpt-oss-120b"
        st.caption("🔑 [Clave de Groq Gratis (Límite 5 págs)](https://console.groq.com/keys)")

# --- INTERFAZ PRINCIPAL ---
st.title("🤖 Evaluador de Informes (Proyectos de Ingeniería)")

tab1, tab2 = st.tabs(["📚 1. Subir Base de Conocimiento", "📝 2. Evaluar Informe del Alumno"])

# --- PESTAÑA 1: BASE DE CONOCIMIENTO ---
with tab1:
    st.header("Alimentar el sistema")
    st.info("Sube apuntes o rúbricas. Se usarán como memoria (RAG) para corregir.")
    
    referencias = st.file_uploader("Sube PDFs de referencia", type="pdf", accept_multiple_files=True)
    
    if st.button("Procesar y guardar referencias"):
        if referencias:
            for ref in referencias:
                with st.spinner(f"Procesando {ref.name}..."):
                    texto = extraer_texto_pdf(ref)
                    chunk_size = 1000
                    chunks = [texto[i:i + chunk_size] for i in range(0, len(texto), chunk_size)]
                    ids = [f"{ref.name}_chunk_{i}" for i in range(len(chunks))]
                    
                    collection.add(
                        documents=chunks,
                        ids=ids,
                        metadatas=[{"fuente": ref.name} for _ in chunks]
                    )
            st.success(f"✅ ¡{len(referencias)} documentos añadidos a la base de conocimiento!")
        else:
            st.warning("Por favor, sube al menos un documento PDF.")

# --- PESTAÑA 2: EVALUACIÓN ---
with tab2:
    st.header("Evaluar un nuevo trabajo")
    informe_alumno = st.file_uploader("Sube el informe del alumno (PDF)", type="pdf", key="alumno")
    
    if st.button("Analizar y Evaluar"):
        
        if proveedor != "Ollama (Local)" and not api_key_usuario:
            st.error(f"⚠️ Falta la API Key. Por favor, introdúcela en la barra lateral.")
            st.stop()
            
        if not informe_alumno:
            st.warning("Sube el informe del alumno para comenzar.")
            st.stop()
            
        with st.spinner("Extrayendo texto del informe..."):
            texto_alumno = extraer_texto_pdf(informe_alumno)
            if proveedor == "Groq":
                texto_alumno = texto_alumno[:15000]
            elif proveedor == "Anthropic (Claude)":
                texto_alumno = texto_alumno[:50000] # Claude no RAG soporta muchísimo, pero limitamos por tokens de salida
            
        with st.spinner("Buscando referencias en la base de conocimiento..."):
            if collection.count() == 0:
                contexto_recuperado = "No hay contexto disponible."
            else:
                resultados = collection.query(query_texts=[texto_alumno[:3000]], n_results=4)
                if resultados["documents"]:
                    contexto_recuperado = "\n\n---\n\n".join(resultados["documents"][0])
                else:
                    contexto_recuperado = "No se encontró contexto relevante."
                    
        with st.spinner(f"La IA ({proveedor}) está evaluando el informe exhaustivamente..."):
            
            prompt = f"""
            Eres un profesor evaluando un informe técnico de ingeniería. 
            Da feedback exhaustivo, constructivo y detallado para que el alumno mejore.
            
            CONTEXTO DE REFERENCIA (Apuntes y rúbricas):
            {contexto_recuperado}
            
            INFORME DEL ALUMNO A EVALUAR:
            {texto_alumno} 
            
            INSTRUCCIONES CRÍTICAS:
            1. Analiza exhaustivamente TODO el documento.
            2. Identifica TODOS los errores técnicos, faltas de formato o ausencias de contenido.
            3. Por cada error, explica qué está mal y cómo corregirlo detalladamente.
            4. Devuelve ÚNICAMENTE formato JSON CRUDO. NO uses markdown (```json).
            
            ESTRUCTURA JSON EXACTA:
            {{
              "nota_global": (número decimal sobre 10),
              "resumen_analisis": "Un párrafo resumiendo el nivel general.",
              "puntos_fuertes": ["Punto fuerte 1"],
              "puntos_a_corregir": [
                {{
                  "que_esta_mal": "Descripción detallada del error",
                  "como_corregir": "Sugerencia concreta sobre cómo solucionarlo"
                }}
              ]
            }}
            """
            
            respuesta_json = None
            error_msg = ""
            
            try:
                if proveedor == "Anthropic (Claude)":
                    cliente_claude = Anthropic(api_key=api_key_usuario)
                    respuesta = cliente_claude.messages.create(
                        model=modelo_nube,
                        max_tokens=4000,
                        temperature=0.1,
                        messages=[
                            {"role": "user", "content": prompt + "\n\nResponde SOLO con el objeto JSON solicitado, empezando por {"}
                        ]
                    )
                    respuesta_json = json.loads(respuesta.content[0].text)
                    
                else:
                    extra_args = {}
                    if proveedor == "Google Gemini":
                        base_url = "[https://generativelanguage.googleapis.com/v1beta/openai/](https://generativelanguage.googleapis.com/v1beta/openai/)"
                        modelo_usar = modelo_nube
                    elif proveedor == "OpenAI (ChatGPT)":
                        base_url = "[https://api.openai.com/v1](https://api.openai.com/v1)"
                        modelo_usar = modelo_nube
                    elif proveedor == "Groq":
                        base_url = "[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)"
                        modelo_usar = modelo_nube
                    elif proveedor == "Ollama (Local)":
                        base_url = "http://localhost:11434/v1"
                        modelo_usar = modelo_local
                        api_key_usuario = "ollama"
                        extra_args = {"extra_body": {"options": {"num_ctx": 32000}}}

                    cliente_llm = OpenAI(base_url=base_url, api_key=api_key_usuario)
                    
                    # Intentos de llamada para la API de OpenAI-compatible
                    intentos = 2
                    for intento in range(intentos):
                        try:
                            respuesta = cliente_llm.chat.completions.create(
                                model=modelo_usar, 
                                messages=[
                                    {"role": "system", "content": "Eres un servidor que SOLO devuelve código JSON válido."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.1,
                                response_format={"type": "json_object"} if proveedor != "Ollama (Local)" else None, 
                                **extra_args
                            )
                            texto_respuesta = respuesta.choices[0].message.content
                            
                            # Limpieza por si Ollama devuelve markdown de todas formas
                            if texto_respuesta.startswith("```json"):
                                texto_respuesta = texto_respuesta[7:-3]
                            
                            respuesta_json = json.loads(texto_respuesta.strip())
                            break # Exito
                            
                        except Exception as e:
                            error_msg = str(e)
                            if "503" in error_msg or "429" in error_msg:
                                st.toast("Servidor ocupado. Reintentando en 5 segundos...", icon="⏳")
                                time.sleep(5) 
                            else:
                                raise e # Falla y salta al except principal

            except Exception as e:
                st.error(f"Fallo en la evaluación: {e}")
            
            # --- MOSTRAR RESULTADOS ---
            if respuesta_json:
                dic_resultado = respuesta_json
                st.success(f"✅ Evaluación completada ({proveedor})")
                st.markdown(f"### 🎯 Nota Global: **{dic_resultado.get('nota_global', 0)} / 10**")
                st.info(f"**Resumen del Análisis:**\n\n{dic_resultado.get('resumen_analisis', 'Sin resumen.')}")
                
                st.divider()
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("🌟 Puntos Fuertes")
                    for punto in dic_resultado.get('puntos_fuertes', []):
                        st.write(f"- {punto}")
                        
                with col2:
                    st.error("🛠️ Áreas de Mejora y Correcciones")
                    for item in dic_resultado.get('puntos_a_corregir', []):
                        st.markdown(f"**❌ Qué está mal:** {item.get('que_esta_mal', '')}")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**💡 Cómo corregir:** _{item.get('como_corregir', '')}_")
                        st.write("")
