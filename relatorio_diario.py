#!/usr/bin/env python3
"""
Relatório diário Meta Ads — PowerMind Brasil
Conta: act_4170730686474512

Filtros disponíveis:
  --data       YYYY-MM-DD              (padrão: hoje)
  --periodo    YYYY-MM-DD:YYYY-MM-DD   (intervalo de datas)
  --nivel      account campaign adset ad  (pode combinar vários)
  --status     ok | abaixo | sem-compra  (filtra por desempenho)
  --campanha   TEXTO                   (filtra pelo nome da campanha)
  --ordenar    roas|cpa|spend|ctr|compras (critério de ordenação)
  --top        N                       (exibe apenas os top N por seção)
  --sem-zero                           (oculta linhas com R$0 gasto)

Exemplos:
  python relatorio_diario.py
  python relatorio_diario.py --data 2026-05-20
  python relatorio_diario.py --nivel campanha adset --status abaixo
  python relatorio_diario.py --ordenar cpa --top 5 --sem-zero
  python relatorio_diario.py --campanha BOFU --nivel adset ad
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ─────────────────────────────────────────────
# FILTROS — argparse
# ─────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Relatório diário Meta Ads — PowerMind",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("--data",    metavar="YYYY-MM-DD",             help="Data específica (padrão: hoje)")
parser.add_argument("--periodo", metavar="YYYY-MM-DD:YYYY-MM-DD",  help="Intervalo de datas (ex: 2026-05-14:2026-05-20)")
parser.add_argument("--nivel",   nargs="+",
                    choices=["account","conta","campaign","campanha","adset","ad"],
                    metavar="NIVEL",
                    help="Níveis a exibir: account campaign adset ad (pode combinar)")
parser.add_argument("--status",  choices=["ok","abaixo","sem-compra"],
                    help="Filtrar por status: ok | abaixo | sem-compra")
parser.add_argument("--campanha", metavar="TEXTO",                 help="Filtrar pelo nome da campanha (busca parcial)")
parser.add_argument("--ordenar", choices=["roas","cpa","spend","ctr","compras","impressoes"],
                    default="spend",
                    help="Ordenar resultados por campo (padrão: spend)")
parser.add_argument("--top",     type=int, metavar="N",            help="Exibir apenas os top N por seção")
parser.add_argument("--sem-zero", action="store_true",             help="Ocultar linhas com R$0,00 gasto")
parser.add_argument("--resumo",  action="store_true",              help="Mostrar apenas o nível conta + diagnóstico")

args = parser.parse_args()

# ─── Configurar período ───────────────────────
if args.periodo:
    partes = args.periodo.split(":")
    DATE_SINCE = partes[0].strip()
    DATE_UNTIL = partes[1].strip() if len(partes) > 1 else partes[0].strip()
elif args.data:
    DATE_SINCE = DATE_UNTIL = args.data.strip()
else:
    DATE_SINCE = DATE_UNTIL = datetime.now().strftime("%Y-%m-%d")

DATE = DATE_SINCE  # compatibilidade com código legado

# ─── Filtros ativos ───────────────────────────
NIVEIS_ATIVOS = set()
if args.nivel:
    mapa = {"conta":"account","account":"account","campanha":"campaign",
            "campaign":"campaign","adset":"adset","ad":"ad"}
    NIVEIS_ATIVOS = {mapa.get(n, n) for n in args.nivel}
else:
    NIVEIS_ATIVOS = {"account","campaign","adset","ad"}

if args.resumo:
    NIVEIS_ATIVOS = {"account"}

FILTRO_STATUS   = args.status
FILTRO_CAMPANHA = (args.campanha or "").lower()
ORDENAR_POR     = args.ordenar
TOP_N           = args.top
SEM_ZERO        = args.sem_zero

TIME_RANGE = json.dumps({"since": DATE_SINCE, "until": DATE_UNTIL})

# Token — lê do .env automaticamente (META_TOKEN)
TOKEN = os.getenv("META_TOKEN") or os.getenv("META_ACCESS_TOKEN", "")

BASE_URL = "https://graph.facebook.com/v19.0"
ACCOUNT_ID = "act_4170730686474512"

FIELDS = "spend,impressions,reach,clicks,ctr,cpc,cpm,actions,action_values"
ROAS_META = 2.5
CPA_META   = 57.0

# ─────────────────────────────────────────────
# HELPERS DE FILTRO
# ─────────────────────────────────────────────
def _sort_key(row):
    m = {"roas":"roas","cpa":"cpa","spend":"spend","ctr":"ctr",
         "compras":"purchases","impressoes":"impressions"}
    field = m.get(ORDENAR_POR, "spend")
    val = row.get(field, 0) or 0
    # CPA: menor é melhor → inverte para ordenação decrescente
    return -val if field != "cpa" else val

def aplicar_filtros(rows, tipo="campaign"):
    """Filtra e ordena uma lista de dicionários de relatório."""
    resultado = list(rows)

    # Filtro: sem gasto zero
    if SEM_ZERO:
        resultado = [r for r in resultado if (r.get("spend") or 0) > 0]

    # Filtro: nome de campanha
    if FILTRO_CAMPANHA:
        campo = "campaign" if tipo in ("adset","ad") else "name"
        resultado = [r for r in resultado
                     if FILTRO_CAMPANHA in (r.get(campo,"") or r.get("name","")).lower()]

    # Filtro: status de desempenho
    if FILTRO_STATUS:
        def match(r):
            p = r.get("purchases", 0) or 0
            roas = r.get("roas", 0) or 0
            cpa  = r.get("cpa", 0) or 0
            if FILTRO_STATUS == "sem-compra":
                return p == 0 and (r.get("spend") or 0) > 0
            elif FILTRO_STATUS == "ok":
                return p > 0 and roas >= ROAS_META and cpa <= CPA_META
            elif FILTRO_STATUS == "abaixo":
                return (p > 0 and (roas < ROAS_META or cpa > CPA_META)) or p == 0
        resultado = [r for r in resultado if match(r)]

    # Ordenação
    resultado.sort(key=_sort_key)

    # Top N
    if TOP_N and TOP_N > 0:
        resultado = resultado[:TOP_N]

    return resultado

def label_filtros():
    """Retorna string descritiva dos filtros ativos para o cabeçalho."""
    parts = []
    if DATE_SINCE != DATE_UNTIL:
        parts.append(f"Período: {DATE_SINCE} → {DATE_UNTIL}")
    else:
        parts.append(f"Data: {DATE_SINCE}")
    if FILTRO_STATUS:    parts.append(f"Status: {FILTRO_STATUS}")
    if FILTRO_CAMPANHA:  parts.append(f"Campanha: '{args.campanha}'")
    if SEM_ZERO:         parts.append("Sem R$0")
    if TOP_N:            parts.append(f"Top {TOP_N}")
    parts.append(f"Ordenado por: {ORDENAR_POR}")
    return " | ".join(parts)

def get_purchases(actions):
    """Extrai compras dos campos de ações."""
    if not actions:
        return 0
    total = 0
    for a in actions:
        if a.get("action_type") in ("purchase", "offsite_conversion.fb_pixel_purchase"):
            total += float(a.get("value", 0))
    return total

def get_purchase_value(action_values):
    """Extrai valor de compras dos campos de action_values."""
    if not action_values:
        return 0.0
    total = 0.0
    for a in action_values:
        if a.get("action_type") in ("purchase", "offsite_conversion.fb_pixel_purchase"):
            total += float(a.get("value", 0))
    return total

def calc_metrics(row):
    spend = float(row.get("spend", 0) or 0)
    purchases = get_purchases(row.get("actions"))
    revenue = get_purchase_value(row.get("action_values"))
    roas = revenue / spend if spend > 0 else 0
    cpa = spend / purchases if purchases > 0 else 0
    return spend, purchases, revenue, roas, cpa

def status_roas(roas):
    return "OK" if roas >= ROAS_META else "ABAIXO"

def status_cpa(cpa, purchases):
    if purchases == 0:
        return "SEM COMPRA"
    return "OK" if cpa <= CPA_META else "ACIMA"

def fetch_insights(params):
    """Faz paginação completa retornando todos os registros."""
    url = f"{BASE_URL}/{ACCOUNT_ID}/insights"
    all_data = []
    params["access_token"] = TOKEN
    params["limit"] = 500

    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"ERRO API: {resp.status_code}")
        print(resp.text)
        return None, resp.json()

    result = resp.json()
    data = result.get("data", [])
    all_data.extend(data)

    # Paginação completa
    paging = result.get("paging", {})
    while paging.get("next"):
        next_url = paging["next"]
        resp = requests.get(next_url)
        if resp.status_code != 200:
            break
        result = resp.json()
        all_data.extend(result.get("data", []))
        paging = result.get("paging", {})

    return all_data, None

def fetch_ads_with_creative():
    """Busca ads com insights + tipo de criativo via paginação completa."""
    # Primeiro busca insights no nível ad
    params = {
        "level": "ad",
        "fields": FIELDS,
        "time_range": TIME_RANGE,
        "access_token": TOKEN,
        "limit": 500,
    }
    url = f"{BASE_URL}/{ACCOUNT_ID}/insights"
    all_insights = []

    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"ERRO API (ad insights): {resp.status_code}")
        print(resp.text)
        return None, resp.json()

    result = resp.json()
    all_insights.extend(result.get("data", []))
    paging = result.get("paging", {})
    while paging.get("next"):
        next_url = paging["next"]
        resp2 = requests.get(next_url)
        if resp2.status_code != 200:
            break
        r2 = resp2.json()
        all_insights.extend(r2.get("data", []))
        paging = r2.get("paging", {})

    # Para cada ad único, busca o tipo de criativo
    ad_creatives = {}
    ad_ids = list({row["ad_id"] for row in all_insights if "ad_id" in row})

    for ad_id in ad_ids:
        cr_url = f"{BASE_URL}/{ad_id}"
        cr_resp = requests.get(cr_url, params={
            "fields": "creative{object_type,name}",
            "access_token": TOKEN
        })
        if cr_resp.status_code == 200:
            cr_data = cr_resp.json()
            creative = cr_data.get("creative", {})
            ad_creatives[ad_id] = creative.get("object_type", "N/A")
        else:
            ad_creatives[ad_id] = "N/A"

    # Injeta tipo de criativo nos insights
    for row in all_insights:
        ad_id = row.get("ad_id", "")
        row["creative_type"] = ad_creatives.get(ad_id, "N/A")

    return all_insights, None

def fmt_brl(v):
    return f"R${v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(v):
    return f"{v:.2f}%"

def fmt_x(v):
    return f"{v:.2f}x"

# ─────────────────────────────────────────────
# EXECUÇÃO
# ─────────────────────────────────────────────
print("=" * 65)
print(f"RELATÓRIO META ADS — POWERMIND BRASIL")
print(f"{label_filtros()}")
print(f"Conta: {ACCOUNT_ID}")
print("=" * 65)

# ── 1. NÍVEL CONTA (sempre buscado para diagnóstico) ─────
print("\nBuscando dados nível CONTA...")
conta_data, err = fetch_insights({
    "level": "account",
    "fields": FIELDS,
    "time_range": TIME_RANGE,
})
if err:
    print(f"ERRO CONTA: {err}")
    sys.exit(1)

# ── 2. NÍVEL CAMPANHA ──────────────────────
camp_data = []
if "campaign" in NIVEIS_ATIVOS:
    print("Buscando dados nível CAMPANHA...")
    camp_data, err = fetch_insights({
        "level": "campaign",
        "fields": FIELDS + ",campaign_name,campaign_id",
        "time_range": TIME_RANGE,
    })
    if err:
        print(f"ERRO CAMPANHA: {err}")
        sys.exit(1)

# ── 3. NÍVEL AD SET ────────────────────────
adset_data = []
if "adset" in NIVEIS_ATIVOS:
    print("Buscando dados nível AD SET...")
    adset_data, err = fetch_insights({
        "level": "adset",
        "fields": FIELDS + ",adset_name,adset_id,campaign_name",
        "time_range": TIME_RANGE,
    })
    if err:
        print(f"ERRO ADSET: {err}")
        sys.exit(1)

# ── 4. NÍVEL AD + CRIATIVO ─────────────────
ad_data = []
if "ad" in NIVEIS_ATIVOS:
    print("Buscando dados nível AD (com tipo de criativo)...")
    ad_data, err = fetch_ads_with_creative()
    if err:
        print(f"ERRO AD: {err}")
        sys.exit(1)

# ─────────────────────────────────────────────
# PROCESSAMENTO E EXIBIÇÃO
# ─────────────────────────────────────────────

# CONTA
print("\n" + "=" * 60)
print("1. VISÃO GERAL DA CONTA")
print("=" * 60)
conta_rows = conta_data or []
conta_report = []
for row in conta_rows:
    spend, purchases, revenue, roas, cpa = calc_metrics(row)
    impressions = int(row.get("impressions", 0) or 0)
    reach = int(row.get("reach", 0) or 0)
    clicks = int(row.get("clicks", 0) or 0)
    ctr = float(row.get("ctr", 0) or 0)
    cpc = float(row.get("cpc", 0) or 0)
    cpm = float(row.get("cpm", 0) or 0)

    print(f"  Investimento:  {fmt_brl(spend)}")
    print(f"  Impressoes:    {impressions:,}")
    print(f"  Alcance:       {reach:,}")
    print(f"  Cliques:       {clicks:,}")
    print(f"  CTR:           {fmt_pct(ctr)}")
    print(f"  CPC:           {fmt_brl(cpc)}")
    print(f"  CPM:           {fmt_brl(cpm)}")
    print(f"  Compras:       {purchases:.0f}")
    print(f"  Receita:       {fmt_brl(revenue)}")
    print(f"  ROAS:          {fmt_x(roas)}  [{status_roas(roas)}] (meta: {ROAS_META}x)")
    print(f"  CPA:           {fmt_brl(cpa)}  [{status_cpa(cpa, purchases)}] (meta: R${CPA_META:.0f})")

    conta_report.append({
        "spend": spend, "impressions": impressions, "reach": reach,
        "clicks": clicks, "ctr": ctr, "cpc": cpc, "cpm": cpm,
        "purchases": purchases, "revenue": revenue, "roas": roas, "cpa": cpa
    })

# CAMPANHA
camp_report = []
for row in (camp_data or []):
    spend, purchases, revenue, roas, cpa = calc_metrics(row)
    name = row.get("campaign_name", row.get("campaign_id", "N/A"))
    camp_report.append({
        "name": name, "spend": spend, "purchases": purchases,
        "revenue": revenue, "roas": roas, "cpa": cpa,
        "impressions": int(row.get("impressions", 0) or 0),
        "ctr": float(row.get("ctr", 0) or 0),
        "cpm": float(row.get("cpm", 0) or 0),
    })

if "campaign" in NIVEIS_ATIVOS:
    camp_filtrado = aplicar_filtros(camp_report, tipo="campaign")
    print("\n" + "=" * 65)
    print(f"2. NÍVEL CAMPANHA  [{len(camp_filtrado)} resultado(s)]")
    print("=" * 65)
    for r in camp_filtrado:
        print(f"\n  Campanha: {r['name']}")
        print(f"    Investimento: {fmt_brl(r['spend'])} | Compras: {r['purchases']:.0f} | Receita: {fmt_brl(r['revenue'])}")
        print(f"    ROAS: {fmt_x(r['roas'])} [{status_roas(r['roas'])}] | CPA: {fmt_brl(r['cpa'])} [{status_cpa(r['cpa'], r['purchases'])}]")
        print(f"    Impressoes: {r['impressions']:,} | CTR: {fmt_pct(r['ctr'])} | CPM: {fmt_brl(r['cpm'])}")
    if not camp_filtrado:
        print("  (nenhum resultado com os filtros aplicados)")

# AD SET
adset_report = []
for row in (adset_data or []):
    spend, purchases, revenue, roas, cpa = calc_metrics(row)
    name = row.get("adset_name", row.get("adset_id", "N/A"))
    camp = row.get("campaign_name", "")
    adset_report.append({
        "name": name, "campaign": camp, "spend": spend, "purchases": purchases,
        "revenue": revenue, "roas": roas, "cpa": cpa,
        "impressions": int(row.get("impressions", 0) or 0),
        "ctr": float(row.get("ctr", 0) or 0),
        "cpm": float(row.get("cpm", 0) or 0),
    })

if "adset" in NIVEIS_ATIVOS:
    adset_filtrado = aplicar_filtros(adset_report, tipo="adset")
    print("\n" + "=" * 65)
    print(f"3. NÍVEL AD SET  [{len(adset_filtrado)} resultado(s)]")
    print("=" * 65)
    for r in adset_filtrado:
        print(f"\n  Ad Set: {r['name']}")
        if r['campaign']:
            print(f"    Campanha: {r['campaign']}")
        print(f"    Investimento: {fmt_brl(r['spend'])} | Compras: {r['purchases']:.0f} | Receita: {fmt_brl(r['revenue'])}")
        print(f"    ROAS: {fmt_x(r['roas'])} [{status_roas(r['roas'])}] | CPA: {fmt_brl(r['cpa'])} [{status_cpa(r['cpa'], r['purchases'])}]")
        print(f"    Impressoes: {r['impressions']:,} | CTR: {fmt_pct(r['ctr'])} | CPM: {fmt_brl(r['cpm'])}")
    if not adset_filtrado:
        print("  (nenhum resultado com os filtros aplicados)")

# AD
ad_report = []
for row in (ad_data or []):
    spend, purchases, revenue, roas, cpa = calc_metrics(row)
    name = row.get("ad_name", row.get("ad_id", "N/A"))
    adset = row.get("adset_name", "")
    camp  = row.get("campaign_name", "")
    creative_type = row.get("creative_type", "N/A")
    ad_report.append({
        "name": name, "adset": adset, "campaign": camp,
        "creative_type": creative_type,
        "spend": spend, "purchases": purchases, "revenue": revenue,
        "roas": roas, "cpa": cpa,
        "impressions": int(row.get("impressions", 0) or 0),
        "ctr": float(row.get("ctr", 0) or 0),
        "cpm": float(row.get("cpm", 0) or 0),
    })

if "ad" in NIVEIS_ATIVOS:
    ad_filtrado = aplicar_filtros(ad_report, tipo="ad")
    print("\n" + "=" * 65)
    print(f"4. NÍVEL AD  [{len(ad_filtrado)} resultado(s)]  (tipo de criativo)")
    print("=" * 65)
    for r in ad_filtrado:
        print(f"\n  Ad: {r['name']}")
        if r['adset']:
            print(f"    Ad Set: {r['adset']}")
        print(f"    Tipo Criativo: {r['creative_type']}")
        print(f"    Investimento: {fmt_brl(r['spend'])} | Compras: {r['purchases']:.0f} | Receita: {fmt_brl(r['revenue'])}")
        print(f"    ROAS: {fmt_x(r['roas'])} [{status_roas(r['roas'])}] | CPA: {fmt_brl(r['cpa'])} [{status_cpa(r['cpa'], r['purchases'])}]")
        print(f"    Impressoes: {r['impressions']:,} | CTR: {fmt_pct(r['ctr'])} | CPM: {fmt_brl(r['cpm'])}")
    if not ad_filtrado:
        print("  (nenhum resultado com os filtros aplicados)")

# ─────────────────────────────────────────────
# DIAGNÓSTICO
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("DIAGNOSTICO EXECUTIVO")
print("=" * 60)

# Conta geral
if conta_report:
    c = conta_report[0]
    roas_ok = c["roas"] >= ROAS_META
    cpa_ok = c["cpa"] <= CPA_META if c["purchases"] > 0 else False
    print(f"\nConta: ROAS={fmt_x(c['roas'])} | CPA={fmt_brl(c['cpa'])} | Investimento={fmt_brl(c['spend'])}")
    if roas_ok and cpa_ok:
        print("  STATUS: Conta dentro das metas de ROAS e CPA.")
    elif c["purchases"] == 0:
        print("  STATUS: Sem compras registradas hoje. Verificar pixel e criativos.")
    else:
        issues = []
        if not roas_ok:
            issues.append(f"ROAS abaixo da meta ({fmt_x(c['roas'])} < {ROAS_META}x)")
        if not cpa_ok:
            issues.append(f"CPA acima da meta ({fmt_brl(c['cpa'])} > R${CPA_META:.0f})")
        print(f"  ATENCAO: {' | '.join(issues)}")

# Ad sets com problema
problemas_adset = [a for a in adset_report if a["roas"] < ROAS_META and a["purchases"] > 0]
adsets_sem_compra = [a for a in adset_report if a["purchases"] == 0 and a["spend"] > 0]

if problemas_adset:
    print(f"\nAd Sets abaixo da meta de ROAS ({ROAS_META}x):")
    for a in problemas_adset:
        print(f"  - {a['name']}: ROAS={fmt_x(a['roas'])} | CPA={fmt_brl(a['cpa'])} | Gasto={fmt_brl(a['spend'])}")

if adsets_sem_compra:
    print(f"\nAd Sets com gasto sem conversao:")
    for a in adsets_sem_compra:
        print(f"  - {a['name']}: Gasto={fmt_brl(a['spend'])} | 0 compras")

# Melhores e piores ads
ads_com_compra = [a for a in ad_report if a["purchases"] > 0]
if ads_com_compra:
    melhor = max(ads_com_compra, key=lambda x: x["roas"])
    pior = min(ads_com_compra, key=lambda x: x["roas"])
    print(f"\nMelhor Ad: {melhor['name']} (ROAS={fmt_x(melhor['roas'])}, CPA={fmt_brl(melhor['cpa'])}, Tipo: {melhor['creative_type']})")
    print(f"Pior Ad:   {pior['name']} (ROAS={fmt_x(pior['roas'])}, CPA={fmt_brl(pior['cpa'])}, Tipo: {pior['creative_type']})")

print("\n" + "=" * 60)

# ─────────────────────────────────────────────
# SALVAR RELATÓRIO .MD
# ─────────────────────────────────────────────

def md_table_conta(rows):
    lines = ["| Métrica | Valor | Meta | Status |", "|---------|-------|------|--------|"]
    for r in rows:
        lines.append(f"| Investimento | {fmt_brl(r['spend'])} | — | — |")
        lines.append(f"| Impressões | {r['impressions']:,} | — | — |")
        lines.append(f"| Alcance | {r['reach']:,} | — | — |")
        lines.append(f"| Cliques | {r['clicks']:,} | — | — |")
        lines.append(f"| CTR | {fmt_pct(r['ctr'])} | — | — |")
        lines.append(f"| CPC | {fmt_brl(r['cpc'])} | — | — |")
        lines.append(f"| CPM | {fmt_brl(r['cpm'])} | — | — |")
        lines.append(f"| Compras | {r['purchases']:.0f} | — | — |")
        lines.append(f"| Receita | {fmt_brl(r['revenue'])} | — | — |")
        lines.append(f"| ROAS | {fmt_x(r['roas'])} | ≥ 2.5x | {status_roas(r['roas'])} |")
        lines.append(f"| CPA | {fmt_brl(r['cpa'])} | ≤ R$57 | {status_cpa(r['cpa'], r['purchases'])} |")
    return "\n".join(lines)

def md_table_camp(rows):
    lines = ["| Campanha | Investimento | Compras | Receita | ROAS | Status ROAS | CPA | Status CPA | Impressões | CTR | CPM |",
             "|----------|-------------|---------|---------|------|-------------|-----|------------|-----------|-----|-----|"]
    for r in rows:
        lines.append(f"| {r['name']} | {fmt_brl(r['spend'])} | {r['purchases']:.0f} | {fmt_brl(r['revenue'])} | {fmt_x(r['roas'])} | {status_roas(r['roas'])} | {fmt_brl(r['cpa'])} | {status_cpa(r['cpa'], r['purchases'])} | {r['impressions']:,} | {fmt_pct(r['ctr'])} | {fmt_brl(r['cpm'])} |")
    return "\n".join(lines)

def md_table_adset(rows):
    lines = ["| Ad Set | Campanha | Investimento | Compras | Receita | ROAS | Status ROAS | CPA | Status CPA | Impressões | CTR | CPM |",
             "|--------|----------|-------------|---------|---------|------|-------------|-----|------------|-----------|-----|-----|"]
    for r in rows:
        lines.append(f"| {r['name']} | {r['campaign']} | {fmt_brl(r['spend'])} | {r['purchases']:.0f} | {fmt_brl(r['revenue'])} | {fmt_x(r['roas'])} | {status_roas(r['roas'])} | {fmt_brl(r['cpa'])} | {status_cpa(r['cpa'], r['purchases'])} | {r['impressions']:,} | {fmt_pct(r['ctr'])} | {fmt_brl(r['cpm'])} |")
    return "\n".join(lines)

def md_table_ad(rows):
    lines = ["| Ad | Ad Set | Tipo Criativo | Investimento | Compras | Receita | ROAS | Status ROAS | CPA | Status CPA | Impressões | CTR | CPM |",
             "|----|--------|--------------|-------------|---------|---------|------|-------------|-----|------------|-----------|-----|-----|"]
    for r in rows:
        lines.append(f"| {r['name']} | {r['adset']} | {r['creative_type']} | {fmt_brl(r['spend'])} | {r['purchases']:.0f} | {fmt_brl(r['revenue'])} | {fmt_x(r['roas'])} | {status_roas(r['roas'])} | {fmt_brl(r['cpa'])} | {status_cpa(r['cpa'], r['purchases'])} | {r['impressions']:,} | {fmt_pct(r['ctr'])} | {fmt_brl(r['cpm'])} |")
    return "\n".join(lines)

# Monta diagnóstico textual para o .md
diag_lines = []
if conta_report:
    c = conta_report[0]
    roas_ok = c["roas"] >= ROAS_META
    cpa_ok = c["cpa"] <= CPA_META if c["purchases"] > 0 else False
    if c["purchases"] == 0:
        diag_lines.append("- **Sem compras registradas** no dia. Verificar disparo do pixel e criativos ativos.")
    else:
        if not roas_ok:
            diag_lines.append(f"- ROAS da conta abaixo da meta: **{fmt_x(c['roas'])}** (meta: {ROAS_META}x). Receita insuficiente para o investimento realizado.")
        else:
            diag_lines.append(f"- ROAS da conta dentro da meta: **{fmt_x(c['roas'])}** >= {ROAS_META}x.")
        if not cpa_ok:
            diag_lines.append(f"- CPA acima do limite: **{fmt_brl(c['cpa'])}** (meta: R${CPA_META:.0f}). Custo por aquisição elevado.")
        else:
            diag_lines.append(f"- CPA dentro da meta: **{fmt_brl(c['cpa'])}** <= R${CPA_META:.0f}.")

if problemas_adset:
    diag_lines.append(f"\n**Ad Sets abaixo da meta de ROAS:**")
    for a in problemas_adset:
        diag_lines.append(f"- {a['name']}: ROAS={fmt_x(a['roas'])}, CPA={fmt_brl(a['cpa'])}, Gasto={fmt_brl(a['spend'])}")

if adsets_sem_compra:
    diag_lines.append(f"\n**Ad Sets com gasto sem conversão:**")
    for a in adsets_sem_compra:
        diag_lines.append(f"- {a['name']}: Gasto={fmt_brl(a['spend'])}, 0 compras")

if ads_com_compra:
    diag_lines.append(f"\n**Melhor Ad:** {melhor['name']} — ROAS {fmt_x(melhor['roas'])}, CPA {fmt_brl(melhor['cpa'])}, Tipo: {melhor['creative_type']}")
    diag_lines.append(f"**Pior Ad:** {pior['name']} — ROAS {fmt_x(pior['roas'])}, CPA {fmt_brl(pior['cpa'])}, Tipo: {pior['creative_type']}")

md_content = f"""# Relatório Diário Meta Ads — PowerMind Brasil
**Data:** {DATE}
**Conta:** {ACCOUNT_ID}
**Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Metas:** ROAS >= {ROAS_META}x | CPA <= R${CPA_META:.0f}

---

## 1. Visão Geral da Conta

{md_table_conta(conta_report)}

---

## 2. Nível Campanha

{md_table_camp(camp_report) if camp_report else "_Sem dados de campanha para o período._"}

---

## 3. Nível Ad Set

{md_table_adset(adset_report) if adset_report else "_Sem dados de ad set para o período._"}

---

## 4. Nível Ad (com Tipo de Criativo)

{md_table_ad(ad_report) if ad_report else "_Sem dados de ad para o período._"}

---

## 5. Diagnóstico Executivo

{chr(10).join(diag_lines) if diag_lines else "_Sem dados suficientes para diagnóstico._"}

---

## 6. Estrutura da Campanha RMKT-V2

| Segmento | ID Ad Set | Audiência | Prazo Engajamento |
|----------|-----------|-----------|-------------------|
| Fundo [RMKT-F] | 6996660758381 | IG engajamento | 7 dias (~24k) |
| Meio [RMKT-M] | 6996660887581 | IG engajamento | 8-30 dias (~24k) |
| Topo [RMKT-T] | 6996661046581 | IG engajamento | 31-90 dias (~16k) |

**Campanha:** [RMKT-V2][CBO] PowerMind Vendas Site [26-04-2026] (ID: 6996659875181)
**Orçamento:** CBO R$70/dia | **Placements:** Instagram Stories + Reels | **Idades:** 25-54
"""

output_path = "/Users/macbookpro/Desktop/Sandbox/obsidian/relatorio_2026-04-27.md"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"\nRelatorio salvo em: {output_path}")
