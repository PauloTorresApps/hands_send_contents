from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener
import socket
import threading
import time

class DeviceDiscovery:
    def __init__(self, device_name, port=5000):
        self.device_name = device_name
        self.port = port
        self.zeroconf = Zeroconf()
        self.service_type = "_aiteleport._tcp.local."
        self.discovered_devices = {}
        self.listener = None
        self.browser = None
        
    def get_local_ip(self):
        """Obtém IP local"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def register_service(self):
        """Registra este dispositivo na rede"""
        local_ip = self.get_local_ip()
        
        info = ServiceInfo(
            self.service_type,
            f"{self.device_name}.{self.service_type}",
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties={
                'device_name': self.device_name.encode('utf-8'),
                'version': b'1.0'
            }
        )
        
        self.zeroconf.register_service(info)
        print(f"Serviço registrado: {self.device_name} em {local_ip}:{self.port}")
        return info
    
    def start_discovery(self):
        """Inicia descoberta de dispositivos"""
        self.listener = DeviceListener(self.discovered_devices)
        self.browser = ServiceBrowser(self.zeroconf, self.service_type, self.listener)
        print("Descoberta de dispositivos iniciada")
    
    def get_devices(self):
        """Retorna lista de dispositivos descobertos"""
        return list(self.discovered_devices.values())
    
    def find_device_by_position(self, x, y, screen_width, screen_height, margin=200):
        """
        Encontra dispositivo baseado na posição da mão na tela.
        Se a mão está na borda direita, procura dispositivo à direita.
        """
        devices = self.get_devices()
        
        if not devices:
            return None
        
        # Por simplicidade, retorna o primeiro dispositivo disponível
        # Em produção, você implementaria lógica espacial mais sofisticada
        if len(devices) == 1:
            return devices[0]
        
        # Se mão na borda direita da tela, pega primeiro dispositivo
        if x > screen_width - margin:
            return devices[0]
        
        return None
    
    def close(self):
        """Encerra discovery"""
        if self.browser:
            self.browser.cancel()
        self.zeroconf.close()

class DeviceListener(ServiceListener):
    def __init__(self, devices_dict):
        self.devices = devices_dict
        
    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            device_name = info.properties.get(b'device_name', b'Unknown').decode('utf-8')
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port
            
            self.devices[name] = {
                'name': device_name,
                'ip': ip,
                'port': port,
                'service_name': name
            }
            print(f"Dispositivo descoberto: {device_name} ({ip}:{port})")
    
    def remove_service(self, zeroconf, service_type, name):
        if name in self.devices:
            device = self.devices.pop(name)
            print(f"Dispositivo removido: {device['name']}")
    
    def update_service(self, zeroconf, service_type, name):
        pass