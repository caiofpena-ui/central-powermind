#!/usr/bin/env python3
"""
PowerMind CRM Server — roda em localhost:8081
Serve o CRM de creators independente do dashboard (porta 8080).
Inicia com o Mac via launchd (com.powermind.crm.plist).
"""
import json, os, random, urllib.request, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PORT               = 8081
CREATORS_FILE      = os.path.join(os.path.dirname(__file__), "creators.json")
CRM_HTML_FILE      = os.path.join(os.path.dirname(__file__), "crm.html")
CADASTRO_HTML_FILE = os.path.join(os.path.dirname(__file__), "cadastro.html")
CONTRATO_HTML_FILE = os.path.join(os.path.dirname(__file__), "contrato.html")


# ── Helpers de persistência ────────────────────────────────────────────────

def load_creators():
    try:
        with open(CREATORS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_creators(data):
    with open(CREATORS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Enriquecimento Instagram ───────────────────────────────────────────────

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


# ── Handler HTTP ───────────────────────────────────────────────────────────

def _cors(handler):
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")

class CRMHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        _cors(self)
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/crm"):
            try:
                with open(CRM_HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"crm.html not found")

        elif self.path.split('?')[0] in ("/contrato", "/contrato.html"):
            try:
                with open(CONTRATO_HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                _cors(self)
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"contrato.html not found")

        elif self.path in ("/cadastro", "/cadastro.html"):
            try:
                with open(CADASTRO_HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                _cors(self)
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"cadastro.html not found")

        elif self.path.startswith("/api/creator/public"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            u = qs.get("u", [""])[0].strip()
            creators = load_creators()
            found = next((c for c in creators if c.get("username") == u), None)
            if found:
                payload = {
                    "nome":     found.get("nome", ""),
                    "foto":     found.get("foto", ""),
                    "username": found.get("username", u),
                    "cpf":      found.get("cpf", ""),
                    "cidade":   found.get("cidade", ""),
                }
            else:
                payload = {"nome": "", "foto": "", "username": u, "cpf": "", "cidade": ""}
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            _cors(self)
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/api/creator/photo"):
            # Proxy para foto do Instagram — evita bloqueio CORS no browser
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            foto_url = qs.get("url", [""])[0]
            if not foto_url:
                self.send_response(400); self.end_headers(); return
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                    "Referer": "https://www.instagram.com/",
                }
                req = urllib.request.Request(foto_url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as r:
                    img_data = r.read()
                    content_type = r.headers.get("Content-Type", "image/jpeg")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "max-age=86400")
                _cors(self)
                self.end_headers()
                self.wfile.write(img_data)
            except Exception as e:
                self.send_response(404); self.end_headers()

        elif self.path == "/api/creators":
            creators = load_creators()
            body = json.dumps(creators, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            _cors(self)
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw    = self.rfile.read(length)

        if self.path == "/api/creator/save":
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
                _cors(self)
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/delete":
            try:
                data     = json.loads(raw)
                username = data.get("username", "").strip()
                creators = load_creators()
                creators = [c for c in creators if c.get("username") != username]
                save_creators(creators)
                resp = json.dumps({"ok": True}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                _cors(self)
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/dados-envio":
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
                _cors(self)
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/contrato-assinar":
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
                resp = json.dumps({"ok": True}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                _cors(self)
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/api/creator/enrich":
            try:
                data     = json.loads(raw)
                username = data.get("username", "").strip()
                result   = enrich_instagram(username)
                resp     = json.dumps(result, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                _cors(self)
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # silencioso


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"PowerMind CRM Server — http://localhost:{PORT}")
    HTTPServer(("", PORT), CRMHandler).serve_forever()
