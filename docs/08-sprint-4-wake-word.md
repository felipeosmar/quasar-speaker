# Sprint 4 — Wake Word Custom ("Ei Quasar")

**Objetivo:** Treinar um modelo de wake word customizado que detecte "Ei Quasar" e substituir o "Hey Jarvis" temporário.

**Duração estimada:** 3-5 dias (inclui coleta de amostras)

## Abordagem

Usar **openWakeWord** pra treinar um modelo custom. O openWakeWord suporta treinamento de wake words customizadas com relativamente poucas amostras (~50-200 gravações).

## Opção A: openWakeWord Custom Training

### Passo 1: Coletar Amostras de Áudio

Gravar "Ei Quasar" várias vezes, por diferentes pessoas da família:

```bash
# Criar diretório de amostras
mkdir -p /home/felipe/work/quasar-speaker/wake-word/positive
mkdir -p /home/felipe/work/quasar-speaker/wake-word/negative

# Gravar amostras (usar arecord ou script Python)
# Cada arquivo: 16kHz, 16-bit, mono, ~2 segundos
for i in $(seq 1 50); do
  echo "Diga 'Ei Quasar' (amostra $i/50)..."
  arecord -f S16_LE -r 16000 -c 1 -d 2 \
    wake-word/positive/felipe_$i.wav
  sleep 1
done
```

**Meta de amostras:**
- Felipe: 50 gravações
- Tailine: 30 gravações
- Miguel: 20 gravações (se aplicável)
- Variações: tom normal, sussurro, alto, longe, perto

### Passo 2: Amostras Negativas

Gravar áudio ambiente e frases que NÃO são a wake word:

```bash
# Áudio ambiente (TV, música, conversa)
arecord -f S16_LE -r 16000 -c 1 -d 60 wake-word/negative/ambient_1.wav

# Frases similares que NÃO devem ativar:
# "E quase", "ei pessoal", "a casa", etc.
```

### Passo 3: Treinar Modelo

```bash
pip install openwakeword

# Usar o training toolkit do openWakeWord
# https://github.com/dscripka/openWakeWord#training-new-models
python -m openwakeword.train \
  --positive_dir wake-word/positive/ \
  --negative_dir wake-word/negative/ \
  --output_dir wake-word/models/ \
  --model_name ei_quasar
```

### Passo 4: Testar Modelo

```bash
python -m openwakeword.test \
  --model wake-word/models/ei_quasar.tflite \
  --audio_dir wake-word/test/
```

### Passo 5: Deploy

1. Copiar modelo pra diretório do Wyoming openWakeWord
2. Atualizar configuração:

```bash
# Systemd service atualizado
wyoming-openwakeword \
  --uri tcp://0.0.0.0:10400 \
  --custom-model-dir /home/felipe/work/quasar-speaker/wake-word/models/ \
  --preload-model 'ei_quasar'
```

3. Atualizar Voice Pipeline no HA: Wake Word → ei_quasar

## Opção B: micro-WakeNet Custom (no ESP32)

A Espressif permite treinar modelos custom pra rodar diretamente no ESP32-S3:

- Mais rápido (sem rede)
- Mais complexo de treinar
- Requer ferramentas da Espressif (ESP-SR)
- Documentação: https://github.com/espressif/esp-sr

**Recomendação:** Começar com openWakeWord (servidor) → migrar pra micro-WakeNet depois se quiser latência zero.

## Opção C: Dupla Detecção (Recomendada ⭐)

Combinar as duas:
1. **micro_wake_word no ESP32** com modelo genérico ("hey jarvis") = gatilho rápido
2. **openWakeWord no servidor** com "ei_quasar" = confirmação precisa

O ESPHome suporta isso: wake word no ESP32 inicia o stream, e o servidor confirma antes de processar STT.

## Dicas de Treinamento

- **Variedade:** Gravar em diferentes cômodos (acústica diferente)
- **Distância:** Gravar de 0.5m, 1m, 2m, 3m
- **Ruído:** Gravar com TV ligada, conversa ao fundo
- **Velocidade:** Normal, rápido, lento
- **Sotaque:** Cada pessoa da família tem padrão diferente
- **Mínimo:** 50 amostras positivas pra resultado razoável, 200+ pra bom

## Validação

- [ ] ≥100 amostras positivas coletadas (multi-speaker)
- [ ] Amostras negativas coletadas (ambiente + frases similares)
- [ ] Modelo treinado com accuracy ≥ 95%
- [ ] False positive rate < 1% (não ativa sem a wake word)
- [ ] Funciona a 2m de distância
- [ ] Funciona com TV ligada ao fundo
- [ ] Deploy no Wyoming openWakeWord
- [ ] Pipeline HA atualizado pra "ei_quasar"
- [ ] Teste com todos os membros da família
