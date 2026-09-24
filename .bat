@echo off
title Iniciando Evaluador IA
echo Iniciando el Evaluador de Proyectos de Ingenieria...
echo Por favor, no cierres esta ventana negra mientras usas la aplicacion.
echo.

:: Este truco hace que vaya a la carpeta actual automaticamente
cd /d "%~dp0"

:: Ejecuta Streamlit
python -m streamlit run app.py

pause
