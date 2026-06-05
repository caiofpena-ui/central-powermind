# PowerMind Auto Publisher — Design Spec
**Data:** 2026-06-05
**Status:** Aprovado

---

## Visão Geral

Auto Publisher é o Subsistema 4 do PowerMind Marketing Hub. Executa automaticamente a publicação nos canais no horário agendado pelo Content Calendar. Roda via launchd (já existente no sistema), verifica a fila a cada 5 minutos e publica o que estiver com status "agendado" e horário atingido.

---

## Escopo

### O que está incluído
- Publicação automática: Instagram (feed, reels, stories), TikTok, WhatsApp broadcast, e-mail
- Boost automático no Meta Ads para posts com alto engajamento (após 2h)
- Worker Python rodando via launchd a cada 5 minutos
- Log de publicações com status e erros
- Painel de status em tempo real na subaba "Publicação"

### O que NÃO está incluído (Fase 2)
- Análise de performance pós-publicação
- A/B testing automático de copies
- Resposta automática a comentários

---

## Arquitetura

```
publisher.py                       → worker Python (launchd, roda a cada 5min)
publisher.log                      → log de publicações

/marketing (subaba Publicação)     → painel de status em marketing.html

/api/publisher/status              → GET últimas 50 publicações do log
/api/publisher/retentar            → POST retenta publicação que falhou
/api/publisher/config              → GET/POST configurações por canal (ativo/inativo, horários)

publisher_config.json              → configurações dos canais
```

---

## Canais e APIs

### Instagram (Meta Graph API)
- Auth: `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_ACCOUNT_ID` no `.env`
- Feed e Carrossel: `POST /me/media` + `POST /me/media_publish`
- Reels: upload de vídeo via container + publish
- Stories: `POST /me/media` com `media_type=STORIES`

### TikTok
- Auth: `TIKTOK_ACCESS_TOKEN` + `TIKTOK_OPEN_ID` no `.env`
- Upload: TikTok Content Posting API v2
- `POST /v2/post/publish/video/init/` → upload → publish

### Meta Ads (boost automático)
- Usa `META_TOKEN` já existente no `.env`
- Após 2h do post Instagram: verifica engajamento
- Se likes + comentários > threshold (configurável): cria campanha de boost automático
- Budget padrão: R$20/dia por 3 dias

### WhatsApp Broadcast
- Usa número já cadastrado no sistema
- Mensagem formatada com copy + link do post
- Lista de broadcast: clientes que compraram + leads capturados

### E-mail
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` no `.env`
- Template HTML com identidade PowerMind
- Lista: leads capturados via pop-up da LP

---

## Worker `publisher.py`

```python
# Roda a cada 5 minutos via launchd
# 1. Lê calendar.json → filtra status="agendado" e data_hora <= agora
# 2. Para cada post:
#    - Publica no canal via API correspondente
#    - Atualiza status: "publicado" ou "falhou" com mensagem de erro
#    - Registra em publisher.log
# 3. Verifica posts Instagram publicados há 2h → boost se engajamento alto
```

---

## Modelo de Dados

### `publisher_config.json`
```json
{
  "canais": {
    "instagram_feed": {"ativo": true, "horario_padrao": "19:00"},
    "instagram_reels": {"ativo": true, "horario_padrao": "18:00"},
    "instagram_stories": {"ativo": true, "horario_padrao": "09:00"},
    "tiktok": {"ativo": true, "horario_padrao": "20:00"},
    "whatsapp_broadcast": {"ativo": true, "horario_padrao": "10:00"},
    "email": {"ativo": true, "horario_padrao": "08:00"},
    "meta_ads_boost": {"ativo": true, "threshold_engajamento": 50, "budget_dia": 20, "duracao_dias": 3}
  }
}
```

---

## Interface — Subaba Publicação

### Painel de Status
- Cards por canal com: status (ativo/inativo), último post, próximo agendado
- Toggle para ativar/desativar canal
- Tabela de logs: data/hora, canal, post, status (publicado/falhou), ação (retentar)

### Configurações
- Horários padrão por canal (editável)
- Threshold de boost Meta Ads
- Budget de boost

---

## launchd — `com.powermind.publisher`

```xml
<!-- ~/Library/LaunchAgents/com.powermind.publisher.plist -->
<key>StartInterval</key>
<integer>300</integer>  <!-- 5 minutos -->
<key>ProgramArguments</key>
<array>
  <string>python3</string>
  <string>/Users/macbookpro/Desktop/Sandbox/financeiro/publisher.py</string>
</array>
```

---

## Arquivos Afetados

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `financeiro/publisher.py` | Criar | Worker de publicação automática |
| `financeiro/publisher_config.json` | Criar | Configuração dos canais |
| `financeiro/publisher.log` | Criar | Log de publicações |
| `financeiro/marketing.html` | Modificar | Subaba Publicação |
| `financeiro/server.py` | Modificar | +3 rotas novas |
| `~/Library/LaunchAgents/` | Criar | plist do publisher worker |

---

## Dependências

- Subsistema 3 (Content Calendar) — calendar.json com posts agendados
- `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_ACCOUNT_ID` no `.env`
- `TIKTOK_ACCESS_TOKEN` + `TIKTOK_OPEN_ID` no `.env`
- `SMTP_HOST` + `SMTP_USER` + `SMTP_PASS` no `.env`
- Meta Token já existente no `.env`

## Nota sobre autenticação Instagram e TikTok

Instagram Graph API e TikTok Content API requerem conta Business/Creator verificada e aprovação de app. Antes da implementação:
1. Criar Facebook App em developers.facebook.com
2. Solicitar permissões `instagram_content_publish`
3. Criar TikTok Developer App em developers.tiktok.com
4. Solicitar permissão `video.publish`
Processo de aprovação leva 3-7 dias úteis.
