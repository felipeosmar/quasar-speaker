# Sprint 6 — Multi-Room (5 Cômodos)

**Objetivo:** Replicar o QuasarBox para todos os cômodos da casa, com identificação de área e comportamento contextual.

**Duração estimada:** 2-3 dias (montagem) + compra de componentes

## Cômodos Planejados

| # | Cômodo | Device Name | Prioridade |
|---|--------|-------------|------------|
| 1 | Sala | `quasarbox-sala` | ⭐ Protótipo (Sprint 1-5) |
| 2 | Quarto Casal | `quasarbox-quarto` | Alta |
| 3 | Quarto Miguel | `quasarbox-miguel` | Alta |
| 4 | Cozinha | `quasarbox-cozinha` | Média |
| 5 | Escritório | `quasarbox-escritorio` | Média |

## Firmware por Cômodo

Cada QuasarBox usa o mesmo YAML base, só mudando `substitutions`:

```yaml
# firmware/quasarbox-quarto.yaml
substitutions:
  device_name: quasarbox-quarto
  friendly_name: "QuasarBox Quarto"

# Inclui a configuração base
packages:
  base: !include quasarbox-base.yaml
```

### Base compartilhada

Extrair o YAML comum pra `firmware/quasarbox-base.yaml`:
- I2S config, mic, speaker, LED, voice_assistant
- Cada device só define nome e Wi-Fi

## Áreas no Home Assistant

Configurar áreas no HA pra cada cômodo:

1. **Settings → Areas & Zones**
2. Criar: Sala, Quarto Casal, Quarto Miguel, Cozinha, Escritório
3. Atribuir cada QuasarBox à sua área
4. Atribuir dispositivos (luzes, sensores) às áreas

Isso permite que o conversation agent saiba: "acende a luz" → acende a do cômodo onde o QuasarBox está.

## Contexto por Cômodo

O OpenClaw recebe o `device_id` e `area` no prompt:

```
Comando recebido do QuasarBox no cômodo: {{ area.name }}

Quando o usuário diz "acende a luz" sem especificar, 
assuma que é a luz do cômodo {{ area.name }}.
```

### Exemplos de Contexto

| Comando | Cômodo | Ação |
|---------|--------|------|
| "Acende a luz" | Sala | `light.sala turn_on` |
| "Acende a luz" | Quarto | `light.quarto turn_on` |
| "Tá frio" | Quarto | `climate.quarto set_temperature 25` |
| "Liga a TV" | Sala | TV Controller API |
| "Liga a TV" | Quarto | Erro: "Não tem TV no quarto" |

## Compras — Lote de 4 unidades adicionais

| Item | Qtd | Unitário | Total |
|------|-----|----------|-------|
| ESP32-S3-DevKitC-1 N16R8 | 4 | R$45 | R$180 |
| INMP441 | 4 | R$15 | R$60 |
| MAX98357A | 4 | R$18 | R$72 |
| Speaker 3W 4Ω 40mm | 4 | R$10 | R$40 |
| WS2812B ring 8 LEDs | 4 | R$5 | R$20 |
| Fontes USB-C 5V 2A | 4 | R$20 | R$80 |
| Fios/conectores | 4 | R$10 | R$40 |
| Cases 3D | 4 | R$15 | R$60 |
| **Total (4 adicionais)** | | | **~R$552** |

**Total projeto (5 unidades):** ~R$119 (protótipo) + ~R$552 (lote) + ~R$60 (filamento) = **~R$731**

## Flash em Lote

```bash
# Compilar todos
for room in quarto miguel cozinha escritorio; do
  esphome compile firmware/quasarbox-$room.yaml
done

# Flash inicial via USB (um por vez)
esphome upload firmware/quasarbox-quarto.yaml --device /dev/ttyUSB0

# Depois, OTA:
esphome upload firmware/quasarbox-quarto.yaml
```

## Multi-Room Audio (Futuro)

Possibilidade de usar os speakers pra:
- **Broadcast:** "Jantar tá pronto!" → fala em todos os QuasarBox
- **Intercom:** Falar de um cômodo pra outro
- **Música sync:** Reproduzir música em múltiplos cômodos (Snapcast)

Isso é extensão futura, não escopo do Sprint 6.

## Validação

- [ ] 5 QuasarBox montados e funcionando
- [ ] Cada um atribuído à sua área no HA
- [ ] Contexto de cômodo funciona (luz correta acende)
- [ ] Todos respondem à wake word
- [ ] OTA update funciona em todos
- [ ] Latência aceitável com 5 devices simultâneos
- [ ] Nenhum QuasarBox interfere com outro (wake word dupla)
