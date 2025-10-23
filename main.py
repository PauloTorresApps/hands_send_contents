import cv2
import time
import threading
from gesture_detector import GestureDetector, GestureState
from clipboard_manager import ClipboardManager
from device_discovery import DeviceDiscovery
from file_transfer_server import FileTransferServer
from file_transfer_client import FileTransferClient
import json
from pathlib import Path

class AITeleportation:
    def __init__(self, config_path='config.json'):
        self.config = self.load_config(config_path)
        
        # Componentes
        self.gesture_detector = GestureDetector()
        self.clipboard_manager = ClipboardManager()
        self.device_discovery = DeviceDiscovery(
            device_name=self.config['device_name'],
            port=self.config['port']
        )
        self.file_server = FileTransferServer(
            port=self.config['port'],
            upload_dir=self.config['upload_dir']
        )
        self.file_client = FileTransferClient()
        
        # Estado
        self.grabbed_file = None
        self.running = False
        self.camera = None
        
    def load_config(self, config_path):
        """Carrega configuração ou cria padrão"""
        default_config = {
            'device_name': 'PC-' + Path.home().name,
            'port': 5000,
            'upload_dir': 'received_files',
            'camera_index': 0,
            'show_preview': True
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge com defaults
                return {**default_config, **config}
        else:
            # Cria arquivo de configuração padrão
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
    def start(self):
        """Inicia o sistema"""
        print("=== AI Teleportation Iniciando ===")
        
        # Inicia servidor HTTP
        self.file_server.start()
        time.sleep(1)  # Aguarda servidor iniciar
        
        # Registra serviço na rede
        self.device_discovery.register_service()
        
        # Inicia descoberta de dispositivos
        self.device_discovery.start_discovery()
        
        # Inicia câmera
        self.camera = cv2.VideoCapture(self.config['camera_index'])
        if not self.camera.isOpened():
            print("ERRO: Não foi possível abrir a câmera")
            return
        
        self.running = True
        print("Sistema iniciado com sucesso!")
        print(f"Dispositivo: {self.config['device_name']}")
        print("Aguardando gestos...\n")
        
        self.main_loop()
    
    def main_loop(self):
        """Loop principal de processamento"""
        last_state = GestureState.IDLE
        
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    print("Erro ao ler frame da câmera")
                    break
                
                # Processa frame e detecta gesto
                annotated_frame, current_state, hand_position = \
                    self.gesture_detector.process_frame(frame)
                
                # Transições de estado
                if current_state != last_state:
                    self.handle_state_change(last_state, current_state, hand_position, frame.shape)
                    last_state = current_state
                
                # Exibe preview se configurado
                if self.config['show_preview']:
                    # Adiciona informações na tela
                    devices = self.device_discovery.get_devices()
                    info_text = f"Dispositivos: {len(devices)}"
                    cv2.putText(annotated_frame, info_text, (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    
                    if self.grabbed_file:
                        file_text = f"Arquivo: {Path(self.grabbed_file).name}"
                        cv2.putText(annotated_frame, file_text, (10, 90),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    cv2.imshow('AI Teleportation', annotated_frame)
                    
                    # ESC para sair
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                
        except KeyboardInterrupt:
            print("\nEncerrando...")
        finally:
            self.stop()
    
    def handle_state_change(self, old_state, new_state, hand_position, frame_shape):
        """Processa mudanças de estado do gesto"""
        
        if new_state == GestureState.GRABBING:
            print("🖐️  Detectando gesto de agarrar...")
        
        elif new_state == GestureState.HOLDING:
            # Captura conteúdo do clipboard
            file_type, filepath = self.clipboard_manager.capture_clipboard()
            
            if filepath:
                self.grabbed_file = filepath
                print(f"✅ Arquivo capturado: {Path(filepath).name} ({file_type})")
            else:
                print("⚠️  Nenhum conteúdo no clipboard")
        
        elif new_state == GestureState.RELEASING:
            if self.grabbed_file and hand_position:
                # Encontra dispositivo alvo
                h, w, _ = frame_shape
                x, y = hand_position
                
                target_device = self.device_discovery.find_device_by_position(
                    x, y, w, h
                )
                
                if target_device:
                    print(f"📤 Enviando para {target_device['name']}...")
                    
                    # Envia arquivo em thread separada
                    transfer_thread = threading.Thread(
                        target=self.transfer_file,
                        args=(self.grabbed_file, target_device),
                        daemon=True
                    )
                    transfer_thread.start()
                else:
                    devices = self.device_discovery.get_devices()
                    if not devices:
                        print("⚠️  Nenhum dispositivo disponível")
                    else:
                        print(f"⚠️  Mova a mão para a borda da tela")
            
            # Reset
            self.grabbed_file = None
    
    def transfer_file(self, filepath, target_device):
        """Transfere arquivo para dispositivo alvo"""
        success, message = self.file_client.send_file(
            filepath,
            target_device['ip'],
            target_device['port']
        )
        
        if success:
            print(f"✨ {message}")
        else:
            print(f"❌ {message}")
    
    def stop(self):
        """Encerra o sistema"""
        self.running = False
        
        if self.camera:
            self.camera.release()
        
        cv2.destroyAllWindows()
        
        self.gesture_detector.release()
        self.device_discovery.close()
        
        print("Sistema encerrado")

def main():
    app = AITeleportation()
    app.start()

if __name__ == '__main__':
    main()