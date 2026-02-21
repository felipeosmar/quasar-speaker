# Sprint 8 — PCB Custom

**Objetivo:** Projetar e encomendar uma PCB custom para o QuasarBox, substituindo a protoboard/perfboard por uma placa profissional e replicável.

**Duração estimada:** 5-7 dias (design) + 10-20 dias (fabricação e entrega)

**Pré-requisito:** Sprint 1 validado (protótipo em protoboard funcionando perfeitamente).

---

## Visão Geral do Processo

```
Esquemático → Layout PCB → DRC → Revisão → Gerber Export → Encomenda → Montagem
    (1)          (2)       (3)     (4)         (5)           (6)        (7)
```

Cada etapa tem seu checklist. NÃO pular etapas.

---

## Etapa 1: Review do Esquemático

O esquemático já está documentado em `docs/hardware-design.md`. Antes de iniciar o layout, fazer review completo:

### 1.1 — Verificar blocos funcionais

- [ ] **Alimentação:** USB-C → 5V rail → AMS1117 → 3.3V rail
  - Polyfuse F1 500mA no VBUS
  - C1 100µF bulk + C2 100nF bypass na entrada
  - C3 22µF + C4 100nF na saída do LDO
- [ ] **ESP32-S3-WROOM-1-N8R8:** bypass caps (C5 100nF + C6 10µF)
  - Circuito reset (R1 10kΩ + C7 1µF + SW1)
  - Circuito boot (R2 10kΩ + SW2)
  - Zona de exclusão da antena respeitada
- [ ] **INMP441:** I2S connections (GPIO 4/5/6), bypass C8 100nF
  - L/R → GND (canal esquerdo)
- [ ] **MAX98357A:** I2S connections (GPIO 15/16/17), SD → GPIO 18
  - Bypass C9 10µF, conector speaker JST PH 2-pin
  - GAIN: não conectado (9dB padrão)
- [ ] **WS2812B:** GPIO 48 → R3 470Ω → DIN, bypass C10 100nF
- [ ] **Botões:** Reset (EN), Boot (GPIO0), Mute opcional (GPIO3)

### 1.2 — Verificar net names e labels

Todas as nets devem ter nomes claros: `5V`, `3V3`, `GND`, `I2S_MIC_BCLK`, `I2S_SPK_DIN`, `LED_DATA`, etc.

### 1.3 — Rodar ERC (Electrical Rules Check)

No EasyEDA: **Design → Design Rule Check** no esquemático. Resolver todos os erros e warnings.

---

## Etapa 2: Layout da PCB

### 2.1 — Formato e Dimensões

- **Forma:** Retangular (ou outra forma a definir com base no case)
- **Dimensões sugeridas:** 70×70mm ou 80×60mm — depende do layout dos componentes e do design do case
- **Layers:** 2 (Top + Bottom) — suficiente pra essa complexidade
- **Espessura:** 1.6mm (padrão)

> **Nota:** O formato final depende do case (Sprint 5). Se o case for cilíndrico, uma PCB retangular inscrita no cilindro funciona bem. Definir dimensões exatas depois de modelar o case.

### 2.2 — Design Rules (JLCPCB-compatible)

| Parâmetro | Valor Mínimo | Recomendado |
|-----------|-------------|-------------|
| Track width (sinal) | 0.127mm (5mil) | 0.25mm (10mil) |
| Track width (power 5V) | 0.3mm | 0.5-1.0mm |
| Track width (power 3.3V) | 0.25mm | 0.4-0.5mm |
| Clearance | 0.127mm (5mil) | 0.2mm (8mil) |
| Via diameter | 0.45mm | 0.6mm |
| Via hole | 0.2mm | 0.3mm |
| Annular ring | 0.13mm | 0.15mm |
| Board outline clearance | 0.3mm | 0.5mm |

### 2.3 — Posicionamento dos Componentes

**Princípios:**
1. **INMP441 no topo** — port acústico virado pra cima (com furo na PCB ou no case)
2. **Antena ESP32 na borda** — sem cobre (GND ou trilha) sob a antena. Zona de exclusão mínima de 10mm ao redor
3. **USB-C na borda** — acessível pelo case
4. **Conector speaker na borda** — JST PH 2-pin
5. **Capacitores bypass** — o mais perto possível do IC respectivo (< 5mm)
6. **Separação analógico/digital** — mic longe do amp e da área de switching

```
    Layout Sugerido (Vista Superior)
    ┌─────────────────────────────────────┐
    │  [MIC INMP441]    [botões RST/BOOT]│
    │                                     │
    │  ┌───────────────────────────┐      │
    │  │   ESP32-S3-WROOM-1       │      │
    │  │                           │      │
    │  │   ▓▓▓ antena ▓▓▓         │← borda!
    │  └───────────────────────────┘      │
    │                                     │
    │  [AMS1117]  [caps]  [MAX98357A]    │
    │                                     │
    │  ═══USB-C═══        ○○JST SPK     │
    └─────────────────────────────────────┘
```

### 2.4 — Ground Plane

- **Bottom layer inteiro** como ground plane (copper fill)
- Vias de GND frequentes (a cada ~10mm em áreas críticas)
- **Não cortar** o ground plane com trilhas de sinal — usar top layer pra roteamento
- Ground sólido sob o INMP441 (reduz ruído no mic)

### 2.5 — Roteamento

**Ordem de roteamento:**
1. Power rails (5V, 3.3V) — trilhas grossas
2. I2S do microfone (sinais sensíveis) — curtas, paralelas
3. I2S do speaker
4. LED data
5. Sinais diversos (botões, etc.)

**Dicas:**
- I2S clock e data devem correr paralelas e próximas, com GND entre grupos
- Evitar trilhas longas paralelas de sinais diferentes (crosstalk)
- Usar vias pra ground plane sempre que um componente tiver pino GND
- Trilhas de áudio (I2S) longe de trilhas de power switching

---

## Etapa 3: DRC (Design Rule Check)

No EasyEDA: **Design → Design Rule Check** na PCB.

### Erros que DEVEM ser zero:
- Clearance violation
- Short circuit
- Unconnected net
- Track width violation

### Warnings aceitáveis:
- Silk overlap (ajustar mas não crítico)
- Courtyard overlap (se intencional)

---

## Etapa 4: Revisão Final

### Checklist antes de encomendar

**Esquemático:**
- [ ] ERC passa sem erros
- [ ] Todos os componentes têm footprint atribuído
- [ ] Valores dos componentes estão corretos (resistores, caps)
- [ ] Polaridade de capacitores eletrolíticos correta
- [ ] USB-C pinagem correta (VBUS, GND, CC1/CC2 se aplicável)
- [ ] Pull-ups no EN e GPIO0 presentes

**PCB Layout:**
- [ ] DRC passa sem erros
- [ ] Zona de exclusão na antena ESP32 respeitada (sem cobre)
- [ ] Ground plane sólido no bottom layer
- [ ] Capacitores bypass próximos aos ICs
- [ ] Trilhas de power com largura adequada (≥0.5mm pra 5V)
- [ ] Furos de montagem (se necessário pra case)
- [ ] Furo acústico sob o INMP441 (se mic no topo da PCB)
- [ ] Silk screen legível (labels dos componentes, versão, nome)
- [ ] Board outline correto (dimensões finais)

**Fabricação:**
- [ ] Gerber gerado e verificado no viewer (JLCPCB tem viewer online)
- [ ] BOM exportado (se usar SMT assembly)
- [ ] Pick & Place file exportado (se usar SMT assembly)

### Review visual

1. Exportar PNG/PDF da PCB (top e bottom)
2. Verificar visualmente que tudo faz sentido
3. Comparar com esquemático — conferir cada net
4. Imprimir em escala 1:1 e colocar componentes físicos em cima (sanity check de tamanho)

---

## Etapa 5: Gerber Export

No EasyEDA Pro:

1. **Fabrication → PCB Fabrication File (Gerber)**
2. Configurações padrão (JLCPCB-compatible):
   - Gerber RS274X
   - Drill: Excellon
3. Baixar ZIP com os arquivos:
   - `*.GTL` (Top Copper)
   - `*.GBL` (Bottom Copper)
   - `*.GTS` (Top Solder Mask)
   - `*.GBS` (Bottom Solder Mask)
   - `*.GTO` (Top Silk Screen)
   - `*.GBO` (Bottom Silk Screen)
   - `*.GKO` (Board Outline)
   - `*.DRL` (Drill file)

Se usar SMT Assembly, também exportar:
- **BOM (CSV):** File → Export BOM
- **Pick & Place (CSV):** Fabrication → Pick and Place File

---

## Etapa 6: Encomenda

### JLCPCB (Recomendado)

**Site:** [jlcpcb.com](https://jlcpcb.com)

1. Upload Gerber ZIP
2. Configurar:
   - **Layers:** 2
   - **Quantity:** 5 (mínimo, preço base)
   - **PCB Thickness:** 1.6mm
   - **Surface Finish:** HASL (mais barato) ou LeadFree HASL
   - **PCB Color:** Verde (mais barato) ou Preto (mais bonito)
   - **Copper Weight:** 1oz (padrão)
   - **Remove Order Number:** Yes (estético, +$1)
3. Opcionalmente: **SMT Assembly** (JLCPCB monta os componentes SMD)

### Custo Estimado (JLCPCB, Fev 2026)

| Item | Custo |
|------|-------|
| PCB 5 unidades (≤100×100mm, 2 layers) | $2-5 |
| SMT Assembly (setup fee) | $8 |
| Componentes SMD (extended parts) | $5-15 |
| Frete (economy, 15-20 dias) | $5-15 |
| **Total estimado (5 PCBs)** | **$20-45 (~R$100-230)** |

**Sem SMT Assembly** (soldar manualmente):

| Item | Custo |
|------|-------|
| PCB 5 unidades | $2-5 |
| Frete | $5-10 |
| **Total** | **$7-15 (~R$35-75)** |

### PCBWay (Alternativa)

Similar ao JLCPCB. Às vezes mais caro na PCB mas mais opções de assembly. Útil como backup.

---

## Etapa 7: Montagem e Teste

### Se usou SMT Assembly

1. Receber as placas com SMD montados
2. Soldar componentes THT: headers, botões, conector USB-C (se THT), JST speaker
3. Soldar módulo ESP32-S3-WROOM-1 (reflow ou ferro de solda com flux)

### Se soldar manualmente

**Ordem de soldagem (SMD first, THT last):**
1. AMS1117 (SOT-223) — pads grandes, fácil
2. Resistores e capacitores 0603 — pinça + ferro fino + flux
3. USB-C connector — mais difícil, usar flux generosamente
4. Módulo ESP32-S3 — castellated pads, soldável com ferro
5. Polyfuse 1206
6. Botões tactile (THT)
7. Headers/conectores (THT)

**Ferramentas necessárias:**
- Ferro de solda com ponta fina (cônica ou chisel 1mm)
- Flux em pasta ou caneta
- Solda 0.5mm (pra SMD) e 0.8mm (pra THT)
- Pinça antiestática
- Lupa ou microscópio USB (ajuda muito com 0603)
- Multímetro (verificar shorts)

### Teste pós-montagem

1. **Antes de ligar:** Verificar com multímetro que não há short entre 5V-GND e 3.3V-GND
2. **Ligar:** Conectar USB-C, verificar 5V e 3.3V nos rails
3. **ESP32:** Deve aparecer no USB como dispositivo serial
4. **Flash firmware:** ESPHome compile + upload
5. **Testar cada periférico:** mic, speaker, LEDs, botões

---

## Versões da PCB

### v1 — Protótipo com Breakouts

- ESP32-S3 módulo soldado direto
- INMP441 e MAX98357A como **breakout boards via headers** (mais fácil de trocar/debug)
- LED Ring via fios (header 3-pin)
- Alguns componentes THT (mais fácil de soldar)
- **Objetivo:** Validar layout, conexões, e fit no case

### v2 — Produção (tudo SMD)

- INMP441 e MAX98357A ICs direto na PCB (sem breakout)
- WS2812B individuais na placa (sem ring separado)
- Conector FPC pro speaker (mais compacto)
- SMT assembly pela JLCPCB
- **Objetivo:** Compacto, profissional, replicável

**Recomendação:** Fazer v1 primeiro. Só investir na v2 depois de validar tudo.

---

## Dicas de Design

### 2 Layers é suficiente?

Sim, absolutamente. O QuasarBox tem poucos componentes e poucas nets. 2 layers (top routing + bottom ground plane) é mais que suficiente. 4 layers seria overkill e mais caro.

### Thermal Relief em Ground Plane

Usar thermal relief nos pads conectados ao ground plane (padrão no EasyEDA). Sem isso, o ground plane age como dissipador e torna a soldagem manual muito difícil.

### Testpoints

Adicionar testpoints acessíveis pra debug:
- TP1: 5V
- TP2: 3.3V
- TP3: GND
- TP4: I2S_MIC_SD (dados do mic)

### Silk Screen

- Nome do projeto: "QuasarBox v1"
- Versão e data
- Pinout labels nos headers
- Indicação de polaridade (USB-C, caps eletrolíticos)

### Fiducials

Se usar SMT assembly, adicionar 3 fiducials no top layer (marcas de referência pra pick-and-place machine). EasyEDA tem footprint pronto.

---

## Checklist Final

- [ ] Esquemático revisado e ERC limpo
- [ ] Layout PCB completo
- [ ] DRC limpo (0 erros)
- [ ] Zona de exclusão da antena respeitada
- [ ] Ground plane sólido
- [ ] Gerber exportado e verificado no viewer
- [ ] BOM + Pick & Place exportados (se SMT assembly)
- [ ] Encomenda enviada (JLCPCB ou PCBWay)
- [ ] PCBs recebidas e inspecionadas visualmente
- [ ] Componentes soldados
- [ ] Teste de continuidade (sem shorts)
- [ ] ESP32 flashado e bootando
- [ ] Mic, speaker, LEDs funcionando
- [ ] Fit no case validado
