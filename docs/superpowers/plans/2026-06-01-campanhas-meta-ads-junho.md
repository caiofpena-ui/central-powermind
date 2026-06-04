# PowerMind — Plano de Campanhas Meta Ads | Junho 2026

**Período:** 01/06 → 30/06/2026  
**Responsável:** Caio  
**Conta:** act_4170730686474512  
**Meta do mês:** 5 compras/dia · CPA < R$78 · ROAS > 3,5x

---

## SITUAÇÃO ATUAL (diagnóstico 01/06)

| O que está funcionando | O que está falhando |
|---|---|
| BOFU remarketing — ROAS 5,34x | TOFU não converte direto |
| CPM baixo no público broad (R$11,92) | "Anuncio 3 Criativo Pendente" queimando budget |
| [DOR-05] Mente Não Para — CPA R$28,60 | Volume de checkouts no TOFU muito baixo (6/semana) |
| CPC eficiente no BOFU (R$1,57) | ROAS geral da conta: 1,16x (puxado pra baixo pelo TOFU) |

**Risco principal:** BOFU depende de volume do TOFU. Se TOFU não gerar checkouts, o remarketing esgota a audiência e para de converter.

---

## ESTRUTURA DE CAMPANHAS — JUNHO

### CAMPANHA 1: BOFU — Manter como está
**Nome:** [BOFU][ABO] PowerMind Você Esqueceu [21-05-2026]  
**Status:** ✅ Não mexer  
**Orçamento:** manter o atual  
**Público:** Checkout Iniciado + Pagamento 7 dias  
**Ação:** Monitorar semanalmente. Só intervir se ROAS cair abaixo de 3,5x por 3 dias seguidos.

---

### CAMPANHA 2: TOFU ESCALA — Reestruturar
**Nome novo:** [TOFU][CBO] PowerMind Ângulos de Dor v2 [01-06]  
**Objetivo:** Conversões → Compra (não mais IC — mudar o objetivo)  
**Orçamento:** R$80/dia (CBO)  
**Público:** Mulheres 25–54 · Brasil · Interesses: saúde, bem-estar, energia, produtividade  

**Criativos iniciais (3 anúncios no mesmo ad set):**

| Anúncio | Ângulo | Formato | Origem |
|---|---|---|---|
| [DOR-05] Mente Não Para | Foco/clareza mental | Estático | Já testado — vencedor atual |
| [DOR-06] A Tarde que Paralisa | Cansaço às 14h | Vídeo 15–30s | Criar novo |
| [DOR-07] Testei 30 dias | UGC / prova social | Vídeo | Criar novo |

**Regra de decisão:**
- Aguardar 7 dias antes de qualquer corte
- Após 7 dias: pausar anúncio com CTR < 1,5% ou CPA > R$130
- Anúncio vencedor (menor CPA com compra) → isolar em ad set exclusivo na semana 2

---

### CAMPANHA 3: MOFU — Criar na semana 2
**Condição para ativar:** quando visitas diárias à LP ultrapassarem 100/dia  
**Nome:** [MOFU][ABO] PowerMind Remarketing Site [08-06]  
**Objetivo:** Conversões → Compra  
**Orçamento:** R$40/dia  
**Público:** Visitantes do site nos últimos 30 dias que não compraram  

**Criativos (2 anúncios):**

| Anúncio | Copy principal | Formato |
|---|---|---|
| [MOFU-01] Sem Crash | "Não é energia emprestada. É energia construída." | Estático comparativo |
| [MOFU-02] Depoimento Real | Print de depoimento + imagem produto | Estático |

---

### CAMPANHA 4: BOFU Ampliado — Criar na semana 3
**Condição para ativar:** quando volume de checkouts > 20/semana  
**Nome:** [BOFU-2][ABO] PowerMind Abandono 14d [15-06]  
**Objetivo:** Conversões → Compra  
**Orçamento:** R$30/dia  
**Público:** Checkout iniciado nos últimos 14 dias (amplia janela do BOFU atual de 7d)  
**Criativos:** reaproveitar os do BOFU atual com copy de urgência ("Ainda está pensando?")

---

## ORÇAMENTO POR SEMANA

| Semana | BOFU atual | TOFU v2 | MOFU | BOFU-2 | Total/dia |
|---|---|---|---|---|---|
| Semana 1 (01–07/06) | manter | R$80 | — | — | ~R$110 |
| Semana 2 (08–14/06) | manter | R$80 | R$40 | — | ~R$150 |
| Semana 3 (15–21/06) | manter | R$80 | R$40 | R$30 | ~R$180 |
| Semana 4 (22–30/06) | escalar se ROAS ok | R$100 | R$40 | R$30 | ~R$200 |

---

## CRIATIVOS A PRODUZIR — JUNHO

### Prioridade 1 (até 05/06)
- [ ] **[DOR-06] A Tarde que Paralisa** — vídeo 9:16, 15–30s
  - Cena: mulher no computador às 14h, cabeça pesada
  - Fala: "Todo dia às 2 da tarde meu cérebro simplesmente desliga. Café não resolve mais."
  - Corte para PowerMind + resultado
  - Sem texto nos primeiros 3 segundos

- [ ] **[MOFU-01] Sem Crash** — estático
  - Visual: gráfico comparando energético (pico/queda) vs PowerMind (linha constante)
  - Copy: "Não é energia emprestada. É energia construída."
  - Rodapé: "30 dias de garantia · Parcele em 12x"

### Prioridade 2 (até 12/06)
- [ ] **[DOR-07] Testei 30 dias** — vídeo UGC
  - Mulher 30–45 anos, filmado no celular, tom honesto
  - Estrutura: Dia 1 / Dia 7 / Dia 30
  - Resultados honestos, sem exagero

- [ ] **[MOFU-02] Depoimento Real** — estático
  - Print de depoimento real de cliente
  - Imagem do produto ao lado
  - "30 dias de garantia · Parcele em 12x"

### Prioridade 3 (até 20/06)
- [ ] **[BOFU-copy] Ainda está pensando?** — estático
  - Para usar no BOFU-2
  - Copy direto: "Você começou a comprar e parou. A oferta ainda está aqui."
  - CTA: "Garantir agora →"

---

## REGRAS DE DECISÃO — JUNHO

| Métrica | Condição | Ação |
|---|---|---|
| CPA | < R$57 por 3 dias | Escalar orçamento 20–30% |
| CPA | ≥ R$78 | Manter, revisar criativos |
| CTR | < 1,5% por 3 dias | Pausar criativo, testar novo ângulo |
| CPM | > R$65 | Revisar segmentação (possível saturação) |
| ROAS | < 2,0x por 7 dias | Reunião de diagnóstico |
| ROAS | > 5x por 3 dias | Escalar 30% no dia seguinte |
| Compras/dia | ≥ 5 por 5 dias | Avançar para Fase 2 (R$400/dia) |

---

## CHECKLIST SEMANAL (toda segunda-feira)

- [ ] Exportar relatório Meta Ads (CPA, ROAS, CTR, CPM, compras/dia)
- [ ] Calcular médias da semana — comparar com metas
- [ ] Identificar criativo vencedor e criativo mais fraco
- [ ] Verificar volume de checkouts iniciados no TOFU
- [ ] Decisão: escalar / pausar / testar novo criativo
- [ ] Atualizar dashboard PowerMind com novos lançamentos
- [ ] Verificar se MOFU/BOFU-2 atingiram condição de ativação

---

## METAS POR SEMANA

| Semana | Compras/dia alvo | ROAS alvo | CPA alvo |
|---|---|---|---|
| Semana 1 | 2–3 | > 2,5x | < R$90 |
| Semana 2 | 3–4 | > 3,0x | < R$82 |
| Semana 3 | 4–5 | > 3,5x | < R$78 |
| Semana 4 | 5+ | > 3,5x | < R$78 |

---

## AÇÃO IMEDIATA (hoje, 01/06)

- [ ] Pausar "Anuncio 3 - Criativo Pendente" (CPM R$171,85)
- [ ] Criar campanha [TOFU][CBO] com objetivo Compra (não IC)
- [ ] Duplicar [DOR-05] Mente Não Para como primeiro anúncio do TOFU v2
- [ ] Iniciar briefing do vídeo [DOR-06] A Tarde que Paralisa

---

*Plano gerado em 01/06/2026 — revisar e ajustar semanalmente*
