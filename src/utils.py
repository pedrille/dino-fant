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

    meta = data.get('meta', {})
    stats = data.get('stats', {})
    lists = data.get('lists', {})
    
    # SEPARATEUR VISUEL
    SEP = "〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"

    # --- SÉCURITÉ 1 : COULEUR (INT OBLIGATOIRE) ---
    raw_color = meta.get('color', DISCORD_COLOR_RED)
    discord_color = DISCORD_COLOR_RED
    if isinstance(raw_color, str):
        try:
            discord_color = int(raw_color.replace('#', ''), 16)
        except:
            pass
    elif isinstance(raw_color, int):
        discord_color = raw_color

    # 1. PODIUM
    podium_txt = ""
    medals = ["🥇", "🥈", "🥉"]
    for p in data.get('podium', []):
        crown = " 👑" if p.get('is_winner') else ""
        podium_txt += f"{medals[p['rank']-1]} **{p['player']}**{crown} • {p['avg']:.1f} pts (Tot: {p['total']})\n"
    
    # 2. COURSE AU TRÔNE
    rotw_txt = ""
    if data.get('rotw_leaderboard'):
        for idx, (player, count) in enumerate(data['rotw_leaderboard'][:10]):
            icon = "🏆" if idx == 0 else "▪️"
            rotw_txt += f"{icon} **{player}** : {count}\n"
    
    # 3. STATS & LISTES
    sniper_txt = format_list_discord(lists.get('sniper', []), " BP")
    muraille_txt = format_simple_list(lists.get('muraille', []))
    remontada_txt = format_list_discord(lists.get('remontada', []), " pts")
    sunday_txt = format_list_discord(lists.get('sunday', []), " pts")
    
    perfect_list = data.get('perfect', [])
    perfect_txt = ", ".join([f"**{p}**" for p in perfect_list]) if perfect_list else "Aucun."

    # 4. ANALYSE (AVEC SÉCURITÉ DES 1024 CARACTÈRES - 8 LIGNES RANDOM)
    import random
    analysis_txt = ""
    if data.get('analysis'):
        # On copie la liste pour pouvoir la mélanger
        lignes_brutes = list(data['analysis'])
        random.shuffle(lignes_brutes) # Mélange aléatoire des joueurs
        
        lignes = [f"🔹 {line}" for line in lignes_brutes]
        
        # On coupe à 8 lignes maximum
        if len(lignes) > 8:
            analysis_txt = "\n".join(lignes[:8]) + f"\n🔹 _... et {len(lignes)-8} autres séries en cours (Voir App) !_"
        else:
            analysis_txt = "\n".join(lignes)
    else:
        analysis_txt = "_Pas de dynamique majeure détectée._"

    # --- SÉCURITÉ 2 : BOUCLIER ANTI-VIDE ---
    def safe_val(text, fallback="_Aucune donnée_"):
        text = str(text).strip()
        return text if text else fallback

    # 5. CONSTRUCTION EMBED AÉRÉ
    embed = {
        "title": safe_val(f"🦖 RAPTORS OF THE WEEK • DECK #{meta.get('week_num', '?')}"),
        "description": safe_val(f"**{meta.get('dates', '?')}**\n\n📊 **Moyenne Team :** {stats.get('avg', 0):.1f} pts ({stats.get('diff', '')})\n\n{SEP}"),
        "color": discord_color,
        "fields": [
            {"name": "🏆 PODIUM SEMAINE", "value": safe_val(podium_txt), "inline": True},
            {"name": "👑 COURSE AU TRÔNE", "value": safe_val(rotw_txt, "_Aucun titre._"), "inline": True},
            
            {"name": "💎 THE PERFECT (30+)", "value": safe_val(perfect_txt) + f"\n\n{SEP}", "inline": False},
            
            {"name": "🎯 SNIPER & CLUTCH", "value": safe_val(f"**Sniper :** {sniper_txt}\n**Sunday Clutch :** {sunday_txt}"), "inline": False},
            
            {"name": "🛡️ DÉFENSE & PROGRESSION", "value": safe_val(f"**Muraille (0 Carotte) :** {muraille_txt}\n**Progression :** {remontada_txt}") + f"\n\n{SEP}", "inline": False},
            
            {"name": "🔬 ANALYSE & DYNAMIQUES", "value": safe_val(analysis_txt, "_Pas de dynamique majeure._") + f"\n\n{SEP}", "inline": False},
            
            {"name": "📈 TEAM PULSE", "value": safe_val(f"🎯 **{stats.get('bp', 0)}** Best Picks  |  🥕 **{stats.get('carrots', 0)}** Carottes  |  🛡️ **{stats.get('safe_zone', 0)}** Safe Zone (>30)"), "inline": False},
            
            # SÉCURITÉ 3 : Nom de champ valide garanti
            {"name": "👉 LIEN RAPIDE", "value": f"[Accéder au Dashboard]({dashboard_url})", "inline": False}
        ],
        "footer": {"text": "War Room V25 • Generated by Python 🦖"}
    }

    payload = {
        "username": "Raptors Bot",
        "avatar_url": "https://raw.githubusercontent.com/pedrille/dino-fant/main/basketball_discord.png", 
        "embeds": [embed]
    }

    try:
        r = requests.post(WEBHOOK_URL, json=payload)
        if r.status_code in [200, 204]: return "success"
        # Si ça plante encore, on affiche le message complet de Discord pour debugger !
        else: return f"Erreur Discord {r.status_code}: {r.text}"
    except Exception as e:
        return str(e)
