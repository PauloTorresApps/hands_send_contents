import cv2
import mediapipe as mp
import socket
import time
import configparser
import os
import threading
from queue import Queue
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

@dataclass
class Config:
    """Configurações do sistema"""
    udp_ip: str = "192.168.0.179"
    udp_port: int = 5005
    detection_confidence: float = 0.7
    tracking_confidence: float = 0.7
    debounce_time: float = 0.5
    finger_threshold: float = 0.08
    min_closed_fingers: int = 4
    
    @classmethod
    def from_file(cls, filename='config.ini'):
        """Carrega configurações de arquivo INI"""
        config = cls()
        if os.path.exists(filename):
            parser = configparser.ConfigParser()
            parser.read(filename)
            
            if 'Network' in parser:
                config.udp_ip = parser.get('Network', 'ip', fallback=config.udp_ip)
                config.udp_port = parser.getint('Network', 'port', fallback=config.udp_port)
            
            if 'Detection' in parser:
                config.detection_confidence = parser.getfloat('Detection', 'min_detection', fallback=config.detection_confidence)
                config.tracking_confidence = parser.getfloat('Detection', 'min_tracking', fallback=config.tracking_confidence)
                config.debounce_time = parser.getfloat('Detection', 'debounce_time', fallback=config.debounce_time)
                config.finger_threshold = parser.getfloat('Detection', 'finger_threshold', fallback=config.finger_threshold)
                config.min_closed_fingers = parser.getint('Detection', 'min_closed_fingers', fallback=config.min_closed_fingers)
        
        return config

class NetworkHandler:
    """Gerencia comunicação UDP"""
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.sock = None
        self.message_queue = Queue()
        self.running = False
        self.thread = None
        
    def start(self):
        """Inicia o handler de rede em thread separada"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.running = True
            self.thread = threading.Thread(target=self._send_loop, daemon=True)
            self.thread.start()
            print(f"Socket UDP configurado para {self.ip}:{self.port}")
            return True
        except socket.error as e:
            print(f"Erro ao criar socket: {e}")
            return False
    
    def _send_loop(self):
        """Loop de envio em thread separada"""
        while self.running:
            try:
                if not self.message_queue.empty():
                    message = self.message_queue.get()
                    self.sock.sendto(message, (self.ip, self.port))
                    print(f"Enviado: {message.decode()}")
                time.sleep(0.01)
            except socket.error as e:
                print(f"Erro ao enviar: {e}")
    
    def send(self, message: bytes):
        """Adiciona mensagem à fila de envio"""
        self.message_queue.put(message)
    
    def stop(self):
        """Para o handler de rede"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.sock:
            self.sock.close()

class HandDetector:
    """Detecta se a mão está aberta ou fechada"""
    
    def __init__(self, finger_threshold: float = 0.08, min_closed_fingers: int = 4):
        self.finger_threshold = finger_threshold
        self.min_closed_fingers = min_closed_fingers
        
    def is_hand_closed(self, landmarks, handedness: str = "Right") -> bool:
        """
        Detecta se a mão está fechada usando distâncias 3D
        
        Args:
            landmarks: Landmarks do MediaPipe
            handedness: "Right" ou "Left"
        """
        closed_fingers = 0
        
        # Dedos: indicador, médio, anelar, mínimo
        finger_pairs = [
            (8, 6, 5),   # Indicador: ponta, PIP, MCP
            (12, 10, 9), # Médio
            (16, 14, 13),# Anelar
            (20, 18, 17) # Mínimo
        ]
        
        for tip_id, pip_id, mcp_id in finger_pairs:
            tip = landmarks[tip_id]
            pip = landmarks[pip_id]
            mcp = landmarks[mcp_id]
            
            # Calcula distância da ponta até a base do dedo
            tip_to_mcp_dist = self._calculate_distance_3d(tip, mcp)
            pip_to_mcp_dist = self._calculate_distance_3d(pip, mcp)
            
            # Se a ponta está mais próxima da base que o PIP, o dedo está fechado
            if tip_to_mcp_dist < pip_to_mcp_dist * 0.9:
                closed_fingers += 1
        
        # Polegar (lógica diferente baseada na lateralidade)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        
        # Para o polegar, verifica a posição relativa no eixo X
        if handedness == "Right":
            if thumb_tip.x < thumb_ip.x:
                closed_fingers += 1
        else:  # Left hand
            if thumb_tip.x > thumb_ip.x:
                closed_fingers += 1
        
        return closed_fingers >= self.min_closed_fingers
    
    def _calculate_distance_3d(self, point1, point2) -> float:
        """Calcula distância euclidiana 3D entre dois pontos"""
        return np.sqrt(
            (point1.x - point2.x) ** 2 +
            (point1.y - point2.y) ** 2 +
            (point1.z - point2.z) ** 2
        )

class GestureDetector:
    """Detecta transições de gestos com debounce"""
    
    def __init__(self, debounce_time: float = 0.5):
        self.debounce_time = debounce_time
        self.hand_states = {}  # Rastreia estado de cada mão
        
    def detect_transition(self, hand_id: int, current_state: str) -> Optional[str]:
        """
        Detecta transições de estado com debounce
        
        Returns:
            "FECHAR", "ABRIR" ou None
        """
        current_time = time.time()
        
        if hand_id not in self.hand_states:
            self.hand_states[hand_id] = {
                'state': current_state,
                'last_trigger': 0
            }
            return None
        
        prev_state = self.hand_states[hand_id]['state']
        last_trigger = self.hand_states[hand_id]['last_trigger']
        
        transition = None
        
        if current_time - last_trigger > self.debounce_time:
            if prev_state == "open" and current_state == "closed":
                transition = "FECHAR"
                self.hand_states[hand_id]['last_trigger'] = current_time
            elif prev_state == "closed" and current_state == "open":
                transition = "ABRIR"
                self.hand_states[hand_id]['last_trigger'] = current_time
        
        self.hand_states[hand_id]['state'] = current_state
        return transition

class FPSCounter:
    """Contador de FPS"""
    
    def __init__(self):
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
    def update(self) -> float:
        """Atualiza e retorna FPS atual"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
        
        return self.fps

def draw_info(image, fps: float, state: str, hand_count: int):
    """Desenha informações na imagem"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Background para texto
    cv2.rectangle(image, (10, 10), (250, 100), (0, 0, 0), -1)
    
    # FPS
    cv2.putText(image, f"FPS: {fps:.1f}", (20, 35),
                font, 0.6, (0, 255, 0), 2)
    
    # Estado
    color = (0, 0, 255) if state == "closed" else (0, 255, 0)
    cv2.putText(image, f"Estado: {state}", (20, 60),
                font, 0.6, color, 2)
    
    # Número de mãos
    cv2.putText(image, f"Maos: {hand_count}", (20, 85),
                font, 0.6, (255, 255, 255), 2)

def main():
    # Carrega configurações
    config = Config.from_file()
    print("Configurações carregadas")
    
    # Inicializa componentes
    network = NetworkHandler(config.udp_ip, config.udp_port)
    if not network.start():
        print("Falha ao iniciar rede. Continuando sem envio de dados.")
    
    hand_detector = HandDetector(
        finger_threshold=config.finger_threshold,
        min_closed_fingers=config.min_closed_fingers
    )
    
    gesture_detector = GestureDetector(debounce_time=config.debounce_time)
    fps_counter = FPSCounter()
    
    # Inicializa MediaPipe
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    
    # Inicializa câmera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro ao abrir câmera")
        return
    
    # Define resolução para melhor performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Sistema iniciado. Pressione ESC para sair.")
    
    try:
        with mp_hands.Hands(
            min_detection_confidence=config.detection_confidence,
            min_tracking_confidence=config.tracking_confidence,
            max_num_hands=2
        ) as hands:
            
            current_state = "unknown"
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("Erro ao capturar frame")
                    break
                
                # Flip horizontal para espelho
                frame = cv2.flip(frame, 1)
                
                # Converte BGR para RGB
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                
                # Processa a imagem
                results = hands.process(image_rgb)
                
                # Converte de volta para BGR
                image_rgb.flags.writeable = True
                image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                
                hand_count = 0
                
                if results.multi_hand_landmarks:
                    for idx, (hand_landmarks, handedness) in enumerate(
                        zip(results.multi_hand_landmarks, results.multi_handedness)
                    ):
                        hand_count += 1
                        
                        # Desenha landmarks
                        mp_drawing.draw_landmarks(
                            image_bgr, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2),
                            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                        )
                        
                        # Detecta se a mão está fechada
                        hand_label = handedness.classification[0].label
                        is_closed = hand_detector.is_hand_closed(
                            hand_landmarks.landmark, hand_label
                        )
                        
                        current_state = "closed" if is_closed else "open"
                        
                        # Detecta transição
                        transition = gesture_detector.detect_transition(idx, current_state)
                        
                        if transition == "FECHAR":
                            print(f"[Mão {idx}] Gesto de FECHAR detectado!")
                            network.send(b"SINAL_ENVIAR")
                        elif transition == "ABRIR":
                            print(f"[Mão {idx}] Gesto de ABRIR detectado!")
                            network.send(b"SINAL_RECEBER")
                
                # Atualiza FPS
                fps = fps_counter.update()
                
                # Desenha informações
                draw_info(image_bgr, fps, current_state, hand_count)
                
                # Mostra a imagem
                cv2.imshow("Detector de Gestos", image_bgr)
                
                # Verifica tecla ESC
                if cv2.waitKey(5) & 0xFF == 27:
                    break
    
    except Exception as e:
        print(f"Erro durante execução: {e}")
    
    finally:
        # Limpeza
        print("Encerrando sistema...")
        network.stop()
        cap.release()
        cv2.destroyAllWindows()
        print("Sistema encerrado")

if __name__ == "__main__":
    main()