# Hardware — Lista de Componentes

## BOM (Bill of Materials) — Por Unidade

### Componentes Essenciais

| # | Componente | Modelo | Interface | Preço Est. | Link Ref |
|---|-----------|--------|-----------|------------|----------|
| 1 | **Microcontrolador** | ESP32-S3-DevKitC-1 (N16R8) | — | ~R$45 | AliExpress / Mercado Livre |
| 2 | **Microfone** | INMP441 (MEMS I2S) | I2S | ~R$15 | AliExpress |
| 3 | **Amplificador** | MAX98357A (I2S DAC+Amp) | I2S | ~R$18 | AliExpress |
| 4 | **Speaker** | 3W 4Ω 40mm (full range) | Fio | ~R$10 | AliExpress |
| 5 | **LED** | WS2812B Ring (8 LEDs) ou tira | Data (GPIO) | ~R$5 | AliExpress |
| 6 | **Fonte** | USB-C 5V 2A | USB-C | ~R$20 | Local |
| 7 | **Fios/conectores** | Jumpers, headers, solda | — | ~R$15 | Local |
| **Total/unidade** | | | | **~R$128** | |

### Alternativa Premium: ESP32-S3-BOX-3

Se preferir um kit pronto da Espressif (~R$180-250):
- Já vem com mic dual, speaker, tela touch 2.4", case
- Suporte oficial ESPHome
- Ideal pra protótipo rápido, mas mais caro pra escalar

## Especificações dos Componentes

### ESP32-S3-DevKitC-1 (N16R8)

```
CPU:        Xtensa LX7 dual-core @ 240MHz
RAM:        512KB SRAM + 8MB PSRAM (octal SPI)
Flash:      16MB (quad SPI)
Wi-Fi:      802.11 b/g/n 2.4GHz
Bluetooth:  BLE 5.0
I2S:        2x canais (1 pra mic, 1 pra speaker)
GPIO:       45 pinos programáveis
USB:        USB-OTG (programação + alimentação)
Consumo:    ~240mA ativo Wi-Fi, ~10μA deep sleep
Preço:      ~R$35-55
```

**Por que N16R8:** 16MB flash (espaço pra OTA dual-partition) + 8MB PSRAM (wake word + buffers de áudio).

### INMP441 — Microfone MEMS I2S

```
Tipo:       MEMS omnidirecional
Interface:  I2S (digital, sem ADC externo)
SNR:        61 dB
Sensib.:    -26 dBFS
Freq:       60Hz – 15kHz
Consumo:    ~1.4mA
Tensão:     1.8V – 3.3V
```

**Pinagem ESP32-S3:**

| INMP441 | ESP32-S3 | Nota |
|---------|----------|------|
| SCK | GPIO 4 | I2S Clock |
| WS | GPIO 5 | I2S Word Select |
| SD | GPIO 6 | I2S Data (mic output) |
| L/R | GND | Canal esquerdo |
| VDD | 3.3V | Alimentação |
| GND | GND | Terra |

### MAX98357A — Amplificador I2S

```
Tipo:       DAC + Amplificador Classe D
Interface:  I2S (digital in, analógico out)
Potência:   3.2W @ 4Ω (5V)
THD:        0.015% @ 1kHz
Sample Rate: 8kHz – 96kHz
Tensão:     2.5V – 5.5V
```

**Pinagem ESP32-S3:**

| MAX98357A | ESP32-S3 | Nota |
|-----------|----------|------|
| BCLK | GPIO 16 | I2S Bit Clock |
| LRC | GPIO 17 | I2S Left/Right Clock |
| DIN | GPIO 15 | I2S Data |
| GAIN | — | Não conectar = 9dB (padrão) |
| SD | GPIO 18 | Shutdown (HIGH=on) |
| VIN | 5V | Alimentação |
| GND | GND | Terra |

### Speaker 3W 4Ω 40mm

- Diâmetro: 40mm (cabe em case compacto)
- Impedância: 4Ω (match com MAX98357A)
- Potência: 3W RMS
- Frequência: 300Hz – 18kHz

### LED WS2812B Ring (8 LEDs)

Feedback visual dos estados:

| Estado | Efeito LED | Cor |
|--------|-----------|-----|
| Idle | Apagado ou 1 LED azul dim | 🔵 |
| Wake word detectado | Flash branco | ⚪ |
| Ouvindo | Rotação azul | 🔵 |
| Processando | Pulsação amarela | 🟡 |
| Respondendo (TTS) | Verde fixo | 🟢 |
| Erro | Flash vermelho | 🔴 |

**Pinagem:** Data → GPIO 48 (ou qualquer GPIO livre)

## Diagrama de Conexões

```
                    ESP32-S3-DevKitC-1
                   ┌──────────────────┐
                   │                  │
    INMP441 ─────► │ GPIO 4 (SCK)    │
    (Mic I2S)      │ GPIO 5 (WS)     │
                   │ GPIO 6 (SD)     │
                   │                  │
                   │ GPIO 15 (DIN)   │ ◄───── MAX98357A
                   │ GPIO 16 (BCLK)  │        (Amp I2S)
                   │ GPIO 17 (LRC)   │           │
                   │ GPIO 18 (SD_EN) │           ▼
                   │                  │       Speaker 3W
                   │ GPIO 48 (LED)   │ ──► WS2812B Ring
                   │                  │
                   │ 5V ─────────────│─► VIN MAX98357
                   │ 3.3V ───────────│─► VDD INMP441
                   │ GND ────────────│─► GND (comum)
                   │                  │
                   │ USB-C ◄─────────│── Fonte 5V/2A
                   └──────────────────┘
```

## Ferramentas Necessárias

- Ferro de solda + estanho (pra headers e conexões permanentes)
- Multímetro (debug)
- Protoboard (pra protótipo antes de soldar)
- Cabo USB-C (programação + alimentação)
- Impressora 3D (case — Sprint 5, pode ser terceirizado)

## Compras — Onde Comprar

| Loja | Tipo | Frete | Tempo |
|------|------|-------|-------|
| AliExpress | Componentes eletrônicos | Grátis/barato | 15-40 dias |
| Mercado Livre | ESP32-S3, fontes | Rápido | 2-5 dias |
| FilipeFlop | Componentes nacionais | Médio | 3-7 dias |
| JLCPCB | PCB custom (futuro) | Barato | 10-20 dias |

## Notas

- GPIO pinagem é sugestão — pode ser alterada no firmware ESPHome
- PSRAM é **essencial** pro wake word (micro-WakeNet usa ~1-2MB)
- N16R8 = 16MB Flash + 8MB PSRAM (modelo mais comum, evitar N4R2 que é muito apertado)
- O primeiro protótipo pode ser montado em protoboard, sem solda
