1. Set up Environment
pip install -r requirements.txt
playwright install
2. Run Server
python server.py

Extra option:
If you want to integrate with Make.com, you can use ngrok.
download & install ngrok
ngrok config add-authtoken <your_authtoken>
ngrok authtoken <your_authtoken>
ngrok http 8000
python server.py