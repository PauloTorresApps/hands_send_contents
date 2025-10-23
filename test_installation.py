
"""
Script de teste para verificar a instalação
"""

import sys

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    print("Verificando dependências...\n")
    
    dependencies = {
        'cv2': 'opencv-python',
        'mediapipe': 'mediapipe',
        'zeroconf': 'zeroconf',
        'flask': 'flask',
        'requests': 'requests',
        'pyperclip': 'pyperclip',
        'PIL': 'Pillow'
    }
    
    missing = []
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - FALTANDO")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Instale os pacotes faltantes:")
        print(f"pip install {' '.join(missing)}")
        return False
    else:
        print("\n✅ Todas as dependências instaladas!")
        return True

def check_camera():
    """Verifica se a câmera está acessível"""
    print("\nVerificando câmera...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print("✅ Câmera funcionando")
                return True
            else:
                print("❌ Câmera não conseguiu capturar frame")
                return False
        else:
            print("❌ Não foi possível abrir a câmera")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar câmera: {e}")
        return False

def check_network():
    """Verifica conectividade de rede"""
    print("\nVerificando rede...")
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        print(f"✅ IP local: {ip}")
        return True
    except Exception as e:
        print(f"⚠️  Não foi possível obter IP: {e}")
        return False

def main():
    print("=" * 50)
    print("AI Teleportation - Teste de Instalação")
    print("=" * 50)
    print()
    
    deps_ok = check_dependencies()
    camera_ok = check_camera()
    network_ok = check_network()
    
    print("\n" + "=" * 50)
    if deps_ok and camera_ok:
        print("✅ Sistema pronto para uso!")
        print("\nExecute: python main.py")
    else:
        print("❌ Corrija os problemas acima antes de executar")
    print("=" * 50)

if __name__ == '__main__':
    main()