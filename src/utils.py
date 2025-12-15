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

# --- FORMATAGE LISTES (Pour Discord) ---
def format_list_discord(lst, suffix=""):
    """Transforme une liste [(Joueur, Val), ...] en string pour Discord."""
    if not lst: return "Personne."
    # Format : Joueur (Val), Joueur (Val)
    items = [f"**{x[0]}** ({x[1]}{suffix})" for x in lst]
    return ", ".join(items)

def format_simple_list(lst):
    """Pour les listes sans valeurs (ex: Murailles [('Joueur', 0)] -> Joueur, Joueur)."""
    if not lst: return "Personne."
    names = [f"**{x[0]}**" for x in lst]
    return ", ".join(names)

# --- FONCTION D'ENVOI ROTW (COMPATIBLE V25) ---
def send_weekly_report_discord(data, dashboard_url):
    """
    Envoie le rapport ROTW structuré vers Discord via Webhook.
    Attend le dictionnaire 'data' généré par weekly.py (V25).
    """
    if not WEBHOOK_URL:
        return "URL Webhook manquante."

    meta = data['meta']
    stats = data['stats']
    lists = data['lists']
    
    # 1. PODIUM
    podium_txt = ""
    medals = ["🥇", "🥈", "🥉"]
    for p in data['podium']:
        crown = " 👑" if p.get('is_winner') else ""
        # Format : 🥇 **Joueur** • 45.2 pts (Tot: 250)
        podium_txt += f"{medals[p['rank']-1]} **{p['player']}**{crown} • {p['avg']:.1f} pts (Tot: {p['total']})\n"
    
    # 2. COURSE AU TRÔNE
    rotw_txt = ""
    if data.get('rotw_leaderboard'):
        for idx, (player, count) in enumerate(data['rotw_leaderboard'][:5]):
            icon = "🏆" if idx == 0 else "▪️"
            rotw_txt += f"{icon} **{player}** : {count}\n"
    else:
        rotw_txt = "_Aucun titre._"

    # 3. STATS & LISTES
    sniper_txt = format_list_discord(lists['sniper'], " BP")
    muraille_txt = format_simple_list(lists['muraille']) # Juste les noms
    remontada_txt = format_list_discord(lists['remontada'], " pts")
    sunday_txt = format_list_discord(lists['sunday'], " pts")
    perfect_txt = ", ".join([f"**{p}**" for p in data['perfect']]) if data['perfect'] else "Aucun."

    # 4. ANALYSE (Bloc Texte)
    analysis_txt = ""
    if data.get('analysis'):
        analysis_txt = "\n".join(data['analysis'])
    else:
        analysis_txt = "_Pas de dynamique majeure détectée._"

    # 5. CONSTRUCTION EMBED
    embed = {
        "title": f"🦖 ROTW • DECK #{meta['week_num']}",
        "description": f"**{meta['dates']}**\n\n📊 **Moyenne Team :** {stats['avg']:.1f} pts ({stats['diff']})",
        "color": meta['color'], # Couleur dynamique (Vert/Jaune/Rouge selon score)
        "fields": [
            # Ligne 1 : Podium & Trône
            {"name": "🏆 PODIUM SEMAINE", "value": podium_txt, "inline": True},
            {"name": "👑 COURSE AU TRÔNE", "value": rotw_txt, "inline": True},
            
            # Ligne 2 : KPIs
            {"name": "💎 THE PERFECT (30+)", "value": perfect_txt, "inline": False},
            
            # Ligne 3 : Distinctions
            {"name": "🎯 SNIPER", "value": sniper_txt, "inline": True},
            {"name": "🛡️ MURAILLE (0 Carotte)", "value": muraille_txt, "inline": True},
            
            # Ligne 4 : Progression & Clutch
            {"name": "🚀 PROGRESSION", "value": remontada_txt, "inline": True},
            {"name": "🌅 SUNDAY CLUTCH", "value": sunday_txt, "inline": True},
            
            # Ligne 5 : Deep Dive
            {"name": "🔬 ANALYSE & DYNAMIQUES", "value": analysis_txt, "inline": False},
            
            # Footer Stats
            {"name": "📈 TEAM PULSE", "value": f"🎯 **{stats['bp']}** Best Picks  |  🥕 **{stats['carrots']}** Carottes  |  🛡️ **{stats['safe_zone']}** Safe Zone (>30)", "inline": False},
            
            {"name": "", "value": f"👉 [Accéder au Dashboard]({dashboard_url})", "inline": False}
        ],
        "footer": {"text": "War Room V25 • Raptors Data Department 🦖"}
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

# --- FONCTION LEGACY (Garder pour compatibilité stats.py si besoin) ---
def format_winner(player): return f"**{player}**"
