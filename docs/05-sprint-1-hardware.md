# Sprint 1 — Protótipo Hardware

**Objetivo:** Montar 1 unidade funcional do QuasarBox em protoboard, verificar todas as conexões e confirmar que áudio entra e sai corretamente.

**Duração estimada:** 1-2 dias (após receber componentes)

## Lista de Compras (1 protótipo — opção mais barata)

| Item | Qtd | Preço Est. | Onde |
|------|-----|------------|------|
| ESP32-S3-DevKitC-1 N16R8 | 1 | R$35-45 | AliExpress |
| INMP441 breakout | 1 | R$12-18 | AliExpress |
| MAX98357A breakout | 1 | R$15-20 | AliExpress |
| Speaker 3W 4Ω 40mm | 1 | R$8-12 | AliExpress |
| WS2812B ring 8 LEDs | 1 | R$5 | AliExpress |
| Protoboard 830 pontos | 1 | R$8 | Local |
| Kit jumpers M-M, M-F | 1 | R$8 | Local |
| Cabo USB-C | 1 | R$10 | Local |
| **Total estimado** | | **~R$100-120** | |

**Dica de economia:** Comprar todos os módulos no AliExpress numa tacada (frete combinado). Tempo de entrega: 15-30 dias. Se tiver pressa, Mercado Livre tem tudo mas ~30-50% mais caro.

> **Nota sobre ESP32-S3-BOX-3:** A Espressif vende o BOX-3 (~R$180-250) que já vem com mic, speaker, tela e case. É prático pra testar o pipeline de voz rapidamente, mas **não é recomendado pra este projeto** porque: (1) mais caro pra escalar pra 5 unidades, (2) não permite customização de hardware, (3) queremos aprender o processo completo. Se quiser um pra brincar/testar o pipeline enquanto espera os componentes, é uma opção válida como ferramenta de dev — mas não será o QuasarBox final.

## Montagem Passo a Passo

### Passo 1: Preparar ESP32-S3

1. Soldar headers no DevKitC (se não vier soldado)
2. Encaixar na protoboard
3. Conectar USB-C ao PC pra teste inicial
4. Verificar: LED de power acende

### Passo 2: Conectar Microfone INMP441

```
INMP441     →  ESP32-S3
─────────────────────────
SCK         →  GPIO 4
WS          →  GPIO 5
SD          →  GPIO 6
L/R         →  GND        (canal esquerdo)
VDD         →  3.3V
GND         →  GND
```

**Teste:** Gravar áudio raw e verificar que captura som (firmware de teste).

### Passo 3: Conectar Amplificador MAX98357A + Speaker

```
MAX98357A   →  ESP32-S3
─────────────────────────
BCLK        →  GPIO 16
LRC         →  GPIO 17
DIN         →  GPIO 15
SD (enable) →  GPIO 18     (ou 3.3V pra always-on)
VIN         →  5V (VBUS)
GND         →  GND

Speaker (+) →  MAX98357A (+)
Speaker (-) →  MAX98357A (-)
```

**Teste:** Reproduzir tom/beep pelo speaker.

### Passo 4: Conectar LED Ring WS2812B

```
WS2812B     →  ESP32-S3
─────────────────────────
DIN         →  GPIO 48
VCC         →  5V (VBUS)
GND         →  GND
```

**Teste:** Acender LEDs em cores diferentes.

### Passo 5: Verificação Completa

1. Alimentar via USB-C (fonte 5V/2A, não porta do PC)
2. Falar perto do mic → verificar que o áudio é capturado
3. Reproduzir áudio → verificar que speaker funciona
4. LEDs → verificar animações

## Esquema Elétrico

```
                        USB-C 5V/2A
                            │
                      ┌─────┴─────┐
                      │  ESP32-S3  │
                      │  DevKitC-1 │
                      │            │
          INMP441     │  GPIO 4 ◄──┤ SCK
          (Mic)       │  GPIO 5 ◄──┤ WS
                      │  GPIO 6 ◄──┤ SD
                      │            │
                      │  GPIO 15──►│ DIN    MAX98357A
                      │  GPIO 16──►│ BCLK   (Amp)
                      │  GPIO 17──►│ LRC        │
                      │  GPIO 18──►│ SD_EN      │
                      │            │         Speaker
                      │  GPIO 48──►│ WS2812B    3W
                      │            │
                      │  3.3V ────►│ INMP441 VDD
                      │  5V ──────►│ MAX98357 VIN + LED VCC
                      │  GND ─────►│ GND comum
                      └────────────┘
```

## Problemas Comuns

| Problema | Causa Provável | Solução |
|----------|---------------|---------|
| Mic não captura | L/R não conectado ao GND | Verificar L/R → GND |
| Áudio muito baixo | GAIN do MAX98357A | Conectar GAIN ao VIN (15dB) |
| Speaker com ruído | GND loop | Manter GND curto, estrela |
| LED não acende | Nível lógico 3.3V | WS2812B aceita 3.3V do ESP32-S3 |
| ESP32 reiniciando | Fonte fraca | Usar fonte 5V/2A dedicada (não PC) |
| Wi-Fi instável | Antena obstruída | Manter antena do ESP32 livre |

## Validação

- [ ] ESP32-S3 bootando e conectando ao Wi-Fi
- [ ] Microfone captura áudio legível
- [ ] Speaker reproduz áudio claro
- [ ] LEDs acendem e mudam de cor
- [ ] Alimentação estável com fonte 5V/2A
- [ ] Sem reinicializações espontâneas em 30min de operação
