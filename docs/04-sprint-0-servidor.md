# Sprint 0 — Setup do Servidor (HA Voice Pipeline)

**Objetivo:** Configurar toda a infraestrutura de voz no DeskFelipeDell para que, quando o ESP32-S3 chegar, seja só conectar e funcionar.

**Duração estimada:** 1-2 dias

## Pré-requisitos

- [x] Home Assistant rodando em Docker em `localhost:8123`
- [x] Whisper instalado no servidor (`whisper-transcribe`)
- [ ] ESPHome rodando via Docker
- [ ] Piper TTS rodando via Docker
- [ ] openWakeWord rodando via Docker
- [ ] Wyoming servers acessíveis pelo HA
- [ ] Voice Pipeline configurado no HA

## Arquitetura Docker

Todos os serviços rodam via Docker Compose no DeskFelipeDell. O HA já roda em Docker, então os serviços Wyoming precisam estar na mesma rede Docker (ou usar `host` networking) para se comunicarem.

```
┌─────────────────────────────────────────────┐
│            Docker (DeskFelipeDell)           │
│                                             │
│  ┌──────────────┐  ┌────────────────────┐   │
│  │ Home Assist. │  │ wyoming-whisper     │   │
│  │  :8123       │  │  :10300             │   │
│  └──────────────┘  └────────────────────┘   │
│  ┌──────────────┐  ┌────────────────────┐   │
│  │ wyoming-piper│  │ wyoming-openwakeword│   │
│  │  :10200      │  │  :10400             │   │
│  └──────────────┘  └────────────────────┘   │
│  ┌──────────────┐                           │
│  │ esphome      │                           │
│  │  :6052       │                           │
│  └──────────────┘                           │
│                                             │
│  Network: quasar-net (bridge)               │
└─────────────────────────────────────────────┘
```

## Tarefas

### 0.1 — Verificar instalação do HA

```bash
# Verificar se HA está rodando
curl -s -H "Authorization: Bearer $HA_TOKEN" http://localhost:8123/api/ | jq

# Verificar versão
curl -s -H "Authorization: Bearer $HA_TOKEN" http://localhost:8123/api/config | jq '.version'

# Verificar rede Docker do HA
docker inspect homeassistant | jq '.[0].NetworkSettings.Networks'
```

### 0.2 — Criar Docker Compose para serviços Wyoming + ESPHome

Criar o arquivo `docker-compose.yml` no diretório do projeto:

```yaml
# /home/felipe/work/quasar-speaker/docker-compose.yml
version: "3.8"

services:
  # ─── ESPHome ─────────────────────────────────────────────
  esphome:
    container_name: esphome
    image: ghcr.io/esphome/esphome:latest
    restart: unless-stopped
    ports:
      - "6052:6052"
    volumes:
      - ./firmware:/config
      - /etc/localtime:/etc/localtime:ro
    network_mode: host  # necessário para mDNS (descoberta de ESPs na rede)

  # ─── Wyoming Faster-Whisper (STT) ───────────────────────
  wyoming-whisper:
    container_name: wyoming-whisper
    image: rhasspy/wyoming-whisper:latest
    restart: unless-stopped
    ports:
      - "10300:10300"
    volumes:
      - whisper-data:/data
    command: >
      --model small
      --language pt
      --uri tcp://0.0.0.0:10300
      --data-dir /data
      --device cpu

  # ─── Wyoming Piper (TTS) ────────────────────────────────
  wyoming-piper:
    container_name: wyoming-piper
    image: rhasspy/wyoming-piper:latest
    restart: unless-stopped
    ports:
      - "10200:10200"
    volumes:
      - piper-data:/data
    command: >
      --voice pt_BR-faber-medium
      --uri tcp://0.0.0.0:10200
      --data-dir /data
      --download-dir /data

  # ─── Wyoming openWakeWord ────────────────────────────────
  wyoming-openwakeword:
    container_name: wyoming-openwakeword
    image: rhasspy/wyoming-openwakeword:latest
    restart: unless-stopped
    ports:
      - "10400:10400"
    command: >
      --uri tcp://0.0.0.0:10400
      --preload-model hey_jarvis

volumes:
  whisper-data:
  piper-data:
```

### 0.3 — Subir os serviços

```bash
cd /home/felipe/work/quasar-speaker

# Subir tudo
docker compose up -d

# Verificar logs
docker compose logs -f wyoming-whisper
docker compose logs -f wyoming-piper
docker compose logs -f wyoming-openwakeword
docker compose logs -f esphome

# Verificar que as portas estão escutando
ss -tlnp | grep -E '10200|10300|10400|6052'
```

### 0.4 — Verificar conectividade do HA com os serviços Wyoming

O HA precisa acessar os containers Wyoming. Se o HA roda com `network_mode: host`, basta usar `localhost`. Se roda em rede bridge, use o IP do host Docker (`172.17.0.1` ou o IP da interface `docker0`):

```bash
# Descobrir IP do host na rede Docker
ip addr show docker0 | grep inet

# Testar conectividade de dentro do container HA
docker exec homeassistant nc -zv localhost 10300
docker exec homeassistant nc -zv localhost 10200
docker exec homeassistant nc -zv localhost 10400

# Se não funcionar com localhost, tentar IP do host:
docker exec homeassistant nc -zv 172.17.0.1 10300
```

**Dica:** Se o HA roda com `network_mode: host`, todos os serviços com portas expostas são acessíveis via `localhost` automaticamente. Essa é a configuração mais simples.

### 0.5 — Configurar Wyoming no Home Assistant

1. Ir em **Settings → Devices & Services → Add Integration**
2. Buscar **Wyoming Protocol**
3. Adicionar 3 instâncias:
   - `localhost:10300` (Whisper STT) — ou IP do host Docker se necessário
   - `localhost:10200` (Piper TTS)
   - `localhost:10400` (openWakeWord)
4. Cada uma deve aparecer como dispositivo

### 0.6 — Criar Voice Pipeline "Quasar"

1. Ir em **Settings → Voice Assistants**
2. **Add Assistant**:
   - Nome: `Quasar`
   - Language: `pt-BR`
   - Conversation Agent: (inicialmente Assist nativo, depois OpenClaw no Sprint 3)
   - Speech-to-Text: Whisper (Wyoming)
   - Text-to-Speech: Piper (Wyoming - pt_BR-faber-medium)
   - Wake Word: openWakeWord (Wyoming - hey_jarvis)

### 0.7 — Testar Pipeline sem Hardware

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

### 0.8 — Dashboard ESPHome

Acessar `http://localhost:6052` para verificar que o ESPHome está funcionando. Esse dashboard será usado nos Sprints 1 e 2 para compilar e flashar o firmware dos QuasarBox.

## Comandos Úteis

```bash
# Parar tudo
docker compose down

# Atualizar imagens
docker compose pull && docker compose up -d

# Reiniciar um serviço específico
docker compose restart wyoming-whisper

# Ver logs de um serviço
docker compose logs -f wyoming-piper

# Verificar uso de recursos
docker stats wyoming-whisper wyoming-piper wyoming-openwakeword esphome
```

## Modelo Whisper — Escolha

| Modelo | VRAM/RAM | Tempo (~3s áudio) | Qualidade pt-BR |
|--------|----------|-------------------|-----------------|
| tiny | ~1GB | ~2s | Razoável |
| base | ~1GB | ~3s | Boa |
| small | ~2GB | ~5s | Muito boa ✅ |
| medium | ~5GB | ~10s | Excelente |

**Recomendação:** `small` para equilíbrio. Se a latência for problema, testar `base`.

Para trocar o modelo, editar o `docker-compose.yml` e reiniciar:
```bash
docker compose restart wyoming-whisper
```

## Checklist de Validação

- [ ] Docker Compose criado e funcionando
- [ ] Wyoming Whisper rodando em `:10300` (container `wyoming-whisper`)
- [ ] Wyoming Piper rodando em `:10200` (container `wyoming-piper`)
- [ ] Wyoming openWakeWord rodando em `:10400` (container `wyoming-openwakeword`)
- [ ] ESPHome rodando em `:6052` (container `esphome`)
- [ ] Todos os 3 Wyoming aparecem no HA como integrações
- [ ] Voice Pipeline "Quasar" criado
- [ ] Teste por texto funciona (HA UI)
- [ ] Teste por voz funciona (HA UI com mic do browser)
- [ ] Containers reiniciam automaticamente após reboot (`restart: unless-stopped`)

## Notas

- Todos os serviços rodam via Docker — não há `pip install` no host
- Se o HA roda com `network_mode: host`, use `localhost` pra tudo
- Se o HA roda em rede bridge, use o IP do host Docker ou crie uma rede compartilhada
- O modelo Whisper `small` é um bom equilíbrio. Se latência for problema, testar `base` (mais rápido, menos preciso)
- Piper `medium` quality é o sweet spot. `high` é mais lento sem ganho perceptível pra speaker 3W
- Volumes Docker (`whisper-data`, `piper-data`) persistem modelos baixados entre reinícios
