# Sprint 7 — Integração HA ↔ Dispositivos Smart

**Objetivo:** Ter dispositivos smart reais no Home Assistant para o QuasarBox controlar por voz. Sem dispositivos, o speaker não tem muito o que fazer.

**Duração estimada:** 1-2 dias (configuração) + tempo de compra/entrega

**Prioridade:** Alta — pode ser feito em paralelo com qualquer outro sprint.

---

## Por Que Este Sprint É Importante

O QuasarBox é um **controlador por voz**. Se não houver nada pra controlar, ele vira um timer glorificado. O mínimo viável:

- "Acende a luz" → precisa de lâmpada smart
- "Liga o ar" → precisa de IR blaster ou ar smart
- "Quanto tá a temperatura?" → precisa de sensor
- "Liga a TV" → ✅ já temos (LG TV Controller)

## O Que Já Temos

| Dispositivo | Integração HA | Status |
|-------------|--------------|--------|
| LG TV 65" (sala) | LG TV Controller (custom API :8888) | ✅ Funcionando |
| Home Assistant | Docker no DeskFelipeDell | ✅ Funcionando |

## Sugestões de Dispositivos Baratos

### Tier 1: Essenciais (começar por aqui)

| Dispositivo | Modelo Sugerido | Preço | Integração HA |
|-------------|----------------|-------|---------------|
| **Smart Plug WiFi** (2x) | Sonoff S26 / Tuya genérica | R$25-40 cada | Tuya / Sonoff |
| **Lâmpada WiFi** (2x) | Positivo Smart / Tuya E27 | R$30-50 cada | Tuya |
| **Sensor Temp/Umidade** | Sonoff SNZB-02D (Zigbee) ou Tuya WiFi | R$40-60 | Tuya / ZHA |

**Custo Tier 1:** ~R$150-280

### Tier 2: Nice to Have

| Dispositivo | Modelo Sugerido | Preço | Integração HA |
|-------------|----------------|-------|---------------|
| **IR Blaster** | Broadlink RM4 Mini | R$80-120 | Broadlink |
| **Fita LED WiFi** | Tuya / Govee WiFi | R$40-70 | Tuya |
| **Sensor de porta** | Sonoff SNZB-04 (Zigbee) | R$35-50 | ZHA |

### Tier 3: Futuro

| Dispositivo | Modelo Sugerido | Preço | Integração HA |
|-------------|----------------|-------|---------------|
| **Fechadura smart** | vários | R$300+ | Tuya |
| **Câmera WiFi** | Tapo C200 | R$150 | ONVIF |
| **Aspirador robô** | Qualquer com Tuya/Valetudo | R$500+ | Tuya / Valetudo |

### Notas sobre Zigbee vs WiFi

| | WiFi | Zigbee |
|---|---|---|
| **Precisa de hub?** | Não | Sim (dongle USB ~R$50-80) |
| **Setup** | Mais fácil | Mais estável |
| **Alcance** | Bom | Mesh (melhora com mais devices) |
| **Recomendação** | Começar com WiFi | Migrar pra Zigbee depois |

Se for WiFi/Tuya: integração [Tuya](https://www.home-assistant.io/integrations/tuya/) ou [LocalTuya](https://github.com/rospogriern/localtuya) (HACS, controle local sem cloud).

Se for Zigbee: comprar dongle USB (ex: Sonoff ZBDongle-P ~R$70) e usar integração [ZHA](https://www.home-assistant.io/integrations/zha/).

---

## Configuração no Home Assistant

### 1. Adicionar Integrações

```
Settings → Devices & Services → Add Integration
```

- **Tuya:** Criar conta Tuya IoT, vincular devices, adicionar integração
- **Sonoff:** Via eWeLink ou Sonoff LAN (HACS)
- **Broadlink:** Descoberta automática na rede local
- **LocalTuya (HACS):** Controle local sem cloud (recomendado pra latência)

### 2. Configurar Áreas

```
Settings → Areas & Zones
```

Criar áreas que correspondem aos cômodos dos QuasarBox:

| Área | Dispositivos Sugeridos |
|------|----------------------|
| Sala | TV LG, lâmpada, smart plug (abajur), sensor temp |
| Quarto Casal | Lâmpada, smart plug (ventilador), sensor temp |
| Quarto Miguel | Lâmpada, smart plug |
| Cozinha | Smart plug (cafeteira) |
| Escritório | Smart plug, lâmpada |

**Atribuir cada dispositivo à sua área.** Isso permite que o QuasarBox do quarto controle "a luz" sem especificar qual — o HA sabe que é a luz daquela área.

### 3. Expor Entidades pro Voice Assistant

```
Settings → Voice Assistants → Expose
```

Marcar quais entidades o conversation agent pode ver/controlar. Expor:
- Todas as luzes
- Todos os switches (smart plugs)
- Sensores de temperatura/umidade (pra consulta)
- Media players
- Climate (se tiver)

### 4. Automações Básicas

Criar automações que o QuasarBox pode acionar por voz (via scripts/scenes):

```yaml
# Exemplo: Scene "Modo Filme"
scene:
  - name: "Modo Filme"
    entities:
      light.sala:
        state: "on"
        brightness: 30
      switch.abajur_sala:
        state: "off"
    # + chamar TV Controller API via script

# Exemplo: Script "Boa Noite"
script:
  boa_noite:
    alias: "Boa Noite"
    sequence:
      - service: light.turn_off
        target:
          area_id: sala
      - service: light.turn_off
        target:
          area_id: cozinha
      - service: switch.turn_off
        target:
          entity_id: switch.tv_sala  # ou TV Controller
```

### 5. Testar via HA UI

Antes de testar por voz, verificar que os dispositivos funcionam pela UI do HA:

1. **Settings → Devices** — todos os devices aparecem?
2. **Overview dashboard** — clicar pra ligar/desligar
3. **Developer Tools → Services** — testar `light.turn_on`, `switch.toggle`, etc.

---

## Integração com LG TV Controller

O LG TV Controller já está rodando em `:8888`. Para integrá-lo ao HA como entidade controlável:

### Opção A: RESTful Switch/Command

```yaml
# configuration.yaml
rest_command:
  tv_power_on:
    url: "http://localhost:8888/api/power"
    method: POST
    content_type: "application/json"
    payload: '{"action":"on"}'
  
  tv_power_off:
    url: "http://localhost:8888/api/power"
    method: POST
    content_type: "application/json"
    payload: '{"action":"off"}'
  
  tv_volume_set:
    url: "http://localhost:8888/api/volume"
    method: POST
    content_type: "application/json"
    payload: '{"action":"set","level":{{ level }}}'
  
  tv_launch_app:
    url: "http://localhost:8888/api/apps"
    method: POST
    content_type: "application/json"
    payload: '{"action":"launch","app_id":"{{ app_id }}"}'
  
  tv_preset:
    url: "http://localhost:8888/api/presets"
    method: POST
    content_type: "application/json"
    payload: '{"action":"execute","id":"{{ preset }}"}'
```

### Opção B: Se usar Opção B do Sprint 3 (Proxy OpenClaw)

O Quasar já sabe controlar a TV diretamente — não precisa de integração HA extra. O comando de voz vai pro OpenClaw que chama a API da TV.

---

## Checklist

- [ ] ≥1 lâmpada smart configurada no HA
- [ ] ≥1 smart plug configurada no HA
- [ ] Áreas criadas (pelo menos Sala e Quarto)
- [ ] Dispositivos atribuídos às áreas corretas
- [ ] Entidades expostas pro Voice Assistant
- [ ] LG TV integrada ao HA (RESTful ou via OpenClaw)
- [ ] Teste: ligar/desligar luz pela UI do HA
- [ ] Teste: ligar/desligar plug pela UI do HA
- [ ] ≥1 automação/scene criada ("Modo Filme" ou "Boa Noite")
- [ ] Teste por voz (se pipeline já estiver funcionando)
