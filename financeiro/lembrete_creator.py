#!/usr/bin/env python3
"""
PowerMind — Lembrete Diário de Postagem de Creators
Roda às 09:00 via launchd (com.powermind.lembrete_creator.plist)
Verifica agendamentos para AMANHÃ e dispara notificação Mac + abre WhatsApp.
"""
import json, os, random, subprocess, urllib.parse
from datetime import datetime, timedelta

BASE_DIR      = os.path.dirname(__file__)
AGENDA_FILE   = os.path.join(BASE_DIR, "agenda.json")
CREATORS_FILE = os.path.join(BASE_DIR, "creators.json")

def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default

def salvar_lembrete_enviado(agenda, aid):
    for a in agenda:
        if a.get("id") == aid:
            a["lembrete_enviado"]    = True
            a["lembrete_enviado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    with open(AGENDA_FILE, "w") as f:
        json.dump(agenda, f, indent=2, ensure_ascii=False)

def gerar_texto(ag, creator):
    nome     = creator.get("nome", ag.get("creator", ""))
    primeiro = nome.split()[0] if nome else "Parceiro"
    tipo     = ag.get("tipo", "postagem")
    hora     = ag.get("hora", "")
    brief    = ag.get("briefing", "")
    tipo_icon = {"Reels":"🎬","Stories":"📲","Feed":"🖼️","TikTok":"🎵","Live":"🔴"}.get(tipo, "📌")

    # Puxar campos do acordo do creator
    ac        = creator.get("acordo", {})
    cupom     = ac.get("cupom", "COMPROUGANHOU")
    mencoes   = ac.get("mencoes", "@powermindbr_")
    hashtags  = ac.get("hashtags", "")
    aprovacao = ac.get("aprovacao", "nao")
    restricoes = ac.get("restricoes", "")

    bloco_obrigacoes = ""
    if cupom:     bloco_obrigacoes += f"🏷️ *Cupom:* {cupom}\n"
    if mencoes:   bloco_obrigacoes += f"👤 *Marcar:* {mencoes}\n"
    if hashtags:  bloco_obrigacoes += f"#️⃣ *Hashtags:* {hashtags}\n"
    if aprovacao == "sim":
        prazo = ac.get("prazo_rascunho", 1)
        bloco_obrigacoes += f"✅ *Atenção:* envie o rascunho {prazo} dia(s) antes para aprovação!\n"

    bloco_restricoes = f"\n⚠️ *Não esqueça:* {restricoes}" if restricoes else ""

    templates = [
        f"Oi, {primeiro}! 🌟\n\nTudo bem? Passando aqui com um lembrete especial: amanhã é o dia do nosso {tipo_icon} *{tipo}* {('às *' + hora + '*') if hora else ''}! 🎉\n\n"
        + (f"📌 *Briefing:* {brief}\n\n" if brief else "")
        + (bloco_obrigacoes + "\n" if bloco_obrigacoes else "")
        + bloco_restricoes
        + f"\nQualquer dúvida, estou aqui! Você vai arrebentar 💚\n\n— Equipe PowerMind 💪",

        f"Oii {primeiro}! ☀️\n\nLembrete do nosso {tipo_icon} *{tipo}* de amanhã{(' às *' + hora + '*') if hora else ''}! 🙌\n\n"
        + (f"✍️ _{brief}_\n\n" if brief else "")
        + (bloco_obrigacoes + "\n" if bloco_obrigacoes else "")
        + bloco_restricoes
        + f"\nObrigado por fazer parte da família PowerMind! 🔥\n\n— PowerMind 💚",

        f"Boa tarde, {primeiro}! 🌿\n\nO nosso combinado de amanhã — {tipo_icon} *{tipo}* {('às ' + hora) if hora else ''} — está chegando! 🚀\n\n"
        + (f"📋 {brief}\n\n" if brief else "")
        + (bloco_obrigacoes + "\n" if bloco_obrigacoes else "")
        + bloco_restricoes
        + f"\nConte com a gente sempre! Vai ser incrível 🌟\n\n— Equipe PowerMind",
    ]
    return random.choice(templates)

def notificar_mac(titulo, mensagem):
    script = f'display notification "{mensagem}" with title "{titulo}" sound name "Ping"'
    subprocess.run(["osascript", "-e", script], check=False)

def main():
    agenda   = load_json(AGENDA_FILE, [])
    creators = load_json(CREATORS_FILE, [])

    hoje   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    amanha = hoje + timedelta(days=1)
    amanha_str = amanha.strftime("%Y-%m-%d")

    pendentes = [
        a for a in agenda
        if not a.get("concluido")
        and not a.get("lembrete_enviado")
        and a.get("data") == amanha_str
    ]

    if not pendentes:
        print(f"[{datetime.now():%H:%M}] Nenhum agendamento para amanhã ({amanha_str}).")
        return

    print(f"[{datetime.now():%H:%M}] {len(pendentes)} agendamento(s) para amanhã.")

    for ag in pendentes:
        creator = next((c for c in creators if c.get("username") == ag.get("creator")), {})
        nome    = creator.get("nome", ag.get("creator", "Creator"))
        tipo    = ag.get("tipo", "postagem")
        tel     = creator.get("telefone", "")

        # Notificação Mac
        notificar_mac(
            f"📅 PowerMind — Postagem Amanhã",
            f"{nome} · {tipo} · {ag.get('hora','')}".strip(" ·")
        )

        # Abrir WhatsApp se tiver telefone
        if tel:
            num = tel.replace(r"\D", "")
            num = "".join(filter(str.isdigit, tel))
            if len(num) <= 11:
                num = "55" + num
            texto = gerar_texto(ag, creator)
            url   = "https://wa.me/" + num + "?text=" + urllib.parse.quote(texto)
            subprocess.Popen(["open", url])
            print(f"  → WhatsApp aberto para {nome} ({num})")
        else:
            print(f"  → {nome} sem telefone cadastrado, apenas notificação Mac.")

        salvar_lembrete_enviado(agenda, ag["id"])


# ─────────────────────────────────────────────────────────────────────────────
# CHECAGEM DE ATRASO — roda às 20:00 via launchd (modo "check_atraso")
# Verifica postagens do dia que não foram marcadas como concluídas
# ─────────────────────────────────────────────────────────────────────────────

def gerar_texto_atraso(ag, creator):
    nome     = creator.get("nome", ag.get("creator", ""))
    primeiro = nome.split()[0] if nome else "Parceiro"
    tipo     = ag.get("tipo", "postagem")
    hora     = ag.get("hora", "")
    tipo_icon = {"Reels":"🎬","Stories":"📲","Feed":"🖼️","TikTok":"🎵","Live":"🔴"}.get(tipo, "📌")
    return (
        f"Oi {primeiro}! 😊\n\n"
        f"Vi que o nosso {tipo_icon} *{tipo}* {('das ' + hora) if hora else 'de hoje'} ainda "
        f"não apareceu no feed. Tudo certo por aí?\n\n"
        f"Se precisar de ajuda com o briefing ou tiver algum imprevisto, me chama aqui! 💬\n\n"
        f"— Equipe PowerMind 💚"
    )

def check_atraso():
    """Verifica postagens de HOJE que passaram do horário e não foram concluídas."""
    agenda   = load_json(AGENDA_FILE, [])
    creators = load_json(CREATORS_FILE, [])
    agora    = datetime.now()
    hoje_str = agora.strftime("%Y-%m-%d")

    atrasados = []
    for ag in agenda:
        if ag.get("concluido"):
            continue
        if ag.get("data") != hoje_str:
            continue
        hora_str = ag.get("hora", "")
        if hora_str:
            try:
                hora_dt = datetime.strptime(hoje_str + " " + hora_str, "%Y-%m-%d %H:%M")
                if agora < hora_dt:
                    continue  # ainda não chegou a hora
            except:
                pass
        atrasados.append(ag)

    if not atrasados:
        print(f"[{agora:%H:%M}] Nenhum atraso de postagem hoje.")
        return

    print(f"[{agora:%H:%M}] {len(atrasados)} postagem(ns) pendente(s) hoje!")
    notificar_mac(
        f"⚠️ PowerMind — {len(atrasados)} postagem(ns) pendente(s)!",
        "Verifique os creators que ainda não postaram hoje."
    )

    for ag in atrasados:
        creator = next((c for c in creators if c.get("username") == ag.get("creator")), {})
        nome    = creator.get("nome", ag.get("creator", "Creator"))
        tipo    = ag.get("tipo", "postagem")
        hora    = ag.get("hora", "")
        print(f"  ⚠️  {nome} — {tipo} {hora}".strip())

        # Resolve WhatsApp: campo whatsapp > telefone
        tel = creator.get("whatsapp","") or creator.get("telefone","")
        if tel:
            num = "".join(filter(str.isdigit, tel))
            if len(num) <= 11:
                num = "55" + num
            texto = gerar_texto_atraso(ag, creator)
            url   = "https://wa.me/" + num + "?text=" + urllib.parse.quote(texto)
            subprocess.Popen(["open", url])
            print(f"     → WhatsApp de cobrança aberto para {nome}")
        else:
            print(f"     → {nome} sem WhatsApp cadastrado.")


if __name__ == "__main__":
    import sys
    modo = sys.argv[1] if len(sys.argv) > 1 else "lembrete"
    if modo == "check_atraso":
        check_atraso()
    else:
        main()
