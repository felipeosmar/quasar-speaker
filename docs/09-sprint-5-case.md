# Sprint 5 — Case e Acabamento

**Objetivo:** Projetar e imprimir um case 3D compacto estilo Echo Dot, migrar da protoboard pra montagem definitiva.

**Duração estimada:** 3-5 dias (design + impressão + montagem)

## Design do Case

### Inspiração

- Amazon Echo Dot (cilindro achatado, ~100mm diâmetro, ~43mm altura)
- Google Nest Mini (disco, tecido, LEDs no topo)
- HomePod Mini (esfera pequena)

### Requisitos

- Abertura pro speaker (parte inferior ou frontal)
- Furos pro microfone (topo)
- Slot USB-C (alimentação)
- LEDs visíveis (anel no topo)
- Ventilação passiva
- Fácil abertura pra manutenção
- Diâmetro: ~80-100mm
- Altura: ~40-60mm

### Layout Interno

```
        ┌─── LED Ring (topo, visível)
        │ ┌─ Microfone INMP441 (topo, furos)
        ▼ ▼
   ╔═══════════════╗
   ║  LED  ●●●●●  ║ ← Topo (removível)
   ║  MIC ○       ║
   ╠═══════════════╣
   ║  ESP32-S3     ║ ← Meio
   ║  MAX98357A    ║
   ║  Fiação       ║
   ╠═══════════════╣
   ║  Speaker )))  ║ ← Base (saída de som)
   ║  USB-C ═══   ║ ← Slot traseiro
   ╚═══════════════╝
```

### Dimensões Estimadas

| Componente | Espaço necessário |
|---|---|
| ESP32-S3 DevKitC | 70 x 25 x 10mm |
| MAX98357A | 25 x 25 x 5mm |
| INMP441 | 15 x 15 x 5mm |
| Speaker 40mm | Ø40 x 15mm |
| LED Ring 8 LEDs | Ø32 x 5mm |
| **Case total** | **~Ø90 x 50mm** |

## Ferramentas de Design

- **FreeCAD** ou **Fusion 360** (free pra hobby)
- **OpenSCAD** (paramétrico, se preferir código)
- **Thingiverse/Printables** — buscar cases de referência pra ESP32 speakers

## Impressão 3D

### Material

- **PLA:** Mais fácil, barato, boa aparência
- **PETG:** Mais resistente ao calor (ESP32 pode aquecer)
- Cor sugerida: preto fosco ou branco

### Configurações

```
Layer height: 0.2mm
Infill: 20-30%
Walls: 3
Top/Bottom: 4 layers
Support: onde necessário (speaker cavity)
Tempo estimado: ~3-4h por case
Filamento: ~30-50g por case
```

### Se não tem impressora 3D

- **Serviço local:** Mercado Livre, OLX (buscar "impressão 3D" na sua cidade)
- **Online:** PCBWay, JLCPCB (mínimo 5 unidades)
- **Custo:** ~R$15-30 por case

## Montagem Definitiva

### Migrar de Protoboard pra Permanente

Opções:
1. **Solda direta** — fios soldados nos headers do ESP32
2. **Perfboard** — placa perfurada com solda
3. **PCB custom** — JLCPCB (mínimo 5, ~R$20 total) — ideal pra produção de 5 unidades

### PCB Custom (Recomendado pra 5 unidades)

Design em **KiCad** (free):
- Footprints: ESP32-S3 module, INMP441, MAX98357A, USB-C, WS2812B
- 2 layers, 100x100mm (preço mínimo JLCPCB)
- Custo: ~R$5/placa + ~R$50 frete = ~R$75 total pra 5 placas

## Validação

- [ ] Case modelado em 3D
- [ ] Componentes cabem no case
- [ ] Speaker alinhado com abertura de som
- [ ] Mic no topo com furos adequados
- [ ] LEDs visíveis pelo case
- [ ] USB-C acessível
- [ ] Case impresso e montado
- [ ] Todos os componentes fixos (sem balanço)
- [ ] Áudio do speaker não fica abafado
- [ ] Mic captura bem através dos furos
