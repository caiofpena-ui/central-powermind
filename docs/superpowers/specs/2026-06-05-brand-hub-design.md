# PowerMind Brand Hub — Design Spec
**Data:** 2026-06-05
**Status:** Aprovado

---

## Visão Geral

Brand Hub é o Subsistema 1 do PowerMind Marketing Hub. É o "cérebro" da marca — um repositório editável que centraliza posicionamento, persona, tom de voz, copy framework e pilares de conteúdo. Toda geração de conteúdo dos subsistemas seguintes (Creative Pipeline, Content Calendar, Auto Publisher) consome este repositório como contexto.

---

## Escopo

### O que está incluído
- Aba "Marketing" no menu do CRM com subaba "Brand Hub"
- Formulário editável com 6 seções da marca
- Persistência em `brand.json`
- Botão "Gerar Briefing" via Claude API (roteiro UGC ou briefing de arte)
- Botão "Gerar Copy" via OpenAI GPT (3 variações de legenda)
- Seletor de tema/pilar antes de cada geração
- Histórico dos últimos 20 briefings gerados

### O que NÃO está incluído (Subsistemas 2-4)
- Envio de briefing para creators via WhatsApp (Subsistema 2)
- Montagem automática de vídeo (Subsistema 2)
- Calendário editorial (Subsistema 3)
- Publicação automática em canais (Subsistema 4)

---

## Arquitetura

```
/marketing                  → marketing.html (aba Brand Hub ativa por padrão)
/api/brand/get              → retorna brand.json completo
/api/brand/save             → salva brand.json
/api/brand/gerar-briefing   → Claude API → retorna briefing de criativo
/api/brand/gerar-copy       → OpenAI GPT → retorna 3 variações de copy
/api/brand/historico        → últimos 20 briefings gerados

brand.json                  → repositório da marca
briefings.json              → histórico de briefings gerados
```

CRM (`crm.html`) → nova aba "Marketing" no menu lateral

---

## Modelo de Dados

### `brand.json`
```json
{
  "posicionamento": {
    "proposta_valor": "Energia limpa e foco mental o dia todo, sem crash, sem cafeína em excesso",
    "diferenciais": ["Sem estimulantes sintéticos", "Fórmula com adaptógenos", "Resultado progressivo"],
    "categoria": "Suplemento cognitivo premium",
    "missao": "Dar às pessoas a clareza mental que precisam para performar no seu melhor todos os dias"
  },
  "persona": {
    "nome": "Ana",
    "idade": "28-42",
    "ocupacao": "Empreendedora, profissional liberal, mãe que trabalha",
    "dores": ["Cansaço crônico", "Queda de foco após almoço", "Café não resolve mais"],
    "desejos": ["Energia consistente", "Clareza mental", "Produtividade sem ansiedade"],
    "objecoes": ["Preço", "Funciona mesmo?", "Demora para fazer efeito"]
  },
  "tom_de_voz": {
    "adjetivos": ["Confiante", "Acolhedor", "Científico sem ser chato", "Direto"],
    "falar": ["Resultados reais", "Ciência acessível", "Comunidade", "Progressão"],
    "nao_falar": ["Milagre", "Emagrecer", "Cura", "Substituição de tratamento médico"]
  },
  "copy_framework": {
    "headline_padrao": "Você chega na tarde sem gasolina pra nada",
    "ganchos_validados": [
      "Todo dia às 2h da tarde meu cérebro simplesmente desliga",
      "Café não resolve mais — descobri o motivo",
      "30 dias testando e o que aconteceu me surpreendeu"
    ],
    "ctas_aprovados": ["Garanta o seu", "Experimente por 30 dias", "Ver mais depoimentos"],
    "estrutura_copy": "Dor → Agitação → Solução → Prova → CTA"
  },
  "identidade_visual": {
    "cores_primarias": ["#7c3aed", "#0a0f1e"],
    "cores_secundarias": ["#34d399", "#fbbf24"],
    "estilo": "Dark premium, minimalista, científico",
    "fontes": ["Inter", "Sora"],
    "elementos_visuais": ["Gradientes roxo-escuro", "Ícones lineares", "Fotos de pessoas reais em contexto de trabalho/foco"]
  },
  "pilares_conteudo": [
    {"nome": "Educação", "descricao": "Como funciona o produto, ingredientes, ciência", "frequencia_pct": 30},
    {"nome": "Prova Social", "descricao": "Depoimentos, resultados, antes/depois", "frequencia_pct": 25},
    {"nome": "Dor e Identificação", "descricao": "Conteúdo que a persona reconhece como próprio", "frequencia_pct": 20},
    {"nome": "Bastidores", "descricao": "Processo, equipe, valores da marca", "frequencia_pct": 15},
    {"nome": "Oferta", "descricao": "Promoções, kits, urgência", "frequencia_pct": 10}
  ]
}
```

### `briefings.json`
```json
[
  {
    "id": "uuid",
    "criado_em": "2026-06-05T10:00:00",
    "tipo": "ugc_roteiro",
    "pilar": "Prova Social",
    "tema_livre": "Creator testa por 30 dias",
    "canal_destino": "Instagram Reels",
    "briefing": "...",
    "copy_variacoes": ["...", "...", "..."],
    "status": "rascunho"
  }
]
```

---

## Interface — Aba Marketing no CRM

### Menu lateral
- Novo item "Marketing" no sidebar do CRM

### Subabas dentro de /marketing
1. **Brand Hub** — edição da marca + geração de briefings
2. **Criativos** *(Subsistema 2 — placeholder por ora)*
3. **Calendário** *(Subsistema 3 — placeholder por ora)*
4. **Publicação** *(Subsistema 4 — placeholder por ora)*

### Brand Hub — Tela Principal

**Seção 1: Posicionamento** (formulário editável)
- Proposta de valor (textarea)
- Diferenciais (lista com +/-)
- Missão (textarea)

**Seção 2: Persona "Ana"** (formulário editável)
- Nome, faixa etária, ocupação
- Dores (lista editável)
- Desejos (lista editável)
- Objeções (lista editável)

**Seção 3: Tom de Voz** (formulário editável)
- Adjetivos da marca
- O que falar / O que nunca falar

**Seção 4: Copy Framework** (formulário editável)
- Headline padrão
- Ganchos validados (lista)
- CTAs aprovados (lista)
- Estrutura de copy

**Seção 5: Identidade Visual** (formulário editável)
- Cores (color pickers)
- Estilo, fontes, elementos visuais

**Seção 6: Pilares de Conteúdo** (5 pilares com % editável)

**Painel de Geração** (direita ou rodapé da página):
- Select: tipo de geração (Briefing UGC / Briefing Arte / Copy)
- Select: pilar de conteúdo
- Input: tema livre (opcional)
- Select: canal destino (Instagram Feed / Reels / Stories / TikTok / Meta Ads)
- Botão "Gerar com Claude" (briefing)
- Botão "Gerar Copies com GPT" (3 variações)
- Área de resultado editável
- Botão "Salvar no Histórico"

**Histórico de Briefings** (tabela):
- Data, tipo, pilar, canal, status, ações (ver, copiar, enviar)

---

## Integração de APIs

### Claude API (Anthropic)
- Chave: `ANTHROPIC_API_KEY` no `.env`
- Modelo: `claude-3-5-haiku-20241022` (barato, rápido para briefings)
- Prompt sistema: injeta brand.json completo como contexto
- Prompt usuário: tipo + pilar + tema + canal → retorna briefing estruturado

### OpenAI GPT
- Chave: `OPENAI_API_KEY` no `.env`
- Modelo: `gpt-4o-mini` (barato, bom para copy)
- Prompt sistema: injeta tom_de_voz + copy_framework do brand.json
- Prompt usuário: tema + pilar + canal → retorna 3 variações de copy/legenda

### Rotas no server.py

```
GET  /api/brand/get              → lê brand.json
POST /api/brand/save             → salva brand.json
POST /api/brand/gerar-briefing   → chama Claude API, salva em briefings.json
POST /api/brand/gerar-copy       → chama OpenAI API, retorna array de 3 copies
GET  /api/brand/historico        → retorna briefings.json (últimos 20)
```

---

## Arquivos Afetados

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `financeiro/marketing.html` | Criar | Página completa Marketing Hub |
| `financeiro/brand.json` | Criar | Repositório da marca (pré-populado) |
| `financeiro/briefings.json` | Criar | Histórico de briefings gerados |
| `financeiro/server.py` | Modificar | +5 rotas novas + serving /marketing |
| `financeiro/crm.html` | Modificar | Nova aba "Marketing" no menu lateral |

---

## Fases de Implementação

### Fase 1 (este spec)
1. brand.json pré-populado com dados reais da PowerMind
2. Interface Brand Hub (formulário completo editável)
3. Integração Claude API para geração de briefing
4. Integração OpenAI GPT para geração de copy
5. Histórico de briefings

### Fase 2 (Subsistemas seguintes)
- Creative Pipeline: envio de briefing para creators, auto-video
- Content Calendar: calendário editorial com sugestões de pauta
- Auto Publisher: Instagram, TikTok, Meta Ads, WhatsApp, e-mail
