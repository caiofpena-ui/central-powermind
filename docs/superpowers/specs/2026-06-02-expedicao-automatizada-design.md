# PowerMind — Sistema de Expedição Automatizada
**Data:** 02/06/2026  
**Status:** Aprovado  
**Autor:** Caio + Claude  

---

## Contexto

Caio opera o PowerMind sozinho em casa. Com o crescimento das vendas (~5-10 pedidos/dia), o processo de despacho precisa ser centralizado no dashboard existente (localhost:8080) e reduzido ao mínimo de cliques possível.

**Plataforma de e-commerce:** Yampi  
**Agregador de fretes:** Melhor Envio (gratuito, desconto de 30-60% vs. balcão Correios)  
**Entrega física:** Caio leva pessoalmente até agência Correios ou ponto Jadlog  

---

## Objetivo

Ao abrir o dashboard, Caio deve conseguir visualizar todos os pedidos pagos pendentes de despacho, cotar o frete com 3 opções (mais barata pré-selecionada), gerar todas as etiquetas com 1 clique, imprimir e ir ao Correios — em menos de 2 minutos por lote.

---

## Arquitetura

### Componentes

```
Dashboard (localhost:8080)
    ↕ HTTP
server.py (Python HTTPServer)
    ↕ HTTPS
Yampi API          Melhor Envio API
(pedidos/status)   (cotação/etiqueta)
```

### Fluxo completo

1. **Monitoramento automático (launchd, a cada 10 min)**
   - Script `monitor_pedidos.py` busca pedidos com `status_id=3` na Yampi
   - Se encontrar novos: notificação Mac via `osascript`
   - Mensagem: "🛍️ Novo pedido! {nome} · {kit} · {cidade}"

2. **Dashboard → aba 🚚 Expedição**
   - Lista todos os pedidos com `status_id=3` (Pgto Aprovado)
   - Colunas: nº pedido, cliente, kit, cidade/UF, peso estimado
   - Botões: `[📦 Etiquetar]` por pedido ou `[🚀 Despachar Todas]` em lote

3. **Cotação de frete (modal)**
   - Ao clicar Etiquetar: chama `/api/expedicao/cotar` com CEP destino + peso + dimensões
   - Exibe top 3 opções ordenadas por preço
   - Mais barata pré-selecionada (radio button)
   - Usuário pode trocar antes de confirmar

4. **Geração de etiqueta**
   - Chama `/api/expedicao/gerar-etiqueta`
   - server.py chama Melhor Envio: criar carrinho → comprar → gerar PDF
   - PDF abre em nova aba automaticamente
   - Yampi atualizado: `status_id=8` (Enviado) + `tracking_code` salvo

5. **Despachar Todas (lote)**
   - Chama `/api/expedicao/despachar-todas`
   - Itera todos os pedidos pendentes
   - Para cada um: cota → seleciona mais barata → gera etiqueta
   - Abre todos os PDFs de uma vez para impressão em lote
   - Atualiza todos os pedidos na Yampi simultaneamente

---

## Rotas Novas no server.py

### `GET /api/expedicao/pedidos`
Busca pedidos com `status_id=3` na Yampi com `include=customer,items,shipping_address`.

**Response:**
```json
{
  "pedidos": [
    {
      "numero": "12345",
      "yampi_id": 98765,
      "cliente": "Ana Silva",
      "email": "ana@email.com",
      "telefone": "11999999999",
      "cep": "01310100",
      "endereco": "Rua X, 123 - Bela Vista",
      "cidade": "São Paulo",
      "uf": "SP",
      "itens": "Kit 2x",
      "peso_g": 550,
      "altura_cm": 8,
      "largura_cm": 12,
      "comprimento_cm": 20,
      "valor": "274.00"
    }
  ]
}
```

### `POST /api/expedicao/cotar`
Consulta Melhor Envio para um pedido específico.

**Request:**
```json
{
  "cep_destino": "01310100",
  "peso_g": 550,
  "altura_cm": 8,
  "largura_cm": 12,
  "comprimento_cm": 20
}
```

**Response:**
```json
{
  "opcoes": [
    {
      "id": "j&t",
      "nome": "J&T Express",
      "preco": 13.90,
      "prazo_dias": 3,
      "recomendado": true
    },
    {
      "id": "jadlog-com",
      "nome": "Jadlog .com",
      "preco": 15.20,
      "prazo_dias": 4,
      "recomendado": false
    },
    {
      "id": "correios-pac",
      "nome": "Correios PAC",
      "preco": 18.50,
      "prazo_dias": 7,
      "recomendado": false
    }
  ]
}
```

### `POST /api/expedicao/gerar-etiqueta`
Gera etiqueta para um pedido com a transportadora escolhida.

**Request:**
```json
{
  "yampi_id": 98765,
  "numero_pedido": "12345",
  "service_id": "j&t",
  "cep_destino": "01310100",
  "nome_destinatario": "Ana Silva",
  "endereco_completo": "Rua X, 123 - Bela Vista - São Paulo/SP",
  "peso_g": 550,
  "altura_cm": 8,
  "largura_cm": 12,
  "comprimento_cm": 20
}
```

**Response:**
```json
{
  "ok": true,
  "tracking_code": "JT123456789BR",
  "label_url": "https://melhorenvio.com.br/...",
  "preco_pago": 13.90
}
```

**Ações internas:**
1. `POST /v2/me/cart` — adiciona ao carrinho Melhor Envio
2. `POST /v2/me/shipment/checkout` — compra (debita saldo)
3. `POST /v2/me/orders/{id}/generate-label` — gera etiqueta
4. `GET /v2/me/orders/{id}/print` — obtém URL do PDF
5. `PUT /api/yampi/orders/{yampi_id}` — atualiza status + tracking na Yampi

### `POST /api/expedicao/despachar-todas`
Processa todos os pedidos pendentes em lote com a opção mais barata.

**Response:**
```json
{
  "processados": 3,
  "etiquetas": [
    {"numero": "12345", "tracking": "JT123456789BR", "label_url": "..."},
    {"numero": "12346", "tracking": "JT987654321BR", "label_url": "..."}
  ],
  "total_gasto": 42.70,
  "erros": []
}
```

---

## Dimensões por Kit

| Kit | Peso | Comprimento | Largura | Altura |
|---|---|---|---|---|
| 1 Pacote | 300g | 15cm | 10cm | 5cm |
| Kit 2x (Power Duo) | 550g | 20cm | 12cm | 8cm |
| Kit 3x | 800g | 25cm | 15cm | 10cm |
| Kit 6x | 1.500g | 30cm | 20cm | 15cm |

*Dimensões são aproximadas. Ajustar após primeira pesagem real do produto embalado.*

---

## Monitor de Pedidos Novos

**Arquivo:** `financeiro/monitor_pedidos.py`  
**Execução:** launchd a cada 10 minutos (`com.powermind.monitor_pedidos.plist`)  
**Lógica:**
- Busca pedidos `status_id=3` na Yampi
- Compara com `pedidos_notificados.json` (cache local)
- Para cada pedido novo: `osascript` dispara notificação Mac
- Salva IDs notificados para não repetir

---

## Configuração Melhor Envio (setup único)

### Passos para o usuário:
1. Criar conta grátis em [melhorenvio.com.br](https://melhorenvio.com.br)
2. Preencher endereço de origem (endereço de casa/despacho do Caio)
3. Ir em **Integrações → Tokens** → gerar token de produção
4. Adicionar ao `.env`: `MELHOR_ENVIO_TOKEN=seu_token_aqui`
5. Carregar saldo inicial: **R$300** (cobre ~15-20 envios)

### Variável de ambiente nova:
```
MELHOR_ENVIO_TOKEN=eyJ0eXAiOiJKV1Qi...
```

### Remetente (fixo no código, configurado uma vez):
```python
REMETENTE = {
    "name": "PowerMind",
    "phone": "83999999999",   # telefone do Caio
    "email": "caiofpena@icloud.com",
    "document": "000.000.000-00",  # CPF do Caio
    "address": "Rua ...",
    "complement": "",
    "number": "123",
    "district": "Bairro",
    "city": "Cidade",
    "country_id": "BR",
    "postal_code": "58000000",
    "note": ""
}
```
*Endereço completo do Caio será preenchido durante implementação.*

---

## Interface — Aba Expedição

### Estado inicial (pedidos pendentes):
```
🚚 Expedição                    [🖨️ Imprimir Todas] [🚀 Despachar Todas]
─────────────────────────────────────────────────────────────────────
⚠️ 3 pedidos aguardando despacho · Saldo Melhor Envio: R$ 287,10

#     Cliente          Kit        Cidade/UF    Peso    Ação
1234  Ana Silva        Kit 2x     São Paulo/SP  550g   [📦 Etiquetar]
1235  João Costa       1 Pacote   Rio de Jan/RJ 300g   [📦 Etiquetar]
1236  Maria Souza      Kit 3x     Belo Hor/MG   800g   [📦 Etiquetar]
```

### Modal de cotação:
```
Cotação — Ana Silva | CEP 01310-100 | Kit 2x (550g)
──────────────────────────────────────────────────
✅ J&T Express      R$ 13,90   3 dias úteis   ← pré-selecionado
○  Jadlog .com      R$ 15,20   4 dias úteis
○  Correios PAC     R$ 18,50   7 dias úteis
──────────────────────────────────────────────────
                    [Cancelar]  [✅ Gerar Etiqueta]
```

### Após gerar:
- PDF abre em nova aba automaticamente
- Linha do pedido vira: `✅ 1234 · Ana Silva · JT123456789BR · [🖨️ Reimprimir]`

---

## Tratamento de Erros

| Erro | Causa | Ação |
|---|---|---|
| Saldo insuficiente | Melhor Envio sem créditos | Alerta vermelho: "Saldo insuficiente. Recarregue em melhorenvio.com.br" |
| CEP não atendido | Transportadora não cobre região | Remove da lista, exibe próxima opção |
| Token inválido | MELHOR_ENVIO_TOKEN expirado | Alerta: "Token Melhor Envio inválido. Acesse Configurações → Tokens" |
| Yampi offline | API Yampi fora | Etiqueta gerada mas status não atualizado — botão "Tentar novamente" |
| Pedido já despachado | Duplo clique | Ignora silenciosamente, não gera segunda etiqueta |

---

## Arquivos a Criar/Modificar

| Arquivo | Ação | Descrição |
|---|---|---|
| `server.py` | Modificar | Adicionar 4 rotas GET/POST de expedição |
| `dashboard.html` | Modificar | Adicionar aba 🚚 Expedição com UI completa |
| `monitor_pedidos.py` | Criar | Script de monitoramento a cada 10 min |
| `.env` | Modificar | Adicionar `MELHOR_ENVIO_TOKEN` |
| `pedidos_notificados.json` | Criar (auto) | Cache de pedidos já notificados |
| `com.powermind.monitor_pedidos.plist` | Criar | launchd para monitor automático |

---

## Estimativa de Economia

Com ~5 pedidos/dia e economia média de R$10/envio vs. balcão Correios:
- **R$50/dia** de economia
- **R$1.500/mês** de economia
- ROI do sistema: imediato no primeiro dia de uso

---

*Spec gerada em 02/06/2026 — pronta para implementação*
