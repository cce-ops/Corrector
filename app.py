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
st.title("🤖 Evaluador de Informes (Proyectos de Ingeniería)")

tab1, tab2 = st.tabs(["📚 1. Subir Base de Conocimiento", "📝 2. Evaluar Informe del Alumno"])

# --- PESTAÑA 1: BASE DE CONOCIMIENTO ---
with tab1:
    st.header("Alimentar el sistema")
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
    st.header("Evaluar un nuevo trabajo")
    informe_alumno = st.file_uploader("Sube el informe del alumno (PDF)", type="pdf", key="alumno")
    
    if st.button("Analizar y Evaluar"):
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
            
            # --- NUEVO PROMPT EXHAUSTIVO ---
            prompt = f"""
            Eres un profesor evaluando un informe técnico de proyectos de ingeniería. 
            Tu objetivo principal es dar feedback exhaustivo, constructivo y detallado para que el alumno mejore.
            
            CONTEXTO DE REFERENCIA (Apuntes y proyectos anteriores):
            {contexto_recuperado}
            
            INFORME DEL ALUMNO A EVALUAR:
            {texto_alumno[:20000]}
            
            INSTRUCCIONES CRÍTICAS:
            1. Analiza exhaustivamente TODO el documento.
            2. Identifica TODOS los errores, fallos de cálculo, faltas de formato o ausencias de contenido. No te limites a unos pocos; enumera TODOS los que encuentres.
            3. Por cada error, DEBES explicar qué está mal y cómo sugerirías corregirlo detalladamente.
            4. Devuelve el resultado ÚNICAMENTE en formato JSON.
            
            ESTRUCTURA JSON EXACTA:
            {{
              "nota_global": (número decimal sobre 10),
              "resumen_analisis": "Un párrafo de 4 o 5 líneas resumiendo el nivel general del trabajo, el esfuerzo demostrado y las deficiencias clave.",
              "puntos_fuertes": [
                "Punto fuerte 1",
                "Punto fuerte 2", ... (todos los que consideres)
              ],
              "puntos_a_corregir": [
                {{
                  "que_esta_mal": "Descripción detallada del error o aspecto deficiente",
                  "como_corregir": "Sugerencia concreta, técnica y constructiva sobre cómo el alumno debe solucionarlo"
                }},
                ... (incluye un bloque como este por CADA error encontrado, sin límite)
              ]
            }}
            """
            
            try:
                # Usamos el modelo GPT OSS 120B como determinamos antes
                respuesta = cliente_llm.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": "Eres un asistente de evaluación estricto. Respondes estrictamente en JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                dic_resultado = json.loads(respuesta.choices[0].message.content)
                
                # --- NUEVA VISUALIZACIÓN EN STREAMLIT ---
                st.success("✅ Evaluación completada")
                
                # 1. Cabecera con Nota y Resumen
                st.markdown(f"### 🎯 Nota Global: **{dic_resultado.get('nota_global', 0)} / 10**")
                st.info(f"**Resumen del Análisis:**\n\n{dic_resultado.get('resumen_analisis', 'Sin resumen.')}")
                
                st.divider()
                
                # 2. Columnas para Puntos Fuertes y Áreas de Mejora
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
                            # Mostramos el error en negrita y la solución debajo con un icono
                            st.markdown(f"**❌ Qué está mal:** {item.get('que_esta_mal', '')}")
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**💡 Cómo corregir:** _{item.get('como_corregir', '')}_")
                            st.write("") # Espaciador
                    else:
                        st.write("No se han encontrado errores significativos. ¡Excelente trabajo!")
                        
            except Exception as e:
                st.error(f"Ocurrió un error al generar la evaluación: {e}")
