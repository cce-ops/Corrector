# 🤖 Evaluador IA para Proyectos de Ingeniería

Esta herramienta utiliza Inteligencia Artificial para corregir y generar feedback exhaustivo y estructurado de informes de alumnos de ingeniería. 

Puede ejecutarse a través de Internet (usando APIs como Google Gemini) o **100% en Local (usando Ollama)** para garantizar la privacidad absoluta de los datos y evitar colas en los servidores.

---

## 🚀 Guía de Instalación Local (Solo la primera vez)

Para ejecutar este proyecto en tu ordenador con máxima privacidad, necesitas preparar tu sistema. Sigue estos pasos **una única vez**:

### 1. Instalar Python (¡Atención al paso clave!)
1. Descarga Python desde su [página oficial](https://www.python.org/downloads/).
2. Al abrir el instalador en Windows, **ANTES de darle a instalar**, asegúrate de **marcar la casilla de abajo que dice "Add Python to PATH"**. *(Si no marcas esto, el ordenador no reconocerá los comandos más adelante).*
3. Haz clic en "Install Now".

### 2. Instalar el "Motor" de Inteligencia Artificial (Ollama)
1. Descarga e instala Ollama desde [ollama.com](https://ollama.com).
2. Una vez instalado, abre la terminal de tu ordenador (Símbolo del sistema o PowerShell).
3. Escribe el siguiente comando para descargar el modelo recomendado para analizar informes de ingeniería (tardará un rato en descargar sus ~4 GB):
   ```bash
   ollama run qwen2.5
Empezará a descargar (pesa unos 4-5 GB, ten paciencia). Cuando termine y te aparezca un cursor para chatear, ya puedes cerrar esa ventana negra.

### 3. Descargar este proyecto
En esta misma página de GitHub, ve arriba del todo, haz clic en el botón verde que dice "<> Code".

Selecciona "Download ZIP".

Extrae la carpeta que te has descargado en tu Escritorio o en la carpeta de Documentos.

### 4. Instalar las librerías del programa
Abre la carpeta que acabas de descomprimir.

Haz clic en la barra de direcciones de la carpeta (arriba, donde pone la ruta), borra todo, escribe cmd y pulsa Enter. Se abrirá una terminal directamente en esa carpeta.

Copia y pega este comando y pulsa Enter:

pip install -r requirements.txt

Espera a que se instalen todas las barras de carga y cierra la ventana.

### Cómo arrancar el programa en el día a día

Una vez completada la Fase 1, cada vez que quieras corregir entregas, el proceso es muy rápido:

Opción A: El método de un clic (Recomendado)
Si dentro de la carpeta del proyecto hay un archivo llamado Arrancar_Evaluador.bat, solo tienes que hacer doble clic en él. Se abrirá una ventana negra (no la cierres) y automáticamente se abrirá tu navegador con la herramienta lista.


Opción B: El método manual
Si no usas el archivo .bat:

Asegúrate de que Ollama está abierto (debe salir el icono de una llama abajo a la derecha de tu pantalla, junto a la hora de Windows).

Abre la carpeta del proyecto, escribe cmd en la barra de direcciones y pulsa Enter.

Escribe este comando y pulsa Enter:
python -m streamlit run app.py

(Se abrirá tu navegador web en la dirección http://localhost:8501).

### 📚 Guía de Uso para Profesores
El flujo de trabajo óptimo para la asignatura de Proyectos de Ingeniería es el siguiente:

1) La Barra Lateral (Configuración):

Selecciona siempre "Ollama (Local)" en el desplegable de Proveedor.

En modelo, asegúrate de que pone qwen2.5 (o el que hayas descargado).

2) Pestaña 1 (Alimentar el sistema):

Sube la rúbrica de la asignatura y los apuntes clave en PDF.

Haz clic en Procesar. Estos archivos se guardarán permanentemente en tu disco duro (en la carpeta interna chroma_db) como la memoria colectiva del corrector. Solo debes hacer esto la primera vez o si cambias el temario.

3) Pestaña 2 (Evaluar nuevo trabajo):

Sube el informe en PDF del alumno.

Dale a "Analizar y Evaluar".

Nota de rendimiento: Como el análisis se hace en tu propio ordenador garantizando la máxima privacidad, el proceso requiere bastante cálculo. Dependiendo de tu procesador y de la longitud del informe del alumno, puede tardar entre 1 y 4 minutos en generar la respuesta. ¡No cierres la pestaña!
