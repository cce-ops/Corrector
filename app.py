import streamlit as st
import chromadb
from pypdf import PdfReader
from openai import OpenAI
import json
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Evaluador de Informes IA", layout="wide")

# --- INICIALIZACIÓN DE LA BASE DE DATOS VECTORIAL (RAG) ---
# Usamos cache_resource para no recargar la base de datos en cada interacción
@st.cache_resource
def init_chroma():
    # Guarda los vectores en una carpeta local llamada "chroma_db"
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

# Dividimos la app en dos pestañas: una para el profesor y otra para evaluar
tab1, tab2 = st.tabs(["📚 1. Subir Base de Conocimiento", "📝 2. Evaluar Informe del Alumno"])

# --- PESTAÑA 1: BASE DE CONOCIMIENTO (INGESTA RAG) ---
with tab1:
    st.header("Alimentar el sistema")
    st.info("Sube apuntes, rúbricas o proyectos excelentes de años anteriores. El modelo los usará como referencia para evaluar.")
    
    referencias = st.file_uploader("Sube PDFs de referencia", type="pdf", accept_multiple_files=True)
    
    if st.button("Procesar y guardar referencias"):
        if referencias:
            for ref in referencias:
                with st.spinner(f"Procesando {ref.name}..."):
                    texto = extraer_texto_pdf(ref)
                    
                    # Dividir el texto en fragmentos (chunks) de 1000 caracteres
                    chunk_size = 1000
                    chunks = [texto[i:i + chunk_size] for i in range(0, len(texto), chunk_size)]
                    ids = [f"{ref.name}_chunk_{i}" for i in range(len(chunks))]
                    
                    # Guardar en ChromaDB
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
            
        # 1. Extraer texto del alumno
        with st.spinner("Extrayendo texto del informe..."):
            texto_alumno = extraer_texto_pdf(informe_alumno)
            
        # 2. Recuperar contexto de la base de datos (RAG)
        with st.spinner("Buscando referencias en la base de conocimiento..."):
            if collection.count() == 0:
                st.warning("No hay base de conocimiento cargada. Se evaluará sin contexto previo.")
                contexto_recuperado = "No hay contexto disponible."
            else:
                # Usamos los primeros 2000 caracteres del alumno para buscar lo más relevante
                resultados = collection.query(query_texts=[texto_alumno[:2000]], n_results=3)
                if resultados["documents"]:
                    contexto_recuperado = "\n\n---\n\n".join(resultados["documents"][0])
                else:
                    contexto_recuperado = "No se encontró contexto relevante."
                    
        # 3. Llamar al LLM (Groq) forzando JSON
        with st.spinner("La IA está evaluando el informe. Esto tomará unos segundos..."):
            cliente_llm = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=st.secrets["GROQ_API_KEY"]
            )
            
            prompt = f"""
            Eres un evaluador de informes técnicos de ingeniería.
            
            CONTEXTO DE REFERENCIA (Apuntes y proyectos anteriores):
            {contexto_recuperado}
            
            INFORME DEL ALUMNO A EVALUAR:
            {texto_alumno[:20000]}  # Limitado para evitar sobrepasar tokens
            
            INSTRUCCIÓN CRÍTICA:
            Evalúa el informe y devuelve el resultado ÚNICAMENTE en formato JSON. 
            Usa exactamente esta estructura:
            {{
              "nota_global": (número decimal sobre 10),
              "desglose_notas": {{
                "formato_y_redaccion": (número),
                "analisis_tecnico": (número),
                "conclusiones": (número)
              }},
              "puntos_fuertes": ["string", "string"],
              "areas_mejora": ["string", "string"],
              "justificacion_general": "string"
            }}
            """
            
            try:
                respuesta = cliente_llm.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": "Respondes estrictamente en JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                # Parsear la respuesta
                dic_resultado = json.loads(respuesta.choices[0].message.content)
                
                # --- MOSTRAR RESULTADOS VISUALES ---
                st.success("✅ Evaluación completada")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric(label="Nota Global", value=f"{dic_resultado.get('nota_global', 0)}/10")
                with col2:
                    st.info(dic_resultado.get('justificacion_general', 'Sin justificación'))
                
                st.divider()
                st.subheader("Desglose por Criterios")
                
                # Gráfico
                df_notas = pd.DataFrame(
                    list(dic_resultado.get('desglose_notas', {}).items()),
                    columns=['Criterio', 'Nota']
                )
                df_notas['Criterio'] = df_notas['Criterio'].str.replace("_", " ").str.title()
                st.bar_chart(df_notas, x='Criterio', y='Nota', height=250)
                
                # Listas de feedback
                col_f, col_m = st.columns(2)
                with col_f:
                    st.success("✅ Puntos Fuertes")
                    for punto in dic_resultado.get('puntos_fuertes', []):
                        st.write(f"- {punto}")
                with col_m:
                    st.warning("🎯 Áreas de Mejora")
                    for mejora in dic_resultado.get('areas_mejora', []):
                        st.write(f"- {mejora}")
                        
            except Exception as e:
                st.error(f"Ocurrió un error al generar la evaluación: {e}")
