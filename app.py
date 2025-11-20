import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import numpy as np
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Raptors War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# --- 2. CSS PREMIUM (CORRECTIONS INCLUSES) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Rajdhani:wght@500;700&display=swap');

    /* BASE */
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Inter', sans-serif; }
    
    /* --- CORRECTION SIDEBAR ICON (IMPORTANT) --- */
    [data-testid="stSidebarCollapseButton"] { color: #FFFFFF !important; }
    [data-testid="stSidebarCollapseButton"] svg { fill: #FFFFFF !important; color: #FFFFFF !important; }
    
    /* SIDEBAR STYLE */
    section[data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #222; }
    
    /* TYPOGRAPHIE */
    h1, h2, h3 { font-family: 'Rajdhani', sans-serif; text-transform: uppercase; letter-spacing: 1px; }
    h1 { 
        font-size: 3.2rem; font-weight: 700; margin-bottom: 0;
        background: linear-gradient(90deg, #FFFFFF, #888); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    }
    h2 { 
        font-size: 1.6rem; color: #CE1141; margin-top: 3rem; margin-bottom: 1.5rem; 
        border-left: 4px solid #CE1141; padding-left: 15px;
    }

    /* UI CARDS */
    .card {
        background: linear-gradient(180deg, rgba(30, 30, 30, 0.4) 0%, rgba(10, 10, 10, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        transition: transform 0.2s;
    }
    .card:hover { border-color: #CE1141; transform: translateY(-3px); }
    
    /* KPI BOXES */
    .kpi-box {
        background: #0F0F0F; border: 1px solid #222; border-radius: 8px;
        padding: 15px; text-align: center; transition: 0.2s;
    }
    .kpi-box:hover { border-color: #CE1141; }
    .kpi-label { font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-val { font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 700; color: white; }
    .kpi-sub { font-size: 0.75rem; color: #CE1141; font-weight: 600; }

    /* BADGES HALL OF FAME */
    .badge { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; margin-bottom: 10px; }
    .bg-gold { background: rgba(255, 215, 0, 0.15); color: #FFD700; border: 1px solid #FFD700; }
    .bg-fire { background: rgba(206, 17, 65, 0.15); color: #FF5252; border: 1px solid #FF5252; }
    .bg-ice { background: rgba(59, 130, 246, 0.15); color: #64B5F6; border: 1px solid #64B5F6; }
    .bg-green { background: rgba(34, 197, 94, 0.15); color: #4ADE80; border: 1px solid #4ADE80; }
    
    /* CLEANUP */
    div[data-testid="stDataFrame"] { border: none !important; }
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return pd.DataFrame()
        df_raw = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", usecols=None, header=None)
        
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_raw.iloc[pick_row_idx, 1:], errors='coerce')
        data_start_idx = pick_row_idx + 1
        
        df_players = df_raw.iloc[data_start_idx:data_start_idx+50].copy()
        df_players = df_players.rename(columns={0: 'Player'})
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme", "0 et négatif"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)]
        df_players = df_players.dropna(subset=['Player'])

        valid_cols_map = {idx: int(val) for idx, val in picks_series.items() if pd.notna(val) and val > 0}
        cols_to_keep = ['Player'] + list(valid_cols_map.keys())
        cols_to_keep = [c for c in cols_to_keep if c in df_players.columns]
        
        df_clean = df_players[cols_to_keep].copy().rename(columns=valid_cols_map)
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        
        return df_long.dropna(subset=['Score', 'Pick'])
    except: return pd.DataFrame()

def compute_stats(df):
    stats = []
    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        scores = d['Score'].values
        
        # Séries & Calculs
        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
            
        carottes = len(scores[scores < 20])
        nukes = len(scores[scores >= 50])
        plus_30 = len(scores[scores >= 30])
        
        # Momentum (Derniers 5 vs Saison)
        last5_avg = scores[-5:].mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        
        stats.append({
            'Player': p,
            'Total': scores.sum(),
            'Moyenne': scores.mean(),
            'Best': scores.max(),
            'Last': scores[-1], # Score de la nuit dernière
            'Last5': last5_avg,
            'Last15': scores[-15:].mean() if len(scores) >= 15 else scores.mean(),
            'Streak30': streak_30,
            'Count30': plus_30,
            'Carottes': carottes,
            'Nukes': nukes,
            'Momentum': momentum,
            'Games': len(scores)
        })
    return pd.DataFrame(stats)

# --- 4. DISCORD ---
def send_discord_webhook(top_player, avg_score, pick_num, url_app):
    if "DISCORD_WEBHOOK" not in st.secrets: return "missing_secret"
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    
    data = {
        "username": "Raptors War Room",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png",
        "embeds": [{
            "title": f"🦖 DEBRIEF • PICK #{int(pick_num)}",
            "description": "Mise à jour des scores effectuée.",
            "color": 13504833,
            "fields": [
                {"name": "🔥 MVP", "value": f"**{top_player['Player']}**\n`{int(top_player['Score'])}` pts", "inline": True},
                {"name": "📊 Moyenne", "value": f"`{int(avg_score)}` pts", "inline": True},
                {"name": "🔗 Accès", "value": f"[Ouvrir le Dashboard]({url_app})", "inline": False}
            ],
            "footer": {"text": "Raptors Elite System"}
        }]
    }
    try:
        result = requests.post(webhook_url, json=data)
        return "success" if result.status_code == 204 else f"error: {result.status_code}"
    except Exception as e: return f"error: {e}"

# --- 5. HELPERS ---
def kpi(label, value, sub=""):
    st.markdown(f"""<div class="kpi-box"><div class="kpi-label">{label}</div><div class="kpi-val">{value}</div><div class="kpi-sub">{sub}</div></div>""", unsafe_allow_html=True)

# --- 6. MAIN APP ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        full_stats = compute_stats(df)
        leader = full_stats.sort_values('Total', ascending=False).iloc[0]
        
        with st.sidebar:
            st.image("raptors-ttfl-min.png", width=100) # Votre logo
            menu = option_menu(
                menu_title=None,
                options=["Dashboard", "Team HQ", "Player Lab", "Formes", "Hall of Fame", "Admin"],
                icons=["grid-fill", "people-fill", "person-bounding-box", "activity", "trophy-fill", "shield-lock"],
                default_index=0,
                styles={"nav-link-selected": {"background-color": "#CE1141", "color": "white"}}
            )
            st.markdown(f"<div style='text-align:center; color:#444; font-size:11px; margin-top:20px'>PICK #{int(latest_pick)}</div>", unsafe_allow_html=True)

        # --- DASHBOARD ---
        if menu == "Dashboard":
            st.markdown(f"<h1>RAPTORS <span style='color:#CE1141'>DASHBOARD</span></h1>", unsafe_allow_html=True)
            st.markdown(f"<p class='subtitle'>Pick #{int(latest_pick)}</p>", unsafe_allow_html=True)
            
            top = day_df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi("MVP DU JOUR", top['Player'], f"{int(top['Score'])} PTS")
            with c2: kpi("MOYENNE TEAM", int(day_df['Score'].mean()), "POINTS")
            with c3: kpi("TOTAL NUIT", int(day_df['Score'].sum()), "POINTS")
            with c4: kpi("MAILLOT JAUNE", leader['Player'], f"{int(leader['Total'])} PTS")
            
            st.markdown("<br>", unsafe_allow_html=True)
            c_left, c_right = st.columns([2, 1])
            with c_left:
                st.markdown("### 📊 Performance Nuit")
                fig = px.bar(day_df, x='Player', y='Score', text='Score', color='Score', color_continuous_scale=['#333', '#CE1141'])
                fig.update_traces(textposition='outside')
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, yaxis=dict(showgrid=True, gridcolor='#222'), height=350, showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            with c_right:
                st.markdown("### 📋 Classement")
                html = "<div style='background:#0F0F0F; border-radius:8px; border:1px solid #222;'>"
                for i, r in day_df.reset_index().iterrows():
                    color = "#CE1141" if i==0 else "#eee"
                    html += f"<div style='padding:10px 15px; border-bottom:1px solid #222; display:flex; justify-content:space-between;'><span style='color:{color}; font-weight:600'>#{i+1} {r['Player']}</span><span style='font-family:Rajdhani; font-weight:700'>{int(r['Score'])}</span></div>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

        # --- TEAM HQ ---
        elif menu == "Team HQ":
            st.markdown("<h1>TEAM <span style='color:#CE1141'>HQ</span></h1>", unsafe_allow_html=True)
            
            st.markdown("### ⚡ Le Sprint (7 Derniers Jours)")
            # Data Logic 7 Jours
            df_sorted = df.sort_values('Pick')
            df_sorted['Cumul'] = df_sorted.groupby('Player')['Score'].cumsum()
            min_zoom = max(1, latest_pick - 7)
            df_zoom = df_sorted[df_sorted['Pick'] >= min_zoom]
            
            # Chart
            fig = px.line(df_zoom, x='Pick', y='Cumul', color='Player', markers=True, color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'},
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#222'),
                hovermode="x unified", height=450
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 🎯 Distribution des Points")
            fig_dist = px.violin(df, x='Player', y='Score', color='Player', box=True, points="all")
            fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, showlegend=False, yaxis=dict(gridcolor='#222'))
            st.plotly_chart(fig_dist, use_container_width=True)

        # --- PLAYER LAB ---
        elif menu == "Player Lab":
            st.markdown("<h1>PLAYER <span style='color:#CE1141'>LAB</span></h1>", unsafe_allow_html=True)
            sel_player = st.selectbox("Joueur", sorted(df['Player'].unique()))
            p_stats = full_stats[full_stats['Player'] == sel_player].iloc[0]
            
            k1, k2, k3, k4 = st.columns(4)
            with k1: kpi("TOTAL", int(p_stats['Total']))
            with k2: kpi("MOYENNE", f"{p_stats['Moyenne']:.1f}")
            with k3: kpi("BEST", int(p_stats['Best']))
            with k4: kpi("CAROTTES", int(p_stats['Carottes']), "⚠️ < 20 pts")
            
            st.markdown("---")
            st.markdown("### 📊 Historique")
            p_hist = df[df['Player'] == sel_player].sort_values('Pick')
            fig = go.Figure([go.Bar(x=p_hist['Pick'], y=p_hist['Score'], marker_color='#333')])
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=350)
            st.plotly_chart(fig, use_container_width=True)

        # --- FORMES ---
        elif menu == "Formes":
            st.markdown("<h1>MOMENTUM <span style='color:#CE1141'>TRACKER</span></h1>", unsafe_allow_html=True)
            hot = full_stats.sort_values('Last5', ascending=False).head(3)
            cold = full_stats.sort_values('Last5', ascending=True).head(3)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🔥 ON FIRE (Last 5)")
                for _, r in hot.iterrows():
                    st.markdown(f"<div class='card' style='border-left:4px solid #CE1141; margin-bottom:10px'><div style='font-weight:bold; font-size:1.2rem'>{r['Player']}</div><div style='font-family:Rajdhani; font-size:2rem; font-weight:700'>{r['Last5']:.1f} <span style='font-size:0.8rem; color:#666'>MOYENNE</span></div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown("### ❄️ DANS LE DUR")
                for _, r in cold.iterrows():
                    st.markdown(f"<div class='card' style='border-left:4px solid #3B82F6; margin-bottom:10px'><div style='font-weight:bold; font-size:1.2rem'>{r['Player']}</div><div style='font-family:Rajdhani; font-size:2rem; font-weight:700'>{r['Last5']:.1f} <span style='font-size:0.8rem; color:#666'>MOYENNE</span></div></div>", unsafe_allow_html=True)

        # --- HALL OF FAME (8 BADGES) ---
        elif menu == "Hall of Fame":
            st.markdown("<h1>HALL OF <span style='color:#CE1141'>FAME</span></h1>", unsafe_allow_html=True)
            
            # Calculs
            sniper = full_stats.sort_values('Moyenne', ascending=False).iloc[0]
            torche = full_stats.sort_values('Last15', ascending=False).iloc[0]
            intouch = full_stats.sort_values('Streak30', ascending=False).iloc[0]
            nuke = full_stats.sort_values('Nukes', ascending=False).iloc[0]
            lapin = full_stats.sort_values('Carottes', ascending=False).iloc[0]
            fusee = full_stats.sort_values('Momentum', ascending=False).iloc[0]
            diamant = day_df.iloc[0] # MVP Nuit
            bouclier = full_stats.sort_values('Count30', ascending=False).iloc[0]
            
            c1, c2 = st.columns(2)
            
            def hof_card(badge, color_class, title, player, val, unit, desc):
                return f"""
                <div class="card" style="margin-bottom:15px;">
                    <div class="badge {color_class}">{badge} {title}</div>
                    <div style="display:flex; justify-content:space-between; align-items:end;">
                        <div><div style="font-size:1.2rem; font-weight:700">{player}</div><div style="color:#888; font-size:0.8rem">{desc}</div></div>
                        <div style="font-family:Rajdhani; font-size:1.8rem; font-weight:700">{val} <span style="font-size:0.8rem">{unit}</span></div>
                    </div>
                </div>
                """

            with c1:
                st.markdown(hof_card("🏆", "bg-gold", "LE SNIPER", sniper['Player'], f"{sniper['Moyenne']:.1f}", "PTS", "Meilleure moyenne saison"), unsafe_allow_html=True)
                st.markdown(hof_card("🔥", "bg-fire", "LA TORCHE", torche['Player'], f"{torche['Last15']:.1f}", "PTS", "Moyenne sur 15 jours"), unsafe_allow_html=True)
                st.markdown(hof_card("🚀", "bg-green", "LA FUSÉE", fusee['Player'], f"+{fusee['Momentum']:.1f}", "DIFF", "Progression vs Moyenne"), unsafe_allow_html=True)
                st.markdown(hof_card("💎", "bg-ice", "LE DIAMANT", diamant['Player'], int(diamant['Score']), "PTS", "MVP de la dernière nuit"), unsafe_allow_html=True)

            with c2:
                st.markdown(hof_card("⚡", "bg-gold", "L'INTOUCHABLE", intouch['Player'], int(intouch['Streak30']), "MATCHS", "Série actuelle > 30 pts"), unsafe_allow_html=True)
                st.markdown(hof_card("🛡️", "bg-green", "LE BOUCLIER", bouclier['Player'], int(bouclier['Count30']), "MATCHS", "Total scores > 30 pts"), unsafe_allow_html=True)
                st.markdown(hof_card("💣", "bg-fire", "ATOMIC BOMB", nuke['Player'], int(nuke['Nukes']), "NUKES", "Scores > 50 pts"), unsafe_allow_html=True)
                st.markdown(hof_card("🥕", "bg-ice", "LE LAPIN", lapin['Player'], int(lapin['Carottes']), "CAROTTES", "Scores < 20 pts"), unsafe_allow_html=True)

        # --- ADMIN ---
        elif menu == "Admin":
            st.markdown("<h1>ZONE <span style='color:#CE1141'>ADMIN</span></h1>", unsafe_allow_html=True)
            if st.button("🚀 ENVOYER NOTIF DISCORD", type="primary"):
                app_url = "https://dino-fant-tvewyye4t3dmqfeuvqsvmg.streamlit.app/"
                with st.spinner("Envoi..."):
                    res = send_discord_webhook(day_df.iloc[0], day_df['Score'].mean(), latest_pick, app_url)
                if res == "success": st.success("Envoyé !")
                else: st.error(f"Erreur : {res}")

    else: st.info("Chargement...")
except Exception as e: st.error("Erreur technique"); st.write(e)
