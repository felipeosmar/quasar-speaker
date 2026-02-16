# Sprint 0 — Setup do Servidor (HA Voice Pipeline)

**Objetivo:** Configurar toda a infraestrutura de voz no DeskFelipeDell para que, quando o ESP32-S3 chegar, seja só conectar e funcionar.

**Duração estimada:** 1-2 dias

## Pré-requisitos

- [x] Home Assistant rodando em `localhost:8123`
- [x] Whisper instalado no servidor (`whisper-transcribe`)
- [ ] ESPHome instalado
- [ ] Piper TTS instalado
- [ ] openWakeWord instalado
- [ ] Wyoming servers rodando
- [ ] Voice Pipeline configurado no HA

## Tarefas

### 0.1 — Verificar instalação do HA

```bash
# Verificar se HA está rodando
curl -s -H "Authorization: Bearer $HA_TOKEN" http://localhost:8123/api/ | jq

# Verificar versão
curl -s -H "Authorization: Bearer $HA_TOKEN" http://localhost:8123/api/config | jq '.version'
```

### 0.2 — Instalar ESPHome

O ESPHome será usado pra compilar e gerenciar firmware dos QuasarBox.

```bash
# Opção A: pip (recomendado)
pip install esphome

# Opção B: Docker
docker run -d \
  --name esphome \
  --restart=unless-stopped \
  -p 6052:6052 \
  -v /home/felipe/work/quasar-speaker/firmware:/config \
  ghcr.io/esphome/esphome

# Verificar
esphome version
```

Dashboard ESPHome: `http://localhost:6052`

### 0.3 — Instalar Wyoming + Faster-Whisper

O Whisper que já temos usa whisper.cpp via CLI. Para integrar com HA Voice Pipeline, precisamos do **Wyoming server** que expõe Whisper como serviço TCP.

```bash
# Instalar faster-whisper (mais rápido que whisper.cpp pra server mode)
pip install wyoming-faster-whisper

# Baixar modelo pt-BR
# (faster-whisper baixa automaticamente na primeira execução)

# Rodar como serviço
wyoming-faster-whisper \
  --model small \
  --language pt \
  --uri tcp://0.0.0.0:10300 \
  --data-dir /home/felipe/.local/share/whisper-wyoming \
  --device cpu

# Testar
echo "teste" | nc -w1 localhost 10300
```

**Systemd service:** `/etc/systemd/system/wyoming-whisper.service`
```ini
[Unit]
Description=Wyoming Faster-Whisper STT
After=network.target

[Service]
User=felipe
ExecStart=/home/felipe/.local/bin/wyoming-faster-whisper \
  --model small \
  --language pt \
  --uri tcp://0.0.0.0:10300 \
  --data-dir /home/felipe/.local/share/whisper-wyoming \
  --device cpu
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 0.4 — Instalar Wyoming + Piper TTS

```bash
# Instalar
pip install wyoming-piper

# Baixar voz pt-BR (faber = masculina, boa qualidade)
# Vozes disponíveis: https://rhasspy.github.io/piper-samples/
mkdir -p /home/felipe/.local/share/piper-voices

# O wyoming-piper baixa vozes automaticamente, mas podemos pré-baixar:
wget -O /tmp/pt_BR-faber-medium.tar.gz \
  "https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-pt_BR-faber-medium.tar.gz"

# Rodar
wyoming-piper \
  --voice pt_BR-faber-medium \
  --uri tcp://0.0.0.0:10200 \
  --data-dir /home/felipe/.local/share/piper-voices \
  --download-dir /home/felipe/.local/share/piper-voices
```

**Systemd service:** `/etc/systemd/system/wyoming-piper.service`
```ini
[Unit]
Description=Wyoming Piper TTS
After=network.target

[Service]
User=felipe
ExecStart=/home/felipe/.local/bin/wyoming-piper \
  --voice pt_BR-faber-medium \
  --uri tcp://0.0.0.0:10200 \
  --data-dir /home/felipe/.local/share/piper-voices \
  --download-dir /home/felipe/.local/share/piper-voices
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 0.5 — Instalar Wyoming + openWakeWord

```bash
# Instalar
pip install wyoming-openwakeword

# Rodar (modelos padrão: "hey jarvis", "ok nabu", etc.)
# Modelo custom "ei quasar" será treinado no Sprint 4
wyoming-openwakeword \
  --uri tcp://0.0.0.0:10400 \
  --preload-model 'hey_jarvis'

# Temporariamente usamos "hey jarvis" até treinar "ei quasar"
```

**Systemd service:** `/etc/systemd/system/wyoming-openwakeword.service`
```ini
[Unit]
Description=Wyoming openWakeWord
After=network.target

[Service]
User=felipe
ExecStart=/home/felipe/.local/bin/wyoming-openwakeword \
  --uri tcp://0.0.0.0:10400 \
  --preload-model 'hey_jarvis'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 0.6 — Configurar Wyoming no Home Assistant

1. Ir em **Settings → Devices & Services → Add Integration**
2. Buscar **Wyoming Protocol**
3. Adicionar 3 instâncias:
   - `localhost:10300` (Whisper STT)
   - `localhost:10200` (Piper TTS)
   - `localhost:10400` (openWakeWord)
4. Cada uma deve aparecer como dispositivo

### 0.7 — Criar Voice Pipeline "Quasar"

1. Ir em **Settings → Voice Assistants**
2. **Add Assistant**:
   - Nome: `Quasar`
   - Language: `pt-BR`
   - Conversation Agent: (inicialmente Assist nativo, depois OpenClaw no Sprint 3)
   - Speech-to-Text: Whisper (Wyoming)
   - Text-to-Speech: Piper (Wyoming - pt_BR-faber-medium)
   - Wake Word: openWakeWord (Wyoming - hey_jarvis)

### 0.8 — Testar Pipeline sem Hardware

O HA permite testar a voice pipeline pela UI:

1. Ir em **Settings → Voice Assistants → Quasar**
2. Clicar no ícone de microfone
3. Falar um comando
4. Verificar: STT transcreve → Agent responde → TTS fala

Ou via API:
```bash
curl -X POST -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pipeline":"quasar","input":{"text":"que horas são?"}}' \
  http://localhost:8123/api/conversation/process
```

## Checklist de Validação

- [ ] Wyoming Whisper rodando em `:10300`
- [ ] Wyoming Piper rodando em `:10200`
- [ ] Wyoming openWakeWord rodando em `:10400`
- [ ] Todos os 3 aparecem no HA como integrações Wyoming
- [ ] Voice Pipeline "Quasar" criado
- [ ] Teste por texto funciona (HA UI)
- [ ] Teste por voz funciona (HA UI com mic do browser)
- [ ] ESPHome instalado e dashboard acessível
- [ ] Os 3 serviços Wyoming são systemd services (boot persistente)

## Notas

- Se o HA roda em Docker, os serviços Wyoming precisam ser acessíveis pelo container (usar IP da rede Docker ou `host.docker.internal`)
- O modelo Whisper `small` é um bom equilíbrio. Se latência for problema, testar `tiny` (mais rápido, menos preciso)
- Piper `medium` quality é o sweet spot. `high` é mais lento sem ganho perceptível pra speaker 3W
