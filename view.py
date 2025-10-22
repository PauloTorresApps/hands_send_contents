import socket

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("Aguardando sinais...")

while True:
    data, addr = sock.recvfrom(1024)
    if data == b"SINAL_ENVIAR":
        print(f"Dispositivo {addr} enviou um arquivo/URL disponível")
    elif data == b"SINAL_RECEBER":
        print(f"Dispositivo {addr} solicitou o envio do arquivo/URL")
