# Sprint 4 — Wake Word

**Objetivo:** Ter uma wake word funcional no QuasarBox e, opcionalmente, treinar uma wake word custom "Ei Quasar".

**Duração estimada:** Fase 1: já pronto (built-in). Fase 2: 3-5 dias (treinamento custom).

---

## Fase 1: Wake Word Provisória (Built-in) ⭐ COMEÇAR AQUI

O componente `micro_wake_word` do ESPHome já inclui modelos pré-treinados que rodam diretamente no ESP32-S3 sem precisar de nada no servidor. **Use uma dessas pra começar:**

### Wake words disponíveis (micro_wake_word)

| Wake Word | Modelo | Qualidade | Nota |
|-----------|--------|-----------|------|
| "Hey Jarvis" | `hey_jarvis` | ✅ Boa | Recomendada pra começar |
| "OK Nabu" | `ok_nabu` | ✅ Boa | Wake word oficial do HA |
| "Alexa" | `alexa` | ✅ Boa | Familiar |
| "Hey Mycroft" | `hey_mycroft` | Razoável | |

### Configuração no ESPHome (firmware)

```yaml
micro_wake_word:
  models:
    - model: hey_jarvis  # ou ok_nabu, alexa
  on_wake_word_detected:
    - voice_assistant.start:
```

Pronto. Sem treinamento, sem coleta de amostras, sem servidor. O modelo roda no ESP32-S3 usando ~1-2MB de PSRAM.

### Configuração no HA

1. **Settings → Voice Assistants → Quasar**
2. Wake Word: pode deixar "None" (pois a detecção é no ESP32, não no servidor)
3. Ou configurar openWakeWord no servidor como **backup/confirmação** (dupla detecção)

### Dupla Detecção (Recomendada)

Combinar as duas camadas:
1. **micro_wake_word no ESP32** com "Hey Jarvis" = gatilho rápido (local, ~100ms)
2. **openWakeWord no servidor** como confirmação = reduz falsos positivos

O ESPHome suporta isso nativamente: o ESP32 detecta a wake word e inicia o stream; o servidor pode confirmar antes de processar o STT.

**Use a wake word provisória até que tudo mais esteja funcionando (Sprints 0-3, 5-6). Só depois invista tempo no treinamento custom.**

---

## Fase 2: Wake Word Custom "Ei Quasar" (Depois de Tudo Funcionar)

Quando o pipeline inteiro estiver estável, treinar uma wake word personalizada.

### Abordagem: openWakeWord Custom Training

O [openWakeWord](https://github.com/dscripka/openWakeWord) permite treinar wake words customizadas com relativamente poucas amostras (~50-200 gravações).

### Passo 1: Coletar Amostras de Áudio

Gravar "Ei Quasar" várias vezes, por diferentes pessoas da família:

```bash
# Criar diretório de amostras
mkdir -p /home/felipe/work/quasar-speaker/wake-word/positive
mkdir -p /home/felipe/work/quasar-speaker/wake-word/negative

# Gravar amostras (16kHz, 16-bit, mono, ~2 segundos)
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

1. Copiar modelo pra volume Docker do openWakeWord (ou montar diretório):

```yaml
# Adicionar ao docker-compose.yml
wyoming-openwakeword:
  volumes:
    - ./wake-word/models:/custom-models
  command: >
    --uri tcp://0.0.0.0:10400
    --custom-model-dir /custom-models
    --preload-model ei_quasar
```

2. Reiniciar: `docker compose restart wyoming-openwakeword`
3. Atualizar Voice Pipeline no HA: Wake Word → ei_quasar

### Alternativa Futura: micro-WakeNet Custom (no ESP32)

A Espressif permite treinar modelos custom pra rodar diretamente no ESP32-S3 via [ESP-SR](https://github.com/espressif/esp-sr). Vantagem: latência zero (tudo local). Desvantagem: processo de treinamento mais complexo. Considerar apenas se a detecção via servidor introduzir latência perceptível.

## Dicas de Treinamento

- **Variedade:** Gravar em diferentes cômodos (acústica diferente)
- **Distância:** Gravar de 0.5m, 1m, 2m, 3m
- **Ruído:** Gravar com TV ligada, conversa ao fundo
- **Velocidade:** Normal, rápido, lento
- **Mínimo:** 50 amostras positivas pra resultado razoável, 200+ pra bom

## Validação

### Fase 1 (Provisória)
- [ ] micro_wake_word funcionando no ESP32 com "Hey Jarvis"
- [ ] Pipeline inicia corretamente após detecção
- [ ] False positives aceitáveis (< 3/hora com TV ligada)

### Fase 2 (Custom)
- [ ] ≥100 amostras positivas coletadas (multi-speaker)
- [ ] Amostras negativas coletadas
- [ ] Modelo treinado com accuracy ≥ 95%
- [ ] False positive rate < 1%
- [ ] Funciona a 2m de distância
- [ ] Funciona com TV ligada ao fundo
- [ ] Deploy no Wyoming openWakeWord (Docker)
- [ ] Pipeline HA atualizado pra "ei_quasar"
- [ ] Teste com todos os membros da família
