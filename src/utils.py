import requests
import json
import streamlit as st
import unicodedata

# --- CONSTANTES ---
DISCORD_COLOR_RED = 13504833  # #CE1141 (Raptors Red)
WEBHOOK_URL = st.secrets["DISCORD_WEBHOOK"] if "DISCORD_WEBHOOK" in st.secrets else ""

# --- FONCTION DE NETTOYAGE ---
def normalize_month(month_str):
    if not isinstance(month_str, str): return "Inconnu"
    month_str = month_str.lower().strip()
    normalized = unicodedata.normalize('NFD', month_str).encode('ascii', 'ignore').decode("utf-8")
    return normalized

# --- FONCTIONS COULEURS ---
def get_uniform_color(score):
    try: s = float(score)
    except: return "#374151"
    if s >= 40: return "#10B981"
    if s < 20:  return "#EF4444"
    return "#374151"

# --- FORMATAGE LISTES ---
def format_list_discord(lst, suffix=""):
    """Transforme une liste [(Joueur, Val), ...] en string pour Discord."""
    if not lst: return "Personne."
    items = [f"**{x[0]}** ({x[1]}{suffix})" for x in lst]
    return ", ".join(items)

def format_simple_list(lst):
    """Pour les listes sans valeurs."""
    if not lst: return "Personne."
    names = [f"**{x[0]}**" for x in lst]
    return ", ".join(names)

# --- FONCTION LEGACY (Obligatoire pour éviter le crash Dashboard) ---
def format_winners_list(winners, suffix=""):
    if not winners: return "Personne."
    names = [f"**{w[0]}**" for w in winners]
    val = winners[0][1] 
    if len(names) == 1: return f"{names[0]} ({val}{suffix})"
    elif len(names) == 2: return f"{names[0]} & {names[1]} ({val}{suffix})"
    else: return f"{', '.join(names[:-1])} & {names[-1]} ({val}{suffix})"

# --- FONCTION D'ENVOI ROTW (V25 WIDE EDITION) ---
def send_weekly_report_discord(data, dashboard_url):
    if not WEBHOOK_URL: return "URL Webhook manquante."

    meta = data['meta']
    stats = data['stats']
    lists = data['lists']
    
    # SEPARATEUR VISUEL (Pour élargir et aérer)
    SEP = "〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"

    # 1. PODIUM
    podium_txt = ""
    medals = ["🥇", "🥈", "🥉"]
    for p in data['podium']:
        crown = " 👑" if p.get('is_winner') else ""
        podium_txt += f"{medals[p['rank']-1]} **{p['player']}**{crown} • {p['avg']:.1f} pts (Tot: {p['total']})\n"
    
    # 2. COURSE AU TRÔNE
    rotw_txt = ""
    if data.get('rotw_leaderboard'):
        for idx, (player, count) in enumerate(data['rotw_leaderboard'][:10]):
            icon = "🏆" if idx == 0 else "▪️"
            rotw_txt += f"{icon} **{player}** : {count}\n"
    else:
        rotw_txt = "_Aucun titre._"

    # 3. STATS & LISTES
    sniper_txt = format_list_discord(lists['sniper'], " BP")
    muraille_txt = format_simple_list(lists['muraille'])
    remontada_txt = format_list_discord(lists['remontada'], " pts")
    sunday_txt = format_list_discord(lists['sunday'], " pts")
    perfect_txt = ", ".join([f"**{p}**" for p in data['perfect']]) if data['perfect'] else "Aucun."

    # 4. ANALYSE
    analysis_txt = ""
    if data.get('analysis'):
        # Ajout d'un tiret pour faire une liste propre
        analysis_txt = "\n".join([f"🔹 {line}" for line in data['analysis']])
    else:
        analysis_txt = "_Pas de dynamique majeure détectée._"

   # 5. CONSTRUCTION EMBED AÉRÉ
    
    # --- CONVERTISSEUR DE COULEUR POUR DISCORD ---
    # Convertit le "#10B981" (texte) en entier pour ne pas faire crasher l'API
    discord_color = meta.get('color', DISCORD_COLOR_RED)
    if isinstance(discord_color, str) and discord_color.startswith('#'):
        try:
            discord_color = int(discord_color.lstrip('#'), 16)
        except:
            discord_color = DISCORD_COLOR_RED
    elif not isinstance(discord_color, int):
        discord_color = DISCORD_COLOR_RED

    embed = {
        "title": f"🦖 RAPTORS OF THE WEEK • DECK #{meta['week_num']}",
        "description": f"**{meta['dates']}**\n\n📊 **Moyenne Team :** {stats['avg']:.1f} pts ({stats['diff']})\n\n{SEP}",
        "color": discord_color, # <--- La couleur sécurisée est injectée ici
        "fields": [
            {"name": "🏆 PODIUM SEMAINE", "value": podium_txt, "inline": True},
            {"name": "👑 COURSE AU TRÔNE", "value": rotw_txt, "inline": True},
            
            {"name": "💎 THE PERFECT (30+)", "value": perfect_txt + f"\n\n{SEP}", "inline": False},
            
            {"name": "🎯 SNIPER & CLUTCH", "value": f"**Sniper :** {sniper_txt}\n**Sunday Clutch :** {sunday_txt}", "inline": False},
            
            {"name": "🛡️ DÉFENSE & PROGRESSION", "value": f"**Muraille (0 Carotte) :** {muraille_txt}\n**Progression :** {remontada_txt}\n\n{SEP}", "inline": False},
            
            {"name": "🔬 ANALYSE & DYNAMIQUES", "value": analysis_txt + f"\n\n{SEP}", "inline": False},
            
            {"name": "📈 TEAM PULSE", "value": f"🎯 **{stats['bp']}** Best Picks  |  🥕 **{stats['carrots']}** Carottes  |  🛡️ **{stats['safe_zone']}** Safe Zone (>30)", "inline": False},
            
            # Utilisation de l'espace invisible \u200B obligatoire pour Discord
            {"name": "\u200B", "value": f"👉 [Accéder au Dashboard]({dashboard_url})", "inline": False}
        ],
        "footer": {"text": "Raptors TTFL • STATS 🦖"}
    }

    payload = {
        "username": "Raptors Bot",
        "avatar_url": "https://raw.githubusercontent.com/pedrille/dino-fant/main/basketball_discord.png", 
        "embeds": [embed]
    }

    try:
        r = requests.post(WEBHOOK_URL, json=payload)
        if r.status_code in [200, 204]: return "success"
        else: return f"Erreur {r.status_code}: {r.text}"
    except Exception as e:
        return str(e)
