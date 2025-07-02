1. Set up Environment
pip install fastapi uvicorn playwright requests pyperclip
playwright install
2. Run Server
uvicorn main:app --reload
python playwright_worker.py