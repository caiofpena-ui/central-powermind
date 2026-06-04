#!/usr/bin/env python3
"""
PowerMind Dashboard Server — roda em localhost:8080
Serve dados em tempo real via /api/data
Inicia com o Mac via launchd.
"""
import json, os, glob, random, urllib.request, urllib.parse, webbrowser, math, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from threading import Thread
import time

PORT             = 8080
ENV_FILE         = os.path.join(os.path.dirname(__file__), "..", ".env")
HIST_DIR         = os.path.join(os.path.dirname(__file__), "historico")
LANC_FILE        = os.path.join(os.path.dirname(__file__), "lancamentos.json")
APPS_SCRIPT_URL  = "https://script.google.com/macros/s/AKfycbypqpQfA_XFnFWdrvrQlaU_MpQ28i7jl2RoSs3ljt-K2Gtw1H2lsnunqTKd4-XaQAA5/exec"
APPS_SCRIPT_VIDEOS_URL = "https://script.google.com/macros/s/AKfycbzgDYwHuYb7yCa-2a4wdN8TmTKHxBpMKaHc7zRRF6NQcbTmQlHLYYTjm4tYbrlOP4KL/exec"

AD_ACCOUNT  = "act_4170730686474512"
YAMPI_ALIAS = "powermind"

FIXOS_FILE         = os.path.join(os.path.dirname(__file__), "custos_fixos.json")

# ── CRM — arquivos ─────────────────────────────────────────────────────────
CREATORS_FILE      = os.path.join(os.path.dirname(__file__), "creators.json")
AGENDA_FILE        = os.path.join(os.path.dirname(__file__), "agenda.json")
CRM_HTML_FILE      = os.path.join(os.path.dirname(__file__), "crm.html")
CADASTRO_HTML_FILE = os.path.join(os.path.dirname(__file__), "cadastro.html")
CONTRATO_HTML_FILE = os.path.join(os.path.dirname(__file__), "contrato.html")
FICHA_HTML_FILE    = os.path.join(os.path.dirname(__file__), "ficha.html")

def load_creators():
    try:
        with open(CREATORS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_creators(data):
    with open(CREATORS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_agenda():
    try:
        with open(AGENDA_FILE) as f:
            return json.load(f)
    except:
        return []

def save_agenda(data):
    with open(AGENDA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _mock_creator(username):
    """Gera dados plausíveis quando o scraping do Instagram falha."""
    clean = username.lstrip("@")
    nomes  = ["Ana Fitness", "João Saúde", "Maria Nutrição", "Carlos Lifestyle", "Fernanda Bem-estar"]
    nichos = ["Musculação e Emagrecimento", "Nutrição Esportiva", "Yoga e Meditação", "Corrida e Performance", "Saúde Holística"]
    cats   = ["Fitness", "Saúde", "Nutrição", "Lifestyle", "Bem-estar"]
    idx = sum(ord(c) for c in clean) % 5
    seg = random.choice([8500, 22000, 45000, 120000, 310000])
    return {
        "username":       username,
        "nome":           nomes[idx],
        "foto":           "",
        "bio":            f"Apaixonado(a) por {cats[idx].lower()} e bem-estar. Compartilhando dicas diárias.",
        "seguidores":     seg,
        "seguindo":       random.randint(200, 800),
        "posts":          random.randint(80, 450),
        "categoria":      cats[idx],
        "nicho":          nichos[idx],
        "cidade":         "São Paulo",
        "link_instagram": f"https://instagram.com/{clean}",
        "link_tiktok":    "",
        "mock":           True,
    }

def enrich_instagram(username):
    """Tenta buscar dados reais do Instagram. Retorna mock em caso de falha."""
    clean = username.lstrip("@")
    headers = {
        "User-Agent":    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Accept":        "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "x-ig-app-id":  "936619743392459",
        "Referer":       f"https://www.instagram.com/{clean}/",
    }
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={clean}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = json.loads(r.read())
        user = raw.get("data", {}).get("user", {})
        if not user:
            raise ValueError("empty user")
        seg  = int(user.get("edge_followed_by", {}).get("count", 0))
        seg2 = int(user.get("edge_follow", {}).get("count", 0))
        posts = int(user.get("edge_owner_to_timeline_media", {}).get("count", 0))
        bio   = user.get("biography", "")
        nome  = user.get("full_name", "") or clean
        foto  = user.get("profile_pic_url_hd") or user.get("profile_pic_url", "")
        cat   = user.get("category_name") or "Outros"
        return {
            "username":       username,
            "nome":           nome,
            "foto":           foto,
            "bio":            bio,
            "seguidores":     seg,
            "seguindo":       seg2,
            "posts":          posts,
            "categoria":      cat,
            "nicho":          cat,
            "cidade":         "",
            "link_instagram": f"https://instagram.com/{clean}",
            "link_tiktok":    "",
            "mock":           False,
        }
    except Exception as e:
        print(f"[CRM] enrich falhou ({e}), retornando mock")
        return _mock_creator(username)

# Formato novo: {"nome": {"valor": float, "categoria": str}}
_FIXOS_DEFAULT = {
    "Mayara":    {"valor": 500.00, "categoria": "Pessoal"},
    "Hostinger": {"valor": 49.99,  "categoria": "Infraestrutura"},
    "Domínio":   {"valor": 29.99,  "categoria": "Infraestrutura"},
}

def _normalize_fixos(d):
    """Converte formato antigo {nome: float} para {nome: {valor, categoria}}"""
    out = {}
    for k, v in d.items():
        if isinstance(v, (int, float)):
            out[k] = {"valor": float(v), "categoria": "Outros"}
        else:
            out[k] = v
    return out

def load_fixos():
    try:
        with open(FIXOS_FILE) as f:
            return _normalize_fixos(json.load(f))
    except:
        return dict(_FIXOS_DEFAULT)

def save_fixos(d):
    with open(FIXOS_FILE, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def fixos_valor(entry):
    return entry["valor"] if isinstance(entry, dict) else float(entry)

# inicializa arquivo se não existir
if not os.path.exists(FIXOS_FILE):
    save_fixos(_FIXOS_DEFAULT)

def get_fixed_daily():
    return sum(fixos_valor(v) for v in load_fixos().values()) / 30

CMV         = {1: 37.00, 2: 86.00, 3: 123.00, 6: 234.00}
YAMPI_FEE   = 0.025
GW_CARD     = 0.0499   # Appmax — cliente paga juros de parcelamento
GW_PIX      = 0.010
IMPOSTO     = 0.10     # 10% sobre receita bruta

def load_env():
    v = {}
    try:
        for line in open(ENV_FILE):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, val = line.split("=", 1)
                v[k.strip()] = val.strip()
    except: pass
    return v

def meta_get(path, params, token):
    params["access_token"] = token
    qs = urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(
            f"https://graph.facebook.com/v19.0/{path}?{qs}", timeout=10
        ) as r:
            return json.loads(r.read())
    except:
        return {"data": []}

def yampi_receita_mes(ano_mes=None):
    """Retorna receita real do mês baseada em pedidos pagos da Yampi (não saques).
    ano_mes: 'YYYY-MM' ou None para mês atual."""
    env    = load_env()
    token  = env.get("YAMPI_TOKEN", "")
    secret = env.get("YAMPI_SECRET", "")
    if not ano_mes:
        ano_mes = datetime.now().strftime("%Y-%m")

    STATUS_PAGO = {"paid", "approved", "complete", "delivered", "on_carriage", "4", "6", "7"}

    receita   = 0.0
    pedidos   = 0
    page      = 1
    encontrou_mes = True

    while encontrou_mes:
        resp  = yampi_get("orders", {"page": page, "include": "transactions"}, YAMPI_ALIAS, token, secret)
        items = resp.get("data", [])
        if not items:
            break

        encontrou_mes = False
        for o in items:
            data_str = o.get("created_at", {}).get("date", "")[:7]  # YYYY-MM
            if data_str == ano_mes:
                encontrou_mes = True
                # Verificar se está pago
                status_alias = _get_status_alias(o.get("status", {}))
                if status_alias.lower() in STATUS_PAGO:
                    valor = float(o.get("value_total") or o.get("buyer_value_total") or 0)
                    receita  += valor
                    pedidos  += 1
            elif data_str < ano_mes:
                # Pedidos mais antigos — para de buscar
                encontrou_mes = False
                break

        meta        = resp.get("meta", {}).get("pagination", {})
        total_pages = meta.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1

    return {"receita": round(receita, 2), "pedidos": pedidos, "mes": ano_mes}

# ── FECHAMENTO MENSAL ────────────────────────────────────────────────────────
FECHAMENTOS_DIR = os.path.join(os.path.dirname(__file__), "fechamentos")

def gerar_fechamento_mes(ano_mes=None):
    """Consolida todos os dados do mês em um relatório de fechamento JSON."""
    if not ano_mes:
        ano_mes = datetime.now().strftime("%Y-%m")
    ano, mes = ano_mes.split("-")
    nome_mes_pt = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                   "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    nome_mes = nome_mes_pt[int(mes)]

    os.makedirs(FECHAMENTOS_DIR, exist_ok=True)

    # 1. Receita real (pedidos pagos Yampi)
    rec = yampi_receita_mes(ano_mes)
    receita_bruta = rec["receita"]
    pedidos_total = rec["pedidos"]
    ticket_medio  = round(receita_bruta / pedidos_total, 2) if pedidos_total else 0

    # 2. Consolidar histórico diário do mês
    hist_dir = HIST_DIR
    dias = []
    for arq in sorted(glob.glob(os.path.join(hist_dir, f"dre_{ano_mes}-*.json"))):
        try:
            with open(arq) as f:
                dias.append(json.load(f))
        except:
            pass

    dias_com_venda   = sum(1 for d in dias if d.get("pedidos", 0) > 0)
    gasto_ads_total  = round(sum(d.get("gasto_ads", 0) for d in dias), 2)
    roas_dias        = [d["roas_real"] for d in dias if d.get("roas_real") and d.get("roas_real") > 0]
    roas_medio       = round(sum(roas_dias) / len(roas_dias), 2) if roas_dias else 0
    cpa_dias         = [d["cpa_real"] for d in dias if d.get("cpa_real") and d.get("cpa_real") > 0]
    cpa_medio        = round(sum(cpa_dias) / len(cpa_dias), 2) if cpa_dias else 0
    margem_dias      = [d.get("margem_pct", 0) for d in dias if d.get("pedidos", 0) > 0]
    margem_media     = round(sum(margem_dias) / len(margem_dias), 2) if margem_dias else 0

    # 3. Lançamentos do mês (despesas e aportes)
    try:
        with open(LANC_FILE) as f:
            todos_lanc = json.load(f)
    except:
        todos_lanc = []
    lanc_mes = [l for l in todos_lanc if (l.get("data") or "")[:7] == ano_mes]

    # Tráfego vem da API Meta Ads (gasto_ads_total) — ignorar categoria "Tráfego" dos lançamentos
    CATS_IGNORADAS = {"Tráfego", "Trafego", "Receita Vendas", "Teste"}

    despesas_cats = {}
    aportes = 0.0
    for l in lanc_mes:
        if l.get("tipo") == "Despesa":
            cat = l.get("categoria", "Outros")
            if cat in CATS_IGNORADAS:
                continue
            despesas_cats[cat] = round(despesas_cats.get(cat, 0) + l.get("valor", 0), 2)
        elif l.get("tipo") in ("Aporte", "Entrada") or l.get("categoria") == "Aporte Sócio":
            aportes += l.get("valor", 0)

    total_despesas_lanc = round(sum(despesas_cats.values()), 2)

    # 4. Custos fixos do mês
    try:
        with open(FIXOS_FILE) as f:
            fixos_raw = json.load(f)
        fixos_total = round(sum(v.get("valor", 0) for v in fixos_raw.values()), 2)
    except:
        fixos_total = 579.98

    # 5. Deduções estimadas sobre receita bruta
    taxa_imposto  = round(receita_bruta * 0.10,  2)
    taxa_gateway  = round(receita_bruta * 0.0499, 2)
    taxa_yampi_   = round(receita_bruta * 0.025,  2)
    frete_total   = round(pedidos_total * 20.0,   2)
    cmv_estimado  = round(pedidos_total * 55.0,   2)  # CMV médio ~R$55/pedido (mix)
    total_deducoes = round(taxa_imposto + taxa_gateway + taxa_yampi_ + frete_total + cmv_estimado, 2)

    receita_liquida = round(receita_bruta - total_deducoes, 2)
    resultado_mes   = round(receita_liquida - gasto_ads_total - fixos_total - total_despesas_lanc, 2)
    margem_liquida  = round((resultado_mes / receita_bruta * 100), 2) if receita_bruta else 0

    # 6. Montar relatório
    relatorio = {
        "mes":              ano_mes,
        "nome_mes":         f"{nome_mes}/{ano}",
        "gerado_em":        datetime.now().strftime("%d/%m/%Y %H:%M"),
        "receita": {
            "bruta":        receita_bruta,
            "pedidos":      pedidos_total,
            "ticket_medio": ticket_medio,
            "deducoes": {
                "imposto":    taxa_imposto,
                "gateway":    taxa_gateway,
                "taxa_yampi": taxa_yampi_,
                "frete":      frete_total,
                "cmv":        cmv_estimado,
                "total":      total_deducoes
            },
            "liquida":      receita_liquida
        },
        "custos": {
            "trafego_pago":     gasto_ads_total,
            "fixos":            fixos_total,
            "despesas_variaveis": despesas_cats,
            "despesas_total":   total_despesas_lanc,
            "total_custos":     round(gasto_ads_total + fixos_total + total_despesas_lanc, 2)
        },
        "resultado": {
            "resultado_mes":    resultado_mes,
            "margem_liquida":   margem_liquida,
            "aportes":          round(aportes, 2)
        },
        "ads": {
            "gasto_total":      gasto_ads_total,
            "roas_medio":       roas_medio,
            "cpa_medio":        cpa_medio,
            "dias_com_venda":   dias_com_venda,
            "total_dias":       len(dias)
        },
        "metas": {
            "roas_meta":        3.5,
            "cpa_meta":         78.0,
            "margem_meta":      13.0,
            "roas_atingido":    roas_medio >= 3.5,
            "cpa_atingido":     0 < cpa_medio <= 78.0,
            "margem_atingida":  margem_liquida >= 13.0
        }
    }

    # 7. Salvar JSON
    arq_saida = os.path.join(FECHAMENTOS_DIR, f"fechamento_{ano_mes}.json")
    with open(arq_saida, "w") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)

    return relatorio

def listar_fechamentos():
    os.makedirs(FECHAMENTOS_DIR, exist_ok=True)
    result = []
    for arq in sorted(glob.glob(os.path.join(FECHAMENTOS_DIR, "fechamento_*.json")), reverse=True):
        try:
            with open(arq) as f:
                d = json.load(f)
            result.append({
                "mes":          d.get("mes"),
                "nome_mes":     d.get("nome_mes"),
                "gerado_em":    d.get("gerado_em"),
                "receita_bruta": d.get("receita",{}).get("bruta",0),
                "resultado_mes": d.get("resultado",{}).get("resultado_mes",0),
                "margem_liquida": d.get("resultado",{}).get("margem_liquida",0),
                "pedidos":      d.get("receita",{}).get("pedidos",0),
            })
        except:
            pass
    return result

# ─────────────────────────────────────────────────────────────────────────────

def yampi_get(path, params, alias, token, secret):
    qs = urllib.parse.urlencode({**params, "limit": 100})
    url = f"https://api.dooki.com.br/v2/{alias}/{path}?{qs}"
    req = urllib.request.Request(url, headers={
        "User-Token": token, "User-Secret-Key": secret,
        "Accept": "application/json",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return {"data": []}

LANC_MES_FILE = os.path.join(os.path.dirname(__file__), "lancamentos_{mes}.json")
LANC_CTRL     = os.path.join(os.path.dirname(__file__), "lancamentos_mes_atual.txt")

def virar_mes_se_necessario():
    """Na primeira execução de um novo mês, arquiva lancamentos.json do mês anterior
    em lancamentos_YYYY-MM.json e cria um novo lancamentos.json zerado."""
    mes_atual = datetime.now().strftime("%Y-%m")

    # Lê o mês registrado no arquivo de controle
    mes_registrado = ""
    try:
        with open(LANC_CTRL) as f:
            mes_registrado = f.read().strip()
    except:
        pass

    if mes_registrado == mes_atual:
        return  # Mesmo mês — nada a fazer

    # Mês mudou — arquiva o arquivo atual se tiver lançamentos
    items_atuais = []
    try:
        with open(LANC_FILE) as f:
            items_atuais = json.load(f)
    except:
        pass

    if items_atuais and mes_registrado:
        arq_arquivo = os.path.join(os.path.dirname(__file__), f"lancamentos_{mes_registrado}.json")
        # Só arquiva se ainda não existir (evita sobrescrever)
        if not os.path.exists(arq_arquivo):
            with open(arq_arquivo, "w") as f:
                json.dump(items_atuais, f, indent=2, ensure_ascii=False)
            print(f"[Virada de Mês] Arquivado: lancamentos_{mes_registrado}.json ({len(items_atuais)} lançamentos)")

        # Zera o arquivo atual
        with open(LANC_FILE, "w") as f:
            json.dump([], f)
        print(f"[Virada de Mês] lancamentos.json zerado para {mes_atual}")

    # Atualiza controle
    with open(LANC_CTRL, "w") as f:
        f.write(mes_atual)

def load_lancamentos():
    try:
        with open(LANC_FILE) as f:
            return json.load(f)
    except:
        return []

def load_lancamentos_mes(ano_mes):
    """Carrega lançamentos de um mês específico (arquivo arquivado ou atual)."""
    mes_atual = datetime.now().strftime("%Y-%m")
    if ano_mes == mes_atual:
        return load_lancamentos()
    arq = os.path.join(os.path.dirname(__file__), f"lancamentos_{ano_mes}.json")
    try:
        with open(arq) as f:
            return json.load(f)
    except:
        return []

def save_lancamento(entry):
    items = load_lancamentos()
    entry["id"] = int(time.time() * 1000)
    entry["criado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    items.append(entry)
    with open(LANC_FILE, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    _cache["ts"] = 0
    Thread(target=sync_gsheets, args=(entry,), daemon=True).start()
    return entry

LOG_EXCLUSAO_FILE = os.path.join(os.path.dirname(__file__), "exclusoes.json")

def load_exclusoes():
    try:
        with open(LOG_EXCLUSAO_FILE) as f:
            return json.load(f)
    except:
        return []

def delete_lancamento(lancamento_id, excluido_por):
    items = load_lancamentos()
    alvo  = next((l for l in items if str(l.get("id")) == str(lancamento_id)), None)
    if not alvo:
        return None
    items = [l for l in items if str(l.get("id")) != str(lancamento_id)]
    with open(LANC_FILE, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    # Registra log de exclusão
    log = load_exclusoes()
    log.append({
        "id_excluido":   lancamento_id,
        "excluido_por":  excluido_por,
        "excluido_em":   datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "dado_original": alvo,
    })
    with open(LOG_EXCLUSAO_FILE, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    _cache["ts"] = 0
    return alvo

def sync_contrato_drive(creator, acordo, data_assinatura, assinatura_b64):
    """Salva o contrato assinado no Google Drive via Apps Script — pasta Contratos Creators."""
    if not APPS_SCRIPT_URL:
        return
    try:
        freq_label = {'diario':'Diário','semanal':'Semanal','mensal':'Mensal','total':'Aleatório','nenhum':'Sem postagem'}
        nome     = creator.get("nome", creator.get("username", "Creator"))
        username = creator.get("username", "")
        cpf      = creator.get("cpf", "—")
        cidade   = creator.get("cidade", "Brasil")

        linhas_postagem = []
        for tipo, icon, qtd_key, freq_key in [
            ("Reels","🎬","qtd_reels","freq_reels"),
            ("Stories","📲","qtd_stories","freq_stories"),
            ("Feed","🖼️","qtd_feed","freq_feed"),
        ]:
            qtd = int(acordo.get(qtd_key) or 0)
            if qtd:
                freq = freq_label.get(acordo.get(freq_key,""), acordo.get(freq_key,""))
                linhas_postagem.append(f"{icon} {tipo}: {qtd} postagens · {freq}")

        redes = acordo.get("redes","Instagram") or "Instagram"
        periodo = f"{acordo.get('inicio','—')} a {acordo.get('fim','—')}"
        hora    = acordo.get("hora","—")
        obs     = acordo.get("info_adicional","")

        conteudo_txt = f"""CONTRATO DE PARCERIA — CREATOR POWERMIND
{'='*50}
Creator : {nome}  ({username})
CPF     : {cpf}
Cidade  : {cidade}
{'='*50}
ACORDO DE POSTAGENS
Redes   : {redes}
Período : {periodo}
Horário : {hora}
{''.join(chr(10)+l for l in linhas_postagem)}
{'Obs: '+obs if obs else ''}
{'='*50}
Assinado em: {data_assinatura}
"""

        payload = {
            "acao":            "salvar_contrato",
            "nome_arquivo":    f"Contrato_{username.replace('@','').replace('/','_')}_{data_assinatura[:10].replace('/','_')}.txt",
            "pasta":           "Contratos Creators",
            "conteudo":        conteudo_txt,
            "assinatura_b64":  assinatura_b64,
            "creator_nome":    nome,
            "creator_username": username,
            "data_assinatura": data_assinatura,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req  = urllib.request.Request(
            APPS_SCRIPT_URL, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            print(f"[Drive Contrato] {resp}")
    except Exception as e:
        print(f"[Drive Contrato] erro: {e}")

def criar_pasta_video_drive(creator):
    """Cria pasta de vídeos no Google Drive para o creator via Apps Script dedicado e retorna a URL."""
    if not APPS_SCRIPT_VIDEOS_URL:
        return None
    try:
        nome     = creator.get("nome", creator.get("username", "Creator"))
        username = creator.get("username", "").lstrip("@")
        cpf      = creator.get("cpf", "")
        payload  = json.dumps({"nome_creator": nome, "username": username, "cpf": cpf})

        # Passo 1: POST → captura header Location (sem seguir redirect)
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", APPS_SCRIPT_VIDEOS_URL,
             "-H", "Content-Type: application/json",
             "-d", payload,
             "-D", "-"],
            capture_output=True, text=True, timeout=30
        )
        # Extrai redirect URL do header ou do HTML body
        redirect_url = None
        for line in result.stdout.splitlines():
            low = line.lower().strip()
            if low.startswith("location:"):
                redirect_url = line.split(":", 1)[1].strip()
                break
        # Fallback: extrair do HTML se vier no body
        if not redirect_url and 'HREF="' in result.stdout:
            import re
            m = re.search(r'HREF="(https://script\.googleusercontent[^"]+)"', result.stdout)
            if m:
                redirect_url = m.group(1)

        with open("/tmp/drive_video_debug2.txt", "w") as dbg:
            dbg.write(f"STDOUT[:300]:\n{result.stdout[:300]}\nREDIRECT:\n{redirect_url}\n")

        if not redirect_url:
            print(f"[Drive Video] sem redirect")
            return None

        # Passo 2: GET na URL de redirect → JSON real
        result2 = subprocess.run(
            ["curl", "-s", redirect_url],
            capture_output=True, text=True, timeout=20
        )
        with open("/tmp/drive_video_debug2.txt", "a") as dbg:
            dbg.write(f"RESP:\n{result2.stdout[:300]}\n")
        resp = json.loads(result2.stdout)
        print(f"[Drive Video] {resp}")
        return resp.get("folder_url") or resp.get("url")
    except Exception as e:
        print(f"[Drive Video] erro: {e}")
        return None

def sync_gsheets(payload):
    if not APPS_SCRIPT_URL:
        return
    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req  = urllib.request.Request(
            APPS_SCRIPT_URL, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
            print(f"[GSheets] {resp}")
    except Exception as e:
        print(f"[GSheets] erro: {e}")

def load_history(days=30):
    records = []
    for path in sorted(glob.glob(os.path.join(HIST_DIR, "dre_*.json"))):
        try:
            with open(path) as f:
                records.append(json.load(f))
        except: pass
    return records[-days:]

def fetch_data():
    env        = load_env()
    token      = env.get("META_TOKEN", "")
    ya_token   = env.get("YAMPI_TOKEN", "")
    ya_secret  = env.get("YAMPI_SECRET", "")
    today      = datetime.now().strftime("%Y-%m-%d")
    d30        = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # ── Yampi pedidos de hoje — lê do arquivo de webhooks ─────────────────
    receita_hoje  = 0.0
    cmv_hoje      = 0.0
    gw_hoje       = 0.0
    yampi_hoje    = 0.0
    imposto_hoje  = 0.0
    pedidos_hoje  = 0

    webhook_orders = _load_yampi_pedidos()
    for o in webhook_orders:
        if o.get("data", "") != today:
            continue
        valor = float(o.get("valor", 0) or 0)
        if valor <= 0:
            continue
        pedidos_hoje  += 1
        receita_hoje  += valor
        gw_hoje       += valor * GW_CARD
        yampi_hoje    += valor * YAMPI_FEE
        imposto_hoje  += valor * IMPOSTO
        # estima CMV pela faixa de valor (conservador)
        if valor <= 200:
            cmv_hoje += CMV[1]
        elif valor <= 320:
            cmv_hoje += CMV[2]
        elif valor <= 500:
            cmv_hoje += CMV[3]
        else:
            cmv_hoje += CMV[6]

    margem_hoje = receita_hoje - cmv_hoje - gw_hoje - yampi_hoje - imposto_hoje

    # ── Meta Ads hoje ──────────────────────────────────────────────────────
    ins_hoje = meta_get(f"{AD_ACCOUNT}/insights", {
        "fields": "spend,impressions,clicks,ctr,cpm,actions",
        "time_range": json.dumps({"since": today, "until": today}),
        "level": "account"
    }, token)
    ads_hoje = 0.0
    impr_hoje = 0
    clicks_hoje = 0
    ctr_hoje = 0.0
    cpm_hoje = 0.0
    if ins_hoje.get("data"):
        d = ins_hoje["data"][0]
        ads_hoje    = float(d.get("spend", 0))
        impr_hoje   = int(d.get("impressions", 0))
        clicks_hoje = int(d.get("clicks", 0))
        ctr_hoje    = float(d.get("ctr", 0))
        cpm_hoje    = (ads_hoje / impr_hoje * 1000) if impr_hoje > 0 else 0

    fixed_costs = load_fixos()
    fixed_total = sum(fixos_valor(v) for v in fixed_costs.values())
    fixed_daily = fixed_total / 30
    resultado_hoje = margem_hoje - ads_hoje - fixed_daily
    roas_hoje = receita_hoje / ads_hoje if ads_hoje > 0 else 0

    # ── Meta campanhas — apenas hoje ─────────────────────────────────────
    camp_ins = meta_get(f"{AD_ACCOUNT}/insights", {
        "fields": "campaign_name,campaign_id,spend,impressions,clicks,ctr,cpm,actions",
        "time_range": json.dumps({"since": today, "until": today}),
        "level": "campaign", "limit": 20
    }, token)

    camp_status = meta_get(f"{AD_ACCOUNT}/campaigns", {
        "fields": "id,name,status,daily_budget",
        "limit": 20
    }, token)
    status_map = {c["id"]: c for c in camp_status.get("data", [])}

    campaigns = []
    for c in camp_ins.get("data", []):
        cid = c.get("campaign_id", "")
        st  = status_map.get(cid, {})
        if st.get("status", "") != "ACTIVE":
            continue
        actions = c.get("actions", []) or []
        def act(name): return int(float(next((a["value"] for a in actions if a["action_type"] == name), 0)))
        purchases       = act("purchase")
        add_to_cart     = act("add_to_cart")
        init_checkout   = act("initiate_checkout")
        spend = float(c.get("spend", 0))
        campaigns.append({
            "name":           c.get("campaign_name", "")[:55],
            "status":         st.get("status", ""),
            "budget":         float(st.get("daily_budget", 0) or 0) / 100,
            "spend":          spend,
            "impressions":    int(c.get("impressions", 0)),
            "clicks":         int(c.get("clicks", 0)),
            "ctr":            float(c.get("ctr", 0)),
            "cpm":            round(spend / int(c.get("impressions", 0) or 1) * 1000, 2),
            "purchases":      purchases,
            "cpa":            spend / purchases if purchases > 0 else 0,
            "add_to_cart":    add_to_cart,
            "custo_carrinho": spend / add_to_cart if add_to_cart > 0 else 0,
            "init_checkout":  init_checkout,
            "custo_checkout": spend / init_checkout if init_checkout > 0 else 0,
        })

    # ── Histórico DRE ──────────────────────────────────────────────────────
    history     = load_history(30)
    history_all = load_history(365)
    total_receita   = sum(r.get("receita_bruta", 0) for r in history)
    total_ads       = sum(r.get("gasto_ads", 0) for r in history)
    total_margem    = sum(r.get("margem_contribuicao", 0) for r in history)
    total_resultado = sum(r.get("resultado", 0) for r in history)
    total_pedidos   = sum(r.get("pedidos", 0) for r in history)

    # ── Salvar DRE de hoje ────────────────────────────────────────────────
    os.makedirs(HIST_DIR, exist_ok=True)
    log_path = os.path.join(HIST_DIR, f"dre_{today}.json")
    existing = {}
    try:
        with open(log_path) as f:
            existing = json.load(f)
    except: pass

    if not existing.get("correcao_manual"):
        log = {
            "data": today,
            "pedidos": pedidos_hoje,
            "ticket_medio": round(receita_hoje / pedidos_hoje, 2) if pedidos_hoje > 0 else 0,
            "receita_bruta": round(receita_hoje, 2),
            "receita_liquida": round(receita_hoje, 2),
            "cmv": round(cmv_hoje, 2),
            "taxa_gateway": round(gw_hoje, 2),
            "taxa_yampi": round(yampi_hoje, 2),
            "imposto": round(imposto_hoje, 2),
            "margem_contribuicao": round(margem_hoje, 2),
            "margem_pct": round(margem_hoje / receita_hoje * 100, 1) if receita_hoje > 0 else 0,
            "gasto_ads": round(ads_hoje, 2),
            "fixos_dia": round(fixed_daily, 2),
            "resultado": round(resultado_hoje, 2),
            "roas_real": round(roas_hoje, 2),
            "cpa_real": round(ads_hoje / pedidos_hoje, 2) if pedidos_hoje > 0 else 0,
        }
        with open(log_path, "w") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        Thread(target=sync_gsheets, args=({**log, "aba": "DRE"},), daemon=True).start()

    return {
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "today": today,
        "hoje": {
            "resultado": round(resultado_hoje, 2),
            "receita": round(receita_hoje, 2),
            "pedidos": pedidos_hoje,
            "ads": round(ads_hoje, 2),
            "roas": round(roas_hoje, 2),
            "impressions": impr_hoje,
            "clicks": clicks_hoje,
            "ctr": round(ctr_hoje, 2),
            "cpm": round(cpm_hoje, 2),
            "margem": round(margem_hoje, 2),
            "margem_pct": round(margem_hoje / receita_hoje * 100, 1) if receita_hoje > 0 else 0,
        },
        "acumulado": {
            "resultado": round(total_resultado, 2),
            "receita": round(total_receita, 2),
            "ads": round(total_ads, 2),
            "margem": round(total_margem, 2),
            "margem_pct": round(total_margem / total_receita * 100, 1) if total_receita > 0 else 0,
            "pedidos": total_pedidos,
            "roas": round(total_receita / total_ads, 2) if total_ads > 0 else 0,
            "ticket_medio": round(total_receita / total_pedidos, 2) if total_pedidos > 0 else 0,
            "fixos_mes": round(fixed_total, 2),
            "fixos_dia": round(fixed_daily, 2),
        },
        "campaigns": campaigns,
        "history": history,
        "history_all": history_all,
        "lancamentos": load_lancamentos()[-50:],
        "fixed_costs": fixed_costs,
        "fixed_total": round(fixed_total, 2),
        "fixed_daily": round(fixed_daily, 2),
        "kits": [
            {"nome": "1 pacote",            "preco": 157, "cmv": 37,  "mixer": 0},
            {"nome": "Power Duo (2 pac.)",  "preco": 274, "cmv": 74,  "mixer": 12},
            {"nome": "3 pacotes",           "preco": 381, "cmv": 111, "mixer": 12},
        ],
    }

# ── Webhook Yampi ─────────────────────────────────────────────────────────
YAMPI_ORDERS_FILE = os.path.join(os.path.dirname(__file__), "yampi_pedidos_hoje.json")
STATUS_PAGO = {"paid", "approved", "complete", "delivered", "on_carriage"}

def _load_yampi_pedidos():
    try:
        with open(YAMPI_ORDERS_FILE) as f:
            return json.load(f)
    except:
        return []

def _save_yampi_pedidos(pedidos):
    with open(YAMPI_ORDERS_FILE, "w") as f:
        json.dump(pedidos, f, indent=2, ensure_ascii=False)

def _get_status_alias(status_obj):
    """Extrai alias do status independente do formato (flat ou nested .data)."""
    if isinstance(status_obj, dict):
        if "data" in status_obj:
            return status_obj["data"].get("alias", "")
        return status_obj.get("alias", "")
    return str(status_obj)

def reconciliar_yampi():
    """Busca pedidos pagos de hoje na API Yampi e adiciona os que faltam no arquivo local."""
    env       = load_env()
    token     = env.get("YAMPI_TOKEN", "")
    secret    = env.get("YAMPI_SECRET", "")
    today     = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    pedidos   = _load_yampi_pedidos()
    ids_existentes = {str(p.get("numero")) for p in pedidos}
    novos = []

    page = 1
    while True:
        resp = yampi_get("orders", {"page": page, "include": "transactions,items"},
                         YAMPI_ALIAS, token, secret)
        items = resp.get("data", [])
        if not items:
            break
        # Para paginação só quando TODA a página for anterior a ontem
        # (evita parar cedo se um pedido antigo aparecer no meio da página)
        all_before_yesterday = True
        for o in items:
            date_str = o.get("created_at", {}).get("date", "")[:10]
            if date_str >= yesterday:
                all_before_yesterday = False
            if date_str != today:
                continue
            status_alias = _get_status_alias(o.get("status", {}))
            if status_alias not in STATUS_PAGO:
                continue
            numero = str(o.get("number", ""))
            if numero in ids_existentes:
                continue
            valor = float(o.get("value_total") or o.get("buyer_value_total") or 0)
            nome  = o.get("customer", {}).get("data", {}).get("name", "—")
            hora  = o.get("created_at", {}).get("date", "")[11:16]
            novos.append({
                "numero": numero, "valor": valor, "nome": nome,
                "status": status_alias, "data": today, "recebido_em": hora,
            })
            ids_existentes.add(numero)
        if all_before_yesterday:
            break
        meta = resp.get("meta", {})
        total_pages = meta.get("pagination", {}).get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1

    if novos:
        pedidos.extend(novos)
        _save_yampi_pedidos(pedidos)
        print(f"[Reconciliação] {len(novos)} pedido(s) recuperado(s) da API: {[n['numero'] for n in novos]}")
        _cache["ts"] = 0
    else:
        print(f"[Reconciliação] Nenhum pedido novo encontrado para {today}")

def _handle_yampi_webhook(payload):
    event   = payload.get("event", "")
    order   = payload.get("resource", payload.get("order", payload))
    status_alias = _get_status_alias(order.get("status", {}))

    numero  = str(order.get("number", "?"))
    valor   = float(order.get("value_total") or order.get("buyer_value_total") or order.get("value") or 0)
    cliente = order.get("customer", {})
    if isinstance(cliente, dict) and "data" in cliente:
        nome = cliente["data"].get("name", "—")
    else:
        nome = cliente.get("name", "—") if isinstance(cliente, dict) else "—"

    print(f"[Webhook Yampi] evento={event} pedido=#{numero} status={status_alias} valor=R${valor}")

    if status_alias not in STATUS_PAGO:
        print(f"[Webhook Yampi] ignorado — status '{status_alias}' não é pago")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    pedidos = _load_yampi_pedidos()

    ids_existentes = {str(p.get("numero")) for p in pedidos}
    if numero in ids_existentes:
        print(f"[Webhook Yampi] pedido #{numero} já registrado")
        return

    pedidos.append({
        "numero":    numero,
        "valor":     valor,
        "nome":      nome,
        "status":    status_alias,
        "data":      today,
        "recebido_em": datetime.now().strftime("%H:%M:%S"),
    })
    _save_yampi_pedidos(pedidos)

    # Notificação no Mac
    os.system(f'osascript -e \'display notification "Pedido #{numero} — R${valor:.2f} ({nome})" with title "💚 PowerMind — Venda!" sound name "Glass"\'')

    # Força atualização do cache do dashboard
    _cache["ts"] = 0
    print(f"[Webhook Yampi] ✅ Pedido #{numero} R${valor} registrado — cache resetado")

# ── Cache de dados (atualiza a cada 2 min) ─────────────────────────────────
_cache = {"data": None, "ts": 0}

def get_cached():
    now = time.time()
    if _cache["data"] is None or now - _cache["ts"] > 60:
        try:
            _cache["data"] = fetch_data()
            _cache["ts"]   = now
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Dados atualizados")
        except Exception as e:
            print(f"Erro ao buscar dados: {e}")
    return _cache["data"]

# ── HTML do dashboard ──────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PowerMind Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0f1117;color:#e0e0e0;min-height:100vh}
.header{background:linear-gradient(135deg,#1a1d2e,#252836);padding:20px 32px;border-bottom:1px solid #2d3047;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100}
.header h1{font-size:1.5rem;font-weight:700;color:#fff}.header h1 span{color:#6c63ff}
.ts{font-size:.8rem;color:#888;margin-top:4px}
.live{display:flex;align-items:center;gap:8px;font-size:.85rem}
.dot{width:8px;height:8px;border-radius:50%;background:#27ae60;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.container{padding:20px 32px;max-width:1600px;margin:0 auto}
.section-title{font-size:.85rem;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:1px;margin:24px 0 12px;border-bottom:1px solid #2d3047;padding-bottom:6px}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px}
.kpi{background:#1a1d2e;border:1px solid #2d3047;border-radius:10px;padding:18px;position:relative;overflow:hidden;transition:.2s}
.kpi:hover{border-color:#3d4060}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--a,#6c63ff)}
.kpi.green{--a:#27ae60}.kpi.red{--a:#e74c3c}.kpi.blue{--a:#3498db}.kpi.purple{--a:#9b59b6}.kpi.orange{--a:#e67e22}.kpi.teal{--a:#1abc9c}
.kpi .label{font-size:.72rem;color:#888;margin-bottom:5px;text-transform:uppercase;letter-spacing:.5px}
.kpi .value{font-size:1.55rem;font-weight:700;color:#fff;transition:.3s}
.kpi .sub{font-size:.72rem;color:#888;margin-top:3px}
.charts-grid{display:grid;grid-template-columns:2fr 1fr;gap:18px}
.chart-box{background:#1a1d2e;border:1px solid #2d3047;border-radius:10px;padding:18px}
.chart-box h3{font-size:.78rem;color:#aaa;margin-bottom:14px;text-transform:uppercase;letter-spacing:.5px}
table{width:100%;border-collapse:collapse;font-size:.82rem}
th{background:#252836;color:#aaa;text-align:left;padding:9px 12px;font-size:.72rem;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #2d3047}
td{padding:9px 12px;border-bottom:1px solid #1e2130}
tr:hover td{background:#1e2130}
.table-box{background:#1a1d2e;border:1px solid #2d3047;border-radius:10px;overflow:hidden;margin-bottom:18px}
.badge{padding:2px 7px;border-radius:4px;font-size:.68rem;font-weight:700;margin-right:5px}
.badge.active{background:#1a4731;color:#27ae60}.badge.paused{background:#3d2b1f;color:#e67e22}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.positive{color:#27ae60;font-weight:700}.negative{color:#e74c3c;font-weight:700}
.meta-tag{font-size:.68rem;color:#e67e22;margin-left:4px}
@media(max-width:900px){.charts-grid,.two-col{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>⚡ <span>PowerMind</span> Dashboard</h1>
    <div class="ts" id="ts">Carregando...</div>
  </div>
  <div style="display:flex;align-items:center;gap:24px">
    <div class="live"><div class="dot"></div><span style="color:#aaa">Ao vivo · atualiza em <span id="countdown">60</span>s</span></div>
    <div id="status-hoje" style="text-align:right"></div>
  </div>
</div>

<div class="container">
  <div class="section-title">Hoje — <span id="today-label"></span></div>
  <div class="kpi-grid" id="kpi-hoje"></div>

  <div class="section-title">Acumulado — últimos 30 dias</div>
  <div class="kpi-grid" id="kpi-acumulado"></div>

  <div class="section-title">Evolução diária</div>
  <div class="charts-grid">
    <div class="chart-box"><h3>Receita vs Gasto Ads (R$)</h3><canvas id="chartBar" height="100"></canvas></div>
    <div class="chart-box"><h3>Resultado líquido diário (R$)</h3><canvas id="chartResult" height="100"></canvas></div>
  </div>

  <div class="section-title">Campanhas Meta Ads</div>
  <div class="table-box">
    <table><thead><tr>
      <th>Campanha</th><th>Status</th><th>Gasto</th><th>Impressões</th>
      <th>Cliques</th><th>CTR</th><th>CPM</th><th>Custo/Carrinho</th><th>Custo/Finalização</th><th>Compras</th><th>CPA</th>
    </tr></thead><tbody id="camp-body"></tbody></table>
  </div>

  <div class="section-title">DRE Histórico</div>
  <div class="table-box">
    <table><thead><tr>
      <th>Data</th><th>Pedidos</th><th>Receita</th><th>Margem</th>
      <th>Ads</th><th>Fixos</th><th>Resultado</th><th>ROAS</th>
    </tr></thead><tbody id="dre-body"></tbody></table>
  </div>

  <div class="section-title">Lançamentos</div>
  <div class="table-box" style="padding:20px 20px 10px">
    <form id="lanc-form" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:18px">
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Data</label>
        <input type="date" id="l-data" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Categoria</label>
        <select id="l-cat" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
          <option>Fornecedor</option><option>Marketing</option><option>Operacional</option>
          <option>Frete</option><option>Outros</option>
        </select>
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Descrição</label>
        <input type="text" id="l-desc" placeholder="Ex: Compra de embalagens" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Valor (R$)</label>
        <input type="number" id="l-valor" step="0.01" min="0" placeholder="0,00" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Tipo</label>
        <select id="l-tipo" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
          <option value="Despesa">Despesa</option><option value="Receita">Receita</option>
        </select>
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Lançado por</label>
        <select id="l-por" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
          <option>Caio</option><option>Felipe</option>
        </select>
      </div>
      <div style="display:flex;align-items:flex-end">
        <button type="submit" id="lanc-btn" style="width:100%;background:#6c63ff;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:.85rem;font-weight:600;cursor:pointer">+ Lançar</button>
      </div>
    </form>
    <table><thead><tr>
      <th>Data</th><th>Por</th><th>Categoria</th><th>Descrição</th><th>Tipo</th><th>Valor</th><th>Lançado em</th>
    </tr></thead><tbody id="lanc-body"></tbody></table>
  </div>

  <div class="section-title">Estrutura de Custos</div>
  <div class="two-col">
  <div class="table-box" style="padding:20px 20px 10px">
    <form id="fixos-form" style="display:grid;grid-template-columns:1fr 180px 120px;gap:10px;margin-bottom:18px;align-items:end">
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Nome do custo</label>
        <input type="text" id="f-nome" placeholder="Ex: Embalagens, Contador..." style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Valor mensal (R$)</label>
        <input type="number" id="f-valor" step="0.01" min="0" placeholder="0,00" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
      </div>
      <div>
        <button type="submit" id="fixos-btn" style="width:100%;background:#27ae60;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:.85rem;font-weight:600;cursor:pointer">+ Adicionar</button>
      </div>
    </form>
    <table>
      <thead><tr>
        <th>Item</th>
        <th>Valor mensal</th>
        <th>Rateio diário</th>
        <th style="width:60px"></th>
      </tr></thead>
      <tbody id="fixos-body"></tbody>
    </table>
  </div>
  <div class="table-box">
    <table><thead><tr>
      <th>Kit</th><th>Preço</th><th>CMV</th><th>Margem cartão</th><th>Margem PIX</th>
    </tr></thead><tbody id="kits-body"></tbody></table>
  </div>
</div>

<script>
const BRL = v => 'R$ ' + Number(v).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const PCT = v => Number(v).toFixed(1) + '%';
let chartBar = null, chartResult = null;

function kpiCard(label, value, sub, cls){
  return `<div class="kpi ${cls}"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub}</div></div>`;
}

function render(d){
  // Header
  document.getElementById('ts').textContent = 'Atualizado em ' + d.updated_at;
  document.getElementById('today-label').textContent = d.today;
  const resHoje = d.hoje.resultado;
  document.getElementById('status-hoje').innerHTML =
    `<div style="font-size:.8rem;color:#aaa">Resultado hoje</div>
     <div style="font-size:1.3rem;font-weight:700;color:${resHoje>=0?'#27ae60':'#e74c3c'}">${resHoje>=0?'🟢 POSITIVO':'🔴 NEGATIVO'}</div>`;

  // KPIs hoje
  const h = d.hoje;
  document.getElementById('kpi-hoje').innerHTML =
    kpiCard('Resultado do dia', BRL(h.resultado), h.pedidos + ' pedido(s)', h.resultado>=0?'green':'red') +
    kpiCard('Receita', BRL(h.receita), 'Bruta hoje', 'blue') +
    kpiCard('Gasto Ads', BRL(h.ads), 'Meta Ads', 'orange') +
    kpiCard('ROAS', h.roas.toFixed(2)+'x', 'Meta: >3,5x', h.roas>=3.5?'green':'red') +
    kpiCard('Impressões', h.impressions.toLocaleString('pt-BR'), 'Meta Ads hoje', 'teal') +
    kpiCard('CTR', PCT(h.ctr), 'Meta: >2%', h.ctr>=2?'green':'red') +
    kpiCard('CPM', BRL(h.cpm), 'Meta: <R$55', h.cpm>0&&h.cpm<55?'green':'red');

  // KPIs acumulado
  const a = d.acumulado;
  document.getElementById('kpi-acumulado').innerHTML =
    kpiCard('Resultado total', BRL(a.resultado), 'Lucro/Prejuízo últimos 30 dias', a.resultado>=0?'green':'red');

  // Gráficos
  const labels  = d.history.map(r => r.data.slice(5));
  const recArr  = d.history.map(r => r.receita_bruta || 0);
  const adsArr  = d.history.map(r => r.gasto_ads || 0);
  const resArr  = d.history.map(r => r.resultado || 0);

  if(chartBar) chartBar.destroy();
  chartBar = new Chart(document.getElementById('chartBar'), {
    type:'bar',
    data:{labels, datasets:[
      {label:'Receita', data:recArr, backgroundColor:'rgba(52,152,219,0.7)', borderRadius:4},
      {label:'Gasto Ads', data:adsArr, backgroundColor:'rgba(231,76,60,0.7)', borderRadius:4}
    ]},
    options:{responsive:true, plugins:{legend:{labels:{color:'#aaa'}}},
      scales:{x:{ticks:{color:'#666'},grid:{color:'#1e2130'}},y:{ticks:{color:'#666'},grid:{color:'#1e2130'}}}}
  });

  if(chartResult) chartResult.destroy();
  chartResult = new Chart(document.getElementById('chartResult'), {
    type:'bar',
    data:{labels, datasets:[{
      label:'Resultado', data:resArr,
      backgroundColor: resArr.map(v => v>=0?'rgba(39,174,96,0.8)':'rgba(231,76,60,0.8)'),
      borderRadius:4
    }]},
    options:{responsive:true, plugins:{legend:{labels:{color:'#aaa'}}},
      scales:{x:{ticks:{color:'#666'},grid:{color:'#1e2130'}},y:{ticks:{color:'#666'},grid:{color:'#1e2130'}}}}
  });

  // Campanhas
  document.getElementById('camp-body').innerHTML = d.campaigns.length === 0
    ? '<tr><td colspan="11" style="text-align:center;color:#888">Sem dados</td></tr>'
    : d.campaigns.map(c => `<tr>
        <td>${c.name}</td>
        <td><span class="badge ${c.status==='ACTIVE'?'active':'paused'}">${c.status==='ACTIVE'?'ATIVO':'PAUSADO'}</span></td>
        <td>${BRL(c.spend)}</td>
        <td>${c.impressions.toLocaleString('pt-BR')}</td>
        <td>${c.clicks.toLocaleString('pt-BR')}</td>
        <td class="${c.ctr>=2?'positive':'negative'}">${PCT(c.ctr)}</td>
        <td class="${c.cpm>0&&c.cpm<55?'positive':'negative'}">${BRL(c.cpm)}</td>
        <td>${c.add_to_cart>0?BRL(c.custo_carrinho):'—'}</td>
        <td>${c.init_checkout>0?BRL(c.custo_checkout):'—'}</td>
        <td>${c.purchases}</td>
        <td>${c.purchases>0?BRL(c.cpa):'—'}</td>
      </tr>`).join('');

  // DRE histórico
  document.getElementById('dre-body').innerHTML = [...d.history].reverse().map(r => {
    const res = r.resultado || 0;
    return `<tr>
      <td>${r.data}${r.correcao_manual?'<span class="meta-tag">⚠️manual</span>':''}</td>
      <td>${r.pedidos||0}</td>
      <td>${BRL(r.receita_bruta||0)}</td>
      <td>${BRL(r.margem_contribuicao||0)} (${r.margem_pct||0}%)</td>
      <td>${BRL(r.gasto_ads||0)}</td>
      <td>${BRL(r.fixos_dia||0)}</td>
      <td class="${res>=0?'positive':'negative'}">${BRL(res)}</td>
      <td>${(r.roas_real||0).toFixed(2)}x</td>
    </tr>`;
  }).join('');

  // Custos Fixos
  const fixTotal = d.fixed_total || 0;
  const fixDaily = d.fixed_daily || 0;
  document.getElementById('fixos-body').innerHTML =
    Object.entries(d.fixed_costs).map(([k,v]) =>
      `<tr>
        <td>${k}</td>
        <td>${BRL(v)}</td>
        <td style="color:#888">${BRL(v/30)}/dia</td>
        <td><button onclick="deleteFixo('${k}')" style="background:#3d1a1a;color:#e74c3c;border:none;border-radius:4px;padding:3px 10px;cursor:pointer;font-size:.75rem">✕</button></td>
      </tr>`).join('') +
    `<tr style="font-weight:700;border-top:2px solid #3d4060;color:#f39c12">
       <td>TOTAL MENSAL</td><td>${BRL(fixTotal)}</td><td style="color:#888">${BRL(fixDaily)}/dia</td><td></td>
     </tr>`;

  // Lançamentos
  renderLancamentos(d.lancamentos || []);

  // Kits
  document.getElementById('kits-body').innerHTML = d.kits.map(k => {
    const cmvT = k.cmv + k.mixer;
    const mc = k.preco - cmvT - k.preco*0.025 - k.preco*0.066;
    const mp = k.preco - cmvT - k.preco*0.025 - k.preco*0.010;
    return `<tr>
      <td>${k.nome}</td><td>${BRL(k.preco)}</td><td>${BRL(cmvT)}</td>
      <td class="positive">${BRL(mc)} (${(mc/k.preco*100).toFixed(0)}%)</td>
      <td class="positive">${BRL(mp)} (${(mp/k.preco*100).toFixed(0)}%)</td>
    </tr>`;
  }).join('');
}

// Lançamentos
function renderLancamentos(items){
  const reversed = [...items].reverse();
  document.getElementById('lanc-body').innerHTML = reversed.length === 0
    ? '<tr><td colspan="7" style="text-align:center;color:#888">Nenhum lançamento ainda</td></tr>'
    : reversed.map(l => `<tr>
        <td>${l.data||'—'}</td>
        <td>${l.lancado_por||'—'}</td>
        <td>${l.categoria||'—'}</td>
        <td>${l.descricao||'—'}</td>
        <td><span class="badge ${l.tipo==='Receita'?'active':'paused'}">${l.tipo||'—'}</span></td>
        <td class="${l.tipo==='Receita'?'positive':'negative'}">${BRL(l.valor||0)}</td>
        <td style="color:#666">${l.criado_em||'—'}</td>
      </tr>`).join('');
}

// Preenche data padrão do formulário
document.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().slice(0,10);
  document.getElementById('l-data').value = today;
});

// Custos Fixos — adicionar
document.getElementById('fixos-form').addEventListener('submit', e => {
  e.preventDefault();
  const btn   = document.getElementById('fixos-btn');
  const nome  = document.getElementById('f-nome').value.trim();
  const valor = parseFloat(document.getElementById('f-valor').value);
  if(!nome || !valor || valor <= 0){ alert('Preencha nome e valor.'); return; }
  btn.textContent = 'Salvando...'; btn.disabled = true;
  fetch('/api/fixos/add', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({nome, valor})
  }).then(r => r.json()).then(() => {
    document.getElementById('f-nome').value = '';
    document.getElementById('f-valor').value = '';
    btn.textContent = '✓ Adicionado!';
    setTimeout(() => { btn.textContent = '+ Adicionar'; btn.disabled = false; }, 1500);
    loadData();
  }).catch(() => { btn.textContent = '+ Adicionar'; btn.disabled = false; });
});

// Custos Fixos — deletar
function deleteFixo(nome) {
  if(!confirm(`Remover "${nome}" dos custos fixos?`)) return;
  fetch('/api/fixos/delete', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({nome})
  }).then(() => loadData());
}

document.getElementById('lanc-form').addEventListener('submit', e => {
  e.preventDefault();
  const btn = document.getElementById('lanc-btn');
  const data  = document.getElementById('l-data').value;
  const cat   = document.getElementById('l-cat').value;
  const desc  = document.getElementById('l-desc').value.trim();
  const valor = parseFloat(document.getElementById('l-valor').value);
  const tipo  = document.getElementById('l-tipo').value;
  const por   = document.getElementById('l-por').value;
  if(!desc || !valor || valor <= 0){ alert('Preencha descrição e valor.'); return; }
  btn.textContent = 'Salvando...'; btn.disabled = true;
  fetch('/api/lancamento', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({data, categoria:cat, descricao:desc, valor, tipo, lancado_por:por})
  })
  .then(r => r.json())
  .then(() => {
    btn.textContent = '✓ Salvo!';
    document.getElementById('l-desc').value = '';
    document.getElementById('l-valor').value = '';
    setTimeout(() => { btn.textContent = '+ Lançar'; btn.disabled = false; }, 1500);
    loadData();
  })
  .catch(() => { btn.textContent = '+ Lançar'; btn.disabled = false; alert('Erro ao salvar.'); });
});

// Countdown e auto-refresh a cada 60s
let cd = 60;
setInterval(() => {
  cd--;
  document.getElementById('countdown').textContent = cd;
  if(cd <= 0){ cd = 60; loadData(); }
}, 1000);

function loadData(){
  fetch('/api/data')
    .then(r => r.json())
    .then(d => { render(d); cd = 120; })
    .catch(e => console.error(e));
}
loadData();
</script>
</body>
</html>"""

# ── Handler HTTP ───────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/data":
            data = get_cached()
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/logo.png":
            logo_file = os.path.join(os.path.dirname(__file__), "logo.png")
            try:
                with open(logo_file, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "max-age=86400")
                self.end_headers()
                self.wfile.write(body)
                return
            except FileNotFoundError:
                self.send_response(404); self.end_headers(); return
        elif self.path.split('?')[0] in ("/crm", "/creators"):
            try:
                with open(CRM_HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404); self.end_headers()

        elif self.path.split('?')[0] in ("/cadastro", "/cadastro.html"):
            try:
                with open(CADASTRO_HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404); self.end_headers()
                self.wfile.write(b"cadastro.html not found")

        elif self.path.split('?')[0] in ("/ficha", "/ficha.html"):
            try:
                with open(FICHA_HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404); self.end_headers()
                self.wfile.write(b"ficha.html not found")

        elif self.path.split('?')[0] in ("/contrato", "/contrato.html"):
            try:
                with open(CONTRATO_HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404); self.end_headers()
                self.wfile.write(b"contrato.html not found")

        elif self.path.startswith("/api/historico-mes"):
            from urllib.parse import urlparse, parse_qs
            qs  = parse_qs(urlparse(self.path).query)
            mes = qs.get("mes", [datetime.now().strftime("%Y-%m")])[0]
            dias = []
            for arq in sorted(glob.glob(os.path.join(HIST_DIR, f"dre_{mes}-*.json"))):
                try:
                    with open(arq) as f:
                        dias.append(json.load(f))
                except:
                    pass
            gasto_ads = round(sum(d.get("gasto_ads", 0) for d in dias), 2)
            body = json.dumps({"gasto_ads": gasto_ads, "dias": len(dias), "mes": mes}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/api/yampi/receita-mes"):
            from urllib.parse import urlparse, parse_qs
            qs   = parse_qs(urlparse(self.path).query)
            mes  = qs.get("mes", [None])[0]
            data = yampi_receita_mes(mes)
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/api/lancamentos"):
            from urllib.parse import urlparse, parse_qs
            qs  = parse_qs(urlparse(self.path).query)
            mes = qs.get("mes", [None])[0]
            if mes:
                data = load_lancamentos_mes(mes)
            else:
                # Listar meses disponíveis
                meses = []
                mes_atual = datetime.now().strftime("%Y-%m")
                meses.append(mes_atual)
                for arq in sorted(glob.glob(os.path.join(os.path.dirname(LANC_FILE), "lancamentos_????-??.json")), reverse=True):
                    nome = os.path.basename(arq).replace("lancamentos_","").replace(".json","")
                    if nome not in meses:
                        meses.append(nome)
                data = {"meses": meses}
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/api/fechamento"):
            from urllib.parse import urlparse, parse_qs
            qs  = parse_qs(urlparse(self.path).query)
            mes = qs.get("mes", [None])[0]
            if self.path.startswith("/api/fechamento/listar"):
                data = listar_fechamentos()
            elif mes:
                arq = os.path.join(FECHAMENTOS_DIR, f"fechamento_{mes}.json")
                if os.path.exists(arq):
                    with open(arq) as f:
                        data = json.load(f)
                else:
                    data = {"erro": "Fechamento não encontrado para " + mes}
            else:
                data = {"erro": "Parâmetro ?mes=YYYY-MM obrigatório"}
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/api/creators":
            creators = load_creators()
            body = json.dumps(creators, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/api/agenda":
            agenda = load_agenda()
            body = json.dumps(agenda, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/api/creator/public"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            u = qs.get("u", [""])[0].strip()
            creators = load_creators()
            found = next((c for c in creators if c.get("username") == u), None)
            if found:
                payload = {
                    "nome":                  found.get("nome", ""),
                    "foto":                  found.get("foto", ""),
                    "username":              found.get("username", u),
                    "cpf":                   found.get("cpf", ""),
                    "telefone":              found.get("telefone", ""),
                    "endereco":              found.get("endereco", ""),
                    "cidade":                found.get("cidade", ""),
                    "acordo":                found.get("acordo", {}),
                    "contrato_assinado":     found.get("contrato_assinado", False),
                    "contrato_assinado_em":  found.get("contrato_assinado_em", ""),
                    "dados_envio_ok":        found.get("dados_envio_ok", False),
                    "dados_envio_em":        found.get("dados_envio_em", ""),
                    "postagens_status":      found.get("postagens_status", {}),
                    "assinatura_base64":     found.get("assinatura_base64", ""),
                }
            else:
                payload = {"nome": "", "foto": "", "username": u, "cpf": "", "cidade": "", "acordo": {}}
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/api/creator/photo"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            foto_url = qs.get("url", [""])[0]
            if not foto_url:
                self.send_response(400); self.end_headers(); return
            try:
                req_headers = {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                    "Referer": "https://www.instagram.com/",
                }
                req = urllib.request.Request(foto_url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=8) as r:
                    img_data = r.read()
                    content_type = r.headers.get("Content-Type", "image/jpeg")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "max-age=86400")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(img_data)
            except Exception:
                self.send_response(404); self.end_headers()

        elif self.path in ("/", "/dashboard"):
            html_file = os.path.join(os.path.dirname(__file__), "dashboard.html")
            try:
                with open(html_file, "rb") as f:
                    body = f.read()
            except FileNotFoundError:
                body = DASHBOARD_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        elif self.path.split("?")[0] == "/api/yampi/pedidos":
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                dias = int(qs.get("dias",["30"])[0])
                env = load_env()
                token = env.get("YAMPI_TOKEN",""); secret = env.get("YAMPI_SECRET","")
                STATUS_LABEL = {1:"Aguardando",2:"Em análise",3:"Aprovado",4:"PIX Pendente",
                                5:"Separando",6:"Entregue",7:"Cancelado",8:"Enviado",
                                10:"Nota Fiscal",12:"Pronto p/ Envio",15:"Estorno"}
                pedidos = []
                for page in range(1, 20):
                    d = yampi_get("orders", {"page": page, "limit": 50,
                        "include": "customer,items,shipping_address"}, YAMPI_ALIAS, token, secret)
                    rows = d.get("data", [])
                    if not rows: break
                    stop = False
                    for o in rows:
                        created_raw = o.get("created_at", "")
                        if isinstance(created_raw, dict): created_raw = created_raw.get("date","")
                        created = created_raw[:10] if created_raw else ""
                        try:
                            from datetime import date
                            diff = (date.today() - date.fromisoformat(created)).days
                            if diff > dias: stop = True; break
                        except: pass
                        c    = o.get("customer",{}).get("data",{}) if isinstance(o.get("customer"),dict) else {}
                        addr = o.get("shipping_address",{}).get("data",{}) if isinstance(o.get("shipping_address"),dict) else {}
                        items= o.get("items",{}).get("data",[]) if isinstance(o.get("items"),dict) else []
                        nome = c.get("name","") or (c.get("first_name","")+" "+c.get("last_name","")).strip()
                        tel_obj = c.get("phone",{})
                        tel = tel_obj.get("full_number","") if isinstance(tel_obj,dict) else str(tel_obj or "")
                        itens_str = ", ".join(
                            (i.get("data",i) if isinstance(i,dict) else i).get("name","?") if isinstance((i.get("data",i) if isinstance(i,dict) else i),dict) else "?"
                            for i in items
                        )
                        valor = float(o.get("total","0") or "0")
                        pedidos.append({
                            "numero": o.get("number",""),
                            "data": created,
                            "cliente": nome,
                            "email": c.get("email",""),
                            "telefone": tel,
                            "itens": itens_str,
                            "valor": f"{valor:.2f}",
                            "pagamento": o.get("payment_method",""),
                            "status_id": o.get("status_id",0),
                            "status": STATUS_LABEL.get(o.get("status_id",0),""),
                            "cupom": (o.get("coupon") or {}).get("code","") if isinstance(o.get("coupon"),dict) else "",
                            "cidade": addr.get("city",""),
                            "rastreio": o.get("tracking_code",""),
                        })
                    if stop: break
                body = json.dumps({"pedidos": pedidos}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({"erro": str(e)}).encode()
                self.send_response(500)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(body)

        elif self.path.split("?")[0] == "/api/yampi/recompra":
            try:
                from datetime import date
                env = load_env()
                token = env.get("YAMPI_TOKEN",""); secret = env.get("YAMPI_SECRET","")
                hoje = date.today()
                recompra = []
                for page in range(1, 20):
                    d = yampi_get("orders", {"page": page, "limit": 50,
                        "include": "customer,items,shipping_address"}, YAMPI_ALIAS, token, secret)
                    rows = d.get("data", [])
                    if not rows: break
                    stop = False
                    for o in rows:
                        sid = o.get("status_id", 0)
                        if sid not in (6, 8, 3): continue
                        created_raw = o.get("created_at","")
                        if isinstance(created_raw, dict): created_raw = created_raw.get("date","")
                        created = created_raw[:10] if created_raw else ""
                        try:
                            diff = (hoje - date.fromisoformat(created)).days
                        except: diff = 0
                        if diff > 60: stop = True; break
                        if diff < 22 or diff > 35: continue
                        c = o.get("customer",{}).get("data",{}) if isinstance(o.get("customer"),dict) else {}
                        items = o.get("items",{}).get("data",[]) if isinstance(o.get("items"),dict) else []
                        nome_completo = c.get("name","") or (c.get("first_name","")+" "+c.get("last_name","")).strip()
                        nome = nome_completo.split()[0] if nome_completo else "Cliente"
                        tel_obj = c.get("phone",{})
                        tel = tel_obj.get("full_number","") if isinstance(tel_obj,dict) else str(tel_obj or "")
                        tel_digits = "".join(filter(str.isdigit, tel))
                        itens_str = ", ".join(
                            (i.get("data",i) if isinstance(i,dict) else i).get("name","?") if isinstance((i.get("data",i) if isinstance(i,dict) else i),dict) else "?"
                            for i in items
                        )
                        valor = float(o.get("total","0") or "0")
                        msg = (f"Oi {nome}! 💚\n\nPercebemos que seu PowerMind deve estar chegando ao fim "
                               f"— já fazem {diff} dias desde o seu pedido.\n\n"
                               f"Muitas clientes já estão no Kit 2x (Power Duo) ou 3x para garantir "
                               f"o resultado sem interrupção — e economiza bastante.\n\n"
                               f"Quer garantir o próximo agora? 👇\n"
                               f"https://www.powermindbr.com.br/")
                        wa_link = f"https://wa.me/55{tel_digits}?text={urllib.parse.quote(msg)}" if tel_digits else ""
                        recompra.append({
                            "nome": nome_completo,
                            "pedido": o.get("number",""),
                            "data": created,
                            "dias_desde": diff,
                            "itens": itens_str,
                            "valor": f"{valor:.2f}",
                            "whatsapp_link": wa_link,
                            "mensagem": msg,
                        })
                    if stop: break
                body = json.dumps({"recompra": recompra}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({"erro": str(e)}).encode()
                self.send_response(500)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(body)

        elif self.path.split("?")[0] == "/api/meta/resumo-dia":
            try:
                env = load_env()
                token = env.get("META_TOKEN","")
                today_str = __import__("datetime").date.today().isoformat()
                time_range_json = '{"since":"' + today_str + '","until":"' + today_str + '"}'
                url = ("https://graph.facebook.com/v19.0/act_4170730686474512/insights"
                       "?level=campaign&fields=campaign_name,spend,impressions,clicks,ctr,cpm,"
                       "actions,action_values&time_range=" + time_range_json +
                       "&access_token=" + token)
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as r:
                    meta = json.loads(r.read())
                camps = []
                totais = {"gasto":0,"impressoes":0,"cliques":0,"compras":0,"receita":0}
                for c in meta.get("data",[]):
                    gasto = float(c.get("spend",0))
                    impr  = int(c.get("impressions",0))
                    cliq  = int(c.get("clicks",0))
                    ctr   = float(c.get("ctr",0))
                    cpm   = float(c.get("cpm",0))
                    acts  = {a["action_type"]:float(a["value"]) for a in c.get("actions",[])}
                    avs   = {a["action_type"]:float(a["value"]) for a in c.get("action_values",[])}
                    compras = acts.get("purchase",acts.get("omni_purchase",0))
                    receita = avs.get("purchase",avs.get("omni_purchase",0))
                    roas  = round(receita/gasto,2) if gasto>0 else 0
                    cpa   = round(gasto/compras,2) if compras>0 else 0
                    camps.append({"nome":c.get("campaign_name",""),"gasto":f"{gasto:.2f}",
                                  "impressoes":impr,"cliques":cliq,"ctr":f"{ctr:.2f}",
                                  "cpm":f"{cpm:.2f}","compras":compras,"receita":f"{receita:.2f}",
                                  "roas":f"{roas:.2f}","cpa":f"{cpa:.2f}"})
                    totais["gasto"]+=gasto; totais["impressoes"]+=impr; totais["cliques"]+=cliq
                    totais["compras"]+=compras; totais["receita"]+=receita
                tg=totais["gasto"]; tc=totais["compras"]; tr=totais["receita"]
                ti=totais["impressoes"]; tcliq=totais["cliques"]
                totais_fmt = {
                    "gasto":f"{tg:.2f}","impressoes":ti,"cliques":tcliq,
                    "ctr":f"{(tcliq/ti*100):.2f}" if ti>0 else "0",
                    "cpm":f"{(tg/ti*1000):.2f}" if ti>0 else "0",
                    "compras":tc,"receita":f"{tr:.2f}",
                    "roas":f"{tr/tg:.2f}" if tg>0 else "0",
                    "cpa":f"{tg/tc:.2f}" if tc>0 else "0",
                }
                body = json.dumps({"campanhas":camps,"totais":totais_fmt}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({"erro": str(e)}).encode()
                self.send_response(500)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/fechamento/gerar":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            try:
                payload = json.loads(body) if length else {}
                mes     = payload.get("mes")
                rel     = gerar_fechamento_mes(mes)
                resp    = json.dumps(rel, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"erro": str(e)}).encode())
            return

        if self.path == "/api/lancamento":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            try:
                entry  = json.loads(body)
                saved  = save_lancamento(entry)
                resp   = json.dumps(saved, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/lancamento/delete":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            try:
                data         = json.loads(body)
                lanc_id      = data.get("id")
                excluido_por = data.get("excluido_por", "Desconhecido")
                alvo         = delete_lancamento(lanc_id, excluido_por)
                if alvo:
                    resp = json.dumps({"ok": True, "excluido": alvo}, ensure_ascii=False).encode()
                    self.send_response(200)
                else:
                    resp = json.dumps({"ok": False, "erro": "não encontrado"}).encode()
                    self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path in ("/api/fixos/add", "/api/fixos/delete"):
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            try:
                data   = json.loads(body)
                fixos  = load_fixos()
                if self.path == "/api/fixos/add":
                    nome      = data.get("nome","").strip()
                    valor     = float(data.get("valor", 0))
                    categoria = data.get("categoria", "Outros").strip()
                    if nome and valor > 0:
                        fixos[nome] = {"valor": valor, "categoria": categoria}
                        save_fixos(fixos)
                        _cache["ts"] = 0
                elif self.path == "/api/fixos/delete":
                    nome = data.get("nome","").strip()
                    if nome in fixos:
                        del fixos[nome]
                        save_fixos(fixos)
                        _cache["ts"] = 0
                resp = json.dumps({"ok": True, "fixos": fixos}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/save":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                entry    = json.loads(raw)
                username = entry.get("username", "").strip()
                if not username:
                    raise ValueError("username obrigatório")
                creators = load_creators()
                if not entry.get("cadastrado_em"):
                    entry["cadastrado_em"] = datetime.now().strftime("%d/%m/%Y")
                idx = next((i for i, c in enumerate(creators) if c.get("username") == username), None)
                if idx is not None:
                    creators[idx] = entry
                else:
                    creators.append(entry)
                save_creators(creators)
                resp = json.dumps({"ok": True}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/delete":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data     = json.loads(raw)
                username = data.get("username", "").strip()
                creators = load_creators()
                creators = [c for c in creators if c.get("username") != username]
                save_creators(creators)
                resp = json.dumps({"ok": True}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/enrich":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data     = json.loads(raw)
                username = data.get("username", "").strip()
                result   = enrich_instagram(username)
                resp     = json.dumps(result, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/agenda/save":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                entry  = json.loads(raw)
                if not entry.get("id"):
                    entry["id"] = str(int(datetime.now().timestamp() * 1000))
                agenda = load_agenda()
                idx = next((i for i, a in enumerate(agenda) if a.get("id") == entry["id"]), None)
                if idx is not None:
                    agenda[idx] = entry
                else:
                    agenda.append(entry)
                save_agenda(agenda)
                self._json({"ok": True})
            except Exception as e:
                self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())

        elif self.path == "/api/agenda/concluir":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data   = json.loads(raw)
                aid    = data.get("id", "")
                agenda = load_agenda()
                for a in agenda:
                    if a.get("id") == aid:
                        a["concluido"]    = True
                        a["concluido_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                save_agenda(agenda)
                self._json({"ok": True})
            except Exception as e:
                self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())

        elif self.path == "/api/agenda/delete":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data   = json.loads(raw)
                aid    = data.get("id", "")
                agenda = load_agenda()
                agenda = [a for a in agenda if a.get("id") != aid]
                save_agenda(agenda)
                self._json({"ok": True})
            except Exception as e:
                self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/contrato-assinar":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data     = json.loads(raw)
                username = data.get("username", "").strip()
                assinatura = data.get("assinatura_base64", "")
                nome     = data.get("nome", "").strip()
                cpf      = data.get("cpf", "").strip()
                cidade   = data.get("cidade", "").strip()
                data_assinatura = data.get("data_assinatura", datetime.now().strftime("%d/%m/%Y %H:%M"))
                creators = load_creators()
                idx = next((i for i, c in enumerate(creators) if c.get("username") == username), None)
                if idx is not None:
                    creators[idx]["contrato_assinado"]    = True
                    creators[idx]["contrato_assinado_em"] = data_assinatura
                    creators[idx]["assinatura_base64"]    = assinatura
                    if cpf and not creators[idx].get("cpf"):
                        creators[idx]["cpf"] = cpf
                    if cidade and not creators[idx].get("cidade"):
                        creators[idx]["cidade"] = cidade
                else:
                    creators.append({
                        "username":            username,
                        "nome":                nome,
                        "foto":                "",
                        "cpf":                 cpf,
                        "cidade":              cidade,
                        "contrato_assinado":    True,
                        "contrato_assinado_em": data_assinatura,
                        "assinatura_base64":    assinatura,
                        "cadastrado_em":        datetime.now().strftime("%d/%m/%Y"),
                    })
                save_creators(creators)

                # Salvar contrato no Google Drive (pasta Contratos Creators)
                creator_data = creators[idx] if idx is not None else {"username": username, "nome": nome, "cpf": cpf, "cidade": cidade}
                ac = creator_data.get("acordo", {})
                Thread(target=sync_contrato_drive, args=(creator_data, ac, data_assinatura, assinatura), daemon=True).start()

                resp = json.dumps({"ok": True}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/postagem-status":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data     = json.loads(raw)
                username = data.get("username", "").strip()
                key      = data.get("key", "").strip()   # "2026-06-06_Reels"
                status   = data.get("status", "enviado") # enviado | pendente
                agora    = datetime.now().strftime("%d/%m/%Y %H:%M")
                creators = load_creators()
                idx = next((i for i, c in enumerate(creators) if c.get("username") == username), None)
                if idx is not None:
                    if "postagens_status" not in creators[idx]:
                        creators[idx]["postagens_status"] = {}
                    if status == "enviado":
                        creators[idx]["postagens_status"][key] = {"status": "enviado", "em": agora}
                    else:
                        creators[idx]["postagens_status"].pop(key, None)
                    save_creators(creators)
                    self._json({"ok": True})
                else:
                    self._json({"ok": False, "error": "creator not found"}, 404)
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)

        elif self.path == "/api/creator/dados-envio":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data        = json.loads(raw)
                username    = data.get("username", "").strip()
                cpf         = data.get("cpf", "").strip()
                telefone    = data.get("telefone", "").strip()
                cep         = data.get("cep", "").strip()
                rua         = data.get("rua", "").strip()
                numero      = data.get("numero", "").strip()
                complemento = data.get("complemento", "").strip()
                bairro      = data.get("bairro", "").strip()
                cidade      = data.get("cidade", "").strip()
                estado      = data.get("estado", "").strip()
                partes = [rua, numero]
                if complemento:
                    partes.append(complemento)
                partes += [bairro, cidade + "-" + estado, "CEP " + cep]
                endereco = ", ".join(p for p in partes if p)
                agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                creators = load_creators()
                idx = next((i for i, c in enumerate(creators) if c.get("username") == username), None)
                if idx is not None:
                    creators[idx]["cpf"]            = cpf
                    creators[idx]["telefone"]       = telefone
                    creators[idx]["endereco"]       = endereco
                    creators[idx]["dados_envio_ok"] = True
                    creators[idx]["dados_envio_em"] = agora
                else:
                    creators.append({
                        "username":       username,
                        "nome":           "",
                        "foto":           "",
                        "cpf":            cpf,
                        "telefone":       telefone,
                        "endereco":       endereco,
                        "dados_envio_ok": True,
                        "dados_envio_em": agora,
                        "cadastrado_em":  datetime.now().strftime("%d/%m/%Y"),
                    })
                save_creators(creators)
                resp = json.dumps({"ok": True}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/video-link":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                data     = json.loads(raw)
                username = data.get("username", "").strip()
                acao     = data.get("acao", "criar")
                creators = load_creators()
                # Busca: exata → sem @/case → por nome
                idx = next((i for i, c in enumerate(creators) if c.get("username","") == username), None)
                if idx is None:
                    u_clean = username.lstrip("@").lower()
                    idx = next((i for i, c in enumerate(creators)
                                if c.get("username","").lstrip("@").lower() == u_clean), None)
                if idx is None:
                    resp = json.dumps({"ok": False, "error": f"Creator '{username}' não encontrado. Salve o creator antes de criar a pasta."}).encode()
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp)
                    return

                creator = creators[idx]

                if acao == "get":
                    link = creator.get("video_drive_link", "")
                    resp = json.dumps({"ok": True, "link": link}, ensure_ascii=False).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp)
                    return

                # acao == "criar"
                link = criar_pasta_video_drive(creator)
                if link:
                    creators[idx]["video_drive_link"] = link
                    creators[idx]["video_pasta_em"]   = datetime.now().strftime("%d/%m/%Y %H:%M")
                    save_creators(creators)
                    resp = json.dumps({"ok": True, "link": link}, ensure_ascii=False).encode()
                    self.send_response(200)
                else:
                    resp = json.dumps({"ok": False, "error": "Falha ao criar pasta no Drive. Verifique o Apps Script."}).encode()
                    self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/script/chat":
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            try:
                body_data = json.loads(raw.decode())
                messages  = body_data.get("messages", [])
                creator   = body_data.get("creator", {})
                campanhas = body_data.get("campanhas", [])
                acordo    = body_data.get("acordo", {})

                env     = load_env()
                api_key = env.get("ANTHROPIC_API_KEY", "")

                if not api_key:
                    resp = json.dumps({"error": "API key não configurada"}).encode()
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp)
                    return

                creator_info = ""
                if creator:
                    creator_info = f"""
CREATOR SELECIONADO:
- Nome: {creator.get('nome', 'N/A')}
- Username: {creator.get('username', 'N/A')}
- Nicho/Categoria: {creator.get('nicho', creator.get('categoria', 'N/A'))}
- Seguidores: {creator.get('seguidores', 'N/A')}
- Compatibilidade PowerMind: {creator.get('compatibilidade', 'N/A')}
- Bio: {creator.get('bio', 'N/A')}
- Cidade: {creator.get('cidade', 'N/A')}
"""

                acordo_info = ""
                if acordo and acordo.get('inicio'):
                    freq_label = {'diario':'Diário','semanal':'Semanal','mensal':'Mensal','total':'Aleatório no período','nenhum':'Sem postagem'}
                    acordo_info = f"""
ACORDO DE PARCERIA (contrato assinado):
- Período: {acordo.get('inicio','—')} até {acordo.get('fim','—')}
- Redes sociais: {acordo.get('redes','Instagram')}
- Horário combinado: {acordo.get('hora','—')}
- Reels: {acordo.get('qtd_reels',0)} postagens · frequência {freq_label.get(acordo.get('freq_reels',''),'—')}
- Stories: {acordo.get('qtd_stories',0)} postagens · frequência {freq_label.get(acordo.get('freq_stories',''),'—')}
- Feed: {acordo.get('qtd_feed',0)} postagens · frequência {freq_label.get(acordo.get('freq_feed',''),'—')}
- Total combinado: {acordo.get('total_posts',0)} postagens
- Observações do acordo: {acordo.get('info_adicional','Nenhuma')}

FORMATOS PADRÃO DO ACORDO:
- Postagem padrão Reels: vídeo vertical 9:16, até 60s, gancho nos 3s iniciais, CTA no final, mencionar @powermindbr_
- Postagem padrão Stories: sequência de 3-5 stories, swipe up ou link na bio, tom direto e urgente
- Postagem padrão Feed: imagem ou carrossel, legenda educativa ou de prova social, hashtags
"""

                camp_info = ""
                if campanhas:
                    camp_info = "Campanhas Meta Ads ativas:\n"
                    for c in campanhas:
                        camp_info += f"- {c.get('name','')}: gasto R${c.get('spend',0)}, CTR {float(c.get('ctr',0)):.1f}%, ROAS {c.get('roas',0)}\n"

                system_prompt = f"""Você é especialista em criação de prompts e scripts de conteúdo para creators parceiros da PowerMind.
Cada prompt gerado deve ser pronto para uso imediato, respeitando o acordo firmado em contrato e o estilo do creator.

SOBRE A POWERMIND:
- Produto: Suplemento em sachê/pó para energia, foco e memória
- Ingredientes: Complexo B, C, D, E, Magnésio, Zinco e Ferro
- Zero açúcar, sabor Frutas Vermelhas, 30 sticks por embalagem
- Preços: 1 pacote R$157 · Power Duo R$274 · 3 pac. R$381 · 6 pac. R$702
- Garantia 30 dias · Cupom: COMPROUGANHOU · powermindbr.com.br
- Público: Mulheres 25-55 anos com cansaço, falta de foco e energia baixa

{creator_info}
{acordo_info}
{camp_info}

DIRETRIZES:
1. Sempre respeite o tipo de postagem do acordo (Reels/Stories/Feed) e o horário combinado
2. Adapte o tom e linguagem ao nicho e perfil do creator — soe natural, não robótico
3. Estrutura base: Dor → Solução PowerMind → Prova social → CTA com cupom COMPROUGANHOU
4. Reels: gancho forte nos primeiros 3s, máximo 60s, CTA verbal no final
5. Stories: 3-5 cards, cada um com 1 mensagem, CTA claro no último ("arrasta pra cima" ou "link na bio")
6. Feed: legenda de 150-300 palavras, educativa ou depoimento, 5-8 hashtags relevantes
7. Sempre incluir menção a @powermindbr_ e garantia de 30 dias
8. Se a postagem tiver data específica no acordo, referencie o contexto (dia da semana, proximidade de evento)

FORMATO DE SAÍDA:
**Tipo:** Reels / Stories / Feed
**Data do acordo:** DD/MM/AAAA (Dia da semana)
**Horário:** HH:MM
**Duração/Formato:** X segundos ou X cards
**Gancho (0-3s):**
**Desenvolvimento:**
**CTA:**
**Caption:**
**Hashtags:**
**Observação de publicação:**"""

                payload = {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 2000,
                    "system": system_prompt,
                    "messages": messages
                }
                req_data = json.dumps(payload).encode()
                import urllib.request as ur, threading, queue as _queue
                req = ur.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=req_data,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }
                )
                result_q = _queue.Queue()
                def _call_api():
                    try:
                        with ur.urlopen(req, timeout=90) as r:
                            result_q.put(("ok", json.loads(r.read())))
                    except Exception as ex:
                        result_q.put(("err", ex))
                t = threading.Thread(target=_call_api, daemon=True)
                t.start()
                t.join(timeout=95)
                if t.is_alive() or result_q.empty():
                    raise TimeoutError("A IA demorou muito para responder. Tente novamente.")
                status, value = result_q.get()
                if status == "err":
                    raise value
                reply = value["content"][0]["text"]
                resp = json.dumps({"reply": reply}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                resp = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)

        elif self.path == "/webhook/yampi":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_path = os.path.join(os.path.dirname(__file__), "webhook.log")
            try:
                payload = json.loads(body)
                # Registra payload bruto antes de processar
                with open(log_path, "a") as lf:
                    lf.write(f"[{ts}] RECEBIDO: {body.decode('utf-8', errors='replace')[:500]}\n")
                _handle_yampi_webhook(payload)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                with open(log_path, "a") as lf:
                    lf.write(f"[{ts}] ERRO: {e} | body: {body[:300]}\n")
                print(f"[Webhook Yampi] erro: {e}")
                self.send_response(200)  # sempre 200 para Yampi não retentar
                self.end_headers()
                self.wfile.write(b'{"ok":false}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # silencioso

# ── Main ───────────────────────────────────────────────────────────────────
def _loop_reconciliar_yampi():
    """Reconcilia pedidos a cada 60 segundos, para não depender só do webhook."""
    while True:
        reconciliar_yampi()
        time.sleep(60)

if __name__ == "__main__":
    print(f"🚀 PowerMind Dashboard — http://localhost:{PORT}")
    # Virada de mês — arquiva lançamentos do mês anterior se necessário
    virar_mes_se_necessario()
    # Reconcilia pedidos de hoje com a API Yampi (recupera webhooks perdidos) — loop a cada 10 min
    Thread(target=_loop_reconciliar_yampi, daemon=True).start()
    # Pré-carrega dados em background
    Thread(target=get_cached, daemon=True).start()
    # Abre browser após 1s
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{PORT}")
    Thread(target=open_browser, daemon=True).start()
    HTTPServer(("", PORT), Handler).serve_forever()
