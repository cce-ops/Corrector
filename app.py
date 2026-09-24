import streamlit as st
import chromadb
from pypdf import PdfReader
from openai import OpenAI
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
    st.info("Elige el motor de IA. Si estás en la web usa Gemini/Groq. Si ejecutas esto en tu PC, usa Ollama para máxima privacidad.")
    
    proveedor = st.selectbox(
        "Proveedor de Inteligencia Artificial",
        ["Google Gemini (Nube)", "Groq (Nube)", "Ollama (Local)"]
    )
    
    if proveedor == "Ollama (Local)":
        modelo_local = st.text_input("Nombre del modelo en Ollama:", value="qwen2.5")
        st.caption("Asegúrate de tener la app Ollama encendida en tu ordenador y el modelo descargado.")
        api_key_usuario = "ollama_no_necesita_clave" # Valor dummy
    else:
        api_key_usuario = st.text_input(f"API Key de {proveedor}:", type="password")
        st.caption("🔑 [Conseguir clave de Gemini](https://aistudio.google.com/app/apikey) | [Clave de Groq](https://console.groq.com/keys)")

# --- INTERFAZ PRINCIPAL ---
st.title("🤖 Evaluador de Informes (Proyectos de Ingeniería)", 
         help="**¿Por qué usar esto y no ChatGPT directamente?**\n\nEsta herramienta utiliza RAG y Salidas JSON.\n\nAl contrario que subir un PDF a Gemini donde la IA opina libremente, este sistema obliga al modelo a leer PRIMERO tus apuntes (Base de Conocimiento) y a devolver el feedback siempre en formato estricto, garantizando consistencia.")

tab1, tab2 = st.tabs(["📚 1. Subir Base de Conocimiento", "📝 2. Evaluar Informe del Alumno"])

# --- PESTAÑA 1: BASE DE CONOCIMIENTO ---
with tab1:
    st.header("Alimentar el sistema", 
              help="**¿Dónde se guardan estos PDF?**\n\nSe procesan y se guardan en una base de datos vectorial interna (ChromaDB). En la nube se borran si el servidor se duerme por inactividad. En local se guardan para siempre en tu disco duro.")
    st.info("Sube apuntes, rúbricas o proyectos excelentes de años anteriores.")
    
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
    st.header("Evaluar un nuevo trabajo", 
              help="**Privacidad del alumno:**\n\nLos informes subidos aquí NO SE GUARDAN. Se analizan en memoria temporal y desaparecen al instante.")
    informe_alumno = st.file_uploader("Sube el informe del alumno (PDF)", type="pdf", key="alumno")
    
    if st.button("Analizar y Evaluar", 
                 help="Si usas la nube y te da error '503' o 'Rate limit', el servidor esperará 5 segundos y reintentará automáticamente."):
        
        if proveedor != "Ollama (Local)" and not api_key_usuario:
            st.error(f"⚠️ Falta la API Key. Por favor, introduce tu clave de {proveedor} en la barra lateral.")
            st.stop()
            
        if not informe_alumno:
            st.warning("Sube el informe del alumno para comenzar.")
            st.stop()
            
        with st.spinner("Extrayendo texto del informe..."):
            texto_alumno = extraer_texto_pdf(informe_alumno)
            
            if proveedor == "Groq":
                texto_alumno = texto_alumno[:15000]
                st.toast("Aviso: Con Groq se limita la lectura a ~5 páginas para evitar saturar la API gratuita.", icon="⚠️")
            
        with st.spinner("Buscando referencias en la base de conocimiento..."):
            if collection.count() == 0:
                contexto_recuperado = "No hay contexto disponible."
            else:
                resultados = collection.query(query_texts=[texto_alumno[:3000]], n_results=4)
                if resultados["documents"]:
                    contexto_recuperado = "\n\n---\n\n".join(resultados["documents"][0])
                else:
                    contexto_recuperado = "No se encontró contexto relevante."
                    
        with st.spinner("La IA está evaluando el informe exhaustivamente..."):
            
            # --- CONFIGURACIÓN DEL MOTOR SEGÚN ELECCIÓN ---
            extra_args = {}
            if proveedor == "Google Gemini (Nube)":
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
                modelos_a_probar = ["gemini-1.5-flash"]
            elif proveedor == "Groq (Nube)":
                base_url = "https://api.groq.com/openai/v1"
                modelos_a_probar = ["openai/gpt-oss-120b"]
            elif proveedor == "Ollama (Local)":
                base_url = "http://localhost:11434/v1"
                modelos_a_probar = [modelo_local]
                # Forzar 32K de contexto para leer informes enteros en local
                extra_args = {"extra_body": {"options": {"num_ctx": 32000}}}

            cliente_llm = OpenAI(base_url=base_url, api_key=api_key_usuario)
            
            prompt = f"""
            Eres un profesor evaluando un informe técnico de proyectos de ingeniería. 
            Tu objetivo principal es dar feedback exhaustivo, constructivo y detallado para que el alumno mejore.
            
            CONTEXTO DE REFERENCIA (Apuntes y proyectos anteriores):
            {contexto_recuperado}
            
            INFORME DEL ALUMNO A EVALUAR:
            {texto_alumno} 
            
            INSTRUCCIONES CRÍTICAS:
            1. Analiza exhaustivamente TODO el documento.
            2. Identifica TODOS los errores, fallos de cálculo, faltas de formato o ausencias de contenido.
            3. Por cada error, DEBES explicar qué está mal y cómo sugerirías corregirlo detalladamente.
            4. Devuelve el resultado ÚNICAMENTE en formato JSON CRUDO. NO incluyas bloques de código Markdown.
            
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
            
            # --- BUCLE DE EVALUACIÓN Y REINTENTOS (CUBRE ERROR 503) ---
            for modelo in modelos_a_probar:
                exito = False
                intentos = 2
                
                for intento in range(intentos):
                    try:
                        st.toast(f"Intentando con {modelo} (Intento {intento+1}/{intentos})...", icon="🔄")
                        respuesta = cliente_llm.chat.completions.create(
                            model=modelo, 
                            messages=[
                                {"role": "system", "content": "Eres un servidor que SOLO devuelve código JSON válido."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.1,
                            response_format={"type": "json_object"},
                            **extra_args # Aplica memoria extra si es Ollama
                        )
                        respuesta_json = json.loads(respuesta.choices[0].message.content)
                        st.toast(f"¡Éxito con {modelo}!", icon="✅")
                        exito = True
                        break
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "503" in error_msg or "429" in error_msg:
                            st.toast("Servidor ocupado. Reintentando en 5 segundos...", icon="⏳")
                            time.sleep(5) 
                        else:
                            break # Error crítico (ej. Ollama apagado o clave falsa)
                            
                if exito:
                    break
            
            # --- MOSTRAR RESULTADOS ---
            if respuesta_json:
                dic_resultado = respuesta_json
                st.success("✅ Evaluación completada")
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
            else:
                st.error(f"Fallo en la evaluación. Último error: {error_msg}")
