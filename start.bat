@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting the Magic Video Remover...
streamlit run app.py
pause
