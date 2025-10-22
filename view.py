import socket
import json
import time
from datetime import datetime
import platform
import threading
from typing import Dict, Tuple

class UDPServer:
    def __init__(self, ip="0.0.0.0", port=5005):
        self.ip = ip
        self.port = port
        self.sock = None
        self.running = False
        
        # Identificação do servidor
        self.server_id = f"{platform.node()}_{platform.system()}"
        
        # Armazena informações dos clientes conectados
        self.clients: Dict[str, dict] = {}
        
        # Dados compartilhados (URL ou arquivo disponível)
        self.shared_data = None
        self.data_lock = threading.Lock()
        
    def start(self):
        """Inicia o servidor UDP"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.ip, self.port))
            self.sock.settimeout(1.0)  # Timeout para permitir parada limpa
            self.running = True
            
            print(f"=== Servidor UDP Iniciado ===")
            print(f"IP: {self.ip}")
            print(f"Porta: {self.port}")
            print(f"ID do Servidor: {self.server_id}")
            print(f"Aguardando sinais...\n")
            
            self.listen()
            
        except socket.error as e:
            print(f"Erro ao iniciar servidor: {e}")
            return False
        
        return True
    
    def listen(self):
        """Loop principal de escuta"""
        while self.running:
            try:
                # Recebe dados
                data, addr = self.sock.recvfrom(1024)
                
                # Processa em thread separada para não bloquear
                thread = threading.Thread(
                    target=self.handle_message,
                    args=(data, addr),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                continue
            except socket.error as e:
                print(f"Erro no socket: {e}")
                break
    
    def handle_message(self, data: bytes, addr: Tuple[str, int]):
        """Processa mensagens recebidas"""
        client_key = f"{addr[0]}:{addr[1]}"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Atualiza informações do cliente
        if client_key not in self.clients:
            self.clients[client_key] = {
                "first_seen": timestamp,
                "last_seen": timestamp,
                "message_count": 0
            }
        
        self.clients[client_key]["last_seen"] = timestamp
        self.clients[client_key]["message_count"] += 1
        
        print(f"\n[{timestamp}] Mensagem de {addr[0]}:{addr[1]}")
        
        try:
            # Tenta decodificar como JSON primeiro
            if data.startswith(b'{'):
                message = json.loads(data.decode())
                self.handle_json_message(message, addr)
            else:
                # Mensagem simples (compatibilidade com código anterior)
                self.handle_simple_message(data, addr)
                
        except json.JSONDecodeError:
            self.handle_simple_message(data, addr)
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
    
    def handle_simple_message(self, data: bytes, addr: Tuple[str, int]):
        """Processa mensagens simples (legado)"""
        if data == b"SINAL_ENVIAR":
            print(f"→ Gesto FECHAR detectado: Cliente tem dados para compartilhar")
            
            # Envia confirmação
            response = json.dumps({
                "type": "ACK_ENVIAR",
                "server_id": self.server_id,
                "message": "Servidor pronto para receber dados",
                "timestamp": time.time()
            }).encode()
            
            self.sock.sendto(response, addr)
            print(f"← Confirmação enviada para {addr[0]}:{addr[1]}")
            
        elif data == b"SINAL_RECEBER":
            print(f"→ Gesto ABRIR detectado: Cliente solicitou dados")
            
            with self.data_lock:
                if self.shared_data:
                    # Envia dados disponíveis
                    response = json.dumps({
                        "type": "DATA_RESPONSE",
                        "server_id": self.server_id,
                        "data": self.shared_data,
                        "timestamp": time.time()
                    }).encode()
                else:
                    # Informa que não há dados
                    response = json.dumps({
                        "type": "NO_DATA",
                        "server_id": self.server_id,
                        "message": "Nenhum dado disponível no momento",
                        "timestamp": time.time()
                    }).encode()
            
            self.sock.sendto(response, addr)
            print(f"← Resposta enviada para {addr[0]}:{addr[1]}")
    
    def handle_json_message(self, message: dict, addr: Tuple[str, int]):
        """Processa mensagens JSON estruturadas"""
        msg_type = message.get("type", "UNKNOWN")
        client_id = message.get("client_id", "unknown")
        
        print(f"→ Tipo: {msg_type} | Cliente ID: {client_id}")
        
        if msg_type == "SEND_DATA":
            # Cliente enviando dados
            data_content = message.get("data")
            if data_content:
                with self.data_lock:
                    self.shared_data = data_content
                print(f"  Dados recebidos: {data_content[:100]}...")
                
                # Confirma recebimento
                response = json.dumps({
                    "type": "DATA_RECEIVED",
                    "server_id": self.server_id,
                    "status": "success",
                    "timestamp": time.time()
                }).encode()
                
                self.sock.sendto(response, addr)
                
        elif msg_type == "REQUEST_DATA":
            # Cliente solicitando dados
            with self.data_lock:
                if self.shared_data:
                    response = json.dumps({
                        "type": "DATA_RESPONSE",
                        "server_id": self.server_id,
                        "data": self.shared_data,
                        "timestamp": time.time()
                    }).encode()
                else:
                    response = json.dumps({
                        "type": "NO_DATA",
                        "server_id": self.server_id,
                        "message": "Nenhum dado disponível",
                        "timestamp": time.time()
                    }).encode()
            
            self.sock.sendto(response, addr)
            print(f"← Resposta enviada")
        
        elif msg_type == "PING":
            # Responde ao ping
            response = json.dumps({
                "type": "PONG",
                "server_id": self.server_id,
                "timestamp": time.time()
            }).encode()
            
            self.sock.sendto(response, addr)
            print(f"← PONG enviado")
    
    def send_broadcast(self, message: dict):
        """Envia mensagem para todos os clientes conhecidos"""
        message["server_id"] = self.server_id
        message["timestamp"] = time.time()
        data = json.dumps(message).encode()
        
        for client_key in self.clients:
            ip, port = client_key.split(':')
            try:
                self.sock.sendto(data, (ip, int(port)))
                print(f"Broadcast enviado para {client_key}")
            except Exception as e:
                print(f"Erro ao enviar para {client_key}: {e}")
    
    def set_shared_data(self, data: str):
        """Define dados para compartilhar"""
        with self.data_lock:
            self.shared_data = data
            print(f"Dados configurados para compartilhamento: {data[:100]}...")
    
    def show_stats(self):
        """Mostra estatísticas dos clientes"""
        print("\n=== Estatísticas dos Clientes ===")
        for client_key, info in self.clients.items():
            print(f"Cliente: {client_key}")
            print(f"  Primeira conexão: {info['first_seen']}")
            print(f"  Última atividade: {info['last_seen']}")
            print(f"  Mensagens recebidas: {info['message_count']}")
        print()
    
    def stop(self):
        """Para o servidor"""
        self.running = False
        if self.sock:
            self.sock.close()
        print("\nServidor UDP encerrado")

def main():
    # Cria e inicia o servidor
    server = UDPServer(ip="0.0.0.0", port=5005)
    
    # Thread para comandos do console
    def console_commands():
        while server.running:
            try:
                cmd = input().strip().lower()
                
                if cmd == "stats":
                    server.show_stats()
                elif cmd == "set":
                    data = input("Digite os dados para compartilhar: ")
                    server.set_shared_data(data)
                elif cmd.startswith("send "):
                    msg = cmd[5:]
                    server.send_broadcast({"type": "MESSAGE", "content": msg})
                elif cmd == "help":
                    print("\nComandos disponíveis:")
                    print("  stats - Mostra estatísticas dos clientes")
                    print("  set   - Define dados para compartilhar")
                    print("  send <msg> - Envia mensagem broadcast")
                    print("  quit  - Encerra o servidor")
                    print()
                elif cmd == "quit":
                    server.stop()
                    break
            except KeyboardInterrupt:
                break
    
    # Inicia thread de comandos
    cmd_thread = threading.Thread(target=console_commands, daemon=True)
    cmd_thread.start()
    
    print("\nDigite 'help' para ver comandos disponíveis")
    print("Ctrl+C ou 'quit' para sair\n")
    
    try:
        # Inicia o servidor
        server.start()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")
    finally:
        server.stop()

if __name__ == "__main__":
    main()