# AI Teleportation - Transferência de Arquivos por Gestos

Sistema de transferência de arquivos entre PCs usando gestos de mão capturados por webcam, inspirado no recurso da Huawei Mate 70.

## 🎯 Funcionalidades

- **Detecção de gestos** com MediaPipe (fechar/abrir mão)
- **Descoberta automática** de dispositivos na rede local (Zeroconf)
- **Transferência via HTTP** com Flask
- **Suporte a múltiplos tipos** de conteúdo (texto, imagens, arquivos)
- **Execução como serviço** em background

## 🚀 Como Funciona

1. **Feche a mão** em frente à webcam (gesto de "agarrar")
2. **Segure por 0.5s** - o sistema captura o conteúdo do clipboard
3. **Mova a mão** para a borda da tela (direção do dispositivo alvo)
4. **Abra a mão** - o arquivo é enviado instantaneamente!

## 📦 Instalação

### Requisitos
- Python 3.8+
- Webcam
- Windows/Linux/macOS

### Passos

```bash
# Clone ou baixe o projeto
cd ai_teleportation

# Instale dependências
pip install -r requirements.txt

# Configure (opcional)
# Edite config.json para personalizar device_name, porta, etc.

# Execute
python main.py
```

## ⚙️ Configuração

Edite `config.json`:

```json
{
    "device_name": "MyPC",        // Nome do dispositivo na rede
    "port": 5000,                 // Porta do servidor HTTP
    "upload_dir": "received_files", // Pasta para arquivos recebidos
    "camera_index": 0,            // Índice da webcam (0 = padrão)
    "show_preview": true          // Mostrar janela de preview
}
```

## 🖥️ Instalação como Serviço

### Windows

```bash
# Instalar serviço
python service_installer.py install

# Iniciar serviço
python service_installer.py start

# Parar serviço
python service_installer.py stop

# Remover serviço
python service_installer.py remove
```

### Linux (systemd)

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/aiteleportation.service
```

Conteúdo:
```ini
[Unit]
Description=AI Teleportation Service
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/caminho/para/ai_teleportation
ExecStart=/usr/bin/python3 /caminho/para/ai_teleportation/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aiteleportation
sudo systemctl start aiteleportation
sudo systemctl status aiteleportation
```

### macOS (launchd)

```bash
# Criar arquivo plist
nano ~/Library/LaunchAgents/com.aiteleportation.plist
```

Conteúdo:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiteleportation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/caminho/para/ai_teleportation/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/caminho/para/ai_teleportation</string>
</dict>
</plist>
```

Ativar:
```bash
launchctl load ~/Library/LaunchAgents/com.aiteleportation.plist
launchctl start com.aiteleportation
```

## 🔧 Estrutura do Projeto

```
ai_teleportation/
├── main.py                    # Aplicação principal
├── gesture_detector.py        # Detecção de gestos com MediaPipe
├── clipboard_manager.py       # Gerenciamento do clipboard
├── device_discovery.py        # Descoberta de dispositivos (Zeroconf)
├── file_transfer_server.py    # Servidor HTTP Flask
├── file_transfer_client.py    # Cliente para envio de arquivos
├── service_installer.py       # Instalador de serviço Windows
├── config.json               # Configuração
├── requirements.txt          # Dependências Python
└── received_files/           # Pasta para arquivos recebidos
```

## 🎮 Uso

### Modo Interativo (com preview)
```bash
python main.py
```
Pressione **ESC** para sair.

### Modo Serviço (background)
O sistema roda sem interface gráfica quando configurado como serviço.

## 🐛 Solução de Problemas

### Câmera não detectada
- Verifique se outra aplicação está usando a webcam
- Tente mudar `camera_index` no config.json (0, 1, 2...)

### Dispositivos não aparecem
- Verifique se estão na mesma rede local
- Verifique firewall (porta 5000 deve estar aberta)
- Certifique-se que ambos estão executando o aplicativo

### Erro ao instalar pywin32
```bash
pip install --upgrade pywin32
python -m pywin32_postinstall -install
```

## 📋 Requisitos de Sistema

- **CPU**: Qualquer processador moderno
- **RAM**: 2GB mínimo
- **Webcam**: Qualquer webcam USB ou integrada
- **Rede**: Wi-Fi ou Ethernet (mesma rede local)

## 🔒 Segurança

- Transfers apenas em rede local (não atravessa internet)
- Sem autenticação (confie na segurança da sua rede local)
- Para produção, considere adicionar HTTPS e autenticação

## 🚀 Melhorias Futuras

- [ ] Autenticação entre dispositivos
- [ ] Criptografia de transferência (HTTPS)
- [ ] Suporte a múltiplos gestos
- [ ] Interface gráfica (system tray)
- [ ] Histórico de transferências
- [ ] Detecção espacial avançada (posição relativa de dispositivos)
- [ ] Suporte a pastas/múltiplos arquivos

## 📄 Licença

MIT License - Livre para uso pessoal e comercial

## 🤝 Contribuições

Contribuições são bem-vindas! Abra issues ou pull requests.

## 👨‍💻 Autor

Desenvolvido como protótipo educacional inspirado no recurso da Huawei Mate 70.