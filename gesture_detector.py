import cv2
import mediapipe as mp
import time
from enum import Enum

class GestureState(Enum):
    IDLE = "idle"
    GRABBING = "grabbing"
    HOLDING = "holding"
    RELEASING = "releasing"

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        self.state = GestureState.IDLE
        self.grab_start_time = None
        self.hold_duration_threshold = 0.5  # segundos
        
    def is_hand_closed(self, hand_landmarks):
        """Detecta se a mão está fechada (punho)"""
        # Pega as coordenadas dos dedos
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        # Base da palma
        wrist = hand_landmarks.landmark[0]
        palm_base = hand_landmarks.landmark[9]
        
        # Calcula distância média das pontas dos dedos até a base da palma
        avg_distance = (
            self._distance(index_tip, palm_base) +
            self._distance(middle_tip, palm_base) +
            self._distance(ring_tip, palm_base) +
            self._distance(pinky_tip, palm_base)
        ) / 4
        
        # Mão fechada = dedos próximos da palma
        return avg_distance < 0.15
    
    def is_hand_open(self, hand_landmarks):
        """Detecta se a mão está aberta"""
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        palm_base = hand_landmarks.landmark[9]
        
        # Calcula distância média das pontas dos dedos até a base da palma
        avg_distance = (
            self._distance(index_tip, palm_base) +
            self._distance(middle_tip, palm_base) +
            self._distance(ring_tip, palm_base) +
            self._distance(pinky_tip, palm_base)
        ) / 4
        
        # Mão aberta = dedos longe da palma
        return avg_distance > 0.20
    
    def _distance(self, point1, point2):
        """Calcula distância euclidiana entre dois pontos"""
        return ((point1.x - point2.x)**2 + 
                (point1.y - point2.y)**2 + 
                (point1.z - point2.z)**2)**0.5
    
    def get_hand_position(self, hand_landmarks, frame_shape):
        """Retorna posição (x, y) do centro da mão em pixels"""
        h, w, _ = frame_shape
        palm_base = hand_landmarks.landmark[9]
        return int(palm_base.x * w), int(palm_base.y * h)
    
    def process_frame(self, frame):
        """
        Processa um frame e retorna:
        - frame anotado
        - estado do gesto
        - posição da mão (x, y) ou None
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        hand_position = None
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Desenha landmarks
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS
                )
                
                # Detecta gesto
                hand_position = self.get_hand_position(hand_landmarks, frame.shape)
                
                is_closed = self.is_hand_closed(hand_landmarks)
                is_open = self.is_hand_open(hand_landmarks)
                
                # Máquina de estados
                if self.state == GestureState.IDLE:
                    if is_closed:
                        self.state = GestureState.GRABBING
                        self.grab_start_time = time.time()
                        
                elif self.state == GestureState.GRABBING:
                    if not is_closed:
                        # Soltou muito rápido, volta ao idle
                        self.state = GestureState.IDLE
                        self.grab_start_time = None
                    elif time.time() - self.grab_start_time > self.hold_duration_threshold:
                        # Segurou tempo suficiente
                        self.state = GestureState.HOLDING
                        
                elif self.state == GestureState.HOLDING:
                    if is_open:
                        self.state = GestureState.RELEASING
                        self.grab_start_time = None
                    elif not is_closed:
                        # Mão não está mais fechada mas não abriu completamente
                        self.state = GestureState.IDLE
                        self.grab_start_time = None
                        
                elif self.state == GestureState.RELEASING:
                    # Reset após release
                    self.state = GestureState.IDLE
        else:
            # Sem mão detectada
            if self.state != GestureState.IDLE:
                self.state = GestureState.IDLE
                self.grab_start_time = None
        
        # Adiciona status no frame
        status_text = f"Estado: {self.state.value.upper()}"
        cv2.putText(frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return frame, self.state, hand_position
    
    def release(self):
        """Libera recursos"""
        self.hands.close()