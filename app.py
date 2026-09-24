import streamlit as st
import chromadb
from pypdf import PdfReader
from openai import OpenAI
import json

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

# --- INTERFAZ DE USUARIO ---
st.title("🤖 Evaluador de Informes (Proyectos de Ingeniería)", 
         help="**¿Por qué usar esto y no ChatGPT directamente?**\n\nEsta herramienta utiliza RAG (Generación Aumentada por Recuperación) y Salidas Estructuradas JSON.\n\nAl contrario que subir un PDF a Gemini o Claude donde la IA opina libremente, este sistema obliga al modelo a leer PRIMERO tus apuntes y rúbricas (Base de Conocimiento) y a devolver el feedback siempre en el mismo formato estricto (Puntos fuertes y Correcciones detalladas), garantizando una consistencia que no se logra en un chat abierto.")

tab1, tab2 = st.tabs(["📚 1. Subir Base de Conocimiento", "📝 2. Evaluar Informe del Alumno"])

# --- PESTAÑA 1: BASE DE CONOCIMIENTO ---
with tab1:
    st.header("Alimentar el sistema", 
              help="**¿Dónde se guardan estos PDF?**\n\nLos archivos que subas aquí SÍ se procesan y se guardan en una base de datos vectorial interna en el servidor (ChromaDB) mientras la aplicación esté activa. Permanecerán ahí como memoria colectiva para evaluar los proyectos nuevos, hasta que el servidor se reinicie tras días de inactividad.")
    st.info("Sube apuntes, rúbricas o proyectos excelentes de años anteriores. El modelo los usará como referencia para evaluar.")
    
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
            st.write(f"Total de fragmentos en base de datos: {collection.count()}")
        else:
            st.warning("Por favor, sube al menos un documento PDF.")

# --- PESTAÑA 2: EVALUACIÓN ---
with tab2:
    st.header("Evaluar un nuevo trabajo", 
              help="**Privacidad del alumno:**\n\nA diferencia de la pestaña anterior, los informes que subas aquí NO SE GUARDAN. Se procesan temporalmente en la memoria RAM del servidor para extraer el texto, se evalúan, y desaparecen en cuanto cierras la aplicación.")
    informe_alumno = st.file_uploader("Sube el informe del alumno (PDF)", type="pdf", key="alumno")
    
    # El botón ahora tiene el tooltip sobre los errores de Rate Limit
    if st.button("Analizar y Evaluar", 
                 help="**Si te da error 'Rate limit exceeded' o '429 Too Many Requests':**\n\nEstás usando una API gratuita que tiene un límite de evaluaciones por minuto/día.\nNo te preocupes, el límite es temporal. Si evalúas muchos proyectos seguidos, espera unos minutos o inténtalo al día siguiente y el servicio se restablecerá automáticamente."):
        
        if not informe_alumno:
            st.warning("Sube el informe del alumno para comenzar.")
            st.stop()
            
        if "GROQ_API_KEY" not in st.secrets:
            st.error("⚠️ Falta la API Key de Groq. Configúrala en los secretos de Streamlit.")
            st.stop()
            
        with st.spinner("Extrayendo texto del informe..."):
            texto_alumno = extraer_texto_pdf(informe_alumno)
            
        with st.spinner("Buscando referencias en la base de conocimiento..."):
            if collection.count() == 0:
                st.warning("No hay base de conocimiento cargada. Se evaluará sin contexto previo.")
                contexto_recuperado = "No hay contexto disponible."
            else:
                resultados = collection.query(query_texts=[texto_alumno[:2000]], n_results=3)
                if resultados["documents"]:
                    contexto_recuperado = "\n\n---\n\n".join(resultados["documents"][0])
                else:
                    contexto_recuperado = "No se encontró contexto relevante."
                    
        with st.spinner("La IA está evaluando el informe exhaustivamente. Esto tomará unos segundos..."):
            cliente_llm = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=st.secrets["GROQ_API_KEY"]
            )
            
            prompt = f"""
            Eres un profesor evaluando un informe técnico de proyectos de ingeniería. 
            Tu objetivo principal es dar feedback exhaustivo, constructivo y detallado para que el alumno mejore.
            
            CONTEXTO DE REFERENCIA (Apuntes y proyectos anteriores):
            {contexto_recuperado}
            
            INFORME DEL ALUMNO A EVALUAR:
            {texto_alumno[:50000]} 
            
            INSTRUCCIONES CRÍTICAS:
            1. Analiza exhaustivamente el documento.
            2. Identifica TODOS los errores, fallos de cálculo, faltas de formato o ausencias de contenido.
            3. Por cada error, DEBES explicar qué está mal y cómo sugerirías corregirlo detalladamente.
            4. Devuelve el resultado ÚNICAMENTE en formato JSON CRUDO. NO incluyas bloques de código Markdown (```json). Empieza directamente con {{ y termina con }}.
            
            ESTRUCTURA JSON EXACTA:
            {{
              "nota_global": (número decimal sobre 10),
              "resumen_analisis": "Un párrafo de 4 o 5 líneas resumiendo el nivel general del trabajo, el esfuerzo demostrado y las deficiencias clave.",
              "puntos_fuertes": [
                "Punto fuerte 1",
                "Punto fuerte 2"
              ],
              "puntos_a_corregir": [
                {{
                  "que_esta_mal": "Descripción detallada del error o aspecto deficiente",
                  "como_corregir": "Sugerencia concreta, técnica y constructiva sobre cómo solucionarlo"
                }}
              ]
            }}
            """
            
            try:
                respuesta = cliente_llm.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": "Eres un servidor que SOLO devuelve código JSON válido. Nada de texto introductorio."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000,
                    response_format={"type": "json_object"}
                )
                
                dic_resultado = json.loads(respuesta.choices[0].message.content)
                
                st.success("✅ Evaluación completada")
                st.markdown(f"### 🎯 Nota Global: **{dic_resultado.get('nota_global', 0)} / 10**")
                st.info(f"**Resumen del Análisis:**\n\n{dic_resultado.get('resumen_analisis', 'Sin resumen.')}")
                
                st.divider()
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("🌟 Puntos Fuertes")
                    puntos_fuertes = dic_resultado.get('puntos_fuertes', [])
                    if puntos_fuertes:
                        for punto in puntos_fuertes:
                            st.write(f"- {punto}")
                    else:
                        st.write("No se han identificado puntos fuertes destacables.")
                        
                with col2:
                    st.error("🛠️ Áreas de Mejora y Correcciones")
                    puntos_a_corregir = dic_resultado.get('puntos_a_corregir', [])
                    if puntos_a_corregir:
                        for item in puntos_a_corregir:
                            st.markdown(f"**❌ Qué está mal:** {item.get('que_esta_mal', '')}")
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**💡 Cómo corregir:** _{item.get('como_corregir', '')}_")
                            st.write("") 
                    else:
                        st.write("No se han encontrado errores significativos. ¡Excelente trabajo!")
                        
            except Exception as e:
                st.error(f"Ocurrió un error al generar la evaluación: {e}")
