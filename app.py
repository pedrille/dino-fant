
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components

# Import Modules
from src.config import C_BG, C_TEXT, C_ACCENT, C_GOLD, C_BLUE, C_GREEN, SEASONS_CONFIG
from src.data_loader import load_data
from src.stats import compute_stats
import src.views as views

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(page_title="Raptors War Room", layout="wide", page_icon="🦖", initial_sidebar_state="expanded")

# --- 2. CSS ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    div[data-testid="stSidebarNav"] {{ display: none; }} 
    h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    h1 {{ font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #FFF, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .glass-card {{ background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
    .kpi-dashboard-fixed {{ height: 190px; display: flex; flex-direction: column; justify-content: center; }}
    .kpi-num {{ font-family: 'Rajdhani'; font-weight: 800; font-size: clamp(1.6rem, 2vw, 2.2rem); line-height: 1.1; color: #FFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .stButton button {{ background-color: #1F2937 !important; color: #FFFFFF !important; border: 1px solid #374151 !important; font-weight: 600 !important; font-family: 'Rajdhani', sans-serif !important; text-transform: uppercase; letter-spacing: 1px; }}
    .stButton button:hover {{ border-color: {C_ACCENT} !important; color: {C_ACCENT} !important; background-color: #111 !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. MAIN APP ---
try:
    components.html("""<script>window.parent.document.querySelector('.main').scrollTo(0, 0);</script>""", height=0, width=0)

    with st.spinner('🦖 Analyse des données en cours...'):
        df, team_rank, bp_map, team_history, daily_max_map = load_data()
    
    with st.sidebar:
        st.markdown("<div style='text-align:center; margin-bottom: 20px;'>", unsafe_allow_html=True)
        try: st.image("raptors-ttfl-min.png", use_container_width=True)
        except: pass
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='font-family:Rajdhani; font-weight:700; color:#AAA; margin-bottom:5px; font-size:0.9rem; letter-spacing:1px'>📅 PÉRIODE ACTIVE</div>", unsafe_allow_html=True)
        real_current_pick = df['Pick'].max() if df is not None and not df.empty else 0
        options_saisons = []
        for s_name, (s_start, s_end) in SEASONS_CONFIG.items():
            if "SAISON COMPLÈTE" in s_name or real_current_pick >= s_start: options_saisons.append(s_name)
        
        default_ix = 0 
        for i, s_name in enumerate(options_saisons):
            s_start, s_end = SEASONS_CONFIG[s_name]
            if "SAISON COMPLÈTE" not in s_name and s_start <= real_current_pick <= s_end:
                default_ix = i; break
        
        selected_season_name = st.selectbox("Période", options_saisons, index=default_ix, label_visibility="collapsed", key="season_selector")
        start_pick, end_pick = SEASONS_CONFIG[selected_season_name]
        
        latest_pick = 0 
        df_full_history = df.copy() if df is not None else pd.DataFrame()

        if df is not None and not df.empty:
            df = df[(df['Pick'] >= start_pick) & (df['Pick'] <= end_pick)].copy()
            if df.empty and selected_season_name != "🏆 SAISON COMPLÈTE":
                st.warning(f"⏳ La période '{selected_season_name}' n'a pas encore commencé.")
                st.stop()
            else: latest_pick = df['Pick'].max() if not df.empty else 0

        menu = option_menu(menu_title=None, options=["Dashboard", "Team HQ", "Player Lab", "Bonus x2", "No-Carrot", "Trends", "Hall of Fame", "Admin"], icons=["grid-fill", "people-fill", "person-bounding-box", "lightning-charge-fill", "shield-check", "fire", "trophy-fill", "shield-lock"], default_index=0, styles={"container": {"padding": "0!important", "background-color": "#000000"}, "nav-link-selected": {"background-color": C_ACCENT, "color": "#FFF"}})
        st.markdown(f"""<div style='position: fixed; bottom: 30px; width: 100%; padding-left: 20px;'><div style='color:#444; font-size:10px; font-family:Rajdhani; letter-spacing:2px; text-transform:uppercase'>Pick Actuel #{int(latest_pick)}<br>War Room v22.0</div></div>""", unsafe_allow_html=True)

    if selected_season_name != "🏆 SAISON COMPLÈTE":
        season_color = C_BLUE if "WINTER" in selected_season_name else (C_GOLD if "NEW YEAR" in selected_season_name else (C_GREEN if "FINAL" in selected_season_name else C_ACCENT))
        st.markdown(f"""<div style="background: linear-gradient(90deg, {season_color} 0%, rgba(0,0,0,0) 100%); padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; border-left: 6px solid #FFF; box-shadow: 0 4px 20px rgba(0,0,0,0.5);"><div style="color: #FFF; font-family: 'Rajdhani'; font-weight: 800; font-size: 1.5rem; text-transform: uppercase;">{selected_season_name.split('(')[0]}</div></div>""", unsafe_allow_html=True)
    
    team_avg_per_pick = df['Score'].mean() if df is not None and not df.empty else 0

    if df is not None and not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False).copy()
        full_stats = compute_stats(df, bp_map, daily_max_map)
        total_bp_team = full_stats['BP_Count'].sum()

        team_streak_nc = 0
        for p_id in sorted(df['Pick'].unique(), reverse=True):
            if df[df['Pick'] == p_id]['Score'].min() >= 20: team_streak_nc += 1
            else: break
            
        if menu == "Dashboard": views.render_dashboard(day_df, full_stats, latest_pick, team_avg_per_pick, team_streak_nc, df)
        elif menu == "Team HQ": views.render_team_hq(df, latest_pick, team_rank, team_history, team_avg_per_pick, total_bp_team)
        elif menu == "Player Lab": views.render_player_lab(df, full_stats)
        elif menu == "Bonus x2": views.render_bonus_x2(df)
        elif menu == "No-Carrot": views.render_no_carrot(df, team_streak_nc, full_stats)
        elif menu == "Trends": views.render_trends(df, latest_pick)
        elif menu == "Hall of Fame": views.render_hall_of_fame(df_full_history, bp_map, daily_max_map)
        elif menu == "Admin": views.render_admin(day_df, latest_pick)

    else: st.warning("⚠️ Aucune donnée trouvée.")
except Exception as e: st.error(f"🔥 Critical Error: {e}")
