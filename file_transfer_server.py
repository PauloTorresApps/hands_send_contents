from flask import Flask, request, jsonify, send_file
import os
from pathlib import Path
import threading
from werkzeug.utils import secure_filename

class FileTransferServer:
    def __init__(self, port=5000, upload_dir='received_files'):
        self.port = port
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        self.app = Flask(__name__)
        self.app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
        self.server_thread = None
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/ping', methods=['GET'])
        def ping():
            return jsonify({'status': 'ok'})
        
        @self.app.route('/upload', methods=['POST'])
        def upload_file():
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file part'}), 400
                
                file = request.files['file']
                
                if file.filename == '':
                    return jsonify({'error': 'No selected file'}), 400
                
                filename = secure_filename(file.filename)
                filepath = self.upload_dir / filename
                
                # Se arquivo já existe, adiciona número
                counter = 1
                while filepath.exists():
                    name, ext = os.path.splitext(filename)
                    filepath = self.upload_dir / f"{name}_{counter}{ext}"
                    counter += 1
                
                file.save(filepath)
                
                print(f"Arquivo recebido: {filepath}")
                
                return jsonify({
                    'status': 'success',
                    'filename': filepath.name,
                    'path': str(filepath)
                }), 200
                
            except Exception as e:
                print(f"Erro ao receber arquivo: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/download/<filename>', methods=['GET'])
        def download_file(filename):
            try:
                filepath = self.upload_dir / secure_filename(filename)
                if filepath.exists():
                    return send_file(filepath)
                return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start(self):
        """Inicia servidor em thread separada"""
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()
        print(f"Servidor HTTP iniciado na porta {self.port}")
    
    def _run_server(self):
        """Executa servidor Flask"""
        self.app.run(
            host='0.0.0.0',
            port=self.port,
            debug=False,
            use_reloader=False
        )
    
    def is_running(self):
        """Verifica se servidor está rodando"""
        return self.server_thread is not None and self.server_thread.is_alive()