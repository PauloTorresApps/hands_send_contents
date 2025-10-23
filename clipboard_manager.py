import pyperclip
import os
import tempfile
from PIL import ImageGrab
import time
from pathlib import Path

class ClipboardManager:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_teleportation"
        self.temp_dir.mkdir(exist_ok=True)
        
    def capture_clipboard(self):
        """
        Captura conteúdo do clipboard e retorna:
        - tipo: 'text', 'image', ou 'file'
        - conteúdo: string de texto ou caminho do arquivo
        """
        try:
            # Tenta capturar imagem primeiro
            image = ImageGrab.grabclipboard()
            if image is not None:
                # Salva imagem temporariamente
                filename = f"clipboard_{int(time.time())}.png"
                filepath = self.temp_dir / filename
                image.save(filepath, 'PNG')
                return 'image', str(filepath)
            
            # Tenta capturar texto
            text = pyperclip.paste()
            if text and text.strip():
                # Verifica se é caminho de arquivo
                if os.path.exists(text):
                    return 'file', text
                else:
                    # Salva texto como arquivo temporário
                    filename = f"clipboard_{int(time.time())}.txt"
                    filepath = self.temp_dir / filename
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(text)
                    return 'text', str(filepath)
            
            return None, None
            
        except Exception as e:
            print(f"Erro ao capturar clipboard: {e}")
            return None, None
    
    def set_clipboard_text(self, text):
        """Define texto no clipboard"""
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"Erro ao definir clipboard: {e}")
            return False
    
    def cleanup_temp_files(self, max_age_hours=24):
        """Remove arquivos temporários antigos"""
        try:
            current_time = time.time()
            for file in self.temp_dir.glob("clipboard_*"):
                if current_time - file.stat().st_mtime > max_age_hours * 3600:
                    file.unlink()
        except Exception as e:
            print(f"Erro ao limpar arquivos temporários: {e}")