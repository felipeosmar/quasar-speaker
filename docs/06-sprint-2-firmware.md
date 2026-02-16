# Sprint 2 — Firmware ESPHome

**Objetivo:** Flashar ESPHome no ESP32-S3 com voice_assistant, conectar ao HA Voice Pipeline e ter o primeiro comando de voz funcionando end-to-end.

**Duração estimada:** 1-2 dias

## Pré-requisitos

- [x] Sprint 0 completo (servidor com Wyoming + HA Pipeline)
- [x] Sprint 1 completo (hardware montado e testado)
- [ ] ESPHome instalado (`pip install esphome` ou Docker)

## Firmware YAML

Arquivo: `firmware/quasarbox-sala.yaml`

```yaml
substitutions:
  device_name: quasarbox-sala
  friendly_name: "QuasarBox Sala"

esphome:
  name: ${device_name}
  friendly_name: ${friendly_name}
  platformio_options:
    board_build.flash_mode: dio
    board_build.arduino.memory_type: qio_opi

esp32:
  board: esp32-s3-devkitc-1
  variant: esp32s3
  framework:
    type: esp-idf
    version: recommended

# --- Logging ---
logger:
  level: DEBUG

# --- Wi-Fi ---
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  power_save_mode: none  # Melhor latência pra streaming áudio

  ap:
    ssid: "${device_name}"
    password: "quasar2026"

captive_portal:

# --- API (conexão com HA) ---
api:
  encryption:
    key: !secret api_key

ota:
  - platform: esphome
    password: !secret ota_password

# --- PSRAM ---
psram:
  mode: octal
  speed: 80MHz

# --- I2S Áudio ---
i2s_audio:
  - id: i2s_mic
    i2s_lrclk_pin: GPIO5   # WS
    i2s_bclk_pin: GPIO4    # SCK

  - id: i2s_spk
    i2s_lrclk_pin: GPIO17  # LRC
    i2s_bclk_pin: GPIO16   # BCLK

# --- Microfone ---
microphone:
  - platform: i2s_audio
    id: mic
    i2s_audio_id: i2s_mic
    adc_type: external
    pdm: false
    channel: left
    bits_per_sample: 32bit
    i2s_din_pin: GPIO6

# --- Speaker ---
speaker:
  - platform: i2s_audio
    id: spk
    i2s_audio_id: i2s_spk
    dac_type: external
    i2s_dout_pin: GPIO15
    mode: mono

# --- LED Ring WS2812B ---
light:
  - platform: neopixelbus
    id: led_ring
    type: GRB
    variant: WS2812
    pin: GPIO48
    num_leds: 8
    name: "LED Ring"
    effects:
      - pulse:
          name: "Pulse Blue"
          color_mode: RGB
          min_brightness: 20%
          max_brightness: 100%
          transition_length: 500ms
          update_interval: 500ms
      - addressable_rainbow:
          name: "Rainbow"

# --- Amplificador Enable ---
switch:
  - platform: gpio
    id: amp_enable
    pin: GPIO18
    name: "Amplifier"
    restore_mode: ALWAYS_ON

# --- Wake Word (micro_wake_word no ESP32) ---
micro_wake_word:
  models:
    - model: hey_jarvis  # Temporário até treinar "ei_quasar"
  on_wake_word_detected:
    - light.turn_on:
        id: led_ring
        brightness: 100%
        red: 100%
        green: 100%
        blue: 100%
        effect: none

# --- Voice Assistant ---
voice_assistant:
  microphone: mic
  speaker: spk
  use_wake_word: true
  micro_wake_word: micro_ww
  noise_suppression_level: 2
  auto_gain: 31dBFS
  volume_multiplier: 2.0

  on_listening:
    - light.turn_on:
        id: led_ring
        brightness: 80%
        red: 0%
        green: 0%
        blue: 100%
        effect: "Pulse Blue"

  on_stt_end:
    - logger.log:
        format: "STT result: %s"
        args: ['x.c_str()']
    - light.turn_on:
        id: led_ring
        brightness: 80%
        red: 100%
        green: 80%
        blue: 0%
        effect: none

  on_tts_start:
    - light.turn_on:
        id: led_ring
        brightness: 80%
        red: 0%
        green: 100%
        blue: 0%
        effect: none

  on_end:
    - light.turn_off:
        id: led_ring

  on_error:
    - light.turn_on:
        id: led_ring
        brightness: 100%
        red: 100%
        green: 0%
        blue: 0%
        effect: none
    - delay: 2s
    - light.turn_off:
        id: led_ring
```

## Secrets

Arquivo: `firmware/secrets.yaml`

```yaml
wifi_ssid: "SuaRedeWiFi"
wifi_password: "SuaSenhaWiFi"
api_key: "GERAR_COM_esphome_generate_key"
ota_password: "quasar2026"
```

Gerar API key:
```bash
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

## Flash Inicial (USB)

```bash
cd /home/felipe/work/quasar-speaker

# Compilar
esphome compile firmware/quasarbox-sala.yaml

# Flash via USB (primeira vez)
esphome upload firmware/quasarbox-sala.yaml --device /dev/ttyUSB0

# Logs
esphome logs firmware/quasarbox-sala.yaml --device /dev/ttyUSB0
```

## Adotar no Home Assistant

1. Após o flash, o ESP32 conecta ao Wi-Fi
2. No HA: **Settings → Devices & Services** → deve aparecer como descoberto (ESPHome)
3. Clicar **Configure** → inserir API encryption key
4. Device "QuasarBox Sala" aparece
5. Ir em **Settings → Voice Assistants → Quasar**
6. Em **Assist Satellites** → adicionar o QuasarBox

## Teste End-to-End

1. Dizer "Hey Jarvis" (wake word temporária)
2. LED fica azul (ouvindo)
3. Dizer "que horas são"
4. LED fica amarelo (processando)
5. LED fica verde (respondendo)
6. Speaker reproduz a resposta
7. LED apaga

## Updates OTA (Over-the-Air)

Após o primeiro flash via USB, todas as atualizações são wireless:

```bash
esphome upload firmware/quasarbox-sala.yaml
# Automaticamente encontra o device via mDNS
```

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Não conecta ao Wi-Fi | Verificar SSID/senha em secrets.yaml; 2.4GHz only |
| HA não descobre | Verificar se estão na mesma rede; mDNS habilitado |
| Áudio cortado | `power_save_mode: none` no Wi-Fi; verificar PSRAM |
| Wake word não detecta | Falar mais perto; verificar que mic funciona |
| Speaker muito baixo | `volume_multiplier: 3.0`; GAIN do MAX98357 |
| Boot loop | PSRAM config incorreta; verificar `memory_type` |

## Validação

- [ ] ESP32-S3 flashado com ESPHome
- [ ] Conectado ao Wi-Fi e visível no HA
- [ ] Voice Pipeline atribuído ao satellite
- [ ] Wake word detectada
- [ ] STT transcreve corretamente em pt-BR
- [ ] Conversation agent responde
- [ ] TTS reproduz pelo speaker
- [ ] LEDs indicam estados corretamente
- [ ] OTA update funciona
