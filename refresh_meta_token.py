#!/usr/bin/env python3
"""
Auto-renovação do Meta Token — roda via launchd todo dia 1 e 15 do mês.
Lê o token atual do .env, gera um novo long-lived (60 dias) e salva de volta.
"""
import urllib.request
import urllib.parse
import json
import os
import re
from datetime import datetime

ENV_FILE   = os.path.join(os.path.dirname(__file__), ".env")
BASE       = "https://graph.facebook.com/v19.0"
LOG_FILE   = os.path.join(os.path.dirname(__file__), "token_refresh.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def read_env():
    vals = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals

def write_env(vals):
    with open(ENV_FILE, "w") as f:
        for k, v in vals.items():
            f.write(f"{k}={v}\n")

env = read_env()
TOKEN      = env.get("META_TOKEN", "")
APP_ID     = env.get("META_APP_ID", "")
APP_SECRET = env.get("META_APP_SECRET", "")

if not all([TOKEN, APP_ID, APP_SECRET]):
    log("❌ Faltam credenciais no .env")
    exit(1)

log(f"Renovando token (primeiros 20 chars): {TOKEN[:20]}...")

params = urllib.parse.urlencode({
    "grant_type":        "fb_exchange_token",
    "client_id":         APP_ID,
    "client_secret":     APP_SECRET,
    "fb_exchange_token": TOKEN,
})

try:
    with urllib.request.urlopen(f"{BASE}/oauth/access_token?{params}") as r:
        result = json.loads(r.read())
        new_token = result.get("access_token", "")
        expires   = result.get("expires_in", 0)
        if not new_token:
            log(f"❌ Token vazio na resposta: {result}")
            exit(1)
        env["META_TOKEN"] = new_token
        write_env(env)
        log(f"✅ Token renovado! Expira em {int(expires)//86400} dias.")
except Exception as e:
    log(f"❌ Erro: {e}")
    exit(1)
