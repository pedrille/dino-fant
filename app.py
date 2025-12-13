# --- app.py ---
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components

# Import Modules
from src.config import C_BG, C_TEXT, C_ACCENT, C_GOLD, C_BLUE, C_GREEN, C_RED, C_BONUS, SEASONS_CONFIG
from src.data_loader import load_data
from src.stats import compute_stats
import src.views as views

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(page_title="Raptors War Room", layout="wide", page_icon="🦖", initial_sidebar_state="expanded")

# --- 2. CSS (RESTAURÉ DEPUIS L'ANCIEN FICHIER) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');
    
    /* GLOBAL */
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    section[data-testid="stSidebar"] img {{ pointer-events: none; }}
    div[data-testid="stSidebarNav"] {{ display: none; }} 
    .nav-link {{ font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }}
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    h1 {{ font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #FFF, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub-header {{ font-size: 0.9rem; color: #666; letter-spacing: 1.5px; margin-bottom: 25px; font-weight: 500; }}
    .widget-title {{ font-family: 'Rajdhani'; font-weight: 700; color: #AAA; margin-bottom: 5px; font-size: 0.9rem; letter-spacing: 1px; }}
    .chart-desc {{ color: #666; font-size: 0.8rem; margin-bottom: 10px; font-style: italic; }}

    /* UI CARDS GENERIQUE */
    .glass-card {{ 
        background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%); 
        backdrop-filter: blur(20px); 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        border-radius: 16px; 
        padding: 24px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }}

    /* KPI DASHBOARD FIXED HEIGHT (Pour alignement parfait) */
    .kpi-dashboard-fixed {{
        height: 190px; 
        display: flex;
        flex-direction: column;
        justify-content: center; 
    }}
    
    /* KPI ELEMENTS */
    .kpi-label {{ color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
    .kpi-num {{ 
        font-family: 'Rajdhani'; 
        font-weight: 800; 
        font-size: clamp(1.6rem, 2vw, 2.2rem); 
        line-height: 1.1; 
        color: #FFF; 
        white-space: nowrap; 
        overflow: hidden;
        text-overflow: ellipsis; 
    }}
    .kpi-sub {{ font-size: 0.8rem; margin-top: 5px; font-weight: 500; opacity: 0.9; }}

    /* MINI STATS GRID (TEAM HQ & LAB) */
    .stat-box-mini {{ 
        background: rgba(255,255,255,0.03); 
        border: 1px solid rgba(255,255,255,0.05); 
        border-radius: 12px; 
        padding: 20px 10px; 
        text-align: center; 
        height: 100%; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
    }}
    .stat-mini-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.8rem; color: #FFF; line-height: 1; }}
    .stat-mini-lbl {{ font-size: 0.75rem; color: #888; text-transform: uppercase; margin-top: 8px; letter-spacing: 1px; }}

    /* RECORDS CARD ROWS */
    .hq-card-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
    .hq-card-row:last-child {{ border-bottom: none; }}
    .hq-lbl {{ font-size: 0.8rem; color: #AAA; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }}
    .hq-val {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 1.8rem; color: #FFF; }}

    /* PLAYER LAB - MATCH PILLS (SCROLL HORIZONTAL) */
    .match-row {{ 
        display: flex; 
        flex-direction: row-reverse; 
        overflow-x: auto;
        gap: 4px; 
        padding-bottom: 8px;
        width: 100%;
        justify-content: flex-start; 
    }}
    .match-pill {{
        flex: 0 0 auto; 
        min-width: 40px; 
        height: 48px; 
        border-radius: 6px; 
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        justify-content: center; 
        font-family: 'Rajdhani'; 
        font-weight: 700; 
        font-size: 0.9rem;
        color: #FFF;
        margin: 0 2px;
        line-height: 1;
        padding-top: 2px;
    }}
    .mp-score {{ font-size: 1rem; }}
    .mp-icon {{ font-size: 0.6rem; margin-top: 2px; opacity: 0.9; }}

    /* TOP 5 PICKS CARDS */
    .top-pick-card {{
        display: flex; 
        align-items: center;
        background: linear-gradient(90deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.05);
        padding: 10px 15px;
        margin-bottom: 8px;
        border-radius: 8px;
        transition: all 0.2s;
    }}
    .top-pick-card:hover {{ background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.1); transform: translateX(5px); }}
    .tp-rank-badge {{ 
        font-family: 'Rajdhani'; font-weight: 800; font-size: 1rem; 
        width: 30px; height: 30px; 
        display: flex; align-items: center; justify-content: center;
        border-radius: 50%; 
        background: #222; border: 2px solid #444; color: #FFF;
        margin-right: 12px;
        flex-shrink: 0;
    }}
    .tp-content {{ flex-grow: 1; overflow: hidden; }}
    .tp-date {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }}
    .tp-tags {{ font-size: 0.7rem; color: {C_BONUS}; font-weight: 600; }}
    .tp-score-big {{ 
        font-family: 'Rajdhani'; font-weight: 800; font-size: 1.8rem; color: #FFF; line-height: 1; 
        margin-left: 15px; flex-shrink: 0; min-width: 60px; text-align: right;
    }}

    /* TRENDS & LEGENDS */
    .legend-box {{ display: flex; flex-direction: column; justify-content: center; height: 100%; padding-left: 20px; border-left: 1px solid #333; }}
    .legend-item {{ margin-bottom: 15px; }}
    .legend-title {{ color: {C_ACCENT}; font-family: 'Rajdhani'; font-weight: 700; font-size: 1rem; margin-bottom: 2px; }}
    .legend-desc {{ color: #888; font-size: 0.8rem; line-height: 1.3; }}
    
    .trend-box {{ background: rgba(255,255,255,0.03); border-radius: 12px; padding: 15px; border: 1px solid rgba(255,255,255,0.05); height: 100%; }}
    .hot-header {{ color: {C_ACCENT}; border-bottom: 1px solid rgba(206, 17, 65, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .cold-header {{ color: {C_BLUE}; border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .trend-card-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .trend-card-row:last-child {{ border: none; }}
    .trend-name {{ font-weight: 500; color: #DDD; }}
    .trend-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.1rem; }}
    .trend-delta {{ font-size: 0.8rem; margin-left: 8px; font-weight: 600; }}

    /* HALL OF FAME */
    .hof-badge {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; background: rgba(255,255,255,0.05); }}
    .hof-player {{ font-family: 'Rajdhani'; font-size: 1.6rem; font-weight: 700; color: #FFF; }}
    .hof-stat {{ font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 800; text-align: right; line-height: 1; }}
    .hof-unit {{ font-size: 0.7rem; color: #666; text-align: right; font-weight: 600; text-transform: uppercase; }}
    
    /* TOOLTIP INFO SAISON */
    .season-info-icon {{ position: absolute; top: 10px; right: 10px; font-size: 1rem; color: rgba(255, 255, 255, 0.3); cursor: help; z-index: 10; transition: color 0.3s; }}
    .season-info-icon:hover {{ color: #FFF; }}
    .season-tooltip {{ visibility: hidden; width: 220px; background-color: rgba(10, 10, 10, 0.95); color: #EEE; text-align: left; border-radius: 8px; padding: 12px; position: absolute; z-index: 100; top: 35px; right: 0; border: 1px solid #444; font-family: 'Inter', sans-serif; font-size: 0.75rem; line-height: 1.4; box-shadow: 0 4px 20px rgba(0,0,0,0.8); opacity: 0; transition: opacity 0.3s; pointer-events: none; }}
    .season-info-icon:hover .season-tooltip {{ visibility: visible; opacity: 1; }}
    .st-label {{ color: #CCC; font-weight:700; display:block; margin-bottom:2px; }}

    /* BOUTONS */
    .stButton button {{ background-color: #1F2937 !important; color: #FFFFFF !important; border: 1px solid #374151 !important; font-weight: 600 !important; font-family: 'Rajdhani', sans-serif !important; text-transform: uppercase; letter-spacing: 1px; }}
    .stButton button:hover {{ border-color: {C_ACCENT} !important; color: {C_ACCENT} !important; background-color: #111 !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. MAIN APP ---
try:
    # UX BOOSTER
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
            if "SAISON COMPLÈTE" in s_name: options_saisons.append(s_name)
            elif real_current_pick >= s_start: options_saisons.append(s_name)
        
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
        season_color = C_ACCENT 
        if "WINTER" in selected_season_name: season_color = C_BLUE 
        elif "NEW YEAR" in selected_season_name: season_color = C_GOLD 
        elif "FINAL" in selected_season_name: season_color = C_GREEN 
        
        st.markdown(f"""<div style="background: linear-gradient(90deg, {season_color} 0%, rgba(0,0,0,0) 100%); padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; border-left: 6px solid #FFF; box-shadow: 0 4px 20px rgba(0,0,0,0.5);"><div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="color: #FFF; font-family: 'Rajdhani'; font-weight: 800; font-size: 1.5rem; text-transform: uppercase; letter-spacing: 2px;">{selected_season_name.split('(')[0]}</div><div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; font-weight: 600; text-transform:uppercase; letter-spacing:1px; margin-top:2px;">🎯 PICKS #{start_pick} à #{end_pick}</div></div><div style="background:rgba(0,0,0,0.4); padding:5px 15px; border-radius:20px; color:#FFF; font-weight:700; font-size:0.8rem; border:1px solid rgba(255,255,255,0.2)">MODE TOURNOI ACTIF</div></div></div>""", unsafe_allow_html=True)
    
    team_avg_per_pick = df['Score'].mean() if df is not None and not df.empty else 0

    if df is not None and not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False).copy()
        full_stats = compute_stats(df, bp_map, daily_max_map)
        total_bp_team = full_stats['BP_Count'].sum()

        # Calcul Streak Team pour Sidebar (restauré)
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
