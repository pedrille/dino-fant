import requests
import random
import streamlit as st
from src.config import PACERS_PUNCHLINES, DISCORD_AVATAR_URL

# --- 4. DISCORD ---
def send_discord_webhook(day_df, pick_num, url_app):
    if "DISCORD_WEBHOOK" not in st.secrets: return "missing_secret"
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
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
            "fields": [{"name": "🏆 LE PODIUM", "value": podium_text, "inline": False}, {"name": "", "value": f"👉 [Voir le Dashboard complet]({url_app})", "inline": False}],
            "footer": {"text": footer_text}
        }]
    }
    try: requests.post(webhook_url, json=data); return "success"
    except Exception as e: return str(e)
