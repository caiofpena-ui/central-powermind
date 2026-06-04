#!/usr/bin/env python3
"""
DRE Diário PowerMind
Puxa dados reais de Yampi + Meta Ads e calcula resultado financeiro do dia.
"""
import urllib.request
import urllib.parse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# ─── Configurações ──────────────────────────────────────────────────────────
ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")

def load_env():
    vals = {}
    try:
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return vals

env = load_env()

META_TOKEN    = env.get("META_TOKEN", "")
YAMPI_ALIAS   = env.get("YAMPI_ALIAS", "powermind")
YAMPI_TOKEN   = env.get("YAMPI_TOKEN", "")
YAMPI_SECRET  = env.get("YAMPI_SECRET", "")
AD_ACCOUNT    = "act_4170730686474512"

# ─── Parâmetros financeiros ──────────────────────────────────────────────────
MIXER_CUSTO = 12.00  # brinde na compra de 2+ pacotes (cupom COMPROU GANHOU)
CMV = {1: 37.00, 2: 74.00 + MIXER_CUSTO, 3: 111.00 + MIXER_CUSTO, 6: 222.00 + MIXER_CUSTO}
YAMPI_FEE     = 0.025   # 2.5% por pedido
GATEWAY_CARD  = 0.0499  # 4.99% cartão (Appmax — cliente paga juros parcelamento)
GATEWAY_PIX   = 0.010   # 1.0% PIX (Appmax)
IMPOSTO       = 0.10    # 10% imposto sobre receita bruta

# Custos fixos mensais (confirmados em 16/05/2026)
FIXED_COSTS_MONTHLY = {
    "mayara":       500.00,  # assistente — R$500/mês fixo
    "hostinger":     49.99,  # hospedagem
    "dominio":       29.99,  # domínio site
}
FIXED_TOTAL_MONTHLY = sum(FIXED_COSTS_MONTHLY.values())  # R$ 579,98/mês
FIXED_DAILY         = FIXED_TOTAL_MONTHLY / 30           # R$ 19,33/dia

# ─── Data alvo (padrão = ontem) ─────────────────────────────────────────────
if len(sys.argv) > 1:
    target_date = sys.argv[1]  # formato YYYY-MM-DD
else:
    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

print(f"\n{'='*56}")
print(f"  DRE PowerMind — {target_date}")
print(f"{'='*56}")

# ─── 1. Yampi: pedidos do dia ────────────────────────────────────────────────
def yampi_get(path, params={}):
    params_str = urllib.parse.urlencode(params)
    url = f"https://api.dooki.com.br/v2/{YAMPI_ALIAS}/{path}?{params_str}"
    req = urllib.request.Request(url, headers={
        "User-Token":      YAMPI_TOKEN,
        "User-Secret-Key": YAMPI_SECRET,
        "Accept":          "application/json",
    })
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"data": [], "meta": {"pagination": {"total": 0}}}

# Puxa todos pedidos paginados
all_orders = []
page = 1
while True:
    resp = yampi_get("orders", {"page": page, "limit": 100,
                                "include": "transactions,items"})
    orders = resp.get("data", [])
    if not orders:
        break
    # Filtra pelo dia alvo
    day_orders = [o for o in orders
                  if o.get("created_at", {}).get("date", "")[:10] == target_date]
    all_orders.extend(day_orders)
    # Se o primeiro pedido da página já é de dia anterior, para
    last_date = orders[-1].get("created_at", {}).get("date", "")[:10]
    if last_date < target_date:
        break
    page += 1

# ─── 2. Processar pedidos ────────────────────────────────────────────────────
receita_bruta   = 0.0
cmv_total       = 0.0
taxa_gateway    = 0.0
taxa_yampi      = 0.0
pedidos_cartao  = 0
pedidos_pix     = 0
pedidos_outros  = 0
qtd_pedidos     = 0
devolucoes      = 0.0

STATUS_VALIDOS = {"paid", "approved", "complete", "delivered", "on_carriage"}

for order in all_orders:
    # status vem em order.status.data.alias
    status_obj = order.get("status", {})
    if isinstance(status_obj, dict) and "data" in status_obj:
        status = status_obj["data"].get("alias", "")
    else:
        status = status_obj.get("alias", "")
    if status not in STATUS_VALIDOS:
        continue

    valor = float(order.get("value_total") or order.get("buyer_value_total") or 0)
    if valor <= 0:
        continue

    qtd_pedidos   += 1
    receita_bruta += valor

    # Gateway
    payment = ""
    txs = order.get("transactions", {}).get("data", [])
    if txs:
        pm = txs[0].get("payment_method", {})
        payment = (pm.get("alias", "") or pm.get("method", "") or "") if isinstance(pm, dict) else str(pm)

    if "pix" in payment.lower():
        taxa_gateway += valor * GATEWAY_PIX
        pedidos_pix  += 1
    elif any(x in payment.lower() for x in ["credit", "card", "cartao", "crédito"]):
        taxa_gateway  += valor * GATEWAY_CARD
        pedidos_cartao += 1
    else:
        taxa_gateway   += valor * GATEWAY_CARD
        pedidos_outros += 1

    taxa_yampi += valor * YAMPI_FEE

    # CMV — conta pacotes pelos itens
    items = order.get("items", {}).get("data", [])
    total_pacotes = sum(int(i.get("quantity", 1)) for i in items) if items else 1
    cmv_total += CMV.get(total_pacotes, total_pacotes * 37.00)

receita_liquida       = receita_bruta - devolucoes
imposto_total         = receita_bruta * IMPOSTO
custos_variaveis      = cmv_total + taxa_gateway + taxa_yampi + imposto_total
margem_contribuicao   = receita_liquida - custos_variaveis
margem_pct            = (margem_contribuicao / receita_liquida * 100) if receita_liquida > 0 else 0

# ─── 3. Meta Ads: gasto do dia ──────────────────────────────────────────────
gasto_ads = 0.0
try:
    params = urllib.parse.urlencode({
        "access_token": META_TOKEN,
        "fields":       "spend",
        "time_range":   json.dumps({"since": target_date, "until": target_date}),
        "level":        "account",
    })
    url = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT}/insights?{params}"
    with urllib.request.urlopen(url) as r:
        meta_data = json.loads(r.read())
        insights = meta_data.get("data", [])
        if insights:
            gasto_ads = float(insights[0].get("spend", 0) or 0)
except Exception as e:
    gasto_ads = 0.0
    print(f"  ⚠️  Meta Ads: {e}")

# ─── 4. Resultado final ──────────────────────────────────────────────────────
lucro_operacional = margem_contribuicao - gasto_ads - FIXED_DAILY
roas_real = (receita_liquida / gasto_ads) if gasto_ads > 0 else 0
cpa_real  = (gasto_ads / qtd_pedidos) if qtd_pedidos > 0 else 0
ticket_medio = (receita_bruta / qtd_pedidos) if qtd_pedidos > 0 else 0

# Breakeven: quantos pedidos para cobrir ads + fixo
# Usando margem média por pedido
margem_por_pedido = (margem_contribuicao / qtd_pedidos) if qtd_pedidos > 0 else 96.62
meta_diaria_ads = gasto_ads + FIXED_DAILY
breakeven_pedidos = (meta_diaria_ads / margem_por_pedido) if margem_por_pedido > 0 else 0

# ─── 5. Exibir DRE ──────────────────────────────────────────────────────────
def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(v): return f"{v:.1f}%"

print(f"\n📦 PEDIDOS")
print(f"  Total válidos:       {qtd_pedidos}")
print(f"  Cartão:              {pedidos_cartao + pedidos_outros}  |  PIX: {pedidos_pix}")
print(f"  Ticket médio:        {fmt(ticket_medio)}")

print(f"\n💰 RECEITA")
print(f"  Receita bruta:       {fmt(receita_bruta)}")
print(f"  Devoluções:          {fmt(devolucoes)}")
print(f"  Receita líquida:     {fmt(receita_liquida)}")

print(f"\n📉 CUSTOS VARIÁVEIS")
print(f"  CMV (produto):       {fmt(cmv_total)}")
print(f"  Taxa gateway:        {fmt(taxa_gateway)}")
print(f"  Taxa Yampi (2.5%):   {fmt(taxa_yampi)}")
print(f"  Imposto (10%):       {fmt(imposto_total)}")
print(f"  TOTAL variável:      {fmt(custos_variaveis)}")

print(f"\n✅ MARGEM DE CONTRIBUIÇÃO")
print(f"  Valor:               {fmt(margem_contribuicao)}  ({pct(margem_pct)})")

print(f"\n📣 META ADS")
print(f"  Gasto do dia:        {fmt(gasto_ads)}")

print(f"\n🏠 CUSTOS FIXOS (rateio diário)")
print(f"  Total fixos/dia:     {fmt(FIXED_DAILY)}")
if FIXED_DAILY == 0:
    print(f"  ⚠️  Preencher custos fixos no script")

print(f"\n{'─'*40}")
status_icon = "🟢" if lucro_operacional >= 0 else "🔴"
print(f"  {status_icon} RESULTADO DO DIA:    {fmt(lucro_operacional)}")
print(f"{'─'*40}")

print(f"\n📊 KPIs")
print(f"  ROAS real:           {roas_real:.2f}x")
print(f"  CPA real:            {fmt(cpa_real)}")
print(f"  Margem contrib.:     {pct(margem_pct)}")
print(f"  Breakeven (pedidos): {breakeven_pedidos:.1f} pedidos/dia para cobrir ads")
print(f"\n{'='*56}\n")

# ─── 6. Salvar log JSON ──────────────────────────────────────────────────────
log_dir = os.path.join(os.path.dirname(__file__), "historico")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"dre_{target_date}.json")

log_data = {
    "data": target_date,
    "pedidos": qtd_pedidos,
    "ticket_medio": round(ticket_medio, 2),
    "receita_bruta": round(receita_bruta, 2),
    "receita_liquida": round(receita_liquida, 2),
    "cmv": round(cmv_total, 2),
    "taxa_gateway": round(taxa_gateway, 2),
    "taxa_yampi": round(taxa_yampi, 2),
    "imposto": round(imposto_total, 2),
    "margem_contribuicao": round(margem_contribuicao, 2),
    "margem_pct": round(margem_pct, 1),
    "gasto_ads": round(gasto_ads, 2),
    "fixos_dia": round(FIXED_DAILY, 2),
    "resultado": round(lucro_operacional, 2),
    "roas_real": round(roas_real, 2),
    "cpa_real": round(cpa_real, 2),
}

with open(log_path, "w") as f:
    json.dump(log_data, f, indent=2, ensure_ascii=False)
print(f"💾 Log salvo: {log_path}")
