import streamlit as st
import pandas as pd
import time
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components

# --- IMPORTS MODULAIRES (V2 ARCHITECTURE) ---
from src.config import C_BG, C_TEXT, C_ACCENT, C_GOLD, C_BLUE, C_GREEN, SEASONS_CONFIG
from src.data_loader import load_data
from src.stats import compute_stats
import src.views as views

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(
    page_title="Raptors War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# --- 2. CSS PREMIUM (ORIGINAL RESTAURÉ) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    section[data-testid="stSidebar"] img {{ pointer-events: none; }}
    div[data-testid="stSidebarNav"] {{ display: none; }} 
    .nav-link {{ font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }}
    h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    h1 {{ font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #FFF, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub-header {{ font-size: 0.9rem; color: #666; letter-spacing: 1.5px; margin-bottom: 25px; font-weight: 500; }}
    
    /* --- FIX SELECTBOX LABEL COLOR --- */
    .stSelectbox label {{ color: #E5E7EB !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem; }}

    /* --- FIX UI DASHBOARD : CLASSE GENERIQUE --- */
    .glass-card {{ 
        background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%); 
        backdrop-filter: blur(20px); 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        border-radius: 16px; 
        padding: 24px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }}

    /* --- NOUVELLE CLASSE SPECIFIQUE POUR LE HAUT DU DASHBOARD --- */
    .kpi-dashboard-fixed {{
        height: 190px; 
        display: flex;
        flex-direction: column;
        justify-content: center; 
    }}
    
    .trend-section-title {{ font-family: 'Rajdhani'; font-size: 1.2rem; font-weight: 700; color: #FFF; margin-bottom: 5px; border-left: 4px solid #555; padding-left: 10px; }}
    .trend-section-desc {{ font-size: 0.8rem; color: #888; margin-bottom: 15px; padding-left: 14px; font-style: italic; }}
    .trend-box {{ background: rgba(255,255,255,0.03); border-radius: 12px; padding: 15px; border: 1px solid rgba(255,255,255,0.05); height: 100%; }}
    .hot-header {{ color: {C_ACCENT}; border-bottom: 1px solid rgba(206, 17, 65, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .cold-header {{ color: {C_BLUE}; border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .t-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .t-row:last-child {{ border-bottom: none; }}
    .t-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.2rem; text-align: right; }}
    .t-sub {{ font-size: 0.7rem; color: #666; display: block; margin-top: 2px; text-align: right; }}
    .t-name {{ font-weight: 500; color: #DDD; font-size: 0.95rem; }}
    .hof-badge {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; background: rgba(255,255,255,0.05); }}
    .hof-player {{ font-family: 'Rajdhani'; font-size: 1.6rem; font-weight: 700; color: #FFF; }}
    .hof-stat {{ font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 800; text-align: right; line-height: 1; }}
    .hof-unit {{ font-size: 0.7rem; color: #666; text-align: right; font-weight: 600; text-transform: uppercase; }}
    .kpi-label {{ color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
    /* CORRECTION TAILLE DE POLICE ADAPTATIVE */
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

    /* --- TOOLTIP INFO SAISON --- */
    .season-info-icon {{
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.3);
        cursor: help;
        z-index: 10;
        transition: color 0.3s;
    }}
    .season-info-icon:hover {{
        color: #FFF;
    }}
    
    .season-tooltip {{
        visibility: hidden;
        width: 220px;
        background-color: rgba(10, 10, 10, 0.95);
        color: #EEE;
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 100;
        top: 35px; /* Apparaît sous l'icône */
        right: 0;
        border: 1px solid #444;
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        line-height: 1.4;
        box-shadow: 0 4px 20px rgba(0,0,0,0.8);
        opacity: 0;
        transition: opacity 0.3s;
        pointer-events: none; 
    }}

    .season-info-icon:hover .season-tooltip {{
        visibility: visible;
        opacity: 1;
    }}
    
    .st-label {{ color: #CCC; font-weight:700; display:block; margin-bottom:2px; }}
    
    /* TEAM HQ & GRILLES */
    .stat-box-mini {{ 
        background: rgba(255,255,255,0.03); 
        border:1px solid rgba(255,255,255,0.05); 
        border-radius:12px; 
        padding: 20px 10px; 
        text-align:center; 
        height:100%; 
        display:flex; 
        flex-direction:column; 
        justify-content:center; 
        margin-bottom: 0px; 
    }}
    .stat-mini-val {{ font-family:'Rajdhani'; font-weight:700; font-size:1.8rem; color:#FFF; line-height:1; }}
    .stat-mini-lbl {{ font-size:0.75rem; color:#888; text-transform:uppercase; margin-top:8px; letter-spacing:1px; }}
    .stat-mini-sub {{ font-size:0.7rem; font-weight:600; margin-top:4px; color:#555; }}
    
    /* Player Lab - Match Pills FIXED CENTERING WITH TARGET BELOW */
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

    .match-row {{ 
        display: flex; 
        flex-direction: row-reverse; 
        overflow-x: auto;
        gap: 4px; 
        padding-bottom: 8px;
        width: 100%;
        justify-content: flex-start; 
    }}

    /* Boutons Streamlit Fix */
    .stButton button {{
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
        font-weight: 600 !important;
        font-family: 'Rajdhani', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .stButton button:hover {{
        border-color: {C_ACCENT} !important;
        color: {C_ACCENT} !important;
        background-color: #111 !important;
    }}

    .stPlotlyChart {{ width: 100% !important; }}
    div[data-testid="stDataFrame"] {{ border: none !important; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 2rem; }}
    
    /* Records Card Adjustment */
    .hq-card-row {{ display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.1); }}
    .hq-card-row:last-child {{ border-bottom:none; }}
    .hq-val {{ font-family:'Rajdhani'; font-weight:800; font-size:1.8rem; color:#FFF; }}
    .hq-lbl {{ font-size:0.8rem; color:#AAA; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
    
    .chart-desc {{ font-size:0.8rem; color:#888; margin-bottom:10px; font-style:italic; }}
    .gauge-container {{ width: 100%; background-color: #222; border-radius: 10px; margin-bottom: 15px; }}
    .gauge-fill {{ height: 10px; border-radius: 10px; transition: width 1s ease-in-out; }}
    .gauge-label {{ display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px; color: #DDD; }}
    
    /* TOP 5 PICKS STYLING */
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
    .tp-tags {{ font-size: 0.7rem; color: {C_GOLD}; font-weight: 600; }}
    
    .tp-score-big {{ 
        font-family: 'Rajdhani'; 
        font-weight: 800; 
        font-size: 1.8rem; 
        color: #FFF; 
        line-height: 1; 
        margin-left: 15px;
        flex-shrink: 0;
        min-width: 60px;
        text-align: right;
    }}

    /* RADAR LEGEND CUSTOM */
    .legend-box {{
        display: flex; flex-direction: column; justify-content: center; height: 100%;
        padding-left: 20px; border-left: 1px solid #333;
    }}
    .legend-item {{ margin-bottom: 15px; }}
    .legend-title {{ color: {C_ACCENT}; font-family: 'Rajdhani'; font-weight: 700; font-size: 1rem; margin-bottom: 2px; }}
    .legend-desc {{ color: #888; font-size: 0.8rem; line-height: 1.3; }}

    /* Widget Title Custom */
    .widget-title {{ font-family: 'Rajdhani'; font-weight: 700; text-transform: uppercase; color: #AAA; letter-spacing: 1px; margin-bottom: 5px; }}
    
    /* TRENDS PAGE STYLING */
    .trend-card-row {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    .trend-card-row:last-child {{ border: none; }}
    .trend-name {{ font-weight: 500; color: #DDD; }}
    .trend-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.1rem; }}
    .trend-delta {{ font-size: 0.8rem; margin-left: 8px; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

# --- 3. MAIN APP ENGINE ---
try:
    # UX BOOSTER (Auto-scroll top)
    components.html("""
    <script>
        window.parent.document.querySelector('.main').scrollTo(0, 0);
        const navLinks = window.parent.document.querySelectorAll('.nav-link');
        navLinks.forEach((link) => {
            link.addEventListener('click', () => {
                setTimeout(() => {
                    const closeBtn = window.parent.document.querySelector('button[data-testid="baseButton-header"]');
                    if (window.parent.innerWidth <= 768 && closeBtn) { closeBtn.click(); }
                }, 200);
            });
        });
    </script>
    """, height=0, width=0)

    with st.spinner('🦖 Analyse des données en cours...'):
        # LOAD DATA
        df, team_rank, bp_map, team_history, daily_max_map = load_data()
    
    # --- SÉLECTEUR TEMPOREL (SIDEBAR) ---
    with st.sidebar:
        st.markdown("<div style='text-align:center; margin-bottom: 20px;'>", unsafe_allow_html=True)
        try:
            st.image("raptors-ttfl-min.png", use_container_width=True) 
        except: pass
        st.markdown("</div>", unsafe_allow_html=True)
        
        # SÉLECTEUR DE PÉRIODE
        st.markdown("<div style='font-family:Rajdhani; font-weight:700; color:#AAA; margin-bottom:5px; font-size:0.9rem; letter-spacing:1px'>📅 PÉRIODE ACTIVE</div>", unsafe_allow_html=True)
        
        # 1. On récupère le dernier pick joué sur la totalité des données
        real_current_pick = df['Pick'].max() if df is not None and not df.empty else 0
        
        # 2. FILTRAGE : On ne garde que "Saison Complète" ET les périodes commencées
        options_saisons = []
        for s_name, (s_start, s_end) in SEASONS_CONFIG.items():
            # Toujours afficher la vue globale
            if "SAISON COMPLÈTE" in s_name:
                options_saisons.append(s_name)
            # Pour les périodes, on affiche SEULEMENT si le pick actuel a dépassé le début
            elif real_current_pick >= s_start:
                options_saisons.append(s_name)
        
        # 3. LOGIQUE AUTO-FOCUS (Sur la liste filtrée)
        default_ix = 0 
        for i, s_name in enumerate(options_saisons):
            # On récupère les bornes via la config globale
            s_start, s_end = SEASONS_CONFIG[s_name]
            
            # Si le pick actuel est DANS cette période (et que ce n'est pas la saison complète)
            if "SAISON COMPLÈTE" not in s_name and s_start <= real_current_pick <= s_end:
                default_ix = i
                break
        
        # 4. Création du sélecteur avec la liste épurée
        selected_season_name = st.selectbox("Période", options_saisons, index=default_ix, label_visibility="collapsed", key="season_selector")
        
        # BOUTON REFRESH INTELLIGENT (ANTI-SPAM 60s)
        st.write("---")
        if 'last_refresh_time' not in st.session_state:
            st.session_state['last_refresh_time'] = 0

        if st.button("🔄 ACTUALISER LES DONNÉES", use_container_width=True):
            current_time = time.time()
            if current_time - st.session_state['last_refresh_time'] > 60:
                st.cache_data.clear()
                st.session_state['last_refresh_time'] = current_time
                st.toast("✅ Données mises à jour !", icon="🦖")
                time.sleep(1) # Petit délai pour l'UX
                st.rerun()
            else:
                wait_time = 60 - int(current_time - st.session_state['last_refresh_time'])
                st.toast(f"⏳ Doucement ! Attendez encore {wait_time}s.", icon="✋")

        start_pick, end_pick = SEASONS_CONFIG[selected_season_name]
        
        latest_pick = 0 
        
        # --- CRUCIAL : ON GARDE UNE COPIE DE TOUTE LA SAISON (POUR HOF & RECORDS & BONUS & NO-CARROT) ---
        df_full_history = df.copy() if df is not None else pd.DataFrame()

        # FILTRAGE POUR L'AFFICHAGE (Dashboard, Lab, etc.)
        if df is not None and not df.empty:
            df = df[(df['Pick'] >= start_pick) & (df['Pick'] <= end_pick)].copy()
            
            if df.empty and selected_season_name != "🏆 SAISON COMPLÈTE":
                st.warning(f"⏳ La période '{selected_season_name}' n'a pas encore commencé.")
                st.stop()
            else:
                latest_pick = df['Pick'].max() if not df.empty else 0

        # MENU NAVIGATION - Weekly Report AJOUTÉ
        menu = option_menu(menu_title=None, options=["Dashboard", "Team HQ", "Player Lab", "Bonus x2", "No-Carrot", "Trends", "Hall of Fame", "Weekly Report"], icons=["grid-fill", "people-fill", "person-bounding-box", "lightning-charge-fill", "shield-check", "fire", "trophy-fill", "calendar-check"], default_index=0, styles={"container": {"padding": "0!important", "background-color": "#000000"}, "icon": {"color": "#666", "font-size": "1.1rem"}, "nav-link": {"font-family": "Rajdhani, sans-serif", "font-weight": "700", "font-size": "15px", "text-transform": "uppercase", "color": "#AAA", "text-align": "left", "margin": "5px 0px", "--hover-color": "#111"}, "nav-link-selected": {"background-color": C_ACCENT, "color": "#FFF", "icon-color": "#FFF", "box-shadow": "0px 4px 20px rgba(206, 17, 65, 0.4)"}})
        st.markdown(f"""<div style='position: fixed; bottom: 30px; width: 100%; padding-left: 20px;'><div style='color:#444; font-size:10px; font-family:Rajdhani; letter-spacing:2px; text-transform:uppercase'>Pick Actuel #{int(latest_pick)}<br>War Room v22.0</div></div>""", unsafe_allow_html=True)

    # --- BANDEAU UI (AMÉLIORÉ) ---
    if selected_season_name != "🏆 SAISON COMPLÈTE":
        season_color = C_ACCENT 
        if "WINTER" in selected_season_name: season_color = C_BLUE 
        elif "NEW YEAR" in selected_season_name: season_color = C_GOLD 
        elif "FINAL" in selected_season_name: season_color = C_GREEN 
        
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, {season_color} 0%, rgba(0,0,0,0) 100%); padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; border-left: 6px solid #FFF; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color: #FFF; font-family: 'Rajdhani'; font-weight: 800; font-size: 1.5rem; text-transform: uppercase; letter-spacing: 2px;">
                        {selected_season_name.split('(')[0]}
                    </div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; font-weight: 600; text-transform:uppercase; letter-spacing:1px; margin-top:2px;">
                        🎯 PICKS #{start_pick} à #{end_pick}
                    </div>
                </div>
                <div style="background:rgba(0,0,0,0.4); padding:5px 15px; border-radius:20px; color:#FFF; font-weight:700; font-size:0.8rem; border:1px solid rgba(255,255,255,0.2)">
                    MODE TOURNOI ACTIF
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # GLOBAL METRIC
    if df is not None and not df.empty:
        team_avg_per_pick = df['Score'].mean()
    else:
        team_avg_per_pick = 0

    if df is not None and not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False).copy()
        
        # COMPUTE STATS
        full_stats = compute_stats(df, bp_map, daily_max_map)
        
        # OPTIMISATION : BP Calculation Check DIRECTEMENT depuis le dataframe
        total_bp_team = full_stats['BP_Count'].sum()

        # --- CALCUL TEAM NO CARROT STREAK (TASK 4) ---
        team_streak_nc = 0
        sorted_picks = sorted(df['Pick'].unique(), reverse=True)
        for p_id in sorted_picks:
            daily_min = df[df['Pick'] == p_id]['Score'].min()
            if daily_min >= 20: team_streak_nc += 1
            else: break
            
        # --- ROUTING VERS LES VUES MODULAIRES ---
        if menu == "Dashboard":
            views.render_dashboard(day_df, full_stats, latest_pick, team_avg_per_pick, team_streak_nc, df)
        
        elif menu == "Team HQ":
            views.render_team_hq(df, latest_pick, team_rank, team_history, team_avg_per_pick, total_bp_team, full_stats)
        
        elif menu == "Player Lab":
            views.render_player_lab(df, full_stats)
        
        elif menu == "Bonus x2":
            # ON PASSE df_full_history POUR AVOIR LA SAISON COMPLETE PAR DEFAUT
            views.render_bonus_x2(df_full_history)
        
        elif menu == "No-Carrot":
            views.render_no_carrot(df, team_streak_nc, full_stats, df_full_history)
        
        elif menu == "Trends":
            views.render_trends(df, latest_pick)
        
        elif menu == "Hall of Fame":
            views.render_hall_of_fame(df_full_history, bp_map, daily_max_map)
        
        elif menu == "Weekly Report":
            # ON PASSE df_full_history POUR ANALYSER TOUTE LA SAISON
            views.render_weekly_report(df_full_history)

    else: 
        st.warning("⚠️ Aucune donnée trouvée.")

except Exception as e: 
    # Affiche l'erreur en mode "Joli" pour le débogage si besoin
    st.error(f"🔥 Critical Error: {e}")
