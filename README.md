# 🤖 Evaluador IA para Proyectos de Ingeniería (Local)

Esta herramienta utiliza Inteligencia Artificial (Modelos Locales vía Ollama) y bases de datos vectoriales (RAG) para corregir y generar feedback exhaustivo y estructurado de informes de alumnos de ingeniería, garantizando la privacidad absoluta de los datos.

## 🚀 Requisitos previos

Para ejecutar este proyecto en tu ordenador, necesitas tener instalados:

1. **Python** (versión 3.9 o superior).
2. **Ollama**: El motor para ejecutar la IA en local. 
   - Descárgalo e instálalo desde [ollama.com](https://ollama.com).

## 🛠️ Instalación paso a paso

### 1. Descargar el modelo de IA en Ollama
Abre una terminal (Símbolo del sistema o PowerShell) y ejecuta el siguiente comando para descargar el modelo recomendado para ingeniería (`qwen2.5` o `llama3.1`). *Este paso puede tardar dependiendo de tu conexión a internet (pesa unos 4-8 GB).*

```bash
ollama run qwen2.5
