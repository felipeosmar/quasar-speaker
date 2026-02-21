# Sprint 3 — Conversation Agent (OpenClaw/Quasar)

**Objetivo:** Substituir o Assist nativo por um conversation agent inteligente (Claude) no HA Voice Pipeline, permitindo comandos em linguagem natural completa.

**Duração estimada:** 2-3 dias

---

## Como Funciona o Voice Pipeline do HA (Contexto Essencial)

Antes de escolher a abordagem, é importante entender como o Home Assistant processa voz. O pipeline tem 5 estágios sequenciais:

```
┌─────────┐    ┌─────┐    ┌──────────────┐    ┌─────┐    ┌─────────┐
│ Wake Word│───►│ STT │───►│ Conversation │───►│ TTS │───►│ Speaker │
│ (detect) │    │     │    │    Agent     │    │     │    │ (ESP32) │
└─────────┘    └─────┘    └──────────────┘    └─────┘    └─────────┘
  openWW       Whisper     ← ESTE SPRINT →    Piper       áudio
```

### Estágio por estágio:

1. **Wake Word** — O ESP32 detecta "Hey Jarvis" localmente (micro_wake_word) e começa a transmitir áudio para o HA via ESPHome Native API.

2. **STT (Speech-to-Text)** — O áudio chega ao HA que encaminha via **Wyoming protocol** para o servidor Whisper (container Docker, porta 10300). Whisper transcreve e retorna texto. Ex: `"acende a luz da sala"`

3. **Conversation Agent** — O HA envia o texto transcrito para o conversation agent configurado. O agent interpreta, executa ações se necessário (via HA API), e retorna texto de resposta. Ex: `"Pronto, luz da sala ligada."`

4. **TTS (Text-to-Speech)** — O HA envia o texto de resposta via Wyoming para o Piper (porta 10200), que gera áudio PCM.

5. **Output** — O áudio volta pelo ESPHome Native API para o ESP32, que reproduz no speaker via MAX98357A.

### O que é o Wyoming Protocol?

Wyoming é um protocolo TCP simples criado pelo projeto Rhasspy/HA para comunicação entre componentes de voz. Cada serviço (Whisper, Piper, openWakeWord) roda como um **Wyoming server** independente, escutando numa porta TCP. O HA conecta neles via a integração **Wyoming Protocol**.

É basicamente um protocolo de mensagens binárias (protobuf-like) que transporta:
- Áudio PCM (mic → STT)
- Texto (STT resultado, TTS input)
- Áudio sintetizado (TTS → speaker)
- Eventos (wake word detectado, VAD, etc.)

**Por que importa:** O conversation agent **NÃO** usa Wyoming. Ele é chamado internamente pelo HA via a interface `conversation.AbstractConversationAgent`. A integração com LLMs é via HTTP (formato OpenAI API) ou custom component Python.

### Como o HA chama o Conversation Agent?

O HA tem uma abstração interna chamada `ConversationAgent`. Qualquer integração pode registrar um agent. O pipeline chama o agent assim:

```python
# Internamente no HA (simplificado):
result = await conversation.async_converse(
    hass=hass,
    text="acende a luz da sala",       # texto do STT
    conversation_id="uuid-sessao",      # mantém contexto
    context=Context(user_id=...),
    language="pt-BR",
    agent_id="conversation.openai",     # qual agent usar
)
# result.response.speech["plain"]["speech"] = "Pronto, luz ligada."
```

As integrações que registram agents incluem:
- **Assist nativo** (intent matching rígido, sem LLM)
- **OpenAI Conversation** (integração oficial, chama API OpenAI)
- **Extended OpenAI Conversation** (HACS, mais features)
- **Google Generative AI** (Gemini)
- **Custom components** (qualquer coisa que implemente a interface)

A integração OpenAI Conversation aceita qualquer endpoint que implemente a API `/v1/chat/completions` no formato OpenAI — não precisa ser a OpenAI de verdade. Isso é o que nos permite apontar pra Anthropic, proxy local, etc.

---

## As 3 Opções

### Opção A: Extended OpenAI Conversation (HACS) → Anthropic API

**Como funciona:**
A integração [Extended OpenAI Conversation](https://github.com/jekalmin/extended_openai_conversation) (instalada via HACS) suporta qualquer API OpenAI-compatible. A Anthropic oferece um endpoint compatível com o formato OpenAI em `https://api.anthropic.com/v1/` (via o header `anthropic-version`), mas na prática o mais fácil é usar um proxy de compatibilidade ou a API direta se a integração suportar.

**Setup:**

1. Instalar HACS no HA (se ainda não tiver)
2. No HACS, buscar e instalar "Extended OpenAI Conversation"
3. Reiniciar HA
4. Settings → Devices & Services → Add Integration → Extended OpenAI Conversation
5. Configurar:
   - **API Key:** `sk-ant-api03-...` (chave Anthropic)
   - **Base URL:** `https://api.anthropic.com/v1` (ou proxy)
   - **Model:** `claude-sonnet-4-20250514`

**Nota importante:** A API da Anthropic **não é 100% compatível** com o formato OpenAI. A Extended OpenAI Conversation pode precisar de um proxy de tradução (ex: [LiteLLM](https://github.com/BerriAI/litellm)) entre o HA e a Anthropic:

```bash
# LiteLLM como proxy OpenAI → Anthropic (Docker)
docker run -d \
  --name litellm \
  --restart unless-stopped \
  -p 4000:4000 \
  -e ANTHROPIC_API_KEY=sk-ant-api03-... \
  ghcr.io/berriai/litellm:main-latest \
  --model anthropic/claude-sonnet-4-20250514
```

Aí no HA, apontar pra `http://localhost:4000/v1` como Base URL.

**O que a Extended OpenAI Conversation faz de especial:**
- **Function calling:** Pode chamar serviços do HA (ligar luz, etc.) via tool use
- **Prompt templates:** Usa Jinja2, pode incluir `{{ exposed_entities }}` no prompt
- **Contexto de conversa:** Mantém histórico por `conversation_id`
- **Exposed entities:** O HA injeta a lista de entidades expostas no system prompt

```
┌──────────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│ HA Voice │────►│ Extended │────►│ LiteLLM │────►│Anthropic │
│ Pipeline │     │ OpenAI   │     │ (proxy) │     │   API    │
│          │◄────│ Conv.    │◄────│ :4000   │◄────│  Claude  │
└──────────┘     └──────────┘     └─────────┘     └──────────┘
```

**Prós:**
- ✅ Claude de verdade (Sonnet/Opus) como cérebro
- ✅ Function calling nativo (controla dispositivos HA)
- ✅ Setup relativamente simples
- ✅ Sem código custom — tudo via configuração
- ✅ Comunidade ativa (HACS popular)
- ✅ Prompt com template Jinja2 (entidades expostas, áreas, etc.)

**Contras:**
- ❌ Custo por request (API Anthropic cobra por token)
- ❌ Depende de internet (API cloud)
- ❌ Latência de rede (~500ms-1s extra vs local)
- ❌ Pode precisar de LiteLLM como proxy intermediário
- ❌ Não tem acesso ao contexto do OpenClaw (TV, Órbita, etc.)
- ❌ É "só" um LLM — não tem as ferramentas/integrações que o Quasar já tem

**Custo estimado:**
- Claude Sonnet: ~$3/1M input tokens, ~$15/1M output tokens
- Comando de voz típico: ~500 tokens input (prompt + entities), ~50 tokens output
- ~1000 comandos/mês = ~$1.50-2.00/mês

---

### Opção B: Proxy Python Local (OpenClaw `sessions_send`)

**Como funciona:**
Criar um pequeno servidor Python que implementa a API `/v1/chat/completions` (formato OpenAI) e por baixo dos panos encaminha a mensagem para o OpenClaw via a API `sessions_send`. O OpenClaw (Quasar) já tem contexto completo: acesso ao HA, TV, Órbita, memória, etc.

**Setup:**

1. Criar o proxy Python:

```python
"""
proxy_openclaw.py — Proxy OpenClaw → OpenAI-compatible API
Roda no DeskFelipeDell, escutando em :5001
"""
from aiohttp import web, ClientSession
import json, os

OPENCLAW_GW = os.getenv("OPENCLAW_GW_URL", "http://localhost:3000")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")

async def chat_completions(request):
    data = await request.json()
    messages = data.get("messages", [])
    
    # Extrair último user message (o texto vindo do STT)
    user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_msg = msg["content"]
            break
    
    # Adicionar contexto de que veio do voice pipeline
    voice_prompt = f"[VOICE COMMAND via QuasarBox] {user_msg}"
    
    # Enviar pro OpenClaw via sessions API
    async with ClientSession() as session:
        async with session.post(
            f"{OPENCLAW_GW}/api/sessions/send",
            json={
                "message": voice_prompt,
                "session": "voice"  # sessão dedicada pra voz
            },
            headers={
                "Authorization": f"Bearer {OPENCLAW_TOKEN}",
                "Content-Type": "application/json"
            }
        ) as resp:
            result = await resp.json()
    
    response_text = result.get("response", "Desculpe, não entendi.")
    
    # Formatar como OpenAI Chat Completion response
    return web.json_response({
        "id": "quasar-voice",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    })

# Health check
async def health(request):
    return web.json_response({"status": "ok"})

# Models endpoint (HA pode chamar isso)
async def models(request):
    return web.json_response({
        "data": [{"id": "quasar", "object": "model"}]
    })

app = web.Application()
app.router.add_post("/v1/chat/completions", chat_completions)
app.router.add_get("/v1/models", models)
app.router.add_get("/health", health)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5001)
```

2. Rodar como container Docker ou systemd service
3. No HA, configurar OpenAI Conversation (ou Extended) apontando pra `http://localhost:5001/v1`

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ HA Voice │────►│ OpenAI   │────►│  Proxy   │────►│ OpenClaw │
│ Pipeline │     │ Conv.    │     │  Python  │     │ (Quasar) │
│          │◄────│ integr.  │◄────│  :5001   │◄────│  Claude  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                        │
                                                   Já tem acesso a:
                                                   - HA API
                                                   - LG TV
                                                   - Órbita
                                                   - Memória/contexto
                                                   - Ferramentas
```

**Prós:**
- ✅ Usa o Quasar completo (com todas as integrações já configuradas)
- ✅ Controle da TV, Órbita, e tudo mais que o Quasar já faz
- ✅ Contexto persistente (memória do OpenClaw)
- ✅ Sem custo adicional de API (usa o mesmo plano do OpenClaw)
- ✅ Pode processar comandos complexos ("modo filme" = TV + luzes + volume)
- ✅ Latência baixa (tudo local, só o LLM é cloud)

**Contras:**
- ❌ Precisa implementar e manter o proxy Python
- ❌ Function calling do HA não funciona direto (o Quasar faz as ações por conta)
- ❌ O OpenClaw precisa estar rodando e saudável
- ❌ API `sessions_send` pode mudar (depende da versão do OpenClaw)
- ❌ Debug mais complexo (mais camadas)
- ❌ Respostas podem ser longas demais pra TTS se o prompt não for bem ajustado

**Nota sobre function calling:**
Nessa opção, o Quasar **ele mesmo** chama a HA API diretamente (já tem token e acesso). O HA não precisa fazer function calling — o agent já executa a ação antes de responder. Isso é mais poderoso mas menos transparente pro HA (o HA não "sabe" o que o agent fez).

---

### Opção C: OpenClaw Expondo Endpoint OpenAI-Compatible

**Como funciona:**
O OpenClaw pode (no futuro) expor nativamente um endpoint `/v1/chat/completions` que seja diretamente compatível com a integração OpenAI Conversation do HA. Isso eliminaria o proxy Python.

**Status:** ⏳ Não disponível ainda. Depende de feature request/implementação no OpenClaw.

Se/quando disponível, o setup seria o mais simples:

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ HA Voice │────►│ OpenAI   │────►│ OpenClaw │
│ Pipeline │     │ Conv.    │     │ endpoint │
│          │◄────│ integr.  │◄────│ /v1/chat │
└──────────┘     └──────────┘     └──────────┘
```

1. No HA: OpenAI Conversation → Base URL: `http://localhost:OPENCLAW_PORT/v1`
2. API Key: token do OpenClaw
3. Pronto.

**Prós:**
- ✅ Setup mínimo (sem proxy, sem código custom)
- ✅ Mantido pelo OpenClaw (menos manutenção)
- ✅ Todas as vantagens da Opção B

**Contras:**
- ❌ Não existe ainda
- ❌ Depende do roadmap do OpenClaw
- ❌ Pode ter limitações na implementação

---

## Comparativo Resumido

| Critério | Opção A (Anthropic direta) | Opção B (Proxy OpenClaw) | Opção C (OpenClaw nativo) |
|----------|---------------------------|--------------------------|---------------------------|
| **Complexidade setup** | Média (HACS + LiteLLM) | Média (proxy Python) | Baixa (config only) |
| **Custo mensal** | ~$2/mês (API tokens) | Incluso no OpenClaw | Incluso no OpenClaw |
| **Latência** | Média (cloud) | Baixa-média | Baixa-média |
| **Integrações** | Só HA entities | Tudo (TV, Órbita, etc.) | Tudo (TV, Órbita, etc.) |
| **Contexto/memória** | Nenhum (stateless) | Completo (OpenClaw) | Completo (OpenClaw) |
| **Function calling HA** | ✅ Nativo | ❌ Agent faz direto | Depende |
| **Manutenção** | Baixa | Média | Baixa |
| **Disponível agora** | ✅ Sim | ✅ Sim | ❌ Futuro |

### Recomendação

**Para começar rápido:** Opção A (Extended OpenAI Conversation + LiteLLM + Anthropic). Setup em 1h, funciona bem pra comandos de HA.

**Para experiência completa:** Opção B (Proxy → OpenClaw). Mais trabalho inicial, mas o Quasar pode fazer tudo que já faz via Telegram, agora por voz.

**Para o futuro:** Opção C quando/se disponível, migrar da B pra C.

É possível começar com A e migrar pra B depois sem perder nada.

---

## Configuração no HA (Comum a Todas as Opções)

### System Prompt (Template Jinja2)

Independente da opção, o system prompt do conversation agent deve ser otimizado pra voz:

```
Você é o Quasar, assistente de voz da casa.
Responda SEMPRE em português brasileiro.
Respostas CURTAS (1-2 frases) — serão faladas em voz alta por TTS.

Ao receber um comando de voz:
1. Interprete a intenção do usuário
2. Se for controle de dispositivo, execute a ação
3. Confirme brevemente

Dispositivos disponíveis:
{%- for entity in exposed_entities %}
- {{ entity.name }} ({{ entity.entity_id }}): {{ entity.state }}
{%- endfor %}

Cômodo de origem: {{ area_name | default('desconhecido') }}

Exemplos de resposta:
- "Acende a luz" → "Pronto."
- "Que horas são?" → "São três e quinze."
- "Tá quente" → "Ligando o ar a 23 graus."
- "Modo filme" → "Modo filme ativado."

NÃO diga coisas como "Claro!", "Com certeza!", "Fico feliz em ajudar!".
Seja direto como um humano seria.
```

### Atualizar Voice Pipeline

1. **Settings → Voice Assistants → Quasar**
2. Trocar **Conversation Agent** de "Home Assistant" para o agent configurado
3. Testar

### Expor Entidades

Em **Settings → Voice Assistants → Expose**, marcar quais entidades o agent pode ver e controlar. Começar com:
- Luzes de cada cômodo
- Switches (tomadas inteligentes)
- Climate (ar condicionado)
- Media players
- Scripts/Scenes

## Context: Identificando o Cômodo

Cada QuasarBox tem um `device_id` no HA atribuído a uma área. O pipeline passa essa info pro conversation agent:

```
O comando veio do dispositivo: {{ satellite.device_name }}
Cômodo: {{ satellite.area }}
```

Assim "acende a luz" no quarto acende a luz do quarto, não da sala.

## Exemplos de Interação

| Comando de voz | Resposta esperada | Ação |
|---|---|---|
| "Acende a luz" | "Pronto." | `light.turn_on` (luz do cômodo) |
| "Tá quente aqui" | "Ligando o ar a 23 graus." | `climate.set_temperature` |
| "Que horas são?" | "São três e quinze." | Nenhuma |
| "Liga a TV na Netflix" | "TV ligando na Netflix." | TV Controller API |
| "Modo filme" | "Modo filme ativado." | Script: TV on, luzes dim |
| "Bom dia" | "Bom dia! Hoje faz 28 graus." | Nenhuma (info) |

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

## Validação

- [ ] Conversation agent escolhido e configurado
- [ ] HA pipeline "Quasar" usando o agent
- [ ] Comandos de controle funcionam (ligar/desligar dispositivos)
- [ ] Respostas são breves e naturais (≤ 2 frases)
- [ ] Context do cômodo funciona corretamente
- [ ] Latência total do pipeline aceitável (< 7s wake-to-response)
- [ ] Sem erros em 10 comandos consecutivos
- [ ] Agent responde em pt-BR consistentemente
