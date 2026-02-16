# 🔊 QuasarBox — Smart Speaker DIY

Smart speaker DIY inspirado no Echo Dot, com ESP32-S3, integrado ao Home Assistant e OpenClaw (Quasar) para controle por voz de toda a casa.

## 🎯 Visão Geral

O QuasarBox é um speaker compacto com microfone always-listening que detecta uma wake word localmente, envia o áudio para processamento STT no servidor, interpreta o comando via IA (Claude/OpenClaw) e executa ações no Home Assistant — tudo com resposta por voz.

```
    ┌─────────────────────────────────────────────────────┐
    │                  QuasarBox (ESP32-S3)                │
    │  Mic ──► Wake Word (local) ──► Streaming Áudio ─────┼──► Wi-Fi
    │  Speaker ◄── Áudio TTS ◄────────────────────────────┼──◄ Wi-Fi
    └─────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────┐
    │             DeskFelipeDell (Servidor)                │
    │                                                     │
    │  Home Assistant ──► Voice Pipeline                  │
    │    ├── STT: Whisper (local)                         │
    │    ├── Conversation Agent: OpenClaw (Quasar/Claude) │
    │    ├── TTS: Piper (local)                           │
    │    └── Wake Word: openWakeWord (backup)             │
    │                                                     │
    │  OpenClaw ──► Interpreta comando ──► Executa ação   │
    │    ├── Home Assistant API (luzes, sensores, etc.)    │
    │    ├── LG TV Controller (TV da sala)                │
    │    └── Qualquer integração futura                   │
    └─────────────────────────────────────────────────────┘
```

## 📋 Índice

- [Arquitetura](docs/01-arquitetura.md)
- [Hardware — Lista de Componentes](docs/02-hardware.md)
- [Software — Stack Completo](docs/03-software.md)
- [Sprint 0 — Setup do Servidor (HA Voice Pipeline)](docs/04-sprint-0-servidor.md)
- [Sprint 1 — Protótipo Hardware](docs/05-sprint-1-hardware.md)
- [Sprint 2 — Firmware ESPHome](docs/06-sprint-2-firmware.md)
- [Sprint 3 — Conversation Agent (OpenClaw)](docs/07-sprint-3-conversation-agent.md)
- [Sprint 4 — Wake Word Custom ("Ei Quasar")](docs/08-sprint-4-wake-word.md)
- [Sprint 5 — Case e Acabamento](docs/09-sprint-5-case.md)
- [Sprint 6 — Multi-Room](docs/10-sprint-6-multi-room.md)
- [Referências](docs/referencias.md)

## 🏗️ Status

| Sprint | Descrição | Status |
|--------|-----------|--------|
| 0 | Setup servidor (HA Voice Pipeline) | 🔲 Não iniciado |
| 1 | Protótipo hardware (1 unidade) | 🔲 Não iniciado |
| 2 | Firmware ESPHome | 🔲 Não iniciado |
| 3 | Conversation Agent (OpenClaw) | 🔲 Não iniciado |
| 4 | Wake Word custom | 🔲 Não iniciado |
| 5 | Case 3D e acabamento | 🔲 Não iniciado |
| 6 | Multi-room (5 cômodos) | 🔲 Não iniciado |

## 💰 Custo Estimado

| Item | Qtd | Unitário | Total |
|------|-----|----------|-------|
| ESP32-S3 (N16R8 ou DevKit) | 5 | ~R$45 | ~R$225 |
| INMP441 (microfone I2S) | 5 | ~R$15 | ~R$75 |
| MAX98357A (amplificador I2S) | 5 | ~R$18 | ~R$90 |
| Speaker 3W 4Ω 40mm | 5 | ~R$10 | ~R$50 |
| LED RGB WS2812B (feedback visual) | 5 | ~R$5 | ~R$25 |
| Cabos, conectores, protoboard | 5 | ~R$15 | ~R$75 |
| Fonte USB-C 5V 2A | 5 | ~R$20 | ~R$100 |
| Filamento PLA (case 3D) | 1 | ~R$60 | ~R$60 |
| **Total (5 unidades)** | | | **~R$700** |

## 🛠️ Infraestrutura Existente

- **Servidor:** DeskFelipeDell (Ubuntu, headless, CPU boa pra Whisper)
- **Home Assistant:** Rodando em `localhost:8123`
- **OpenClaw (Quasar):** Instância ativa com acesso a HA API
- **Whisper:** Já instalado (`whisper-transcribe`, modelo small, ~7s/3s áudio)
- **Rede:** Wi-Fi 2.4GHz em toda a casa

## 📄 Licença

MIT
