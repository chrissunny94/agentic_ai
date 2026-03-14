python -m ensurepip --upgrade
pip3 install -r requirements.txt

curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1
