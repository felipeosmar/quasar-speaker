# Sprint 3 — Conversation Agent (OpenClaw/Quasar)

**Objetivo:** Substituir o Assist nativo por OpenClaw (Quasar/Claude) como conversation agent do HA Voice Pipeline, permitindo comandos em linguagem natural completa.

**Duração estimada:** 2-3 dias

## Conceito

O Home Assistant suporta **conversation agents** plugáveis. A integração **OpenAI Conversation** aceita qualquer API OpenAI-compatible. O OpenClaw pode expor um endpoint nesse formato, ou podemos criar um proxy leve.

## Abordagem: Proxy Local OpenClaw → OpenAI-compatible

Criar um pequeno servidor que:
1. Recebe requests no formato OpenAI Chat Completions
2. Encaminha pro OpenClaw (via API ou sessions)
3. Retorna resposta no formato OpenAI

### Opção A: OpenClaw como OpenAI-compatible API

Se o OpenClaw já expõe (ou vier a expor) um endpoint `/v1/chat/completions`, basta apontar a integração OpenAI Conversation direto pra ele.

```
HA OpenAI Conversation → http://localhost:PORTA/v1/chat/completions
```

### Opção B: Proxy Python (fallback)

Se precisarmos adaptar o formato:

```python
"""
proxy_openai.py — Proxy OpenClaw → OpenAI-compatible API
Roda no DeskFelipeDell, escutando em :5001
"""
from aiohttp import web, ClientSession
import json

OPENCLAW_URL = "http://localhost:OPENCLAW_PORT"  # ajustar

async def chat_completions(request):
    data = await request.json()
    messages = data.get("messages", [])
    
    # Extrair último user message
    user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_msg = msg["content"]
            break
    
    # Enviar pro OpenClaw via sessions API
    async with ClientSession() as session:
        async with session.post(
            f"{OPENCLAW_URL}/api/sessions/send",
            json={"message": user_msg},
            headers={"Authorization": "Bearer TOKEN"}
        ) as resp:
            result = await resp.json()
    
    # Formatar como OpenAI response
    return web.json_response({
        "id": "quasar-voice",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result.get("response", "Desculpe, não entendi.")
            },
            "finish_reason": "stop"
        }]
    })

app = web.Application()
app.router.add_post("/v1/chat/completions", chat_completions)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5001)
```

### Opção C: Custom Conversation Agent (HA Integration)

Criar uma integração HA custom que chama o OpenClaw diretamente:

```
ha-config/custom_components/openclaw_conversation/
├── __init__.py
├── manifest.json
├── config_flow.py
└── conversation.py
```

Mais complexa, mas a integração mais limpa.

## Configuração no HA

### Usando integração OpenAI Conversation

1. **Settings → Devices & Services → Add Integration → OpenAI**
2. API Key: qualquer valor (o proxy não valida, ou usar token real)
3. **Configure:**
   - Base URL: `http://localhost:5001/v1` (proxy local)
   - Model: `claude-opus-4-20250725` (informativo, o proxy decide)
   - Instructions (system prompt):

```
Você é o Quasar, assistente de voz da família de Aviz.
Você controla a casa via Home Assistant.

Ao receber um comando de voz:
1. Interprete a intenção do usuário
2. Se for controle de dispositivo, chame o serviço HA apropriado
3. Responda de forma breve e natural (será falado em voz alta)

Dispositivos disponíveis:
{%- for entity in exposed_entities %}
- {{ entity.name }} ({{ entity.entity_id }}): {{ entity.state }}
{%- endfor %}

Mantenha respostas curtas (1-2 frases) — serão reproduzidas por TTS.
Responda sempre em português brasileiro.
```

4. **Control Home Assistant:** ✅ Habilitado
5. Expor entidades relevantes em **Settings → Voice Assistants → Expose**

### Atualizar Voice Pipeline

1. **Settings → Voice Assistants → Quasar**
2. Trocar **Conversation Agent** de "Home Assistant" para "OpenClaw/OpenAI"

## System Prompt — Otimizado pra Voz

O prompt é crucial porque respostas longas = TTS lento + experiência ruim.

Princípios:
- **Brevidade:** Máximo 1-2 frases por resposta
- **Confirmação:** "Pronto, luz da sala ligada" (não "Eu liguei a luz da sala para você")
- **Natural:** Como um humano responderia por voz
- **Contexto do cômodo:** Saber de qual QuasarBox veio o comando

### Exemplos de Interação

| Comando de voz | Resposta esperada | Ação HA |
|---|---|---|
| "Acende a luz" | "Pronto." | `light.turn_on` (luz do cômodo) |
| "Tá quente aqui" | "Ligando o ar a 23 graus." | `climate.set_temperature` |
| "Que horas são?" | "São três e quinze." | Nenhuma |
| "Liga a TV na Netflix" | "TV ligando na Netflix." | TV Controller API |
| "Modo filme" | "Modo filme ativado." | Script: TV on, luzes dim |
| "Bom dia" | "Bom dia! Hoje vai fazer 28 graus." | Nenhuma (info) |

## Context: Identificando o Cômodo

Cada QuasarBox tem um `device_id` no HA. O conversation agent pode usar isso:

```
O comando veio do dispositivo: {{ satellite.device_name }}
Cômodo: {{ satellite.area }}
```

Assim "acende a luz" no quarto acende a luz do quarto, não da sala.

## Teste

### Via HA UI
1. Settings → Voice Assistants → Quasar
2. Clicar mic → falar comando
3. Verificar resposta

### Via API
```bash
curl -X POST -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "pt-BR",
    "text": "acende a luz da sala",
    "pipeline": "quasar"
  }' \
  http://localhost:8123/api/conversation/process | jq
```

### Via QuasarBox
1. "Hey Jarvis" (wake word)
2. "Acende a luz da sala"
3. Verificar: luz acende + speaker fala confirmação

## Validação

- [ ] Proxy/integration OpenClaw rodando
- [ ] HA conversation agent configurado
- [ ] Pipeline "Quasar" usando OpenClaw como agent
- [ ] Comandos de controle funcionam (ligar/desligar dispositivos)
- [ ] Respostas são breves e naturais
- [ ] Context do cômodo funciona
- [ ] Latência total aceitável (< 7s)
- [ ] Sem erros em 10 comandos consecutivos
