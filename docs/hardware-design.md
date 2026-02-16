# 🔧 Hardware Design — QuasarBox

Documento de referência para criação do esquemático e PCB no EasyEDA.

---

## 1. Decisão: Módulo vs Chip

| Abordagem | Prós | Contras |
|---|---|---|
| **ESP32-S3-WROOM-1 (módulo)** | Antena integrada, mais fácil de rotear, certificado RF | Maior, mais caro |
| **ESP32-S3 chip nu** | Menor, mais barato em volume | Precisa antena, matching, mais complexo |

**Escolha: ESP32-S3-WROOM-1-N8R8** (módulo com 8MB Flash + 8MB PSRAM)
- Simplifica enormemente o design — Wi-Fi, flash, PSRAM, cristal, tudo dentro do módulo
- A PCB custom só precisa lidar com: alimentação, I2S, LED, conectores

---

## 2. Esquemático — Blocos Funcionais

```
┌─────────────────────────────────────────────────────────────┐
│                     QuasarBox PCB                           │
│                                                             │
│  ┌──────────┐     ┌────────────────────────────────────┐   │
│  │  USB-C    │────►│  Alimentação                       │   │
│  │  5V Input │     │  ├─ 5V rail → MAX98357A, LED       │   │
│  └──────────┘     │  └─ 3.3V (LDO AMS1117) → ESP32,Mic │   │
│                    └────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────┐                 │
│  │  ESP32-S3-WROOM-1-N8R8                 │                 │
│  │                                        │                 │
│  │  I2S0 (Mic Input)     I2S1 (Speaker)   │                 │
│  │  ├ GPIO4  (BCLK)      ├ GPIO16 (BCLK)  │                │
│  │  ├ GPIO5  (WS)        ├ GPIO17 (WS)    │                │
│  │  ├ GPIO6  (DIN)       ├ GPIO15 (DOUT)  │                │
│  │  │                    │                 │                │
│  │  GPIO18 (AMP_SD)      GPIO48 (LED)     │                │
│  │  GPIO0  (BOOT)        EN (RESET)       │                │
│  └────────────────────────────────────────┘                │
│       │          │           │          │                   │
│       ▼          ▼           ▼          ▼                   │
│  ┌────────┐ ┌────────┐ ┌─────────┐ ┌────────┐             │
│  │INMP441 │ │MAX98357│ │WS2812B  │ │Botões  │             │
│  │Mic I2S │ │Amp I2S │ │LED Ring │ │Boot/Rst│             │
│  └────────┘ └───┬────┘ └─────────┘ └────────┘             │
│                  │                                          │
│              ┌───▼───┐                                      │
│              │Speaker│                                      │
│              │3W 4Ω  │                                      │
│              └───────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Pinout Definitivo do ESP32-S3

### GPIOs Usados

| GPIO | Função | Periférico | Direção | Notas |
|------|--------|-----------|---------|-------|
| **GPIO4** | I2S0_BCLK | INMP441 SCK | OUT | Clock do mic |
| **GPIO5** | I2S0_WS | INMP441 WS | OUT | Word Select mic |
| **GPIO6** | I2S0_DIN | INMP441 SD | IN | Data do mic |
| **GPIO15** | I2S1_DOUT | MAX98357A DIN | OUT | Data pro amp |
| **GPIO16** | I2S1_BCLK | MAX98357A BCLK | OUT | Clock do amp |
| **GPIO17** | I2S1_WS | MAX98357A LRC | OUT | Word Select amp |
| **GPIO18** | AMP_SD | MAX98357A SD | OUT | Shutdown (HIGH=on) |
| **GPIO48** | LED_DATA | WS2812B DIN | OUT | NeoPixel data |
| **GPIO0** | BOOT | Botão Boot | IN | Pull-up interno, LOW=boot mode |
| **EN** | RESET | Botão Reset | IN | Pull-up externo, LOW=reset |

### GPIOs Reservados (NÃO usar)

| GPIO | Motivo |
|------|--------|
| GPIO35, 36, 37 | Usados internamente pelo PSRAM (Octal SPI) |
| GPIO26-32 | Usados internamente pelo Flash (Octal SPI) — depende do módulo |
| GPIO19, 20 | USB D-/D+ (USB-OTG) |
| GPIO38 | LED RGB onboard (DevKitC v1.1) |

### GPIOs Livres (expansão futura)

| GPIO | Sugestão |
|------|----------|
| GPIO1 | Sensor de temperatura (futuro) |
| GPIO2 | Sensor de luminosidade (futuro) |
| GPIO3 | Botão mute físico |
| GPIO7 | Botão de ação / volume |
| GPIO8 | IR transmitter (controle remoto futuro) |
| GPIO9-14 | Livres |
| GPIO21 | Livre |
| GPIO38 | LED onboard (pode usar como status) |
| GPIO39-42 | Livres (JTAG, mas usável) |
| GPIO43-44 | UART0 TX/RX (debug serial) |
| GPIO45-46 | Strapping pins (cuidado na inicialização) |
| GPIO47 | Livre |

---

## 4. Esquemático Detalhado por Bloco

### 4.1 — Alimentação

```
                    USB-C Connector (16-pin ou 6-pin simple)
                    ┌───────────┐
           VBUS ────┤ 1   VBUS  │──── 5V_RAW
           GND  ────┤ 4   GND   │──── GND
           D+   ────┤ 2   D+    │──── (não conectar pra power-only)
           D-   ────┤ 3   D-    │──── (não conectar pra power-only)
                    └───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │   Proteção ESD + Fuse  │
            │                        │
            │  F1: Fuse 500mA resett │ (Polyfuse MF-R050)
            │  D1: TVS diode (opt.)  │ (USBLC6-2SC6)
            └────────┬───────────────┘
                     │ 5V_FUSED
                     │
            ┌────────┼────────────────────────────────────┐
            │        │                                     │
            │  C1: 100µF/10V eletrolítico (bulk)          │
            │  C2: 100nF cerâmico (bypass)                │
            │        │                                     │
            ├────────┼──► 5V rail ──► MAX98357A VIN       │
            │        │              ──► WS2812B VCC        │
            │        │                                     │
            │  ┌─────▼──────┐                              │
            │  │ AMS1117-3.3│                              │
            │  │ VIN    VOUT├──► 3.3V rail                 │
            │  │    GND     │    │                         │
            │  └─────┬──────┘    ├─► ESP32 3V3             │
            │        │          ├─► INMP441 VDD            │
            │       GND         │                          │
            │                   C3: 22µF/10V (output LDO)  │
            │                   C4: 100nF (bypass)         │
            └──────────────────────────────────────────────┘
```

**Componentes de alimentação:**

| Ref | Componente | Valor | Package | Notas |
|-----|-----------|-------|---------|-------|
| J1 | USB-C Female | 16-pin ou 6-pin | SMD | Só power (VBUS+GND) |
| F1 | Polyfuse | 500mA | 1206 | Proteção overcurrent |
| U1 | AMS1117-3.3 | 3.3V LDO | SOT-223 | 5V→3.3V, 1A max |
| C1 | Capacitor eletrolítico | 100µF/10V | Radial 5mm | Bulk input |
| C2 | Capacitor cerâmico | 100nF | 0603 | Bypass input |
| C3 | Capacitor cerâmico | 22µF/10V | 0805 | Output LDO |
| C4 | Capacitor cerâmico | 100nF | 0603 | Bypass output |

**Consumo estimado:**

| Componente | Corrente típica | Rail |
|---|---|---|
| ESP32-S3 (Wi-Fi ativo) | ~240mA | 3.3V |
| INMP441 | ~1.4mA | 3.3V |
| MAX98357A (3W@4Ω) | ~500mA pico | 5V |
| WS2812B (8 LEDs, branco full) | ~480mA pico | 5V |
| **Total máximo** | **~750mA @5V** | |

Fonte de 5V/2A tem margem suficiente.

### 4.2 — ESP32-S3-WROOM-1 (Módulo)

```
                ESP32-S3-WROOM-1-N8R8
         ┌──────────────────────────────┐
         │                              │
    EN ──┤ 1  EN              GND    39 ├── GND
  GPIO4 ─┤ 2  IO4             IO48  38 ├── GPIO48 (LED)
  GPIO5 ─┤ 3  IO5             IO47  37 ├── (livre)
  GPIO6 ─┤ 4  IO6             IO21  36 ├── (livre)
  GPIO7 ─┤ 5  IO7             IO20  35 ├── (USB D+)
  GPIO15 ┤ 6  IO15            IO19  34 ├── (USB D-)
  GPIO16 ┤ 7  IO16            IO18  33 ├── GPIO18 (AMP_SD)
  GPIO17 ┤ 8  IO17            IO17  -- ├── (ver pin 8)
  GPIO18 ┤ --  (ver pin 33)   IO16  -- ├── (ver pin 7)
    3V3 ─┤ 9  3V3             IO15  -- ├── (ver pin 6)
    3V3 ─┤ 10 3V3             GND   32 ├── GND
   GND  ─┤ 11 GND             IO14  31 ├── (livre)
         │                    IO13  30 ├── (livre)
         │  ... (ver datasheet pra pinout completo)
         │                              │
         │  GND PAD (bottom) ───────── GND
         └──────────────────────────────┘
```

**Capacitores de bypass no módulo:**
- C5: 100nF entre 3V3 e GND (o mais perto possível do módulo)
- C6: 10µF entre 3V3 e GND

**Circuito de Reset:**
```
3.3V ──┬── R1 (10kΩ) ──┬── EN (pin 1)
       │                │
       │           C7 (1µF)
       │                │
       │               GND
       │
       └── SW1 (Reset button) ── GND
```

**Circuito de Boot:**
```
3.3V ── R2 (10kΩ) ──┬── GPIO0
                     │
                SW2 (Boot button) ── GND
```

### 4.3 — Microfone INMP441

```
                INMP441 Breakout
              ┌─────────────────┐
              │                 │
  GPIO4  ────┤ SCK    VDD  ├──── 3.3V
  GPIO5  ────┤ WS     GND  ├──── GND
  GPIO6  ◄───┤ SD     L/R  ├──── GND (canal esquerdo)
              │                 │
              └─────────────────┘

  Bypass: C8 100nF entre VDD e GND (junto ao INMP441)
```

**Notas de layout:**
- Manter INMP441 no TOPO da PCB (virado pra cima)
- Furo acústico na PCB ou no case alinhado com o port do mic
- Trilhas I2S curtas (< 50mm idealmente)
- GND plane sólido sob o mic (reduz ruído)

### 4.4 — Amplificador MAX98357A + Speaker

```
                MAX98357A Breakout
              ┌─────────────────────┐
              │                     │
  GPIO16 ────┤ BCLK     VIN    ├──── 5V
  GPIO17 ────┤ LRC      GND    ├──── GND
  GPIO15 ────┤ DIN      OUT+   ├────┐
  GPIO18 ────┤ SD       OUT-   ├──┐ │
              │  GAIN    (nc)   │  │ │
              └──┬──────────────┘  │ │
                 │                 │ │
                 NC (9dB default)  │ │
                                   │ │
                              ┌────┘ │
                              │      │
                          ┌───▼──────▼───┐
                          │   Speaker    │
                          │   3W 4Ω      │
                          │   40mm       │
                          └──────────────┘

  Bypass: C9 10µF entre VIN e GND (junto ao MAX98357A)
```

**Configuração do GAIN:**

| GAIN pin | Ganho |
|----------|-------|
| Não conectado (float) | 9dB (padrão, recomendado) |
| GND | 12dB (mais alto) |
| VIN | 15dB (máximo, pode distorcer) |

**SD (Shutdown):**
- HIGH (3.3V ou via GPIO18) = amplificador ligado
- LOW = desligado (modo sleep, consumo ~2µA)
- Permite desligar o amp quando não tá reproduzindo = economia de energia

**Conector do Speaker:**
- JST PH 2.0mm 2-pin (fácil de conectar/desconectar)
- Ou pads de solda direta

### 4.5 — LED Ring WS2812B

```
         3.3V                5V
          │                   │
     R3 (470Ω)          C10 (100nF por LED)
          │                   │
  GPIO48 ─┴──► DIN    VCC ◄──┘
              ┌─────────────────┐
              │  WS2812B Ring   │
              │  8 LEDs         │
              │  DOUT → (nc)    │
              │  GND ──────────►│──── GND
              └─────────────────┘
```

**Notas:**
- R3 (470Ω) no DIN: proteção contra reflexão no sinal de dados
- Capacitor 100nF entre VCC e GND de cada LED (os rings geralmente já têm)
- O ESP32 S3 opera a 3.3V, WS2812B aceita nível lógico 3.3V com VCC a 5V (threshold ~0.7×VCC = 3.5V, marginal mas funciona)
- Se tiver problemas de nível lógico: adicionar level shifter (SN74HCT125) ou usar 3.3V no VCC dos LEDs (menor brilho)

### 4.6 — Botões

```
  3.3V ── R1 (10kΩ) ──┬── EN        (Reset)
                       │
                  SW1 (tactile)
                       │
                      GND

  3.3V ── R2 (10kΩ) ──┬── GPIO0     (Boot)
                       │
                  SW2 (tactile)
                       │
                      GND

  3.3V ── R4 (10kΩ) ──┬── GPIO3     (Mute - opcional)
                       │
                  SW3 (tactile)
                       │
                      GND
```

---

## 5. BOM Completo (PCB Custom)

| Ref | Componente | Valor | Package | Qtd | Notas |
|-----|-----------|-------|---------|-----|-------|
| U1 | AMS1117-3.3 | 3.3V LDO | SOT-223 | 1 | Regulador |
| U2 | ESP32-S3-WROOM-1-N8R8 | Módulo | SMD | 1 | MCU principal |
| U3 | INMP441 | Mic MEMS I2S | Breakout/SMD | 1 | Microfone |
| U4 | MAX98357A | DAC+Amp I2S | Breakout/SMD | 1 | Amplificador |
| J1 | USB-C Female | Power only | SMD 16-pin | 1 | Alimentação |
| J2 | JST PH 2.0mm | 2-pin | THT | 1 | Conector speaker |
| J3 | Header 1x8 | (opcional) | 2.54mm | 1 | Expansão/debug |
| LS1 | Speaker | 3W 4Ω 40mm | Wire | 1 | Alto-falante |
| LED1 | WS2812B Ring | 8 LEDs | Wire/SMD | 1 | Feedback visual |
| SW1 | Tactile switch | Reset | 6x6mm THT | 1 | Reset |
| SW2 | Tactile switch | Boot | 6x6mm THT | 1 | Boot/Flash |
| SW3 | Tactile switch | Mute | 6x6mm THT | 1 | Opcional |
| R1 | Resistor | 10kΩ | 0603 | 1 | Pull-up EN |
| R2 | Resistor | 10kΩ | 0603 | 1 | Pull-up GPIO0 |
| R3 | Resistor | 470Ω | 0603 | 1 | LED data line |
| R4 | Resistor | 10kΩ | 0603 | 1 | Pull-up mute (opt) |
| C1 | Capacitor eletrolítico | 100µF/10V | Radial 5mm | 1 | Bulk 5V |
| C2 | Capacitor cerâmico | 100nF | 0603 | 1 | Bypass 5V |
| C3 | Capacitor cerâmico | 22µF/10V | 0805 | 1 | Output LDO |
| C4 | Capacitor cerâmico | 100nF | 0603 | 1 | Bypass 3.3V |
| C5 | Capacitor cerâmico | 100nF | 0603 | 1 | Bypass ESP32 |
| C6 | Capacitor cerâmico | 10µF | 0805 | 1 | Bulk ESP32 |
| C7 | Capacitor cerâmico | 1µF | 0603 | 1 | Reset RC |
| C8 | Capacitor cerâmico | 100nF | 0603 | 1 | Bypass mic |
| C9 | Capacitor cerâmico | 10µF | 0805 | 1 | Bypass amp |
| C10 | Capacitor cerâmico | 100nF | 0603 | 1 | Bypass LED |
| F1 | Polyfuse | 500mA | 1206 | 1 | Proteção |

**Total de componentes únicos:** ~25
**Custo estimado PCB (JLCPCB, 5 unidades):** ~R$25 + R$50 frete

---

## 6. Layout da PCB

### Dimensões

- **Forma:** Circular, Ø85mm (cabe no case cilíndrico)
- **Layers:** 2 (Top + Bottom) — suficiente pra essa complexidade
- **Espessura:** 1.6mm (padrão)

### Posicionamento dos Componentes

```
            Vista Superior (Top Layer)
        ┌─────────────────────────────────┐
        │           ○ ○ ○ ○ ○ ○ ○ ○      │  ← LED Ring (borda)
        │         ╭─────────────────╮     │
        │         │    INMP441      │     │  ← Mic no centro-topo
        │         │    (furo acúst.)│     │
        │         ╰─────────────────╯     │
        │                                 │
        │  ┌─────────────────────────┐    │
        │  │                         │    │
        │  │   ESP32-S3-WROOM-1     │    │  ← Módulo no centro
        │  │                         │    │
        │  │   ▓▓▓ antena ▓▓▓       │    │  ← Antena na borda!
        │  └─────────────────────────┘    │
        │                                 │
        │  ┌──────┐  ┌──────┐  [SW][SW]  │
        │  │AMS1117│  │MAX98 │  Rst Boot  │
        │  └──────┘  │357A  │            │
        │             └──────┘            │
        │                                 │
        │  ═══ USB-C ═══    ○○ JST SPK   │  ← Conectores na borda
        └─────────────────────────────────┘

            Vista Inferior (Bottom Layer)
        ┌─────────────────────────────────┐
        │                                 │
        │     ████████████████████████    │  ← GND plane (quase solid)
        │     ████████████████████████    │
        │     ████████████████████████    │
        │     ████████████████████████    │
        │                                 │
        └─────────────────────────────────┘
```

### Regras de Layout

1. **Antena ESP32:** NENHUM cobre (GND ou trilha) sob a antena do módulo. Manter zona de exclusão de ~10mm
2. **GND plane:** Bottom layer inteiro como ground plane. Vias de GND frequentes
3. **Separação analógico/digital:** Manter mic longe do amp e do switching do ESP32
4. **Trilhas de potência:** ≥0.5mm pra 5V (corrente do speaker), ≥0.3mm pra 3.3V
5. **Trilhas I2S:** Manter curtas e paralelas, com GND entre grupos mic/speaker
6. **Capacitores bypass:** O mais perto possível de cada IC (< 5mm)
7. **USB-C na borda:** Acessível pelo case

---

## 7. Guia EasyEDA — Passo a Passo

### 7.1 — Criar Projeto

1. Abrir [easyeda.com](https://easyeda.com) ou EasyEDA Desktop
2. **File → New Project**: "QuasarBox"
3. Criar **Schematic** primeiro, depois **PCB**

### 7.2 — Bibliotecas de Componentes

Buscar no EasyEDA Library (LCSC integrado):

| Componente | Buscar por | LCSC Part # (ref) |
|---|---|---|
| ESP32-S3-WROOM-1-N8R8 | "ESP32-S3-WROOM-1" | C2913196 |
| AMS1117-3.3 | "AMS1117-3.3" | C6186 |
| USB-C 16pin | "USB TYPE-C 16P" | C168688 |
| INMP441 | "INMP441" | — (usar breakout header) |
| MAX98357A | "MAX98357A" | — (usar breakout header) |
| Tactile Switch | "TS-1187A" | C318884 |
| WS2812B | "WS2812B" | C2761795 |

**Nota sobre breakouts:** INMP441 e MAX98357A são mais fáceis de usar como breakout boards conectadas via header. Pra PCB v1 (protótipo), usar headers 2.54mm. Pra v2 (produção), colocar os chips SMD direto na placa.

### 7.3 — Fluxo de Trabalho

1. **Esquemático:** Desenhar todos os blocos (alimentação → ESP32 → periféricos)
2. **Verificar DRC** (Design Rule Check) no esquemático
3. **Converter pra PCB:** Assign footprints → Update PCB
4. **Layout:** Posicionar componentes conforme seção 6
5. **Rotear trilhas:** Power primeiro, depois sinais
6. **GND plane:** Fill zone no bottom layer
7. **Verificar DRC** da PCB
8. **Gerar Gerber** → enviar pra JLCPCB

### 7.4 — Design Rules (EasyEDA/JLCPCB)

| Parâmetro | Valor |
|---|---|
| Track width mínimo | 0.2mm (sinal), 0.5mm (power) |
| Clearance mínimo | 0.2mm |
| Via diameter | 0.6mm (hole 0.3mm) |
| Board outline | Ø85mm circular |
| Copper layers | 2 |
| Board thickness | 1.6mm |
| Surface finish | HASL (mais barato) ou ENIG |

---

## 8. Versões da PCB

### v1 — Protótipo (breakouts)

- ESP32-S3 módulo soldado direto
- INMP441 e MAX98357A como breakout boards via headers
- LED Ring via fios
- Componentes THT onde possível (mais fácil de soldar)
- Objetivo: validar funcionalidade

### v2 — Produção (tudo SMD)

- Todos componentes SMD na placa
- INMP441 e MAX98357A direto no PCB
- WS2812B individuais no anel da PCB (sem ring separado)
- Conector FPC pro speaker
- Pré-montagem SMT pela JLCPCB (Assembly service)
- Objetivo: compacto, profissional

---

## 9. Considerações Térmicas

- ESP32-S3: ~0.5W → sem dissipador necessário
- MAX98357A: ~0.3W @ 1W output → OK sem dissipador
- AMS1117: P = (5V-3.3V) × 0.25A = 0.42W → pad de cobre no PCB como heatsink
- **Total dissipação:** ~1.2W → case com ventilação passiva suficiente

---

## 10. Checklist pra EasyEDA

- [ ] Projeto criado no EasyEDA
- [ ] Esquemático: bloco alimentação completo
- [ ] Esquemático: ESP32-S3 módulo com bypass caps
- [ ] Esquemático: circuito reset + boot
- [ ] Esquemático: INMP441 (I2S mic)
- [ ] Esquemático: MAX98357A (I2S amp)
- [ ] Esquemático: WS2812B (LED)
- [ ] Esquemático: USB-C connector
- [ ] Esquemático: botões (reset, boot, mute)
- [ ] DRC esquemático: 0 erros
- [ ] PCB: footprints atribuídos
- [ ] PCB: board outline Ø85mm
- [ ] PCB: componentes posicionados
- [ ] PCB: zona de exclusão na antena
- [ ] PCB: trilhas roteadas
- [ ] PCB: GND fill no bottom layer
- [ ] PCB: DRC 0 erros
- [ ] Gerber exportado
