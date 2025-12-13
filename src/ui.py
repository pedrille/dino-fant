
import streamlit as st
import random
import requests
from src.config import C_ACCENT, C_GOLD, C_BLUE, C_GREEN, C_RED, C_TEXT, C_BONUS, DISCORD_AVATAR_URL, PACERS_PUNCHLINES

def kpi_card(label, value, sub, color="#FFF", is_fixed=False):
    # Si is_fixed est True (pour le haut du dashboard), on ajoute la classe spécifique
    style_class = "glass-card kpi-dashboard-fixed" if is_fixed else "glass-card"
    st.markdown(f"""<div class="{style_class}" style="text-align:center"><div class="kpi-label">{label}</div><div class="kpi-num" style="color:{color}">{value}</div><div class="kpi-sub" style="color:{C_ACCENT}">{sub}</div></div>""", unsafe_allow_html=True)

def section_title(title, subtitle):
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)

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
