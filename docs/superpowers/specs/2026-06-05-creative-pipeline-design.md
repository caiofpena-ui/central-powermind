# PowerMind Creative Pipeline — Design Spec
**Data:** 2026-06-05
**Status:** Aprovado

---

## Visão Geral

Creative Pipeline é o Subsistema 2 do PowerMind Marketing Hub. Gerencia a produção de todo conteúdo visual e em vídeo da marca. Dois fluxos paralelos: posts estáticos/carrosséis via Canva API (automático) e conteúdo UGC via creators com roteiro gerado por IA (semi-automático). Todo conteúdo aprovado vai para a biblioteca de assets que alimenta o Content Calendar (Subsistema 3).

---

## Escopo

### O que está incluído
- Geração de posts via Canva API com templates pré-cadastrados
- Geração de roteiro UGC via Claude API
- Envio de briefing para creator via WhatsApp
- Upload de conteúdo gravado pela creator
- Fluxo de aprovação (rascunho → aprovado → biblioteca)
- Biblioteca de assets com filtros
- Cadastro de templates Canva no sistema

### O que NÃO está incluído (outros subsistemas)
- Agendamento e publicação (Subsistema 3 e 4)
- Geração de copy de legenda para posts (Brand Hub — Subsistema 1)
- Montagem automática de vídeo com IA generativa (Fase 2)

---

## Arquitetura

```
/marketing (subaba Criativos)    → seção dentro de marketing.html

/api/creative/templates          → GET lista templates Canva cadastrados
/api/creative/templates/save     → POST cadastra/edita template
/api/creative/gerar-post         → POST Canva API → retorna URL da arte gerada
/api/creative/briefing-ugc       → POST Claude API → retorna roteiro UGC
/api/creative/enviar-briefing    → POST envia roteiro via WhatsApp para creator
/api/creative/upload             → POST creator faz upload do conteúdo gravado
/api/creative/assets             → GET biblioteca de assets
/api/creative/aprovar            → POST aprova asset → status vira "aprovado"

canva_templates.json             → templates cadastrados com IDs do Canva
assets.json                      → biblioteca de conteúdos produzidos
```

---

## Modelo de Dados

### `canva_templates.json`
```json
[
  {
    "id": "uuid",
    "nome": "Post Feed Produto",
    "canva_design_id": "DAxxxxxx",
    "tipo": "post_feed",
    "canal": "instagram_feed",
    "dimensoes": "1080x1080",
    "campos_editaveis": ["headline", "subtext", "cta", "foto_produto"],
    "pilar": "Oferta",
    "thumbnail_url": "https://..."
  }
]
```

### `assets.json`
```json
[
  {
    "id": "uuid",
    "criado_em": "2026-06-05T10:00:00",
    "tipo": "post_feed",
    "fluxo": "canva",
    "pilar": "Prova Social",
    "canal": "instagram_feed",
    "titulo": "Depoimento Ana - Junho",
    "arquivo_url": "https://...",
    "canva_url": "https://...",
    "copy": "Depois de 30 dias usando PowerMind...",
    "status": "aprovado",
    "template_id": "uuid",
    "briefing_id": "uuid",
    "creator_username": null,
    "aprovado_em": "2026-06-05T11:00:00",
    "aprovado_por": "Julia"
  }
]
```

---

## Fluxo 1: Posts Estáticos via Canva API

### Interface
- Subaba "Criativos" em marketing.html
- Select: template (lista de canva_templates.json com thumbnail)
- Campos dinâmicos: renderiza os `campos_editaveis` do template escolhido
- GPT sugere copy automaticamente baseado no Brand Hub
- Botão "Gerar Arte" → chama Canva API
- Preview da arte gerada
- Botão "Aprovar → Biblioteca" ou "Editar no Canva"

### Integração Canva API
- Chave: `CANVA_API_KEY` no `.env`
- Endpoint: `POST /v1/designs/{design_id}/autofill`
- Preenche campos de texto e imagem no template
- Retorna URL de exportação da arte pronta

---

## Fluxo 2: UGC — Roteiro para Creators

### Interface
- Select: creator (lista do CRM)
- Select: pilar de conteúdo
- Input: tema livre (opcional)
- Select: canal destino (Reels / TikTok / Stories)
- Botão "Gerar Roteiro com Claude"
- Área de roteiro editável com estrutura:
  - **Gancho (0-3s):** frase de abertura
  - **Desenvolvimento (3-25s):** corpo do conteúdo
  - **CTA (25-30s):** chamada para ação
  - **Legenda sugerida** (GPT)
  - **Hashtags** (GPT)
- Botão "Enviar para Creator via WhatsApp"
- Status do briefing: enviado → gravado → upload → aprovado

### WhatsApp
- Usa `resolverWhatsApp(creator)` já existente no CRM
- Mensagem formatada com roteiro completo + instruções de gravação
- Link de upload direto para o creator

### Upload pelo Creator
- Rota GET `/upload-criativo?briefing_id=xxx` → página simples de upload
- Creator acessa pelo celular, faz upload do vídeo gravado
- Sistema registra o arquivo e notifica Julia

---

## Biblioteca de Assets

### Interface
- Grid de cards com thumbnail, tipo, pilar, canal, status
- Filtros: tipo (post/reels/stories/tiktok), pilar, canal, status, creator
- Ações por card: ver, aprovar, editar copy, enviar para calendário, arquivar
- Status visual: rascunho (cinza) → em revisão (amarelo) → aprovado (verde)

---

## Arquivos Afetados

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `financeiro/marketing.html` | Modificar | Subaba Criativos |
| `financeiro/canva_templates.json` | Criar | Templates cadastrados |
| `financeiro/assets.json` | Criar | Biblioteca de assets |
| `financeiro/server.py` | Modificar | +8 rotas novas |

---

## Dependências

- Subsistema 1 (Brand Hub) deve estar implementado — Claude usa brand.json como contexto
- `CANVA_API_KEY` no `.env`
- `ANTHROPIC_API_KEY` no `.env` (já usado no Brand Hub)
- `OPENAI_API_KEY` no `.env` (já usado no Brand Hub)
