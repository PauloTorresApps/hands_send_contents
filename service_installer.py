"""
Instalador de Serviço Windows para AI Teleportation
Requer: pip install pywin32

Uso:
    python service_installer.py install   # Instala o serviço
    python service_installer.py start     # Inicia o serviço
    python service_installer.py stop      # Para o serviço
    python service_installer.py remove    # Remove o serviço
"""

import sys
import os

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("ERRO: pywin32 não está instalado")
    print("Instale com: pip install pywin32")
    sys.exit(1)

from pathlib import Path

# Adiciona diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from main import AITeleportation

class AITeleportationService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AITeleportation"
    _svc_display_name_ = "AI Teleportation Service"
    _svc_description_ = "Serviço de transferência de arquivos por gestos"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.app = None
    
    def SvcStop(self):
        """Chamado quando o serviço é parado"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        
        if self.app:
            self.app.stop()
    
    def SvcDoRun(self):
        """Chamado quando o serviço é iniciado"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.main()
    
    def main(self):
        """Loop principal do serviço"""
        try:
            # Muda para diretório do script
            os.chdir(Path(__file__).parent)
            
            # Desabilita preview no modo serviço
            self.app = AITeleportation()
            self.app.config['show_preview'] = False
            
            # Inicia aplicação
            self.app.start()
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Erro no serviço: {str(e)}")

def install_service():
    """Instala o serviço"""
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AITeleportationService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AITeleportationService)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Comandos: install, start, stop, remove
        install_service()
    else:
        print("Uso:")
        print("  python service_installer.py install   # Instala o serviço")
        print("  python service_installer.py start     # Inicia o serviço")
        print("  python service_installer.py stop      # Para o serviço")
        print("  python service_installer.py remove    # Remove o serviço")