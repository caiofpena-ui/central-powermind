# PowerMind — Base de Contexto Compartilhada

Este arquivo é lido automaticamente pelo Claude Code. Ele contém todo o contexto do projeto PowerMind para que Caio e Felipe possam trabalhar com a mesma base de dados no Claude.

---

## Sobre a Empresa

**Marca:** PowerMind
**Produto:** Suplemento para energia, foco e memória (formato sachê/pó)
**Site:** https://www.powermindbr.com.br/
**Instagram:** @powermindbr_
**Plataforma de e-commerce:** Yampi
**Meta Ads Account ID:** act_4170730686474512

### SKUs e Preços
| Kit | Preço |
|---|---|
| 1 pacote | R$157 |
| Power Duo (2 pacotes) | R$274 (default selecionado na LP) |
| 3 pacotes | R$381 |
| 6 pacotes | R$702 |

**Ticket médio estimado:** R$195 (mix 50% kit 1cx + 50% Power Duo)
**Ticket médio original:** R$142

---

## Modelo Financeiro (atualizado 23/05/2026)

### CMV por Kit
| Kit | CMV (produto) | Mixer | CMV Total |
|---|---|---|---|
| 1 Pacote | R$37,00 | R$0,00 | R$37,00 |
| 2 Pacotes (Power Duo) | R$74,00 | R$12,00 | R$86,00 |
| 3 Pacotes | R$111,00 | R$12,00 | R$123,00 |
| 6 Pacotes | R$222,00 | R$12,00 | R$234,00 |

### Deduções sobre a Receita
| Item | Taxa |
|---|---|
| Imposto | 10,00% |
| Gateway cartão (Yampi/Kiwify) | 4,99% |
| Gateway PIX | 1,00% |
| Taxa Yampi (plataforma) | 2,50% |
| Frete estimado | R$20,00/pedido |

### Custos Fixos Mensais (base)
| Item | Valor/mês |
|---|---|
| Mayara | R$500,00 |
| Hostinger | R$49,99 |
| Domínio | R$29,99 |
| **Total** | **R$579,98 → R$19,33/dia** |

> Custos fixos são gerenciados dinamicamente no dashboard (localhost:8080 → aba Custos Fixos).

### Metas Financeiras
| Métrica | Meta |
|---|---|
| ROAS mínimo | 3,5x |
| CPA máximo | R$78 |
| Margem líquida alvo | ≥13% |

---

## Equipe

| Sócio | Responsabilidade |
|---|---|
| **Caio** | Tráfego pago — Meta Ads, campanhas, criativos, métricas |
| **Felipe** | Landing page, Instagram, e-mail, automações |

---

## Situação Atual (Mai/2026)

- Vendas: ~1 produto/dia
- Meta: R$1.000/dia (5-7 compras/dia) em 90 dias
- Campanha ativa: `[TOPO-FRIO][CBO] PowerMind Felipinho Scale [30-04-2026]`
- Orçamento atual: R$100/dia (TOFU apenas)
- Pixel Meta: sem histórico de Purchase ainda

### Métricas Baseline (30/04/2026)
| Métrica | Valor | Meta |
|---|---|---|
| Gasto/dia | R$48,64 | R$100 |
| Impressões | 836 | — |
| CTR | 2,99% | >2% ✅ |
| CPM | R$58,18 | <R$55 ⚠️ |
| LP View Rate | 64% | >75% 🔴 |
| CPC (link) | R$3,47 | — |
| Compras | 0 | — |
| ROAS | — | >2,5x |

---

## Diagnóstico Principal

1. **LP lenta no mobile** — React SPA (JS ~366kb), LCP possivelmente >3s. Causa direta do LP View Rate em 64%.
2. **LP estruturada como catálogo**, não funil — abre com nome do produto, não com dor do visitante.
3. **Funil incompleto** — apenas TOFU ativo. MOFU e BOFU inexistentes.
4. **Zero captura de lead** — visitante que não compra some para sempre.
5. **Botão de compra com ícone WhatsApp** — gera confusão (usuário espera chat, não checkout).

---

## Fases de Receita

| Fase | Prazo | Orçamento/dia | Conv. LP | Compras/dia | Receita/dia |
|---|---|---|---|---|---|
| Atual | — | R$100 | ~0% | 0 | R$0 |
| 1 | 30 dias | R$200 | 2% | 2-3 | R$350-500 |
| 2 | 60 dias | R$400 | 3% | 5-6 | R$800-950 |
| 3 | 90 dias | R$600 | 3,5% | 7-8 | R$1.000-1.200 |

---

## PROJETO CAIO — Tráfego Pago

### Estrutura de Campanhas (Meta Ads)

| Campanha | Objetivo | Orçamento | Público | Status |
|---|---|---|---|---|
| TOFU Escala (CBO) | LP Views → Conversão | R$100/dia | Fem. 25-54, BR, saúde/energia | ✅ Ativa |
| TOFU Teste Criativo (ABO) | Testar novos ângulos | R$50/dia | Mesmo público | 🔜 Criar |
| MOFU Remarketing | Conversão | R$40/dia | Visitantes 30d sem compra | 🔜 Criar |
| BOFU Quente | Conversão | R$30/dia | Checkout abandonado (7d) | 🔜 Criar (quando visitas >150/dia) |

### Criativos Ativos
- **Felipinho Video Principal** — CTR 2,99% ✅ — manter como base

### Briefing de Novos Criativos

**Criativo 1 — "A tarde que paralisa"**
- Cena: mulher, computador, 14h, cabeça pesada
- Fala: "Todo dia às 2 da tarde meu cérebro simplesmente desliga. Café não resolve mais."
- Corte para PowerMind
- Formato: 9:16, 15-30s, sem texto nos primeiros 3s

**Criativo 2 — "Testei 30 dias" (UGC)**
- Mulher 30-45 anos, filmado no celular, tom honesto
- Estrutura: Dia 1 / Dia 7 / Dia 30
- Resultados honestos, sem exagero

**Criativo 3 — "Sem crash" (estático)**
- Comparação visual: energético (pico/queda) vs PowerMind (linha constante)
- Copy: "Não é energia emprestada. É energia construída."
- Uso: MOFU/BOFU

**Criativo 4 — Prova social (estático)**
- Print de depoimento real + imagem produto
- "30 dias de garantia · Parcele em 12x"
- Uso exclusivo: remarketing

### Regras de Decisão
- CPA <R$57 por 3 dias → escalar TOFU em 20-30%
- CPA ≥R$57 → manter, revisar criativos
- CTR <1,5% por 3 dias → pausar criativo, testar novo ângulo
- LP View Rate <70% → acionar Felipe para investigar velocidade
- CPM >R$65 → revisar público (possível saturação)
- ROAS <2,0x por 2 semanas → reunião urgente

### Checklist Semanal Caio (toda segunda)
- [ ] Exportar relatório Meta Ads com 8 métricas
- [ ] Calcular médias de CPA, ROAS e compras/dia
- [ ] Identificar melhor e pior criativo da semana
- [ ] Verificar se visitas à LP ultrapassaram 150/dia
- [ ] Reunião com Felipe: apresentar métricas, decidir ação
- [ ] Executar ajustes de orçamento e subir criativos aprovados

---

## PROJETO FELIPE — Landing Page & Instagram

### Correções da LP por Prioridade

**🔴 URGENTE — Semana 1**
- [ ] Testar velocidade no mobile (Google Lighthouse) — se LCP >3s → criar versão HTML estática
- [ ] Reescrever hero section:
  - Headline: *"Você chega na tarde sem gasolina pra nada — e não adianta mais café."*
  - Subheadline: *"PowerMind entrega energia constante o dia inteiro, sem pico, sem queda, sem ansiedade."*
- [ ] Mover depoimentos para logo após o hero (antes dos ingredientes)
- [ ] Corrigir ícone do botão "COMPRAR AGORA" (WhatsApp → carrinho)
- [ ] Criar seção de garantia dedicada após o botão:
  - Copy: *"Tomou, não sentiu diferença, devolvemos 100% do seu dinheiro. Sem perguntas, sem burocracia."*
- [ ] Configurar abandono de checkout na Yampi (e-mail automático em 1h)

**🟡 Semana 2**
- [ ] Instalar pop-up exit-intent com guia gratuito
- [ ] Adicionar urgência (contador ou "Frete grátis apenas hoje")
- [ ] Criar sequência de 5 e-mails:
  - D+0: Guia + boas-vindas
  - D+2: Explicação dos ingredientes
  - D+4: Depoimento de cliente real
  - D+6: Quebra de objeção (preço, eficácia)
  - D+7: Oferta com urgência (desconto R$20)

**🟢 Semanas 3-4**
- [ ] Analisar heatmap e ponto de maior abandono
- [ ] Testar variação de CTA se conversão <2%

### Checklist Instagram Semanal (Felipe)

**Stories (4-5/dia)**
- [ ] Bastidor / dia a dia da marca
- [ ] Depoimento republicado da LP
- [ ] Conteúdo de autoridade sobre ingrediente
- [ ] CTA com link da LP
- [ ] Engajamento (enquete, pergunta, quiz)

**Posts no Feed (3/semana)**
- [ ] Autoridade sobre ingrediente
- [ ] Depoimento ou prova social
- [ ] Educativo ou de posicionamento

**Reels (1/semana)**
- [ ] Ângulo de dor ou transformação (pode reaproveitar criativo dos ads)

---

## Dashboard Conjunto — Toda Segunda-Feira

| Métrica | Meta | Responsável por atingir | Quem monitora |
|---|---|---|---|
| LP View Rate | >75% | Felipe (velocidade/UX da LP) | Caio (Meta Ads) |
| CTR do criativo | >2% | Caio | Caio |
| CPM | <R$55 | Caio | Caio |
| Taxa de conversão LP | >2% | Felipe | Felipe (Yampi) |
| CPA | <R$57 | Caio | Caio |
| ROAS | >3,5x | Caio + Felipe | Caio |
| Compras/dia | F1:2-3 / F2:5-6 / F3:7-8 | Caio + Felipe | Caio |
| Abandono de checkout | <60% | Felipe | Felipe (Yampi) |

**Semáforo:**
- 🟢 Dentro da meta
- 🟡 Até 20% abaixo da meta — atenção
- 🔴 Mais de 20% abaixo — ação imediata

---

## Reunião Semanal

**Quando:** Todo domingo às 07:30
**Participantes:** Caio + Felipe
**Pauta padrão:**
1. Dashboard das 8 métricas (Caio apresenta)
2. Status das tarefas da LP e Instagram (Felipe apresenta)
3. Decisões: escalar, pausar, testar criativo novo
4. Prioridades da semana seguinte

---

## Agenda (Caio)

Compromissos já agendados:
- **04/05** — Robson Gastão Bobst · 10:00
- **11/05** — Almoço Melissa · Gráfica Andorinha · 11:30
- **20/05** — Reunião Artivinco · 14:30 *(lembrete: 10:00)*
- **18/06** — Treinamento Welpack
- **Todo dia 10** — Pagamento CPFL - WhatsApp (recorrente)
- **Todo domingo** — Reunião Semanal PowerMind · 07:30

---

## Como Usar Este Arquivo

1. **Caio:** abra o Claude Code na pasta deste projeto. O Claude já lê este arquivo automaticamente e entende todo o contexto.
2. **Felipe:** clone este repositório, abra o Claude Code na mesma pasta e use normalmente.
3. **Atualizações:** sempre que houver uma decisão importante (novo criativo aprovado, mudança na LP, nova campanha), atualize este arquivo para manter os dois alinhados.
4. **Nunca apague o histórico** — adicione novas seções embaixo das existentes com a data.

---

---

## Dashboard — Acesso

- **Arquivo local:** `file:///Users/macbookpro/Desktop/Sandbox/financeiro/dashboard.html`
- **Servidor ao vivo:** `http://localhost:8080` (launchd — inicia automaticamente com o Mac)
- **Backup salvo:** `dashboard_backup_20260523.html`
- **Último backup completo:** `financeiro/backup_20260531/` (31/05/2026) — contém crm, contrato, ficha, dashboard, server.py, creators.json
- Atualização automática a cada 60 segundos
- Para regerar o HTML: `python3 financeiro/dashboard.py`

---

## Histórico Financeiro Real — Out/2025 a Mai/2026 (Planilha RM12)

> Dados extraídos da planilha `Fluxo de Caixa - POWERMIND [RM12] (1).xlsx` em 23/05/2026.
> Todos os lançamentos foram importados no `lancamentos.json` do dashboard.

### Gastos por Categoria (Acumulado)

| Categoria | Total |
|---|---|
| Tráfego Pago | R$ 19.422,06 |
| Produto / Estoque | R$ 13.053,58 |
| Despesas Operacionais | R$ 25.858,35 |
| Logística | R$ 5.120,16 |
| Eventos | R$ 237,00 |
| Marketing / Conteúdo | R$ 4.378,53 |
| **TOTAL GASTO** | **R$ 68.069,68** |

### Aportes do Sócio (Caio) por Mês

| Mês | Valor |
|---|---|
| Novembro/25 | R$ 5.000,00 |
| Dezembro/25 | R$ 3.000,00 |
| Janeiro/26 | R$ 8.000,00 |
| Fevereiro/26 | R$ 3.000,00 |
| Março/26 | R$ 12.300,00 |
| Abril/26 | R$ 8.000,00 |
| Maio/26 | R$ 4.000,00 |
| **TOTAL APORTADO** | **R$ 43.300,00** |

### Receita de Vendas (Saques Yampi)

| Período | Valor |
|---|---|
| Abril/26 | R$ 12.048,93 |
| Maio/26 (parcial) | R$ 5.457,00 |
| **TOTAL RECEITA** | **R$ 17.505,93** |

### Compras de Estoque (Lotes Identificados)

| Data | Valor |
|---|---|
| Out/25 (sachês) | R$ 8.900,00 |
| Mar/26 (fábrica) | R$ 6.755,00 |
| Abr/26 (fábrica) | R$ 9.465,30 |
| Mai/26 (embalagens) | R$ 3.398,28 |

### Saldos em Caixa — Evolução

| Mês | Saldo Final |
|---|---|
| Nov/25 | R$ 3.360,00 |
| Dez/25 | R$ 2.449,35 |
| Jan/26 | R$ 3.048,79 |
| Fev/26 | R$ 787,10 |
| **Mar/26** | **R$ 28,07** ← ponto crítico |
| Abr/26 | R$ 2.213,72 |
| Mai/26 | R$ 43,72 |

---

*Última atualização: 23/05/2026*
