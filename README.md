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
