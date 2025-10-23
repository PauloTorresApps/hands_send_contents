import requests
from pathlib import Path

class FileTransferClient:
    def __init__(self, timeout=30):
        self.timeout = timeout
    
    def send_file(self, filepath, target_ip, target_port=5000):
        """
        Envia arquivo para dispositivo alvo
        Retorna: (success: bool, message: str)
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                return False, f"Arquivo não encontrado: {filepath}"
            
            url = f"http://{target_ip}:{target_port}/upload"
            
            with open(filepath, 'rb') as f:
                files = {'file': (filepath.name, f)}
                response = requests.post(url, files=files, timeout=self.timeout)
            
            if response.status_code == 200:
                return True, f"Arquivo enviado com sucesso: {filepath.name}"
            else:
                return False, f"Erro ao enviar: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout ao enviar arquivo"
        except requests.exceptions.ConnectionError:
            return False, f"Não foi possível conectar a {target_ip}:{target_port}"
        except Exception as e:
            return False, f"Erro ao enviar arquivo: {str(e)}"
    
    def ping_device(self, target_ip, target_port=5000):
        """
        Verifica se dispositivo está acessível
        """
        try:
            url = f"http://{target_ip}:{target_port}/ping"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False