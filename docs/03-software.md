# Software — Stack Completo

## Camadas do Sistema

```
┌─────────────────────────────────────────────┐
│          Camada 5: Conversation Agent        │
│          OpenClaw (Quasar / Claude)          │
├─────────────────────────────────────────────┤
│          Camada 4: Voice Pipeline            │
│          Home Assistant Assist               │
├───────────────┬──────────────┬──────────────┤
│  Camada 3a    │  Camada 3b   │  Camada 3c   │
│  STT: Whisper │  TTS: Piper  │  WW: openWW  │
│  (Wyoming)    │  (Wyoming)   │  (Wyoming)   │
├───────────────┴──────────────┴──────────────┤
│          Camada 2: ESPHome Native API        │
│          Comunicação ESP32 ↔ HA              │
├─────────────────────────────────────────────┤
│          Camada 1: Firmware ESPHome          │
│          ESP32-S3 (mic + speaker + LED)      │
└─────────────────────────────────────────────┘
```

## Componentes de Software

### No ESP32-S3 (Firmware)

| Componente | Tecnologia | Função |
|---|---|---|
| Firmware base | **ESPHome** | Framework de configuração YAML, OTA, API nativa |
| Voice Assistant | `voice_assistant` component | Streaming áudio ↔ HA pipeline |
| Wake Word | `micro_wake_word` component | Detecção local no ESP32 (TFLite) |
| Microfone | `i2s_audio` + `microphone` | Captura áudio I2S do INMP441 |
| Speaker | `i2s_audio` + `speaker` | Reprodução áudio I2S via MAX98357A |
| LED | `light` + `neopixelbus` | Feedback visual WS2812B |
| Wi-Fi | `wifi` component | Conexão à rede local |
| Logger | `logger` component | Debug via USB serial |

### No Servidor (DeskFelipeDell)

| Componente | Tecnologia | Porta | Função |
|---|---|---|---|
| **Home Assistant** | HA Core | :8123 | Orquestrador central + Voice Pipeline |
| **Whisper** | whisper.cpp / faster-whisper | Wyoming | Speech-to-Text local |
| **Piper** | piper-tts | Wyoming | Text-to-Speech neural local |
| **openWakeWord** | openWakeWord | Wyoming | Wake word backup (treinamento custom) |
| **OpenClaw** | Clawdbot | — | Conversation Agent (Claude API) |
| **HA Integrations** | Wyoming + OpenAI Conv. | — | Cola entre componentes |

## Home Assistant — Configuração necessária

### Integrações

1. **Wyoming Protocol** — Conecta Whisper, Piper e openWakeWord
2. **ESPHome** — Conecta os QuasarBox satellites
3. **OpenAI Conversation** (ou custom) — Conversation agent apontando pro OpenClaw

### Voice Pipeline (Assist)

```yaml
# Configuração via UI do HA: Settings → Voice Assistants
# Pipeline "Quasar":
#   - STT: Whisper (Wyoming)
#   - Conversation Agent: OpenClaw (custom/OpenAI-compatible)
#   - TTS: Piper (Wyoming - pt-BR)
#   - Wake Word: openWakeWord (Wyoming)
```

## Serviços Wyoming

O Wyoming protocol roda cada componente como um serviço TCP independente:

```
┌──────────────────────────────────┐
│ faster-whisper (Wyoming server)  │ :10300
│ Modelo: small / medium           │
│ Língua: pt-BR                    │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ piper-tts (Wyoming server)       │ :10200
│ Voz: pt_BR-faber-medium          │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ openWakeWord (Wyoming server)    │ :10400
│ Modelo: custom "ei_quasar"       │
└──────────────────────────────────┘
```

## Conversation Agent — OpenClaw como "Cérebro"

### Forma 1: HA como Ponte (escolhida ✅)

O HA tem suporte nativo a conversation agents via integração **OpenAI Conversation**, que aceita qualquer API compatível com o formato OpenAI Chat Completions.

O OpenClaw expõe (ou pode expor) um endpoint compatível. O fluxo:

```
Voice Pipeline → STT → texto
  → Conversation Agent (OpenClaw API)
    → Claude interpreta o comando
    → Chama HA API se necessário (tools/function calling)
    → Retorna texto de resposta
  → TTS → áudio
  → Volta pro ESP32
```

**Vantagens sobre Assist nativo:**
- Entende linguagem natural complexa ("tá um forno aqui")
- Mantém contexto da conversa
- Pode executar ações compostas ("modo filme")
- Integra com serviços externos (Órbita, TV, etc.)

### Alternativa: Extended OpenAI Conversation (HACS)

Se a integração nativa não for suficiente, existe o [Extended OpenAI Conversation](https://github.com/jekalmin/extended_openai_conversation) via HACS que suporta:
- Function calling (chamar serviços HA)
- Prompt templates
- Qualquer API OpenAI-compatible

## Dependências de Software

### Servidor (pip / Docker)

```
# Whisper (já instalado)
whisper-cpp ou faster-whisper

# Piper TTS
piper-tts

# openWakeWord
openwakeword

# Wyoming servers
wyoming-faster-whisper
wyoming-piper
wyoming-openwakeword
```

### ESPHome (pip)

```
esphome >= 2024.2.0
```

## Versionamento

| Componente | Versão mínima |
|---|---|
| Home Assistant | 2024.2+ (voice pipeline v2) |
| ESPHome | 2024.2+ (voice_assistant v2, micro_wake_word) |
| Whisper | large-v3 / medium (pt-BR) |
| Piper | 1.2+ (pt_BR voices) |
| Python (servidor) | 3.10+ |
