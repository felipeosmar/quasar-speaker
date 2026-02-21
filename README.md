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
    │  Home Assistant (Docker) ──► Voice Pipeline          │
    │    ├── STT: Whisper (Docker)                        │
    │    ├── Conversation Agent: OpenClaw (Quasar/Claude) │
    │    ├── TTS: Piper (Docker)                          │
    │    └── Wake Word: openWakeWord (Docker, backup)     │
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
- [Sprint 4 — Wake Word](docs/08-sprint-4-wake-word.md)
- [Sprint 5 — Case e Acabamento](docs/09-sprint-5-case.md)
- [Sprint 6 — Multi-Room](docs/10-sprint-6-multi-room.md)
- [Sprint 7 — Integração HA ↔ Dispositivos](docs/11-sprint-7-integracao-ha.md)
- [Sprint 8 — PCB Custom](docs/12-sprint-8-pcb-custom.md)
- [Hardware Design (Referência)](docs/hardware-design.md)
- [Referências](docs/referencias.md)

## 🏗️ Status

| Sprint | Descrição | Status |
|--------|-----------|--------|
| 0 | Setup servidor (HA Voice Pipeline via Docker) | 🔲 Não iniciado |
| 1 | Protótipo hardware (1 unidade, protoboard) | 🔲 Não iniciado |
| 2 | Firmware ESPHome | 🔲 Não iniciado |
| 3 | Conversation Agent (OpenClaw) | 🔲 Não iniciado |
| 4 | Wake Word (provisória + custom) | 🔲 Não iniciado |
| 5 | Case 3D e acabamento | 🔲 Não iniciado |
| 6 | Multi-room (5 cômodos) | 🔲 Não iniciado |
| 7 | Integração HA ↔ dispositivos smart | 🔲 Não iniciado |
| 8 | PCB custom (design + fabricação) | 🔲 Não iniciado |

## 💰 Custo Estimado

### Protótipo (1 unidade, protoboard)

| Item | Preço Est. |
|------|------------|
| ESP32-S3-DevKitC-1 N16R8 | ~R$40 |
| INMP441 breakout | ~R$15 |
| MAX98357A breakout | ~R$18 |
| Speaker 3W 4Ω 40mm | ~R$10 |
| WS2812B ring 8 LEDs | ~R$5 |
| Protoboard + jumpers | ~R$16 |
| Cabo USB-C | ~R$10 |
| **Total protótipo** | **~R$115** |

### Produção (5 unidades com PCB)

| Item | Qtd | Total |
|------|-----|-------|
| Componentes eletrônicos (5x) | 5 | ~R$440 |
| PCB custom (JLCPCB, 5 un.) | 5 | ~R$50-120 |
| Fontes USB-C 5V 2A | 5 | ~R$100 |
| Filamento PLA (cases 3D) | 1 | ~R$60 |
| Dispositivos smart (lâmpadas, plugs) | — | ~R$150-280 |
| **Total estimado (5 unidades + devices)** | | **~R$800-1000** |

## 🛠️ Infraestrutura Existente

- **Servidor:** DeskFelipeDell (Ubuntu, headless, Docker)
- **Home Assistant:** Rodando em Docker, `localhost:8123`
- **OpenClaw (Quasar):** Instância ativa com acesso a HA API
- **Whisper:** Já instalado (`whisper-transcribe`, modelo small, ~7s/3s áudio)
- **LG TV Controller:** API local em `:8888`
- **Rede:** Wi-Fi 2.4GHz em toda a casa

## 📄 Licença

MIT
