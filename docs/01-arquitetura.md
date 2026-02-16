# Arquitetura — QuasarBox

## Visão Geral

A arquitetura segue o modelo **satellite + servidor central**, onde cada QuasarBox é um dispositivo leve (ESP32-S3) que captura e reproduz áudio, enquanto todo o processamento pesado acontece no servidor (DeskFelipeDell).

## Diagrama de Fluxo

```
┌──────────────────────┐
│  QuasarBox (ESP32-S3) │
│                      │
│  1. Mic captura áudio│
│  2. Wake word local  │─── "Ei Quasar" detectado
│     (micro-WakeNet)  │
│  3. Streaming áudio  │──────────────────────────┐
│  6. Reproduz TTS     │◄─────────────────────┐   │
│     via speaker      │                      │   │
└──────────────────────┘                      │   │
                                              │   │
            Wi-Fi (LAN)                       │   │
                                              │   ▼
┌─────────────────────────────────────────────────────────┐
│                Home Assistant (DeskFelipeDell)           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Assist Voice Pipeline                  │   │
│  │                                                   │   │
│  │  3. STT ─────────► Whisper (whisper.cpp local)   │   │
│  │     "acende a luz da sala"                        │   │
│  │                                                   │   │
│  │  4. Conversation ─► OpenClaw Agent (Quasar)      │   │
│  │     Interpreta NLU + Executa ação                 │   │
│  │     → Chama HA API: light.sala turn_on            │   │
│  │     → Retorna: "Luz da sala ligada"               │   │
│  │                                                   │   │
│  │  5. TTS ─────────► Piper (neural TTS local)      │   │
│  │     Gera áudio da resposta                        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Dispositivos  │  │ LG TV        │  │ Órbita       │ │
│  │ Zigbee/WiFi   │  │ Controller   │  │ (Django)     │ │
│  └───────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Componentes da Arquitetura

### 1. QuasarBox (Satellite — ESP32-S3)

| Responsabilidade | Detalhe |
|---|---|
| Captura de áudio | Microfone INMP441 via I2S |
| Wake word local | micro-WakeNet (Espressif) rodando no ESP32-S3 |
| Streaming de áudio | Envia PCM via protocolo ESPHome → HA |
| Reprodução de áudio | Speaker 3W via MAX98357A (I2S) |
| Feedback visual | LED RGB indica estado (ouvindo, processando, respondendo) |
| Conectividade | Wi-Fi 2.4GHz |

**Firmware:** ESPHome com componente `voice_assistant`

### 2. Home Assistant (Orquestrador)

O HA funciona como hub central usando o **Assist Voice Pipeline**:

| Etapa | Componente | Tecnologia |
|---|---|---|
| Wake Word (backup) | openWakeWord | Wyoming add-on |
| Speech-to-Text | Whisper | whisper.cpp (já instalado no servidor) |
| Conversation Agent | **OpenClaw (Quasar)** | Custom integration (OpenAI-compatible) |
| Text-to-Speech | Piper | Neural TTS local |

### 3. OpenClaw / Quasar (Conversation Agent)

Ao invés do Assist nativo (que só entende intents rígidos), usamos o Quasar como conversation agent. Isso permite:

- **Linguagem natural completa** — "tá muito quente aqui" → liga o ar condicionado
- **Contexto** — "e na sala?" → sabe que você estava falando de temperatura
- **Ações complexas** — "prepara a casa pra filme" → preset: TV liga, luzes dim, cortina fecha
- **Integração existente** — Quasar já controla a TV, acessa Órbita, etc.

### 4. Protocolo de Comunicação

```
ESP32-S3 ◄──► ESPHome Native API ◄──► Home Assistant
                                          │
                                    Voice Pipeline
                                          │
                              ┌───────────┼───────────┐
                              │           │           │
                         Whisper STT   OpenClaw    Piper TTS
                         (Wyoming)    (Conv Agent) (Wyoming)
```

- **ESPHome ↔ HA:** API nativa ESPHome (conexão persistente, auto-reconnect)
- **HA ↔ STT/TTS:** Wyoming protocol (TCP local)
- **HA ↔ OpenClaw:** HTTP API (OpenAI-compatible conversation agent)

## Decisões de Arquitetura

| Decisão | Escolha | Motivo |
|---|---|---|
| Wake word | Local no ESP32 | Privacidade, menor latência, sem tráfego desnecessário |
| STT | Whisper no servidor | ESP32 não tem poder pra STT; servidor já tem Whisper |
| Conversation | OpenClaw (Claude) | NLU superior a intents; já integrado com HA + TV |
| TTS | Piper local | Rápido, neural, offline, pt-BR disponível |
| Protocolo satellite | ESPHome Voice | Mais maduro, YAML config, OTA updates, grande comunidade |
| Formato áudio | PCM 16kHz 16-bit mono | Padrão Whisper, boa qualidade pra voz |

## Latência Estimada

| Etapa | Tempo estimado |
|---|---|
| Wake word detection | ~100ms (local) |
| Streaming áudio (Wi-Fi) | ~50ms |
| STT (Whisper small) | ~2-3s |
| Conversation (Claude) | ~1-3s |
| TTS (Piper) | ~0.5-1s |
| Streaming resposta | ~50ms |
| **Total** | **~4-7s** |

Nota: A maior parte da latência vem do STT + LLM. Com Whisper `tiny` e Claude Haiku, pode cair pra ~2-3s total. Trade-off: qualidade vs velocidade.

## Escalabilidade

O design suporta múltiplos satellites sem alteração no servidor:

- Cada QuasarBox é independente e stateless
- HA gerencia todos os satellites centralmente
- OpenClaw identifica o cômodo de origem pelo `device_id`
- Adicionar um novo cômodo = flashar mais um ESP32-S3
