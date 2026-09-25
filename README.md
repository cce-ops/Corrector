# 🤖 Evaluador IA para Proyectos de Ingeniería

Herramienta basada en **Inteligencia Artificial** para analizar, corregir y generar **feedback estructurado sobre informes de alumnos de ingeniería**.

La aplicación está diseñada especialmente para facilitar el trabajo de profesores y docentes que necesitan evaluar numerosos informes siguiendo una **rúbrica y unos contenidos de referencia determinados**.

El sistema permite trabajar de dos formas:

* ☁️ **Modo online**, utilizando proveedores de IA mediante API, como Google Gemini.
* 🔒 **Modo local**, utilizando **Ollama**, para procesar los documentos directamente en el ordenador y evitar enviar los informes a servicios externos.

La aplicación cuenta con una interfaz web desarrollada con **Streamlit**.

---

## 🌐 Aplicación online

La versión desplegada de la aplicación está disponible en:

👉 **[Abrir Evaluador IA para Proyectos de Ingeniería](https://corrector-informes.streamlit.app/)**

> La versión online y la versión local pueden tener diferentes configuraciones de proveedores de IA. Para trabajar con documentación sensible o confidencial, se recomienda utilizar el modo local y comprobar la configuración antes de procesar los documentos.

---

## 📁 Repositorio

Código fuente:

👉 **[GitHub — cce-ops/Corrector-Informes](https://github.com/cce-ops/Corrector-Informes)**

---

# 🎯 Objetivo

El objetivo del proyecto es automatizar y facilitar parte del proceso de **corrección y evaluación de informes de ingeniería** mediante Inteligencia Artificial.

El sistema permite proporcionar al modelo:

1. 📚 **Rúbrica de evaluación**.
2. 📖 **Apuntes y documentación de referencia**.
3. 📄 **Informe del alumno**.

A partir de esta información, la aplicación puede analizar el trabajo y generar un **feedback estructurado**, utilizando el material proporcionado como contexto para la evaluación.

El flujo general es:

```text
             DOCUMENTACIÓN
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    RÚBRICA                 APUNTES
        │                     │
        └──────────┬──────────┘
                   ▼
             BASE DE CONOCIMIENTO
                   │
                   ▼
           ┌───────────────┐
           │  INFORME DEL  │
           │    ALUMNO     │
           └───────┬───────┘
                   │
                   ▼
            INTELIGENCIA
             ARTIFICIAL
                   │
                   ▼
          EVALUACIÓN + FEEDBACK
```

---

# ✨ Características principales

## 🤖 Evaluación mediante IA

El sistema utiliza modelos de Inteligencia Artificial para analizar los informes y generar una evaluación estructurada.

La evaluación puede utilizar como contexto:

* La rúbrica de la asignatura.
* Apuntes proporcionados por el profesor.
* Documentación de referencia.
* El propio informe del alumno.

Esto permite orientar el análisis hacia los criterios específicos de la asignatura.

---

## 📚 Base de conocimiento

Una de las características principales del proyecto es la posibilidad de **alimentar el sistema con documentación de referencia**.

El profesor puede cargar:

* Rúbricas.
* Apuntes.
* Material docente.
* Documentación técnica.
* Otros documentos relevantes para la evaluación.

Estos documentos se procesan y almacenan como una **base de conocimiento** que posteriormente puede utilizarse durante la evaluación de los informes.

---

# 🧠 RAG y memoria documental

El sistema utiliza un enfoque basado en una **base de conocimiento documental**, permitiendo que la IA consulte información previamente proporcionada por el profesor.

De forma conceptual:

```text
              PDF
               │
               ▼
        Extracción de texto
               │
               ▼
          Fragmentación
               │
               ▼
       Representación vectorial
               │
               ▼
          ChromaDB
               │
               ▼
       Recuperación de contexto
               │
               ▼
        Modelo de Inteligencia
             Artificial
               │
               ▼
          Evaluación final
```

La información procesada se almacena localmente en la carpeta:

```text
chroma_db/
```

Esto permite mantener una base de conocimiento reutilizable entre diferentes evaluaciones.

---

# 🔒 Modo Local — Ollama

Una de las características más importantes del proyecto es la posibilidad de ejecutar el modelo de IA **localmente mediante Ollama**.

Esto permite que el análisis pueda realizarse en el propio ordenador, evitando enviar los informes a una API externa.

### Ventajas del modo local

* 🔒 Mayor control sobre los documentos.
* 💻 Procesamiento en el propio ordenador.
* 🌐 No depende necesariamente de una API externa.
* 💰 No requiere necesariamente pagar por cada consulta a una API.
* 📚 Permite mantener localmente la base documental.

El rendimiento dependerá de las características del ordenador y del modelo utilizado.

---

# 🤖 Modelo recomendado para Ollama

La configuración original del proyecto recomienda utilizar:

```bash
ollama run qwen2.5
```

El modelo debe descargarse previamente antes de utilizarlo en modo local.

El tamaño de la descarga puede ser de varios gigabytes, por lo que el proceso puede tardar dependiendo de la conexión a Internet y del equipo.

Una vez descargado el modelo, Ollama puede utilizarlo localmente para realizar las evaluaciones.

---

# ☁️ Modo Online

El proyecto también permite trabajar con proveedores de IA mediante API.

Entre los proveedores contemplados por la aplicación se encuentra **Google Gemini**.

El modo online puede ser útil cuando:

* No se dispone de suficiente capacidad de cálculo local.
* Se desea utilizar modelos alojados en la nube.
* Se busca reducir el tiempo de procesamiento.
* El entorno de trabajo ya dispone de una API configurada.

La disponibilidad y configuración de cada proveedor dependerán de la versión de la aplicación.

---

# 👨‍🏫 Guía de uso para profesores

El flujo de trabajo está especialmente pensado para asignaturas en las que los alumnos deben entregar informes técnicos.

## 1. ⚙️ Configuración

Desde la barra lateral de la aplicación se selecciona el proveedor de Inteligencia Artificial.

Para trabajar localmente:

```text
Proveedor → Ollama (Local)
```

A continuación se selecciona el modelo disponible, por ejemplo:

```text
Modelo → qwen2.5
```

---

## 2. 📚 Alimentar el sistema

En la primera pestaña se cargan los documentos que servirán como referencia para las evaluaciones.

Por ejemplo:

* Rúbrica de la asignatura.
* Apuntes.
* Material docente.
* Documentación técnica.

Los documentos pueden proporcionarse en formato PDF.

Una vez cargados:

```text
Subir documentos
       │
       ▼
    Procesar
       │
       ▼
Base de conocimiento
```

La información procesada queda disponible para las siguientes evaluaciones.

---

## 3. 📄 Evaluar un nuevo trabajo

En la segunda pestaña se carga el informe del alumno.

El flujo es:

```text
        INFORME DEL ALUMNO
                 │
                 ▼
        Subir archivo PDF
                 │
                 ▼
       Analizar y Evaluar
                 │
                 ▼
          Procesamiento IA
                 │
                 ▼
       RESULTADO + FEEDBACK
```

La IA utiliza el informe junto con la información de referencia disponible para generar la evaluación.

---

# ⏱️ Tiempo de procesamiento

Cuando se utiliza **Ollama en local**, el tiempo necesario para analizar un informe depende principalmente de:

* Procesador.
* Memoria RAM.
* GPU, si está disponible.
* Modelo utilizado.
* Longitud del informe.
* Cantidad de información que debe procesarse.

Como referencia, el README original del proyecto indicaba aproximadamente:

> **1–4 minutos por informe**

aunque este tiempo puede variar considerablemente según el ordenador y la configuración utilizada.

Durante el análisis se recomienda no cerrar la pestaña del navegador.

---

# 📝 Formato de los documentos

El flujo original del proyecto está orientado principalmente al uso de documentos en:

```text
PDF
```

Los documentos pueden incluir:

* Informes de alumnos.
* Rúbricas.
* Apuntes.
* Material docente.
* Documentación técnica.

---

# 🔄 Flujo completo de evaluación

El funcionamiento puede resumirse en dos fases.

## Fase 1 — Preparación

```text
       RÚBRICA
          │
          ├──────────────┐
          │              │
       APUNTES      DOCUMENTACIÓN
          │              │
          └───────┬──────┘
                  ▼
          PROCESAMIENTO
                  │
                  ▼
             CHROMA_DB
```

Esta fase normalmente se realiza cuando se configura el sistema o cuando cambia el material de referencia.

## Fase 2 — Evaluación

```text
       INFORME ALUMNO
              │
              ▼
       RECUPERACIÓN DE
          CONTEXTO
              │
              ▼
      RÚBRICA + APUNTES
              │
              ▼
          MODELO IA
              │
              ▼
       EVALUACIÓN
              │
              ▼
       FEEDBACK FINAL
```

---

# 🎓 Aplicaciones

Aunque el proyecto está especialmente orientado a informes de ingeniería, el enfoque puede aplicarse a diferentes tipos de documentación académica.

### Ingeniería

* Informes de proyectos.
* Memorias técnicas.
* Informes de laboratorio.
* Estudios técnicos.
* Trabajos de asignaturas.
* Trabajos de fin de grado.
* Trabajos de fin de máster.

### Docencia

* Corrección asistida.
* Feedback personalizado.
* Evaluación preliminar.
* Comprobación respecto a una rúbrica.
* Apoyo al profesor durante la revisión.

### Evaluación mediante rúbricas

El sistema puede resultar especialmente útil cuando existe una rúbrica claramente definida, ya que permite proporcionar al modelo los criterios que debe tener en cuenta durante el análisis.

---

# 🛠️ Tecnologías

El proyecto utiliza un conjunto de tecnologías orientadas a la construcción de un sistema de evaluación documental mediante IA.

Entre los componentes principales se encuentran:

| Tecnología           | Función                                        |
| -------------------- | ---------------------------------------------- |
| 🐍 **Python**        | Lenguaje principal                             |
| 🌐 **Streamlit**     | Interfaz web                                   |
| 🤖 **Ollama**        | Ejecución local de modelos IA                  |
| 🧠 **Qwen 2.5**      | Modelo recomendado para ejecución local        |
| 📚 **ChromaDB**      | Almacenamiento de la base documental/vectorial |
| ☁️ **Google Gemini** | Proveedor de IA online                         |
| 📄 **PDF**           | Formato principal de documentación             |

La configuración exacta y las versiones de las dependencias se encuentran en los archivos del repositorio.

---

# 📂 Estructura conceptual

El funcionamiento del proyecto puede representarse mediante:

```text
Corrector-Informes/
│
├── app.py
├── requirements.txt
├── ...
│
├── chroma_db/
│   └── Base de conocimiento
│
└── README.md
```

La carpeta `chroma_db` contiene la información procesada que se utiliza como memoria documental del sistema.

> La estructura exacta puede variar según la versión del proyecto.

---

# 💻 Instalación local

## 1. Instalar Python

Descarga Python desde:

👉 [python.org](https://www.python.org/downloads/)

En Windows, durante la instalación es importante activar:

```text
Add Python to PATH
```

antes de comenzar la instalación.

---

# 2. Instalar Ollama

Descarga Ollama desde:

👉 [ollama.com](https://ollama.com)

Una vez instalado, abre una terminal y ejecuta:

```bash
ollama run qwen2.5
```

Ollama descargará el modelo y lo dejará disponible para su utilización local.

---

# 3. Descargar el proyecto

Clona el repositorio:

```bash
git clone https://github.com/cce-ops/Corrector-Informes.git
```

O descarga el proyecto directamente desde GitHub mediante:

**Code → Download ZIP**

Después, descomprime el proyecto en tu ordenador.

---

# 4. Instalar las dependencias

Abre una terminal dentro de la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

Espera hasta que finalice la instalación.

---

# ▶️ Ejecutar la aplicación

Una vez instalados Python, Ollama y las dependencias, ejecuta:

```bash
python -m streamlit run app.py
```

La aplicación estará disponible normalmente en:

```text
http://localhost:8501
```

---

# ⚡ Inicio rápido en Windows

Si el proyecto incluye un archivo `.bat`, puede utilizarse como acceso directo para simplificar el proceso de inicio.

El flujo sería:

```text
Doble clic en .bat
       │
       ▼
Arranque de Streamlit
       │
       ▼
Apertura del navegador
       │
       ▼
Aplicación disponible
```

Ollama debe estar correctamente instalado y disponible para que el modo local funcione.

---

# 🔐 Privacidad

La ejecución local mediante Ollama permite diseñar un flujo en el que los informes y la base documental permanezcan en el ordenador donde se ejecuta la aplicación.

Esto resulta especialmente interesante cuando los informes contienen:

* Datos personales de alumnos.
* Información académica.
* Información confidencial.
* Documentación interna.
* Material docente no público.

No obstante, la privacidad real depende de la configuración completa del sistema. Si se utiliza un proveedor mediante API, los datos enviados a dicho proveedor estarán sujetos a sus propias condiciones de procesamiento y privacidad.

---

# ⚠️ Consideraciones sobre la evaluación mediante IA

La evaluación generada por Inteligencia Artificial debe considerarse una **herramienta de apoyo al profesor**, no necesariamente un sustituto de la evaluación docente.

Es recomendable:

* Revisar los resultados generados.
* Comprobar las referencias utilizadas.
* Verificar que las recomendaciones son coherentes.
* Supervisar especialmente las calificaciones o conclusiones importantes.
* Mantener el criterio académico del profesor.

Los modelos de IA pueden cometer errores o interpretar incorrectamente determinados contenidos técnicos.

---

# 🔮 Posibles mejoras futuras

El proyecto puede evolucionar incorporando nuevas funcionalidades:

* [ ] Generación automática de una nota según la rúbrica.
* [ ] Desglose de la puntuación por criterio.
* [ ] Comparación entre informe y rúbrica.
* [ ] Identificación automática de incumplimientos.
* [ ] Detección de errores técnicos.
* [ ] Comparación entre versiones de un informe.
* [ ] Historial de evaluaciones.
* [ ] Exportación de resultados a PDF.
* [ ] Exportación de resultados a Excel.
* [ ] Generación automática de comentarios para el alumno.
* [ ] Configuración de diferentes rúbricas.
* [ ] Gestión de diferentes asignaturas.
* [ ] Diferentes modelos de IA.
* [ ] Soporte para más formatos de documentos.
* [ ] Evaluación de presentaciones.
* [ ] Panel de estadísticas para profesores.
* [ ] Procesamiento masivo de informes.
* [ ] Comparación de resultados entre grupos.
* [ ] Integración con plataformas educativas.

---

# 📊 Posible evolución del sistema

El proyecto podría evolucionar hacia una plataforma completa de evaluación asistida:

```text
                 PROFESOR
                    │
                    ▼
          ┌──────────────────┐
          │ RÚBRICA + TEMARIO│
          └────────┬─────────┘
                   │
                   ▼
            BASE DE CONOCIMIENTO
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
      INFORME 1          INFORME 2
          │                 │
          └────────┬────────┘
                   ▼
              MOTOR DE IA
                   │
                   ▼
          ┌─────────────────┐
          │   EVALUACIÓN    │
          ├─────────────────┤
          │ Nota            │
          │ Feedback        │
          │ Errores         │
          │ Mejoras         │
          └─────────────────┘
                   │
                   ▼
              PROFESOR
```

---

# 🤝 Contribuciones

Las contribuciones son bienvenidas.

Para contribuir al proyecto:

1. Realiza un fork del repositorio.
2. Crea una nueva rama:

```bash
git checkout -b feature/nueva-funcionalidad
```

3. Realiza los cambios.
4. Haz commit:

```bash
git add .
git commit -m "Añadir nueva funcionalidad"
```

5. Sube la rama:

```bash
git push origin feature/nueva-funcionalidad
```

6. Abre un Pull Request.

---

# 📄 Licencia

Consulta el repositorio para comprobar la licencia actualmente asociada al proyecto.

Si el proyecto no dispone de una licencia específica, se recomienda añadir un archivo `LICENSE` para establecer las condiciones de uso, modificación y distribución del código.

---

# 🌐 Enlaces

### Aplicación web

👉 **[Corrector de Informes](https://corrector-informes.streamlit.app/)**

### Código fuente

👉 **[GitHub — cce-ops/Corrector-Informes](https://github.com/cce-ops/Corrector-Informes)**

### Ollama

👉 **[Ollama](https://ollama.com/)**

### Python

👉 **[Python](https://www.python.org/)**

---

# 👨‍💻 Proyecto

## 🤖 Evaluador IA para Proyectos de Ingeniería

Sistema de evaluación y generación de feedback para informes de ingeniería mediante Inteligencia Artificial.

**Python · Streamlit · Ollama · Qwen · ChromaDB · Google Gemini**

---

⭐ Si este proyecto te resulta útil, puedes darle una estrella al repositorio.

