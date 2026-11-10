@echo off
rem Abre VenomScope sin internet. Doble clic el dia de la demo.
set HF_HUB_OFFLINE=1
set PYTHONUTF8=1
cd /d "%USERPROFILE%\VenomScope"
".venv\Scripts\streamlit.exe" run app.py
pause
