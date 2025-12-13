import unicodedata
import requests
import random
from src.config import DISCORD_AVATAR_URL, PACERS_PUNCHLINES

def get_uniform_color(score):
    """
    Retourne la couleur associée au score pour les graphiques.
    """
    if score < 20: return "#EF4444"   # C_RED (< 20)
    elif score < 40: return "#374151" # GRIS-MID  (20-39)
    else: return "#10B981"            # C_GREEN (40+)

def normalize_month(month_str):
    """
    Normalise une chaîne de caractères représentant un mois.
    Supprime les accents et met en minuscules.
    Ex: 'décembre' -> 'decembre'
    """
    if not isinstance(month_str, str):
        return month_str

    # Mettre en minuscule
    s = month_str.lower().strip()

    # Supprimer les accents
    # NFD décompose les caractères (ex: é -> e + accent aigu)
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

    return s

def send_discord_webhook(day_df, pick_num, url_app):
    """
    Envoie un récapitulatif du pick sur Discord via un Webhook.
    """
    import streamlit as st
    
    if "DISCORD_WEBHOOK" not in st.secrets: 
        return "missing_secret"
    
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    
    # Podium du jour (Top 3)
    top_3 = day_df.head(3).reset_index(drop=True)
    podium_text = ""
    medals = ["🥇", "🥈", "🥉"]
    
    for i, row in top_3.iterrows():
        bonus_icon = " 🌟x2" if row['IsBonus'] else ""
        bp_icon = " 🎯BP" if row.get('IsBP', False) else ""
        podium_text += f"{medals[i]} **{row['Player']}** • {int(row['Score'])} pts{bonus_icon}{bp_icon}\n"
    
    avg_score = int(day_df['Score'].mean())
    random_quote = random.choice(PACERS_PUNCHLINES)
    footer_text = "Pensée du jour • " + random_quote

    data = {
        "username": "RaptorsTTFL Dashboard",
        "avatar_url": DISCORD_AVATAR_URL,
        "embeds": [{
            "title": f"🏀 RECAP DU PICK #{int(pick_num)}",
            "description": f"Les matchs sont terminés, voici les scores de l'équipe !\n\n📊 **MOYENNE TEAM :** {avg_score} pts",
            "color": 13504833, 
            "fields": [
                {"name": "🏆 LE PODIUM", "value": podium_text, "inline": False}, 
                {"name": "", "value": f"👉 [Voir le Dashboard complet]({url_app})", "inline": False}
            ],
            "footer": {"text": footer_text}
        }]
    }
    
    try: 
        requests.post(webhook_url, json=data)
        return "success"
    except Exception as e: 
        return str(e)
