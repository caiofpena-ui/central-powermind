# PowerMind Content Calendar — Design Spec
**Data:** 2026-06-05
**Status:** Aprovado

---

## Visão Geral

Content Calendar é o Subsistema 3 do PowerMind Marketing Hub. Organiza quando e onde cada conteúdo será publicado. Claude sugere a pauta semanal baseada nos pilares do Brand Hub, Julia arrasta e aprova, o sistema agenda para o Auto Publisher (Subsistema 4) executar automaticamente.

---

## Escopo

### O que está incluído
- Calendário visual semanal/mensal por canal
- Sugestão automática de pauta semanal via Claude (baseada nos pilares)
- Fila de publicação por canal com horários otimizados
- Status por post: rascunho → aprovado → agendado → publicado → falhou
- Aprovação em lote (semana inteira com 1 clique)
- Vinculação com assets da biblioteca (Subsistema 2)

### O que NÃO está incluído
- Publicação em si (Subsistema 4)
- Criação de conteúdo (Subsistema 2)
- Métricas de resultado pós-publicação (Fase 2)

---

## Arquitetura

```
/marketing (subaba Calendário)     → seção dentro de marketing.html

/api/calendar/semana               → GET posts agendados da semana
/api/calendar/mes                  → GET posts agendados do mês
/api/calendar/sugerir-pauta        → POST Claude sugere pauta para próxima semana
/api/calendar/agendar              → POST agenda um post (vincula asset + canal + horário)
/api/calendar/aprovar-semana       → POST aprova todos os posts da semana
/api/calendar/update-status        → POST atualiza status de um post

calendar.json                      → fila de posts agendados
```

---

## Modelo de Dados

### `calendar.json`
```json
[
  {
    "id": "uuid",
    "asset_id": "uuid",
    "canal": "instagram_feed",
    "data_hora": "2026-06-10T19:00:00",
    "pilar": "Prova Social",
    "copy": "Depois de 30 dias usando PowerMind...",
    "hashtags": "#energia #foco #powermindbr",
    "status": "agendado",
    "publicado_em": null,
    "resultado": null,
    "criado_por": "Julia",
    "sugerido_ia": true
  }
]
```

---

## Horários Otimizados por Canal

| Canal | Horário padrão | Frequência |
|---|---|---|
| Instagram Feed | 19:00 | 3x/semana |
| Instagram Reels | 18:00 | 4x/semana |
| Instagram Stories | 09:00 e 20:00 | Diário |
| TikTok | 20:00 | 4x/semana |
| Meta Ads boost | — | Posts com maior engajamento |
| WhatsApp broadcast | 10:00 | 1x/semana |
| E-mail | 08:00 | 2x/semana |

---

## Interface — Subaba Calendário

### Visão Semanal
- Grade 7 dias × canais
- Cada célula mostra thumbnail do post agendado + pilar + status
- Drag-and-drop para mover posts entre dias/horários
- Clique no post abre detalhes (copy, asset, canal, horário)
- Botão "Sugerir Pauta da Semana" → Claude gera sugestão completa
- Botão "Aprovar Semana" → todos os posts vão para status "agendado"

### Visão Mensal
- Grid mensal com indicador de quantidade de posts por dia por canal
- Filtro por canal

### Painel de Sugestão de Pauta
- Claude recebe: pilares do Brand Hub + frequências + posts das últimas 2 semanas (evitar repetição)
- Retorna: 7 dias de sugestões com tipo, pilar, copy rascunho, canal, horário
- Julia edita ou aprova cada sugestão
- Sugestões aprovadas buscam asset correspondente da biblioteca ou criam rascunho

---

## Arquivos Afetados

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `financeiro/marketing.html` | Modificar | Subaba Calendário |
| `financeiro/calendar.json` | Criar | Fila de posts agendados |
| `financeiro/server.py` | Modificar | +6 rotas novas |

---

## Dependências

- Subsistema 1 (Brand Hub) — pilares e frequências
- Subsistema 2 (Creative Pipeline) — biblioteca de assets
