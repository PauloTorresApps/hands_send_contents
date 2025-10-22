import cv2
import mediapipe as mp
import socket
import json
import time
import platform
import threading
from queue import Queue
import uuid

class GestureClient:
    """Cliente que detecta gestos e envia/recebe dados via UDP"""
    
    def __init__(self, server_ip="192.168.0.105", server_port=5005):
        # Configuração de rede
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = None
        
        # Identificação única do cliente
        self.client_id = f"{platform.node()}_{uuid.uuid4().hex[:8]}"
        
        # Fila de respostas recebidas
        self.response_queue = Queue()
        self.listening = False
        
        # MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Estado do gesto
        self.prev_state = None
        self.last_trigger_time = 0
        self.debounce_time = 0.5
        
    def start_network(self):
        """Inicia comunicação de rede"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(0.1)  # Non-blocking para receber respostas
            
            # Inicia thread para escutar respostas
            self.listening = True
            thread = threading.Thread(target=self._listen_responses, daemon=True)
            thread.start()
            
            print(f"Cliente iniciado com ID: {self.client_id}")
            print(f"Conectando ao servidor: {self.server_ip}:{self.server_port}\n")
            
            # Envia ping inicial
            self.send_ping()
            
            return True
        except socket.error as e:
            print(f"Erro ao iniciar rede: {e}")
            return False
    
    def _listen_responses(self):
        """Thread para escutar respostas do servidor"""
        while self.listening:
            try:
                data, addr = self.sock.recvfrom(1024)
                
                # Tenta decodificar como JSON
                try:
                    response = json.loads(data.decode())
                    self.handle_response(response)
                except json.JSONDecodeError:
                    print(f"Resposta não-JSON recebida: {data}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.listening:
                    print(f"Erro ao receber: {e}")
    
    def handle_response(self, response: dict):
        """Processa respostas do servidor"""
        msg_type = response.get("type", "UNKNOWN")
        server_id = response.get("server_id", "unknown")
        timestamp = response.get("timestamp", 0)
        
        print(f"\n📥 Resposta do servidor [{server_id}]")
        print(f"   Tipo: {msg_type}")
        
        if msg_type == "DATA_RESPONSE":
            data = response.get("data")
            print(f"   ✅ Dados recebidos: {data}")
            # Aqui você pode processar os dados recebidos
            # Por exemplo, abrir uma URL, salvar um arquivo, etc.
            
        elif msg_type == "NO_DATA":
            print(f"   ℹ️ {response.get('message', 'Sem dados disponíveis')}")
            
        elif msg_type == "ACK_ENVIAR":
            print(f"   ✅ Servidor pronto para receber")
            # Aqui você pode enviar os dados reais
            self.send_data("https://exemplo.com/arquivo.pdf")  # Exemplo
            
        elif msg_type == "DATA_RECEIVED":
            print(f"   ✅ Dados foram recebidos pelo servidor")
            
        elif msg_type == "PONG":
            print(f"   🏓 PONG recebido - Conexão OK")
        
        elif msg_type == "MESSAGE":
            content = response.get("content", "")
            print(f"   💬 Mensagem: {content}")
    
    def send_ping(self):
        """Envia ping para o servidor"""
        message = {
            "type": "PING",
            "client_id": self.client_id
        }
        self.sock.sendto(json.dumps(message).encode(), (self.server_ip, self.server_port))
    
    def send_gesture_closed(self):
        """Envia sinal de mão fechada (dados disponíveis)"""
        # Versão simples para compatibilidade
        self.sock.sendto(b"SINAL_ENVIAR", (self.server_ip, self.server_port))
        print("👊 Gesto FECHAR enviado - Dados disponíveis")
    
    def send_gesture_open(self):
        """Envia sinal de mão aberta (solicitar dados)"""
        # Versão simples para compatibilidade
        self.sock.sendto(b"SINAL_RECEBER", (self.server_ip, self.server_port))
        print("✋ Gesto ABRIR enviado - Solicitando dados")
    
    def send_data(self, data: str):
        """Envia dados para o servidor"""
        message = {
            "type": "SEND_DATA",
            "client_id": self.client_id,
            "data": data,
            "timestamp": time.time()
        }
        self.sock.sendto(json.dumps(message).encode(), (self.server_ip, self.server_port))
        print(f"📤 Dados enviados: {data}")
    
    def request_data(self):
        """Solicita dados do servidor (versão JSON)"""
        message = {
            "type": "REQUEST_DATA",
            "client_id": self.client_id
        }
        self.sock.sendto(json.dumps(message).encode(), (self.server_ip, self.server_port))
        print("📥 Solicitando dados...")
    
    def is_hand_closed(self, landmarks):
        """Detecta se a mão está fechada"""
        closed_fingers = 0
        
        # Verifica dedos (exceto polegar)
        for tip_id, pip_id in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            if landmarks[tip_id].y > landmarks[pip_id].y:
                closed_fingers += 1
        
        # Polegar
        if landmarks[4].x < landmarks[3].x:  # Assumindo mão direita
            closed_fingers += 1
        
        return closed_fingers >= 4
    
    def detect_gesture_transition(self, current_state):
        """Detecta transições de gesto com debounce"""
        current_time = time.time()
        transition = None
        
        if current_time - self.last_trigger_time > self.debounce_time:
            if self.prev_state == "open" and current_state == "closed":
                transition = "FECHAR"
                self.last_trigger_time = current_time
            elif self.prev_state == "closed" and current_state == "open":
                transition = "ABRIR"
                self.last_trigger_time = current_time
        
        self.prev_state = current_state
        return transition
    
    def run(self):
        """Loop principal de detecção de gestos"""
        if not self.start_network():
            print("Continuando sem rede...")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Erro ao abrir câmera")
            return
        
        print("\n=== Detector de Gestos Iniciado ===")
        print("👊 Fechar mão = Enviar dados")
        print("✋ Abrir mão = Solicitar dados")
        print("ESC para sair\n")
        
        with self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        ) as hands:
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Processa imagem
                frame = cv2.flip(frame, 1)
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(image_rgb)
                image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                
                # Adiciona informações na tela
                cv2.putText(image_bgr, f"Cliente: {self.client_id}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Desenha landmarks
                        self.mp_drawing.draw_landmarks(
                            image_bgr, hand_landmarks, 
                            self.mp_hands.HAND_CONNECTIONS
                        )
                        
                        # Detecta estado da mão
                        is_closed = self.is_hand_closed(hand_landmarks.landmark)
                        current_state = "closed" if is_closed else "open"
                        
                        # Mostra estado
                        color = (0, 0, 255) if is_closed else (0, 255, 0)
                        cv2.putText(image_bgr, f"Estado: {current_state}", 
                                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
                        # Detecta transição
                        transition = self.detect_gesture_transition(current_state)
                        
                        if transition == "FECHAR":
                            self.send_gesture_closed()
                        elif transition == "ABRIR":
                            self.send_gesture_open()
                
                cv2.imshow("Detector de Gestos", image_bgr)
                
                if cv2.waitKey(5) & 0xFF == 27:  # ESC
                    break
        
        # Limpeza
        self.stop()
        cap.release()
        cv2.destroyAllWindows()
    
    def stop(self):
        """Para o cliente"""
        self.listening = False
        if self.sock:
            self.sock.close()
        print("\nCliente encerrado")

def main():
    # Configurações (pode ler de config.ini se preferir)
    SERVER_IP = "192.168.0.105"  # Ajuste para o IP do servidor
    SERVER_PORT = 5005
    
    # Cria e executa cliente
    client = GestureClient(server_ip=SERVER_IP, server_port=SERVER_PORT)
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")
        client.stop()

if __name__ == "__main__":
    main()