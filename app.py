import json
import time
from anthropic import Anthropic
import chromadb
import google.generativeai as genai
from openai import OpenAI
from pypdf import PdfReader
import streamlit as st

# Intentar importar cliente nativo de Groq
try:
  from groq import Groq

  GROQ_INSTALADO = True
except ImportError:
  GROQ_INSTALADO = False

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


# --- DICCIONARIOS DE MODELOS (Estructura: Label -> Model ID) ---
GEMINI_MODELS = {
    "Gemini 3.8 Flash (Más inteligente, flujos complejos)": "gemini-3.8-flash",
    "Gemini 3.8 Live (Voz, baja latencia)": "gemini-3.8-live",
    "Gemini 3.8 Live Extended Thinking (Alto razonamiento)": (
        "gemini-3.8-live-extended-thinking"
    ),
    "Gemini 3.7 Flash (Programación y varios pasos)": "gemini-3.7-flash",
    "Gemini 3.6 Flash (Equilibrio tareas cotidianas)": "gemini-3.6-flash",
    "Gemini 3.5 Flash (Velocidad para cargas rutinarias)": "gemini-3.5-flash",
    "Gemini 3.5 Flash-Lite (Más rápido y rentable)": "gemini-3.5-flash-lite",
    "Gemini 3.1 Flash-Lite (Rendimiento Frontier)": "gemini-3.1-flash-lite",
}

NVIDIA_MODELS = {
    "Nemotron 3 Ultra (NVIDIA 550B)": "nvidia/nemotron-3-ultra-550b-a55b",
    "Nemotron 4 340B (NVIDIA)": "nvidia/nemotron-4-340b-instruct",
}

OPENROUTER_MODELS = {
    "Nemotron 3 Ultra (OpenRouter Gratis)": (
        "nvidia/nemotron-3-ultra-550b-a55b:free"
    ),
    "Space Bunny Alpha (OpenRouter)": "stealth/space-bunny-alpha",
}

GROQ_MODELS = {
    "GPT OSS 120B (Groq)": "openai/gpt-oss-120b",
    "GPT OSS 20B (Groq)": "openai/gpt-oss-20b",
}


# --- BARRA LATERAL: CONFIGURACIÓN DEL PROFESOR ---
with st.sidebar:
  st.header("⚙️ Configuración")
  st.info(
      "Elige el motor de IA. En la nube usarás tu API Key. En local (Ollama) el"
      " proceso es privado y gratuito."
  )

  proveedor = st.selectbox(
      "Proveedor de Inteligencia Artificial",
      [
          "Google Gemini",
          "NVIDIA NIM",
          "OpenRouter - Gratis",
          "Groq - Gratis",
          "OpenAI (ChatGPT)",
          "Anthropic (Claude)",
          "Ollama (Local)",
      ],
  )

  api_key_usuario = ""
  modelo_local = ""
  modelo_nube = ""

  if proveedor == "Google Gemini":
    api_key_usuario = st.text_input("API Key de Gemini:", type="password")
    opcion_gemini = st.selectbox("Modelo:", list(GEMINI_MODELS.keys()))
    modelo_nube = GEMINI_MODELS[opcion_gemini]
    st.caption(
        "🔑 [Conseguir clave de Gemini"
        " Gratis](https://aistudio.google.com/app/apikey)"
    )

  elif proveedor == "NVIDIA NIM":
    api_key_usuario = st.text_input("API Key de NVIDIA NIM:", type="password")
    opcion_nvidia = st.selectbox("Modelo:", list(NVIDIA_MODELS.keys()))
    modelo_nube = NVIDIA_MODELS[opcion_nvidia]
    st.caption(
        "🔑 [Conseguir clave de NVIDIA"
        " NIM](https://build.nvidia.com/explore/discover)"
    )

  elif proveedor == "OpenRouter - Gratis":
    api_key_usuario = st.text_input("API Key de OpenRouter:", type="password")
    opcion_or = st.selectbox("Modelo:", list(OPENROUTER_MODELS.keys()))
    modelo_nube = OPENROUTER_MODELS[opcion_or]
    st.caption(
        "🔑 [Conseguir clave de OpenRouter](https://openrouter.ai/keys)"
    )

  elif proveedor == "Groq - Gratis":
    api_key_usuario = st.text_input("API Key de Groq:", type="password")
    opcion_groq = st.selectbox("Modelo:", list(GROQ_MODELS.keys()))
    modelo_nube = GROQ_MODELS[opcion_groq]
    st.caption("🔑 [Clave de Groq Gratis](https://console.groq.com/keys)")

  elif proveedor == "OpenAI (ChatGPT)":
    api_key_usuario = st.text_input("API Key de OpenAI:", type="password")
    modelo_nube = st.selectbox("Modelo:", ["gpt-4o", "gpt-4o-mini"])

  elif proveedor == "Anthropic (Claude)":
    api_key_usuario = st.text_input("API Key de Anthropic:", type="password")
    modelo_nube = st.selectbox(
        "Modelo:", ["claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"]
    )

  elif proveedor == "Ollama (Local)":
    opcion_modelo = st.selectbox(
        "Selecciona el modelo descargado:",
        ["qwen2.5", "llama3.1", "mistral-nemo", "Otro (Escribir manualmente)"],
    )
    if opcion_modelo == "Otro (Escribir manualmente)":
      modelo_local = st.text_input(
          "Escribe el nombre exacto del modelo:", value="llama3.2"
      )
    else:
      modelo_local = opcion_modelo
    st.caption("Asegúrate de tener la app Ollama abierta en tu PC.")


# --- INTERFAZ PRINCIPAL ---
st.title(
    "🤖 Evaluador de Informes (Proyectos de Ingeniería)",
    help=(
        "**¿Por qué usar esto y no ChatGPT directamente?**\n\nEsta herramienta"
        " utiliza RAG (Generación Aumentada por Recuperación) y Salidas"
        " Estructuradas JSON."
    ),
)

tab1, tab2 = st.tabs(
    ["📚 1. Subir Base de Conocimiento", "📝 2. Evaluar Informe del Alumno"]
)

# --- PESTAÑA 1: BASE DE CONOCIMIENTO ---
with tab1:
  st.header("Alimentar el sistema")
  st.info(
      "Sube apuntes o rúbricas. Se usarán como memoria (RAG) para corregir."
  )

  referencias = st.file_uploader(
      "Sube PDFs de referencia", type="pdf", accept_multiple_files=True
  )

  if st.button("Procesar y guardar referencias"):
    if referencias:
      for ref in referencias:
        with st.spinner(f"Procesando {ref.name}..."):
          texto = extraer_texto_pdf(ref)
          chunk_size = 1000
          chunks = [
              texto[i : i + chunk_size]
              for i in range(0, len(texto), chunk_size)
          ]
          ids = [f"{ref.name}_chunk_{i}" for i in range(len(chunks))]

          collection.add(
              documents=chunks,
              ids=ids,
              metadatas=[{"fuente": ref.name} for _ in chunks],
          )
      st.success(
          f"✅ ¡{len(referencias)} documentos añadidos a la base de"
          " conocimiento!"
      )
    else:
      st.warning("Por favor, sube al menos un documento PDF.")

# --- PESTAÑA 2: EVALUACIÓN ---
with tab2:
  st.header("Evaluar un nuevo trabajo")
  informe_alumno = st.file_uploader(
      "Sube el informe del alumno (PDF)", type="pdf", key="alumno"
  )

  if st.button("Analizar y Evaluar"):

    if proveedor != "Ollama (Local)" and not api_key_usuario:
      st.error("⚠️ Falta la API Key. Por favor, introdúcela en la barra lateral.")
      st.stop()

    if not informe_alumno:
      st.warning("Sube el informe del alumno para comenzar.")
      st.stop()

    with st.spinner("Extrayendo texto del informe..."):
      texto_alumno = extraer_texto_pdf(informe_alumno)
      if proveedor == "Groq - Gratis":
        texto_alumno = texto_alumno[:15000]
      elif proveedor == "Anthropic (Claude)":
        texto_alumno = texto_alumno[:50000]

    with st.spinner("Buscando referencias en la base de conocimiento..."):
      if collection.count() == 0:
        contexto_recuperado = "No hay contexto disponible."
      else:
        resultados = collection.query(
            query_texts=[texto_alumno[:3000]], n_results=4
        )
        if resultados["documents"]:
          contexto_recuperado = "\n\n---\n\n".join(resultados["documents"][0])
        else:
          contexto_recuperado = "No se encontró contexto relevante."

    with st.spinner(
        f"La IA ({proveedor}) está evaluando el informe exhaustivamente..."
    ):

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
            4. Devuelve ÚNICAMENTE formato JSON CRUDO. NO uses markdown.
            
            ESTRUCTURA JSON EXACTA:
            {{
              "nota_global": 7.5,
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
      exito = False

      # --- LISTA DE MODELOS A PROBAR ---
      if proveedor == "Google Gemini":
        lista_gemini = list(GEMINI_MODELS.values())
        idx = (
            lista_gemini.index(modelo_nube) if modelo_nube in lista_gemini else 0
        )
        modelos_a_probar = lista_gemini[idx:]
      elif proveedor == "Ollama (Local)":
        modelos_a_probar = [modelo_local]
      else:
        modelos_a_probar = [modelo_nube]

      # --- BUCLE DE EVALUACIÓN ---
      for modelo in modelos_a_probar:
        if exito:
          break

        intentos_por_modelo = 2
        for intento in range(intentos_por_modelo):
          try:
            st.toast(
                f"Evaluando con {modelo} (Intento"
                f" {intento+1}/{intentos_por_modelo})...",
                icon="🔄",
            )

            # 1. GOOGLE GEMINI (SDK OFICIAL)
            if proveedor == "Google Gemini":
  genai.configure(api_key=api_key_usuario)
  modelo_gemini = genai.GenerativeModel(
      modelo,
      generation_config={
          "temperature": 0.2,  # <-- Añadido aquí
          "response_mime_type": "application/json",
      },
  )
  response = modelo_gemini.generate_content(prompt)
  texto_resp = response.text

  if texto_resp.startswith("```json"):
    texto_resp = texto_resp[7:-3]
  elif texto_resp.startswith("```"):
    lines = texto_resp.strip().splitlines()
    texto_resp = "\n".join([l for l in lines if not l.startswith("```")])

  respuesta_json = json.loads(texto_resp.strip())

            # 2. ANTHROPIC (CLAUDE)
            elif proveedor == "Anthropic (Claude)":
              cliente_claude = Anthropic(api_key=api_key_usuario)
              respuesta = cliente_claude.messages.create(
                  model=modelo,
                  max_tokens=4000,
                  temperature=0.2,
                  messages=[{
                      "role": "user",
                      "content": (
                          prompt
                          + "\n\nResponde SOLO con el objeto JSON, empezando"
                          " por {"
                      ),
                  }],
              )
              respuesta_json = json.loads(respuesta.content[0].text)

            # 3. GROQ NATIVO (SI ESTÁ INSTALADO)
            elif proveedor == "Groq - Gratis" and GROQ_INSTALADO:
              cliente_groq = Groq(api_key=api_key_usuario)
              respuesta = cliente_groq.chat.completions.create(
                  model=modelo,
                  messages=[
                      {
                          "role": "system",
                          "content": (
                              "Eres un servidor que SOLO devuelve código JSON"
                              " válido."
                          ),
                      },
                      {"role": "user", "content": prompt},
                  ],
                  temperature=0.2,
                  response_format={"type": "json_object"},
              )
              texto_respuesta = respuesta.choices[0].message.content
              if texto_respuesta.startswith("```json"):
                texto_respuesta = texto_respuesta[7:-3]
              respuesta_json = json.loads(texto_respuesta.strip())

            # 4. RESTO DE PROVEEDORES VÍA CLIENTE OPENAI (OPENROUTER, NVIDIA, OLLAMA, OPENAI)
            else:
              headers = {}
              extra_args = {}

              if proveedor == "OpenRouter - Gratis":
                base_url = "https://openrouter.ai/api/v1"
                headers = {
                    "HTTP-Referer": "https://corrector-ia.streamlit.app",
                    "X-Title": "Evaluador de Informes IA",
                }
              elif proveedor == "Groq - Gratis":
                base_url = "https://api.groq.com/openai/v1"
              elif proveedor == "NVIDIA NIM":
                base_url = "https://integrate.api.nvidia.com/v1"
              elif proveedor == "OpenAI (ChatGPT)":
                base_url = "https://api.openai.com/v1"
              elif proveedor == "Ollama (Local)":
                base_url = "http://localhost:11434/v1"
                api_key_usuario = "ollama"
                extra_args = {"extra_body": {"options": {"num_ctx": 32000}}}

              cliente_llm = OpenAI(
                  base_url=base_url,
                  api_key=api_key_usuario,
                  default_headers=headers if headers else None,
                  timeout=60.0,  # Previene timeouts y cortes de conexión repentinos
              )

              respuesta = cliente_llm.chat.completions.create(
                  model=modelo,
                  messages=[
                      {
                          "role": "system",
                          "content": (
                              "Eres un servidor que SOLO devuelve código JSON"
                              " válido."
                          ),
                      },
                      {"role": "user", "content": prompt},
                  ],
                  temperature=0.2,
                  response_format={"type": "json_object"}
                  if proveedor != "Ollama (Local)"
                  else None,
                  **extra_args,
              )
              texto_respuesta = respuesta.choices[0].message.content

              if texto_respuesta.startswith("```json"):
                texto_respuesta = texto_respuesta[7:-3]
              elif texto_respuesta.startswith("```"):
                lines = texto_respuesta.strip().splitlines()
                texto_respuesta = "\n".join(
                    [l for l in lines if not l.startswith("```")]
                )

              respuesta_json = json.loads(texto_respuesta.strip())

            st.toast(f"¡Éxito con {modelo}!", icon="✅")
            exito = True
            break

          except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "429" in error_msg:
              st.toast("Servidor ocupado. Reintentando en 5s...", icon="⏳")
              time.sleep(5)
            else:
              st.toast(f"Fallo en {modelo}: {error_msg[:80]}...", icon="⚠️")
              break

      # --- MOSTRAR RESULTADOS ---
      if exito and respuesta_json:
        dic_resultado = respuesta_json
        st.success(f"✅ Evaluación completada con éxito ({proveedor})")
        st.markdown(
            "### 🎯 Nota Global:"
            f" **{dic_resultado.get('nota_global', 0)} / 10**"
        )
        st.info(
            "**Resumen del Análisis:**\n\n"
            f"{dic_resultado.get('resumen_analisis', 'Sin resumen.')}"
        )

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
          st.success("🌟 Puntos Fuertes")
          for punto in dic_resultado.get("puntos_fuertes", []):
            st.write(f"- {punto}")

        with col2:
          st.error("🛠️ Áreas de Mejora y Correcciones")
          for item in dic_resultado.get("puntos_a_corregir", []):
            st.markdown(f"**❌ Qué está mal:** {item.get('que_esta_mal', '')}")
            st.markdown(
                "&nbsp;&nbsp;&nbsp;&nbsp;**💡 Cómo corregir:**"
                f" _{item.get('como_corregir', '')}_"
            )
            st.write("")
      else:
        st.error(
            f"Todos los intentos fallaron. Último error: {error_msg}"
        )
