import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import numpy as np
import requests
import streamlit.components.v1 as components
import random

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(
    page_title="Raptors War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# ✅ LIEN DE L'IMAGE DISCORD (RAW)
DISCORD_AVATAR_URL = "https://raw.githubusercontent.com/pedrille/dino-fant/main/basketball_discord.png"

# --- 1.5 CONFIG PUNCHLINES (ANTI-PACERS MIXÉES) ---
PACERS_PUNCHLINES = [
    "Un bon Pacer est un Pacer sous carotte 🥕",
    "PACERS : Petit Animal Chétif Et Rarement Stylé 🐁",
    "Les Pacers gèrent leur avance comme Doc Rivers gère un 3-1 📉",
    "Info : Les Pacers mangent les kiwis avec la peau 🥝",
    "Les Pacers c'est les Clippers : beaucoup de bruit, zéro bague 💍",
    "Si on change quelques lettres à Pacers, ça donne 'Trompette' 🎺",
    "PACER : Personne Ayant une Chatte EnoRme 🐱",
    "Stat du jour : 100% des Pacers portent des chaussettes avec des sandales 🧦",
    "L'effectif des Pacers est aussi solide que les genoux de Derrick Rose 🌹💔",
    "Définition de Pacers : 'Groupe de personnes ayant beaucoup de chance' 🍀",
    "Les Pacers sont une erreur de casting, comme Marvin Bagley devant Luka 🇸🇮",
    "Sondage : Les Pacers préfèrent les raisins secs aux pépites de chocolat 🍪",
    "PACERS : Pas Assez Compétents Et Réellement Surcotés 📉",
    "Le classement est formel : Les Pacers trichent (source : tkt) 🕵️‍♂️",
    "Ball Don't Lie : Les Pacers vont finir par payer l'addition 🗣️",
    "Info : Les Pacers applaudissent quand l'avion atterrit 👏✈️",
    "Les Pacers sont aussi aimés que Dillon Brooks 🐻",
    "Pacers ? Connais pas. Ça se mange ? 🍔",
    "Les Pacers font plus de briques que Westbrook un soir de pleine lune 🌕",
    "Un Pacer ne fait pas de Best Pick, il fait un 'Pick par erreur' 🤷‍♂️",
    "Le QI Basket des Pacers est inférieur au temps de jeu de Thanasis 🇬🇷",
    "Insolite : 100% des Pacers mettent de la pizza sur leur ananas 🍍",
    "Les Pacers passeront le 2ème tour quand Embiid le passera (jamais) 🚑",
    "Les Pacers c'est comme les éclairs au café... C'est de la m**** ☕",
    "Les Pacers croient que 'Tanking' est le nom d'un joueur chinois 🇨🇳",
    "Si on retourne le classement, les Pacers sont enfin à leur vraie place 🙃"
]

# Palette de couleurs (Globales)
C_BG = "#050505"
C_ACCENT = "#CE1141" # Raptors Red
C_TEXT = "#E5E7EB"
C_GOLD = "#FFD700"
C_SILVER = "#C0C0C0"
C_BRONZE = "#CD7F32"
C_GREEN = "#10B981"
C_BLUE = "#3B82F6"
C_PURPLE = "#8B5CF6"
C_ALPHA = "#F472B6"
C_IRON = "#A1A1AA"
C_BONUS = "#06B6D4"
C_PURE = "#14B8A6"
C_ORANGE = "#F97316"
C_RED = "#EF4444"
C_DARK_GREY = "#1F2937"
C_GREY_BAR = "#374151" 
C_ALIEN = "#84CC16"

# --- 2. CSS PREMIUM ---
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
    .glass-card {{ background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 24px; margin-bottom: 20px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3); }}
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
    .kpi-num {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 2.8rem; line-height: 1; color: #FFF; }}
    
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
        margin-bottom: 0px; /* Géré par le gap de Streamlit */
    }}
    .stat-mini-val {{ font-family:'Rajdhani'; font-weight:700; font-size:1.8rem; color:#FFF; line-height:1; }}
    .stat-mini-lbl {{ font-size:0.75rem; color:#888; text-transform:uppercase; margin-top:8px; letter-spacing:1px; }}
    .stat-mini-sub {{ font-size:0.7rem; font-weight:600; margin-top:4px; color:#555; }}
    
    /* Player Lab - Match Pills FULL WIDTH RESPONSIVE */
    .match-pill {{
        flex: 1 0 auto; /* Grow to fill space */
        min-width: 25px;
        height: 35px; 
        border-radius: 4px; 
        display: flex; align-items: center; justify-content: center; 
        font-family: 'Rajdhani'; font-weight: 700; font-size: 0.8rem;
        color: #FFF;
        margin: 0 1px;
    }}
    .match-row {{ 
        display: flex; 
        justify-content: space-between; 
        width: 100%; 
        gap: 2px; 
        margin: 15px 0; 
        overflow-x: auto;
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
    .top-pick-row {{
        display: flex; justify-content: space-between; align-items: center;
        background: rgba(255,255,255,0.03);
        border-left: 4px solid {C_ACCENT};
        padding: 12px 15px;
        margin-bottom: 8px;
        border-radius: 4px;
        transition: background 0.2s;
    }}
    .top-pick-row:hover {{ background: rgba(255,255,255,0.08); }}
    .tp-rank {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 1.2rem; color: #666; width: 25px; }}
    .tp-info {{ flex-grow: 1; padding-left: 10px; }}
    .tp-pick {{ color: #888; font-size: 0.75rem; text-transform: uppercase; }}
    .tp-score {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.5rem; color: #FFF; }}
    .tp-bonus {{ font-size: 0.9rem; color: {C_BONUS}; margin-left: 5px; }}

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

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=0, show_spinner=False) # HIDE DEFAULT SPINNER
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return None, None, None, None, [], 0

        # A. VALEURS
        df_valeurs = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", header=None, ttl=0).astype(str)
        month_row = df_valeurs.iloc[0]
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_valeurs.iloc[pick_row_idx, 1:], errors='coerce')
        
        pick_to_month = {}
        current_month = "Inconnu"
        for col_idx in range(1, len(month_row)):
            val_month = str(month_row[col_idx]).strip()
            if val_month and val_month.lower() != 'nan' and val_month != '': current_month = val_month
            pick_val = pd.to_numeric(df_valeurs.iloc[pick_row_idx, col_idx], errors='coerce')
            if pd.notna(pick_val) and pick_val > 0: pick_to_month[int(pick_val)] = current_month

        bp_row = df_valeurs[df_valeurs[0].str.contains("Score BP", na=False)]
        bp_series = pd.to_numeric(bp_row.iloc[0, 1:], errors='coerce') if not bp_row.empty else pd.Series()
        df_players = df_valeurs.iloc[pick_row_idx+1:pick_row_idx+50].copy().rename(columns={0: 'Player'})
        stop = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme"]
        df_players = df_players[~df_players['Player'].isin(stop)].dropna(subset=['Player'])
        df_players['Player'] = df_players['Player'].str.strip()

        valid_map = {idx: int(val) for idx, val in picks_series.items() if pd.notna(val) and val > 0}
        cols = ['Player'] + list(valid_map.keys())
        cols = [c for c in cols if c in df_players.columns]
        df_clean = df_players[cols].copy().rename(columns=valid_map)
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='ScoreRaw')
        
        df_long['IsBonus'] = df_long['ScoreRaw'].str.contains(r'\*', na=False)
        df_long['ScoreClean'] = df_long['ScoreRaw'].str.replace(r'\*', '', regex=True)
        df_long['ScoreVal'] = pd.to_numeric(df_long['ScoreClean'], errors='coerce')
        df_long['Score'] = np.where(df_long['IsBonus'], df_long['ScoreVal'] * 2, df_long['ScoreVal'])
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        final_df = df_long.dropna(subset=['Score', 'Pick'])
        final_df['Player'] = final_df['Player'].str.strip()
        final_df['Month'] = final_df['Pick'].map(pick_to_month).fillna("Inconnu")
        
        bp_map = {int(picks_series[idx]): val for idx, val in bp_series.items() if idx in valid_map}
        daily_max_map = final_df.groupby('Pick')['Score'].max().to_dict()

        daily_stats = final_df.groupby('Pick')['Score'].agg(['mean', 'std']).reset_index()
        daily_stats.rename(columns={'mean': 'DailyMean', 'std': 'DailyStd'}, inplace=True)
        final_df = pd.merge(final_df, daily_stats, on='Pick', how='left')
        final_df['ZScore'] = np.where(final_df['DailyStd'] > 0, (final_df['Score'] - final_df['DailyMean']) / final_df['DailyStd'], 0)

        # B. STATS & RECUP BP
        df_stats = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Stats_Raptors_FR", header=None, ttl=0)
        team_rank_history = []
        team_current_rank = 0
        team_bp_real = 0
        
        # 1. Recherche de la colonne "BP" dans les 20 premières lignes (headers)
        bp_col_idx = -1
        header_row_idx = -1
        for r in range(20):
            for c in range(len(df_stats.columns)):
                val = str(df_stats.iloc[r, c]).strip()
                if val == "BP":
                    bp_col_idx = c
                    header_row_idx = r
                    break
            if bp_col_idx != -1: break
        
        # 2. Si colonne trouvée, on cherche "Team Raptors" dans la colonne 0 ou 1
        if bp_col_idx != -1:
            for r_idx in range(header_row_idx + 1, len(df_stats)):
                val_col0 = str(df_stats.iloc[r_idx, 0]).strip()
                val_col1 = str(df_stats.iloc[r_idx, 1]).strip()
                if "Team Raptors" in val_col0 or "Team Raptors" in val_col1:
                    try:
                        raw_bp = df_stats.iloc[r_idx, bp_col_idx]
                        team_bp_real = int(float(str(raw_bp).replace(',', '.')))
                    except: 
                        team_bp_real = 0
                    break

        # 3. Récupération Historique Rang
        start_row_rank = -1
        col_start_rank = -1
        for r_idx, row in df_stats.iterrows():
            for c_idx, val in enumerate(row):
                if str(val).strip() == "Classement":
                    start_row_rank = r_idx; col_start_rank = c_idx; break
            if start_row_rank != -1: break
        if start_row_rank != -1:
            for i in range(start_row_rank+1, start_row_rank+30):
                if i >= len(df_stats): break
                p_name = str(df_stats.iloc[i, col_start_rank]).strip()
                if "Team Raptors" in p_name:
                    hist_vals = df_stats.iloc[i, col_start_rank+1:col_start_rank+25].values
                    valid_history = []
                    for x in hist_vals:
                        try:
                            clean_x = str(x).replace(',', '').replace(' ', '')
                            val = float(clean_x)
                            if val > 0: valid_history.append(int(val))
                        except: pass
                    if valid_history:
                        team_current_rank = valid_history[-1]
                        team_rank_history = valid_history
                    break
        return final_df, team_current_rank, bp_map, team_rank_history, daily_max_map, team_bp_real

    except: return pd.DataFrame(), 0, {}, [], {}, 0

# OPTIMISATION : CACHING STATS CALCULATION TO SPEED UP NAVIGATION
@st.cache_data(ttl=300, show_spinner=False) # HIDE DEFAULT SPINNER
def compute_stats(df, bp_map, daily_max_map):
    stats = []
    latest_pick = df['Pick'].max()
    season_avgs = df.groupby('Player')['Score'].mean()
    season_avgs_raw = df.groupby('Player')['ScoreVal'].mean()
    df_15 = df[df['Pick'] > (latest_pick - 15)]
    avg_15 = df_15.groupby('Player')['Score'].mean()
    df_10 = df[df['Pick'] > (latest_pick - 10)]
    avg_10 = df_10.groupby('Player')['Score'].mean()
    trend_data = {}
    for p, d in df.sort_values('Pick').groupby('Player'): trend_data[p] = d['Score'].tail(20).tolist()

    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        scores = d['Score'].values
        scores_raw = d['ScoreVal'].values
        picks = d['Pick'].values
        bonuses = d['IsBonus'].values
        z_scores = d['ZScore'].values
        
        bonus_data = d[d['IsBonus'] == True]
        scores_with_bonus = bonus_data['Score'].values
        scores_without_bonus = d[d['IsBonus'] == False]['Score'].values
        avg_with_bonus = scores_with_bonus.mean() if len(scores_with_bonus) > 0 else 0
        avg_without_bonus = scores_without_bonus.mean() if len(scores_without_bonus) > 0 else 0
        best_with_bonus = scores_with_bonus.max() if len(scores_with_bonus) > 0 else 0
        best_without_bonus = scores_without_bonus.max() if len(scores_without_bonus) > 0 else 0
        
        # CALCULATION NO CARROT STREAK
        current_no_carrot_streak = 0
        for s in reversed(scores):
            if s >= 20: current_no_carrot_streak += 1
            else: break
            
        # CALCULATION MAX HISTORICAL NO CARROT STREAK
        max_no_carrot = 0
        current_count = 0
        for s in scores:
            if s >= 20:
                current_count += 1
                if current_count > max_no_carrot: max_no_carrot = current_count
            else:
                current_count = 0
        
        # CALCULATION ALIEN STREAK (>60)
        max_alien_streak = 0
        current_alien = 0
        for s in scores:
            if s >= 60:
                current_alien += 1
                if current_alien > max_alien_streak: max_alien_streak = current_alien
            else:
                current_alien = 0
        
        # CALCULATION MODE (MOST FREQUENT SCORE)
        try:
            vals, counts = np.unique(scores, return_counts=True)
            max_count_idx = np.argmax(counts)
            mode_score = vals[max_count_idx]
            mode_count = counts[max_count_idx]
        except:
            mode_score = 0
            mode_count = 0

        # CALCULATION SPREAD (ALBATROSS)
        spread = scores.max() - scores.min()

        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        bp_count = 0; alpha_count = 0; bonus_points_gained = 0; bonus_scores_list = []
        
        for i, (pick_num, score) in enumerate(zip(picks, scores)):
            if pick_num in bp_map and score >= bp_map[pick_num] and score > 0: bp_count += 1
            if pick_num in daily_max_map and score >= daily_max_map[pick_num] and score > 0: alpha_count += 1
            if bonuses[i]: 
                gain = score - scores_raw[i]
                bonus_points_gained += gain
                bonus_scores_list.append(score)
        
        best_bonus = max(bonus_scores_list) if bonus_scores_list else 0
        worst_bonus = min(bonus_scores_list) if bonus_scores_list else 0
        avg_bonus_score = np.mean(bonus_scores_list) if bonus_scores_list else 0
        s_avg = season_avgs.get(p, 0)
        s_avg_raw = season_avgs_raw.get(p, 0)
        l15_avg = avg_15.get(p, s_avg)
        l10_avg = avg_10.get(p, s_avg)
        progression_pct = ((l15_avg - s_avg) / s_avg) * 100 if s_avg > 0 else 0
        reliability_pct = ((len(scores) - len(scores[scores < 20])) / len(scores)) * 100
        avg_z = np.mean(z_scores) if len(z_scores) > 0 else 0
        
        # Custom Stats for Hall of Fame
        count_20_30 = len(scores[(scores >= 20) & (scores <= 30)])

        stats.append({
            'Player': p, 'Total': scores.sum(), 'Moyenne': scores.mean(), 'Moyenne_Raw': s_avg_raw,
            'StdDev': scores.std(), 'Best': scores.max(), 'Best_Raw': scores_raw.max(),
            'Worst': scores.min(), 'Worst_Raw': scores_raw.min(), 'Last': scores[-1], 
            'LastIsBonus': bonuses[-1] if len(bonuses) > 0 else False, 'Last5': last5_avg, 'Last10': l10_avg, 'Last15': l15_avg,
            'Streak30': streak_30, 'Count30': len(scores[scores >= 30]), 'Count40': len(scores[scores >= 40]),
            'Count35': len(scores[scores > 35]), 'Count2030': count_20_30,
            'Carottes': len(scores[scores < 20]), 'Nukes': len(scores[scores >= 50]),
            'BP_Count': bp_count, 'Alpha_Count': alpha_count,
            'Bonus_Gained': bonus_points_gained, 'Best_Bonus': best_bonus, 'Worst_Bonus': worst_bonus,
            'Avg_Bonus': avg_bonus_score, 'Momentum': momentum, 'Games': len(scores),
            'ProgressionPct': progression_pct, 'ReliabilityPct': reliability_pct, 'AvgZ': avg_z,
            'Trend': trend_data.get(p, []), 'AvgWithBonus': avg_with_bonus, 'AvgWithoutBonus': avg_without_bonus, 'BonusPlayed': len(scores_with_bonus),
            'CurrentNoCarrot': current_no_carrot_streak, 'MaxNoCarrot': max_no_carrot, 'ModeScore': mode_score, 'ModeCount': mode_count, 'Spread': spread,
            'MaxAlien': max_alien_streak
        })
    return pd.DataFrame(stats)

def get_comparative_stats(df, current_pick, lookback=15):
    start_pick = max(1, current_pick - lookback)
    current_stats = df.groupby('Player')['Score'].agg(['sum', 'mean'])
    current_stats['rank'] = current_stats['sum'].rank(ascending=False)
    df_past = df[df['Pick'] <= start_pick]
    if df_past.empty: return pd.DataFrame() 
    past_stats = df_past.groupby('Player')['Score'].agg(['sum', 'mean'])
    past_stats['rank'] = past_stats['sum'].rank(ascending=False)
    stats_delta = pd.DataFrame(index=current_stats.index)
    stats_delta['mean_diff'] = current_stats['mean'] - past_stats['mean']
    stats_delta['rank_diff'] = past_stats['rank'] - current_stats['rank'] 
    return stats_delta

def render_gauge(label, value, color):
    return f"""
    <div class="gauge-container">
        <div class="gauge-label"><span>{label}</span><span>{int(value)}%</span></div>
        <div style="width:100%; background:#333; height:8px; border-radius:4px; overflow:hidden">
            <div style="width:{value}%; background:{color}; height:100%"></div>
        </div>
    </div>
    """

# --- 4. DISCORD ---
def send_discord_webhook(day_df, pick_num, url_app):
    if "DISCORD_WEBHOOK" not in st.secrets: return "missing_secret"
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    top_3 = day_df.head(3).reset_index(drop=True)
    podium_text = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, row in top_3.iterrows():
        bonus_mark = " 🔥" if row['IsBonus'] else ""
        podium_text += f"{medals[i]} **{row['Player']}** • {int(row['Score'])} pts{bonus_mark}\n"
    
    avg_score = int(day_df['Score'].mean())
    
    # SELECTION DU PUNCHLINE (IDENTIQUE A GSHEET)
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

# --- 5. UI COMPONENTS ---
def kpi_card(label, value, sub, color="#FFF"):
    st.markdown(f"""<div class="glass-card" style="text-align:center"><div class="kpi-label">{label}</div><div class="kpi-num" style="color:{color}">{value}</div><div class="kpi-sub" style="color:{C_ACCENT}">{sub}</div></div>""", unsafe_allow_html=True)
def section_title(title, subtitle):
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)

# --- 6. MAIN APP ---
try:
    # UX BOOSTER: SCRIPT JS POUR SCROLL TOP + FERMETURE SIDEBAR MOBILE
    components.html("""
    <script>
        // Fonction pour scroller en haut (simule un chargement page neuve)
        window.parent.document.querySelector('.main').scrollTo(0, 0);

        // Fonction pour fermer la sidebar sur mobile après un clic
        const navLinks = window.parent.document.querySelectorAll('.nav-link');
        navLinks.forEach((link) => {
            link.addEventListener('click', () => {
                // On attend un peu que Streamlit réagisse
                setTimeout(() => {
                    const closeBtn = window.parent.document.querySelector('button[data-testid="baseButton-header"]');
                    // Si on est sur un écran petit (mobile) et que le bouton existe
                    if (window.parent.innerWidth <= 768 && closeBtn) {
                        closeBtn.click();
                    }
                }, 200);
            });
        });
    </script>
    """, height=0, width=0)

    # CHARGEMENT DES DONNÉES AVEC SPINNER
    with st.spinner('🦖 Analyse des données en cours...'):
        df, team_rank, bp_map, team_history, daily_max_map, team_bp_real_load = load_data()
    
    # GLOBAL METRIC
    if df is not None and not df.empty:
        team_avg_per_pick = df['Score'].mean()
    else:
        team_avg_per_pick = 0

    if df is not None and not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False).copy()
        full_stats = compute_stats(df, bp_map, daily_max_map)
        leader = full_stats.sort_values('Total', ascending=False).iloc[0]
        
        # BP Calculation Check
        total_bp_team = team_bp_real_load if team_bp_real_load > 0 else full_stats['BP_Count'].sum()

        with st.sidebar:
            st.markdown("<div style='text-align:center; margin-bottom: 30px;'>", unsafe_allow_html=True)
            st.image("raptors-ttfl-min.png", use_container_width=True) 
            st.markdown("</div>", unsafe_allow_html=True)
            menu = option_menu(menu_title=None, options=["Dashboard", "Team HQ", "Player Lab", "Bonus x2", "Trends", "Hall of Fame", "Admin"], icons=["grid-fill", "people-fill", "person-bounding-box", "lightning-charge-fill", "fire", "trophy-fill", "shield-lock"], default_index=0, styles={"container": {"padding": "0!important", "background-color": "#000000"}, "icon": {"color": "#666", "font-size": "1.1rem"}, "nav-link": {"font-family": "Rajdhani, sans-serif", "font-weight": "700", "font-size": "15px", "text-transform": "uppercase", "color": "#AAA", "text-align": "left", "margin": "5px 0px", "--hover-color": "#111"}, "nav-link-selected": {"background-color": C_ACCENT, "color": "#FFF", "icon-color": "#FFF", "box-shadow": "0px 4px 20px rgba(206, 17, 65, 0.4)"}})
            st.markdown(f"""<div style='position: fixed; bottom: 30px; width: 100%; padding-left: 20px;'><div style='color:#444; font-size:10px; font-family:Rajdhani; letter-spacing:2px; text-transform:uppercase'>Data Pick #{int(latest_pick)}<br>War Room v16.1</div></div>""", unsafe_allow_html=True)
            
        if menu == "Dashboard":
            section_title("RAPTORS <span class='highlight'>DASHBOARD</span>", f"Daily Briefing • Pick #{int(latest_pick)}")
            top = day_df.iloc[0]
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("MVP DU SOIR", top['Player'], f"{int(top['Score'])} PTS", C_GOLD)
            total_day = day_df['Score'].sum()
            with c2: kpi_card("TOTAL TEAM SOIR", int(total_day), "POINTS")
            team_daily_avg = day_df['Score'].mean()
            diff_perf = ((team_daily_avg - team_avg_per_pick) / team_avg_per_pick) * 100
            perf_col = C_GREEN if diff_perf > 0 else "#F87171"
            with c3: kpi_card("PERF. TEAM SOIR", f"{diff_perf:+.1f}%", "VS MOY. SAISON", perf_col)
            with c4: kpi_card("LEADER SAISON", leader['Player'], f"TOTAL: {int(leader['Total'])}", C_ACCENT)
            
            day_merged = pd.merge(day_df, full_stats[['Player', 'Moyenne']], on='Player')
            day_merged['Delta'] = day_merged['Score'] - day_merged['Moyenne']
            top_clutch = day_merged.sort_values('Delta', ascending=False).head(3)
            
            bins = [-1, 35, 45, 200]
            labels = ['< 35', '35-45', '45+']
            day_df['Range'] = pd.cut(day_df['Score'], bins=bins, labels=labels)
            dist_counts = day_df['Range'].value_counts().reset_index()
            dist_counts.columns = ['Range', 'Count']
            
            c_perf, c_clutch = st.columns([2, 1])
            with c_perf:
                st.markdown("<h3 style='margin-bottom:10px; margin-top:0; color:#FFF; font-family:Rajdhani; font-weight:700'>📊 SCORES DU SOIR</h3>", unsafe_allow_html=True)
                
                def get_bar_color(score):
                    if score < 35: return C_RED
                    elif score <= 45: return C_GREY_BAR
                    else: return C_GREEN
                
                day_df['BarColor'] = day_df['Score'].apply(get_bar_color)
                
                fig = px.bar(day_df, x='Player', y='Score', text='Score', color='BarColor', color_discrete_map="identity")
                fig.update_traces(textposition='outside', marker_line_width=0, textfont_size=14, textfont_family="Rajdhani", cliponaxis=False)
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA', 'family': 'Inter'}, yaxis=dict(showgrid=False, visible=False), xaxis=dict(title=None, tickfont=dict(size=14, family='Rajdhani', weight=600)), height=350, showlegend=False, coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            
            with c_clutch:
                st.markdown("<h3 style='margin-bottom:10px; margin-top:0; color:#FFF; font-family:Rajdhani; font-weight:700'>⚡ CLUTCH DU SOIR</h3>", unsafe_allow_html=True)
                st.markdown("<div class='chart-desc'>Joueurs ayant le plus dépassé leur moyenne habituelle ce soir.</div>", unsafe_allow_html=True)
                for i, row in enumerate(top_clutch.itertuples()):
                    st.markdown(f"""<div class='glass-card' style='margin-bottom:10px; padding:12px'><div style='display:flex; justify-content:space-between; align-items:center'><div><div style='font-weight:700; color:{C_TEXT}'>{row.Player}</div><div style='font-size:0.75rem; color:#666'>Moy: {row.Moyenne:.1f}</div></div><div style='text-align:right'><div style='font-size:1.2rem; font-weight:800; color:{C_GREEN}'>+{row.Delta:.1f}</div><div style='font-size:0.8rem; color:#888'>{int(row.Score)} pts</div></div></div></div>""", unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#FFF; font-family:Rajdhani; font-weight:700; margin-bottom:20px'>🏆 ANALYSE & CLASSEMENTS</h3>", unsafe_allow_html=True)
            c_gen, c_form, c_text = st.columns(3)
            medals = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            df_minus_last = df[df['Pick'] < latest_pick].groupby('Player')['Score'].sum().rank(ascending=False)
            current_ranks = full_stats.set_index('Player')['Total'].rank(ascending=False)
            
            with c_gen:
                st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_ACCENT}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🏆 TOP 5 GÉNÉRAL</div><div class='chart-desc'>Classement saison et évolution vs veille.</div>", unsafe_allow_html=True)
                top_5_season = full_stats.sort_values('Total', ascending=False).head(5).reset_index()
                for i, r in top_5_season.iterrows():
                    medal = medals.get(i, f"{i+1}")
                    prev_rank = df_minus_last.get(r['Player'], i+1)
                    curr_rank = current_ranks.get(r['Player'], i+1)
                    diff = prev_rank - curr_rank 
                    evo = f"<span style='color:{C_GREEN}; font-size:0.8rem'>▲{int(diff)}</span>" if diff > 0 else (f"<span style='color:{C_RED}; font-size:0.8rem'>▼{int(abs(diff))}</span>" if diff < 0 else "<span style='color:#444; font-size:0.8rem'>=</span>")
                    st.markdown(f"<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px'><div style='display:flex; align-items:center; gap:10px'><div style='font-size:1.2rem; width:20px'>{medal}</div><div style='font-family:Rajdhani; font-weight:600; font-size:1rem; color:#FFF'>{r['Player']}</div></div><div style='text-align:right'><span style='font-family:Rajdhani; font-weight:700; color:{C_ACCENT}'>{int(r['Total'])}</span> {evo}</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c_form:
                st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_GREEN}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🔥 TOP 5 FORME (15J)</div><div class='chart-desc'>Meilleures moyennes sur les 15 derniers picks.</div>", unsafe_allow_html=True)
                top_5_form = full_stats.sort_values('Last15', ascending=False).head(5).reset_index()
                for i, r in top_5_form.iterrows():
                    medal = medals.get(i, f"{i+1}")
                    st.markdown(f"<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px'><div style='display:flex; align-items:center; gap:10px'><div style='font-size:1.2rem; width:20px'>{medal}</div><div style='font-family:Rajdhani; font-weight:600; font-size:1rem; color:#FFF'>{r['Player']}</div></div><div style='font-family:Rajdhani; font-weight:700; color:{C_GREEN}'>{r['Last15']:.1f}</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c_text:
                st.markdown(f"""
                <div class='glass-card' style='height:100%'>
                    <div style='color:{C_TEXT}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🎨 TEXTURE DES PICKS</div>
                    <div class='chart-desc'>Rouge < 35 | Gris 35-45 | Vert > 45.</div>
                    """ , unsafe_allow_html=True)
                
                fig_donut = px.pie(dist_counts, values='Count', names='Range', hole=0.4, color='Range', color_discrete_map={'< 35': C_RED, '35-45': C_DARK_GREY, '45+': C_GREEN})
                fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=220, paper_bgcolor='rgba(0,0,0,0)')
                fig_donut.update_traces(textposition='inside', textinfo='label+value', textfont_size=14)
                st.plotly_chart(fig_donut, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        elif menu == "Team HQ":
            section_title("TEAM <span class='highlight'>HQ</span>", "Vue d'ensemble de l'effectif")
            total_pts_season = df['Score'].sum()
            daily_agg = df.groupby('Pick')['Score'].sum()
            best_night = daily_agg.max(); worst_night = daily_agg.min(); avg_night = daily_agg.mean()
            
            # KPIS
            total_nukes_team = len(df[df['Score'] >= 50])
            total_carrots_team = len(df[df['Score'] < 20])
            safe_zone_team = len(df[df['Score'] > 35])
            
            total_bonus_played = len(df[df['IsBonus'] == True])
            current_rank_disp = f"#{int(team_rank)}" if team_rank > 0 else "-"
            best_rank_ever = f"#{min(team_history)}" if len(team_history) > 0 else "-"
            bonus_df = df[df['IsBonus'] == True]
            avg_bonus_team = bonus_df['Score'].mean() if not bonus_df.empty else 0
            daily_totals = df.groupby('Pick')['Score'].sum()
            avg_team_15 = daily_totals[daily_totals.index > (latest_pick - 15)].mean() if len(daily_totals) > 15 else daily_totals.mean()
            col_dyn = C_GREEN if (avg_team_15 - daily_totals.mean()) > 0 else C_ORANGE
            team_daily_totals = df.groupby('Pick')['Score'].sum().reset_index()
            last_15_team = team_daily_totals[team_daily_totals['Pick'] > (latest_pick - 15)]
            team_season_avg_total = team_daily_totals['Score'].mean()
            
            k1, k2, k3, k4 = st.columns(4)
            with k1: kpi_card("TOTAL SAISON", int(total_pts_season), "POINTS CUMULÉS", C_GOLD)
            with k2: kpi_card("MOYENNE / PICK", f"{team_avg_per_pick:.1f}", "PAR JOUEUR", "#FFF")
            with k3: kpi_card("MOYENNE ÉQUIPE / SOIR", f"{int(avg_night)}", "TOTAL COLLECTIF", C_BLUE)
            
            diff_dyn_team = ((avg_team_15 - avg_night) / avg_night) * 100
            col_dyn_team = C_GREEN if diff_dyn_team > 0 else C_RED
            with k4: kpi_card("DYNAMIQUE 15J", f"{diff_dyn_team:+.1f}%", "VS MOY. SAISON", col_dyn_team)

            st.markdown("<br>", unsafe_allow_html=True)

            c_grid, c_rec = st.columns([3, 1], gap="medium")
            with c_grid:
                # Ajout de gap="medium" dans les colonnes pour aérer
                g1, g2, g3 = st.columns(3, gap="medium")
                with g1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(latest_pick)}</div><div class='stat-mini-lbl'>MATCHS JOUÉS</div></div>", unsafe_allow_html=True)
                with g2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_ACCENT}'>{current_rank_disp}</div><div class='stat-mini-lbl'>CLASSEMENT ACTUEL</div></div>", unsafe_allow_html=True)
                with g3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>{best_rank_ever}</div><div class='stat-mini-lbl'>BEST RANK EVER</div></div>", unsafe_allow_html=True)
                
                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True) # Spacer vertical

                g4, g5, g6 = st.columns(3, gap="medium")
                with g4: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BLUE}'>{safe_zone_team}</div><div class='stat-mini-lbl'>SAFE ZONE (> 35 PTS)</div></div>", unsafe_allow_html=True)
                with g5: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GREEN}'>{total_nukes_team}</div><div class='stat-mini-lbl'>NUKES (> 50 PTS)</div></div>", unsafe_allow_html=True)
                with g6: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_RED}'>{total_carrots_team}</div><div class='stat-mini-lbl'>CAROTTES (< 20 PTS)</div></div>", unsafe_allow_html=True)
                
                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

                g7, g8, g9 = st.columns(3, gap="medium")
                with g7: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_PURPLE}'>{total_bp_team}</div><div class='stat-mini-lbl'>TOTAL BEST PICKS</div></div>", unsafe_allow_html=True)
                with g8: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BONUS}'>{total_bonus_played}</div><div class='stat-mini-lbl'>BONUS JOUÉS</div></div>", unsafe_allow_html=True)
                with g9: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{avg_bonus_team:.1f}</div><div class='stat-mini-lbl'>MOYENNE SOUS BONUS</div></div>", unsafe_allow_html=True)

            with c_rec:
                st.markdown(f"""<div class="glass-card" style="height:100%; display:flex; flex-direction:column; justify-content:center; padding:25px;"><div style="text-align:center; margin-bottom:20px; font-family:Rajdhani; font-weight:700; font-size:1.1rem; color:#AAA; letter-spacing:1px; border-bottom:1px solid #333; padding-bottom:10px;">RECORDS & MOYENNE</div><div class="hq-card-row"><div class="hq-lbl">🚀 RECORD</div><div class="hq-val" style="color:{C_GREEN}">{int(best_night)}</div></div><div class="hq-card-row"><div class="hq-lbl">⚖️ MOYENNE</div><div class="hq-val">{int(avg_night)}</div></div><div class="hq-card-row"><div class="hq-lbl">🧱 PLANCHER</div><div class="hq-val" style="color:{C_ACCENT}">{int(worst_night)}</div></div></div>""", unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)
            if len(team_history) > 1:
                st.markdown("### 📈 ÉVOLUTION DU CLASSEMENT")
                hist_df = pd.DataFrame({'Deck': range(1, len(team_history)+1), 'Rank': team_history})
                fig_h = px.line(hist_df, x='Deck', y='Rank', markers=True)
                fig_h.update_traces(line_color=C_ACCENT, line_width=3, marker_size=8)
                fig_h.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, yaxis=dict(autorange="reversed", gridcolor='#222'), xaxis=dict(showgrid=False))
                st.plotly_chart(fig_h, use_container_width=True)

            st.markdown("### 🔥 HEATMAP DE LA SAISON")
            st.markdown(f"<div class='chart-desc'>Rouge < 35 | Gris 35-45 (Neutre) | Vert > 45.</div>", unsafe_allow_html=True)
            
            # --- NOUVEAU : FILTRE HEATMAP ---
            heat_filter = st.selectbox("📅 Filtrer la Heatmap", ["VUE GLOBALE"] + list(df['Month'].unique()), key='heat_filter')
            
            if heat_filter == "VUE GLOBALE":
                df_heat = df
            else:
                df_heat = df[df['Month'] == heat_filter]
            
            heatmap_data = df_heat.pivot_table(index='Player', columns='Pick', values='Score', aggfunc='sum')
            custom_colors = [[0.0, '#EF4444'], [0.43, '#1F2937'], [0.56, '#1F2937'], [1.0, '#10B981']]
            
            # Ajustement taille auto selon le nombre de colonnes pour rester lisible
            fig_height = 500
            
            fig_heat = px.imshow(heatmap_data, labels=dict(x="Pick", y="Player", color="Score"), x=heatmap_data.columns, y=heatmap_data.index, color_continuous_scale=custom_colors, zmin=0, zmax=80, aspect="auto")
            fig_heat.update_traces(xgap=1, ygap=1)
            fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=fig_height, xaxis={'showgrid': False}, yaxis={'showgrid': False})
            st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("### 📊 DATA ROOM")
            st.dataframe(full_stats[['Player', 'Trend', 'Total', 'Moyenne', 'BP_Count', 'Nukes', 'Carottes', 'Bonus_Gained']].sort_values('Total', ascending=False), hide_index=True, use_container_width=True, column_config={
                "Player": st.column_config.TextColumn("Joueur", width="medium"),
                "Trend": st.column_config.LineChartColumn("Forme (20j)", width="medium", y_min=0, y_max=80),
                "Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()),
                "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f"),
                "Carottes": st.column_config.NumberColumn("🥕", help="Scores < 20"),
                "Nukes": st.column_config.NumberColumn("☢️", help="Scores > 50"),
                "BP_Count": st.column_config.NumberColumn("🎯", help="Best Picks"),
                "Bonus_Gained": st.column_config.NumberColumn("⚗️", help="Pts Bonus Gagnés")
            })

        elif menu == "Player Lab":
            section_title("PLAYER <span class='highlight'>LAB</span>", "Deep Dive Analytics")
            
            # UI SELECTOR HEADER
            st.markdown("<div class='widget-title'>👤 SÉLECTION DU JOUEUR</div>", unsafe_allow_html=True)
            sel_player = st.selectbox("Recherche", sorted(df['Player'].unique()), label_visibility="collapsed")
            
            p_data = full_stats[full_stats['Player'] == sel_player].iloc[0]
            p_hist_all = df[df['Player'] == sel_player]
            
            # CALCS
            alpha_rate = (p_data['Alpha_Count'] / p_data['Games']) * 100 if p_data['Games'] > 0 else 0
            sniper_pct = (p_data['BP_Count'] / p_data['Games']) * 100
            sorted_team = full_stats.sort_values('Total', ascending=False).reset_index(drop=True)
            internal_rank = sorted_team[sorted_team['Player'] == sel_player].index[0] + 1
            nb_players = len(sorted_team)
            form_10 = p_data['Last10']
            form_15 = p_data['Last15']
            diff_form = ((form_15 - p_data['Moyenne']) / p_data['Moyenne']) * 100
            sign = "+" if diff_form > 0 else ""
            color_diff = C_GREEN if diff_form > 0 else "#F87171"
            z_val = p_data['CurrentNoCarrot']
            z_col = C_GREEN if z_val > 3 else (C_RED if z_val == 0 else "#FFF")

            rank_col = C_GOLD if internal_rank == 1 else (C_SILVER if internal_rank == 2 else (C_BRONZE if internal_rank == 3 else "#FFF"))

            # --- KPI ROW 1 (ON GARDE) ---
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: kpi_card("TOTAL POINTS", int(p_data['Total']), "SAISON")
            with c2: kpi_card("MOYENNE", f"{p_data['Moyenne']:.1f}", "PTS / PICK")
            with c3: kpi_card("SÉRIE NO-CAROTTE", f"{int(z_val)}", "MATCHS (>20 PTS)", z_col)
            with c4: kpi_card("CLASSEMENT", f"#{internal_rank}", f"SUR {nb_players}", rank_col)
            with c5: kpi_card("BEST SCORE", int(p_data['Best']), "RECORD", C_GOLD)

            # --- NEW ROW: LAST 30 PICKS VISUALIZER (REVERSE ORDER) ---
            st.markdown("<div style='margin-top:20px; margin-bottom:5px; color:#888; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; text-align:center'>FORME RÉCENTE (30 DERNIERS MATCHS)</div>", unsafe_allow_html=True)
            last_30_picks = p_hist_all.sort_values('Pick', ascending=False).head(30)
            last_30_picks = last_30_picks.sort_values('Pick', ascending=True) # REVERSE ORDER
            
            if not last_30_picks.empty:
                html_picks = "<div class='match-row' style='width:100%'>"
                for _, r in last_30_picks.iterrows():
                    sc = r['Score']
                    
                    # Logic Color Bonus Yellow
                    if r['IsBonus']:
                        bg = C_GOLD
                        txt_col = "#000000"
                        border = f"2px solid {C_GOLD}"
                    else:
                        bg = C_RED if sc < 20 else (C_GREEN if sc > 40 else "#333")
                        txt_col = "#FFF"
                        border = "1px solid rgba(255,255,255,0.1)"
                        
                    html_picks += f"<div class='match-pill' style='background:{bg}; color:{txt_col}; border:{border}' title='Pick #{r['Pick']}'>{int(sc)}</div>"
                html_picks += "</div>"
                st.markdown(html_picks, unsafe_allow_html=True)
            else:
                st.info("Pas encore assez de matchs joués.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SPLIT 3/4 (GRID) + 1/4 (TOP 5) ---
            col_grid, col_top5 = st.columns([3, 1], gap="medium")

            with col_grid:
                # CUSTOM GRID 3x4 (12 KPIs) - UNIFORMISÉ
                r1c1, r1c2, r1c3 = st.columns(3, gap="small")
                with r1c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['ReliabilityPct'])}%</div><div class='stat-mini-lbl'>FIABILITÉ (> 20 PTS)</div></div>", unsafe_allow_html=True)
                with r1c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Last15']:.1f}</div><div class='stat-mini-lbl'>MOYENNE 15 JOURS</div></div>", unsafe_allow_html=True)
                with r1c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{color_diff}'>{sign}{diff_form:.1f}%</div><div class='stat-mini-lbl'>DYNAMIQUE 15J</div></div>", unsafe_allow_html=True)
                
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                
                r2c1, r2c2, r2c3 = st.columns(3, gap="small")
                # UPDATE REQUEST: Moyenne Pure & Best Raw (Meilleur Score Sec)
                with r2c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Moyenne_Raw']:.1f}</div><div class='stat-mini-lbl'>MOYENNE PURE</div></div>", unsafe_allow_html=True)
                with r2c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Best_Raw'])}</div><div class='stat-mini-lbl'>MEILLEUR SCORE SEC</div></div>", unsafe_allow_html=True)
                with r2c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Worst'])}</div><div class='stat-mini-lbl'>PIRE SCORE</div></div>", unsafe_allow_html=True)
                
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                
                r3c1, r3c2, r3c3 = st.columns(3, gap="small")
                with r3c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BLUE}'>{int(p_data['Count35'])}</div><div class='stat-mini-lbl'>SAFE ZONE (> 35 PTS)</div></div>", unsafe_allow_html=True)
                with r3c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GREEN}'>{int(p_data['Nukes'])}</div><div class='stat-mini-lbl'>NUKES (> 50 PTS)</div></div>", unsafe_allow_html=True)
                with r3c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_RED}'>{int(p_data['Carottes'])}</div><div class='stat-mini-lbl'>CAROTTES (< 20 PTS)</div></div>", unsafe_allow_html=True)

                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

                r4c1, r4c2, r4c3 = st.columns(3, gap="small")
                with r4c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_PURPLE}'>{int(p_data['BP_Count'])}</div><div class='stat-mini-lbl'>TOTAL BEST PICKS</div></div>", unsafe_allow_html=True)
                with r4c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>{int(p_data['Alpha_Count'])}</div><div class='stat-mini-lbl'>MVP DU SOIR</div></div>", unsafe_allow_html=True)
                with r4c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BONUS}'>{p_data['Avg_Bonus']:.1f}</div><div class='stat-mini-lbl'>MOYENNE SOUS BONUS</div></div>", unsafe_allow_html=True)


            with col_top5:
                st.markdown("#### 🌟 TOP 5 PICKS")
                st.markdown("<div class='chart-desc'>Meilleurs scores de la saison.</div>", unsafe_allow_html=True)
                top_5 = p_hist_all.sort_values('Score', ascending=False).head(5)
                for i, r in top_5.reset_index().iterrows():
                    rank_num = i + 1
                    b_icon = "⚡ x2" if r['IsBonus'] else ""
                    st.markdown(f"""
                    <div class="top-pick-row">
                        <div class="tp-rank">#{rank_num}</div>
                        <div class="tp-info">
                            <div class="tp-pick">Pick #{r['Pick']}</div>
                            <span class="tp-bonus">{b_icon}</span>
                        </div>
                        <div class="tp-score">{int(r['Score'])}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom:10px'>📡 PROFIL ATHLÉTIQUE</h3>", unsafe_allow_html=True)

            # --- ROW 4 : RADAR PROFILE FULL WIDTH (2/3 + 1/3) ---
            c_radar_graph, c_radar_legend = st.columns([2, 1], gap="large")
            
            with c_radar_graph:
                max_avg = full_stats['Moyenne'].max(); max_best = full_stats['Best'].max(); max_last10 = full_stats['Last10'].max(); max_nukes = full_stats['Nukes'].max()
                reg_score = 100 - ((p_data['StdDev'] / full_stats['StdDev'].max()) * 100)
                
                r_vals = [
                    (p_data['Moyenne'] / max_avg) * 100, 
                    (p_data['Best'] / max_best) * 100, 
                    (p_data['Last10'] / max_last10) * 100, 
                    reg_score, 
                    (p_data['Nukes'] / (max_nukes if max_nukes > 0 else 1)) * 100
                ]
                r_cats = ['SCORING', 'CEILING', 'FORME', 'RÉGULARITÉ', 'CLUTCH']
                
                fig_radar = go.Figure(data=go.Scatterpolar(r=r_vals + [r_vals[0]], theta=r_cats + [r_cats[0]], fill='toself', line_color=C_ACCENT, fillcolor="rgba(206, 17, 65, 0.3)"))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=14, family="Rajdhani"), margin=dict(t=20, b=20, l=40, r=40), height=400)
                st.plotly_chart(fig_radar, use_container_width=True)
            
            with c_radar_legend:
                st.markdown("""
                <div class='legend-box'>
                    <div class='legend-item'>
                        <div class='legend-title'>SCORING</div>
                        <div class='legend-desc'>Volume de points moyen sur la saison.</div>
                    </div>
                    <div class='legend-item'>
                        <div class='legend-title'>CEILING (PLAFOND)</div>
                        <div class='legend-desc'>Record personnel (Potentiel max sur un match).</div>
                    </div>
                    <div class='legend-item'>
                        <div class='legend-title'>FORME</div>
                        <div class='legend-desc'>Dynamique actuelle sur les 10 derniers matchs.</div>
                    </div>
                    <div class='legend-item'>
                        <div class='legend-title'>RÉGULARITÉ</div>
                        <div class='legend-desc'>Capacité à éviter les gros écarts de score (inverse de la volatilité).</div>
                    </div>
                    <div class='legend-item'>
                        <div class='legend-title'>CLUTCH</div>
                        <div class='legend-desc'>Fréquence des très gros scores (> 50 points).</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


            # --- GRAPHS ---
            c_dist, c_trend = st.columns(2, gap="medium")
            with c_dist:
                if not p_hist_all.empty:
                    st.markdown("#### 📊 DISTRIBUTION DES SCORES", unsafe_allow_html=True)
                    st.markdown("<div class='chart-desc'>Répartition de tous les scores de la saison par tranches de points.</div>", unsafe_allow_html=True)
                    fig_hist = px.histogram(p_hist_all, x="Score", nbins=15, color_discrete_sequence=[C_ACCENT], text_auto=True)
                    fig_hist.update_traces(marker_line_color='white', marker_line_width=1, opacity=0.8)
                    fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=10, b=0), height=250, xaxis_title=None, yaxis_title=None, bargap=0.1)
                    st.plotly_chart(fig_hist, use_container_width=True)
            
            with c_trend:
                if not p_hist_all.empty:
                    st.markdown("#### 📈 TENDANCE (15 DERNIERS MATCHS)", unsafe_allow_html=True)
                    st.markdown("<div class='chart-desc'>Évolution du score sur les 15 derniers matchs joués.</div>", unsafe_allow_html=True)
                    last_15_data = p_hist_all.sort_values('Pick').tail(15)
                    if not last_15_data.empty:
                        fig_trend = px.line(last_15_data, x="Pick", y="Score", markers=True)
                        fig_trend.update_traces(line_color=C_GOLD, marker_color=C_ACCENT, marker_size=8)
                        fig_trend.add_hline(y=p_data['Moyenne'], line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Saison", annotation_position="bottom right")
                        fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=10, b=0), height=250, xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig_trend, use_container_width=True)
                    else:
                        st.info("Pas assez de données récentes.")
            
            if not p_hist_all.empty:
                st.markdown("#### 🏔️ PARCOURS SAISON COMPLÈTE", unsafe_allow_html=True)
                st.markdown("<div class='chart-desc'>Vue globale de la saison comparée à la moyenne de l'équipe.</div>", unsafe_allow_html=True)
                team_season_avg = df['Score'].mean()
                fig_evol = px.line(p_hist_all, x="Pick", y="Score", markers=True)
                fig_evol.update_traces(line_color=C_BLUE, line_width=2, marker_size=4)
                fig_evol.add_hline(y=p_data['Moyenne'], line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Joueur", annotation_position="top left")
                fig_evol.add_hline(y=team_season_avg, line_dash="dash", line_color=C_ORANGE, annotation_text="Moy. Team", annotation_position="bottom right", annotation_font_color=C_ORANGE)
                fig_evol.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=30, b=0), height=300, xaxis_title="Pick #", yaxis_title="Points TTFL")
                st.plotly_chart(fig_evol, use_container_width=True)

        elif menu == "Bonus x2":
            section_title("BONUS <span class='highlight'>ZONE</span>", "Analyse de Rentabilité")
            
            # FILTER DATA
            df_bonus = df[df['IsBonus'] == True].copy()
            # Calculate Real Gain (Score - Score without bonus)
            df_bonus['RealGain'] = df_bonus['Score'] - df_bonus['ScoreVal']
            
            available_months = df['Month'].unique().tolist()
            sel_month = st.selectbox("Filtrer par Mois", ["Tous"] + [m for m in available_months if m != "Inconnu"])
            
            if sel_month != "Tous": 
                df_bonus_disp = df_bonus[df_bonus['Month'] == sel_month]
            else: 
                df_bonus_disp = df_bonus

            if df_bonus_disp.empty: 
                st.info("Aucun bonus trouvé pour cette sélection.")
            else:
                # 5 STRATEGIC KPIS
                nb_bonus = len(df_bonus_disp)
                avg_bonus = df_bonus_disp['Score'].mean()
                total_gain = df_bonus_disp['RealGain'].sum()
                success_rate = (len(df_bonus_disp[df_bonus_disp['Score'] >= 40]) / nb_bonus * 100) if nb_bonus > 0 else 0
                best_bonus = df_bonus_disp['Score'].max()

                k1, k2, k3, k4, k5 = st.columns(5)
                with k1: kpi_card("BONUS JOUÉS", nb_bonus, "VOLUME", C_BONUS)
                with k2: kpi_card("MOYENNE", f"{avg_bonus:.1f}", "PTS / BONUS", "#FFF")
                with k3: kpi_card("GAIN RÉEL", f"+{int(total_gain)}", "PTS AJOUTÉS", C_GREEN)
                with k4: kpi_card("RENTABILITÉ", f"{int(success_rate)}%", "SCORES > 40 PTS", C_PURPLE)
                with k5: kpi_card("RECORD", int(best_bonus), "MAX SCORE", C_GOLD)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # CHARTS: IMPACT & SCATTER
                c_chart1, c_chart2 = st.columns(2, gap="medium")
                
                with c_chart1:
                    st.markdown("#### 💰 IMPACT MENSUEL (GAINS RÉELS)")
                    st.markdown("<div class='chart-desc'>Points supplémentaires générés par le x2 chaque mois.</div>", unsafe_allow_html=True)
                    monthly_gain = df_bonus.groupby('Month')['RealGain'].sum().reindex(["Octobre", "Novembre", "Decembre", "Janvier", "Fevrier", "Mars", "Avril"]).dropna().reset_index()
                    fig_m = px.bar(monthly_gain, x='Month', y='RealGain', text='RealGain', color='RealGain', color_continuous_scale='Teal')
                    fig_m.update_traces(texttemplate='+%{text}', textposition='outside')
                    fig_m.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, xaxis=dict(title=None), yaxis=dict(showgrid=False, visible=False), height=300, showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig_m, use_container_width=True)
                
                with c_chart2:
                    st.markdown("#### 🎯 MATRICE DE RENTABILITÉ")
                    st.markdown("<div class='chart-desc'>Distribution des scores bonus. Cible : Coin supérieur droit.</div>", unsafe_allow_html=True)
                    fig_scat = px.scatter(df_bonus_disp, x="Pick", y="Score", color="Score", size="Score", hover_data=['Player'], color_continuous_scale='RdYlGn')
                    fig_scat.add_hline(y=40, line_dash="dash", line_color="#666", annotation_text="Seuil Rentabilité (40)", annotation_position="bottom right")
                    fig_scat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=300, xaxis_title="Pick #", yaxis_title="Score Total", coloraxis_showscale=False)
                    st.plotly_chart(fig_scat, use_container_width=True)

                st.markdown("### 📜 HISTORIQUE DÉTAILLÉ")
                st.dataframe(
                    df_bonus_disp[['Pick', 'Player', 'Month', 'ScoreVal', 'Score', 'RealGain']].sort_values('Pick', ascending=False), 
                    hide_index=True, 
                    use_container_width=True, 
                    column_config={
                        "Pick": st.column_config.NumberColumn("Pick #", format="%d"),
                        "ScoreVal": st.column_config.NumberColumn("Score Brut", format="%d pts"),
                        "Score": st.column_config.NumberColumn("Score Final (x2)", format="%d pts"),
                        "RealGain": st.column_config.NumberColumn("Gain Net", format="+%d pts")
                    }
                )

        elif menu == "Trends":
            section_title("TENDANCES", "Analyse de la forme récente (15 derniers jours)")
            
            # DATA PREP TRENDS (15 DAYS FIXED)
            df_15 = df[df['Pick'] > (latest_pick - 15)]
            
            # Team Stats 15 days
            team_daily_15 = df_15.groupby('Pick')['Score'].sum()
            avg_15_team = team_daily_15.mean()
            
            # Season Stats for comparison
            team_daily_season = df.groupby('Pick')['Score'].sum()
            season_avg_team = team_daily_season.mean()
            
            # Dynamic Diff
            team_trend_diff = ((avg_15_team - season_avg_team) / season_avg_team) * 100
            
            # Best Player 15 days
            best_form_player = df_15.groupby('Player')['Score'].mean().idxmax()
            best_form_val = df_15.groupby('Player')['Score'].mean().max()
            
            # Average Individual Score over last 15 days
            avg_15_indiv = df_15['Score'].mean()
            
            # Max Team 15d
            max_team_15 = team_daily_15.max()

            # --- TOP KPI ROW (5 KPIs) ---
            k1, k2, k3, k4, k5 = st.columns(5)
            with k1: kpi_card("MOYENNE TEAM (15J)", f"{avg_15_team:.0f}", "POINTS / SOIR", C_BLUE)
            with k2: kpi_card("MOYENNE / PICK (15J)", f"{avg_15_indiv:.1f}", "INDIVIDUEL", "#FFF")
            
            col_trend = C_GREEN if team_trend_diff > 0 else C_RED
            sign_trend = "+" if team_trend_diff > 0 else ""
            with k3: kpi_card("DYNAMIQUE", f"{sign_trend}{team_trend_diff:.1f}%", "VS SAISON", col_trend)
            
            with k4: kpi_card("PLAFOND TEAM (15J)", int(max_team_15), "MEILLEUR SOIR", C_GOLD)
            with k5: kpi_card("MVP PÉRIODE", best_form_player, f"{best_form_val:.1f} PTS", C_ACCENT)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- TEAM GRAPH (15 DAYS) ---
            st.markdown("#### 📉 ÉVOLUTION DU SCORE D'ÉQUIPE (15 DERNIERS JOURS)")
            st.markdown("<div class='chart-desc'>Comparatif du total journalier vs la moyenne de la saison.</div>", unsafe_allow_html=True)
            
            # Plot
            fig_team_15 = px.line(team_daily_15, markers=True)
            fig_team_15.update_traces(line_color=C_ACCENT, line_width=3, marker_size=8)
            # Add Season Avg Line
            fig_team_15.add_hline(y=season_avg_team, line_dash="dot", line_color=C_TEXT, annotation_text=f"Moyenne Saison ({int(season_avg_team)})", annotation_position="bottom right")
            
            fig_team_15.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                font={'color': '#AAA'}, 
                xaxis=dict(showgrid=False, title=None), 
                yaxis=dict(showgrid=True, gridcolor='#222', title="Points Totaux"), 
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig_team_15, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- HOT VS COLD COLUMNS (15 DAYS LOGIC) ---
            # Calculate Delta: Avg Last 15 - Avg Season
            player_season_avg = df.groupby('Player')['Score'].mean()
            player_15_avg = df[df['Pick'] > (latest_pick - 15)].groupby('Player')['Score'].mean()
            
            delta_df = pd.DataFrame({'Season': player_season_avg, 'Last15': player_15_avg})
            delta_df['Delta'] = delta_df['Last15'] - delta_df['Season']
            delta_df = delta_df.dropna()

            hot_players = delta_df[delta_df['Delta'] > 0].sort_values('Delta', ascending=False).head(5)
            cold_players = delta_df[delta_df['Delta'] < 0].sort_values('Delta', ascending=True).head(5)

            c_hot, c_cold = st.columns(2, gap="large")
            
            with c_hot:
                st.markdown(f"<div class='trend-box'><div class='hot-header'>🔥 EN FEU (SUR-PERFORMANCE)</div><div style='font-size:0.8rem; color:#888; margin-bottom:10px'>Joueurs au-dessus de leur moyenne saison sur les 15 derniers matchs.</div>", unsafe_allow_html=True)
                if hot_players.empty:
                    st.info("Personne n'est en sur-régime actuellement.")
                else:
                    for p, row in hot_players.iterrows():
                        st.markdown(f"""
                        <div class='trend-card-row'>
                            <div class='trend-name'>{p}</div>
                            <div style='text-align:right'>
                                <div class='trend-val' style='color:{C_GREEN}'>{row['Last15']:.1f}</div>
                                <div class='trend-delta' style='color:{C_GREEN}'>+{row['Delta']:.1f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c_cold:
                st.markdown(f"<div class='trend-box'><div class='cold-header'>❄️ DANS LE DUR (SOUS-PERFORMANCE)</div><div style='font-size:0.8rem; color:#888; margin-bottom:10px'>Joueurs en-dessous de leur moyenne saison sur les 15 derniers matchs.</div>", unsafe_allow_html=True)
                if cold_players.empty:
                    st.info("Tout le monde tient son rang !")
                else:
                    for p, row in cold_players.iterrows():
                        st.markdown(f"""
                        <div class='trend-card-row'>
                            <div class='trend-name'>{p}</div>
                            <div style='text-align:right'>
                                <div class='trend-val' style='color:{C_RED}'>{row['Last15']:.1f}</div>
                                <div class='trend-delta' style='color:{C_RED}'>{row['Delta']:.1f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- MOMENTUM CHART (ALL PLAYERS 15 DAYS) ---
            st.markdown("#### 📉 MOMENTUM (15 DERNIERS JOURS)")
            st.markdown("<div class='chart-desc'>Trajectoire de tous les joueurs actifs sur la période.</div>", unsafe_allow_html=True)
            
            # Filter only players who played in last 15 days
            active_players = df_15['Player'].unique()
            momentum_data = df_15[df_15['Player'].isin(active_players)].sort_values('Pick')
            
            fig_mom = px.line(momentum_data, x='Pick', y='Score', color='Player', markers=True)
            fig_mom.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                font={'color': '#AAA'}, 
                xaxis=dict(showgrid=False), 
                yaxis=dict(showgrid=True, gridcolor='#222'), 
                height=500,
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_mom, use_container_width=True)

        elif menu == "Hall of Fame":
            section_title("HALL OF <span class='highlight'>FAME</span>", "Records & Trophées de la saison")
            
            # DATA HOF CALCULATIONS
            sniper = full_stats.sort_values('Moyenne', ascending=False).iloc[0]
            pure_avg = full_stats.sort_values('Moyenne_Raw', ascending=False).iloc[0]
            sniper_bp = full_stats.sort_values('BP_Count', ascending=False).iloc[0]
            alpha_dog = full_stats.sort_values('Alpha_Count', ascending=False).iloc[0]
            peak = full_stats.sort_values('Best', ascending=False).iloc[0]
            pure_peak = full_stats.sort_values('Best_Raw', ascending=False).iloc[0]
            nuke = full_stats.sort_values('Nukes', ascending=False).iloc[0]
            heavy = full_stats.sort_values('Count40', ascending=False).iloc[0]
            alchemist = full_stats.sort_values('Bonus_Gained', ascending=False).iloc[0]
            rock = full_stats.sort_values('Count30', ascending=False).iloc[0]
            torche = full_stats.sort_values('Last15', ascending=False).iloc[0]
            progression = full_stats.sort_values('ProgressionPct', ascending=False).iloc[0]
            zen_master = full_stats.sort_values('ReliabilityPct', ascending=False).iloc[0]
            intouch = full_stats.sort_values('Streak30', ascending=False).iloc[0]
            
            metronome = full_stats.sort_values('StdDev', ascending=True).iloc[0]
            iron_wall = full_stats.sort_values('Worst', ascending=False).iloc[0]
            
            maniac = full_stats.sort_values('ModeCount', ascending=False).iloc[0]
            iron_man = full_stats.sort_values('MaxNoCarrot', ascending=False).iloc[0]
            albatross = full_stats.sort_values('Spread', ascending=False).iloc[0]
            alien = full_stats.sort_values('MaxAlien', ascending=False).iloc[0]

            bad_business = full_stats.sort_values('Bonus_Gained', ascending=True).iloc[0]
            has_bonus = full_stats[full_stats['Worst_Bonus'] > 0]
            crash_test = has_bonus.sort_values('Worst_Bonus', ascending=True).iloc[0] if not has_bonus.empty else full_stats.iloc[0]
            brick_layer = full_stats.sort_values('Worst_Raw', ascending=True).iloc[0]
            lapin = full_stats.sort_values('Carottes', ascending=False).iloc[0]

            # LIST OF 24 CARDS WITH UNIQUE COLORS
            hof_list = [
                {"title": "THE GOAT", "icon": "🏆", "color": C_GOLD, "player": sniper['Player'], "val": f"{sniper['Moyenne']:.1f}", "unit": "PTS MOYENNE (TOTAL)", "desc": "Meilleure moyenne générale de la saison (Bonus incl.)"},
                {"title": "REAL MVP", "icon": "💎", "color": C_PURE, "player": pure_avg['Player'], "val": f"{pure_avg['Moyenne_Raw']:.1f}", "unit": "PTS MOYENNE (BRUT)", "desc": "Meilleure moyenne sans compter les bonus"},
                {"title": "THE SNIPER", "icon": "🎯", "color": C_PURPLE, "player": sniper_bp['Player'], "val": int(sniper_bp['BP_Count']), "unit": "BEST PICKS", "desc": "Le plus de Best Picks trouvés"},
                {"title": "ALPHA DOG", "icon": "🐺", "color": C_ALPHA, "player": alpha_dog['Player'], "val": int(alpha_dog['Alpha_Count']), "unit": "TOPS TEAM", "desc": "Le plus souvent meilleur scoreur de l'équipe"},
                {"title": "THE CEILING", "icon": "🏔️", "color": "#FB7185", "player": peak['Player'], "val": int(peak['Best']), "unit": "PTS MAX", "desc": "Record absolu sur un match (Bonus inclus)"},
                {"title": "PURE SCORER", "icon": "🏀", "color": "#7C3AED", "player": pure_peak['Player'], "val": int(pure_peak['Best_Raw']), "unit": "PTS MAX (BRUT)", "desc": "Record absolu sur un match (Sans bonus)"},
                {"title": "THE ALCHEMIST", "icon": "⚗️", "color": C_BONUS, "player": alchemist['Player'], "val": int(alchemist['Bonus_Gained']), "unit": "PTS BONUS", "desc": "Le plus de points gagnés grâce aux bonus"},
                {"title": "NUCLEAR", "icon": "☢️", "color": C_ACCENT, "player": nuke['Player'], "val": int(nuke['Nukes']), "unit": "BOMBS", "desc": "Le plus de scores > 50 pts"},
                {"title": "HEAVY HITTER", "icon": "🥊", "color": "#DC2626", "player": heavy['Player'], "val": int(heavy['Count40']), "unit": "PICKS > 40", "desc": "Le plus de scores > 40 pts"},
                {"title": "THE ROCK", "icon": "🛡️", "color": C_GREEN, "player": rock['Player'], "val": int(rock['Count30']), "unit": "MATCHS", "desc": "Le plus de scores dans la Safe Zone (> 30 pts)"},
                {"title": "HUMAN TORCH", "icon": "🔥", "color": "#BE123C", "player": torche['Player'], "val": f"{torche['Last15']:.1f}", "unit": "PTS / 15J", "desc": "Meilleure forme actuelle (Moyenne 15j)"},
                {"title": "RISING STAR", "icon": "🚀", "color": "#34D399", "player": progression['Player'], "val": f"+{progression['ProgressionPct']:.1f}%", "unit": "PROGRESSION", "desc": "Plus grosse progression (Moyenne 15j vs Saison)"},
                {"title": "ZEN MASTER", "icon": "🧘", "color": "#38BDF8", "player": zen_master['Player'], "val": f"{int(zen_master['ReliabilityPct'])}%", "unit": "FIABILITÉ", "desc": "Plus haut taux de fiabilité (Moins de carottes)"},
                {"title": "UNSTOPPABLE", "icon": "⚡", "color": "#F59E0B", "player": intouch['Player'], "val": int(intouch['Streak30']), "unit": "SERIE", "desc": "Plus longue série consécutive > 30 pts"},
                {"title": "THE METRONOME", "icon": "⏰", "color": C_IRON, "player": metronome['Player'], "val": f"{metronome['StdDev']:.1f}", "unit": "ECART TYPE", "desc": "Le joueur le plus régulier (Faible variation)"},
                {"title": "THE MANIAC", "icon": "🤪", "color": "#D946EF", "player": maniac['Player'], "val": f"{maniac['ModeScore']}", "unit": f"{maniac['ModeCount']} FOIS", "desc": "Le score le plus souvent répété par ce joueur"},
                {"title": "IRON WALL", "icon": "🧱", "color": "#78350F", "player": iron_wall['Player'], "val": int(iron_wall['Worst']), "unit": "PIRE SCORE", "desc": "Le 'Pire score' le plus élevé (Plancher haut)"},
                {"title": "THE ALBATROSS", "icon": "🦅", "color": "#2DD4BF", "player": albatross['Player'], "val": int(albatross['Spread']), "unit": "AMPLITUDE", "desc": "Plus grand écart entre le record et le pire score"},
                {"title": "IRON MAN", "icon": "🤖", "color": "#4F46E5", "player": iron_man['Player'], "val": int(iron_man['MaxNoCarrot']), "unit": "MATCHS", "desc": "Plus longue série historique sans carotte (< 20 pts)"},
                {"title": "THE ALIEN", "icon": "👽", "color": C_ALIEN, "player": alien['Player'], "val": int(alien['MaxAlien']), "unit": "MATCHS", "desc": "Plus longue série de matchs consécutifs à +60 pts"},
                {"title": "CRASH TEST", "icon": "💥", "color": C_RED, "player": crash_test['Player'], "val": int(crash_test['Worst_Bonus']), "unit": "PTS MIN (X2)", "desc": "Le pire score réalisé avec un bonus actif"},
                {"title": "BAD BUSINESS", "icon": "💸", "color": "#9CA3AF", "player": bad_business['Player'], "val": int(bad_business['Bonus_Gained']), "unit": "PTS BONUS", "desc": "Le moins de points gagnés grâce aux bonus"},
                {"title": "THE BRICK", "icon": "🏗️", "color": "#6B7280", "player": brick_layer['Player'], "val": int(brick_layer['Worst_Raw']), "unit": "PTS MIN (BRUT)", "desc": "Le pire score brut enregistré"},
                {"title": "THE FARMER", "icon": "🥕", "color": C_ORANGE, "player": lapin['Player'], "val": int(lapin['Carottes']), "unit": "CAROTTES", "desc": "Le plus grand nombre de carottes (< 20 pts)"}
            ]

            # GRID DISPLAY (2 COLUMNS LOGIC)
            rows = [hof_list[i:i+2] for i in range(0, len(hof_list), 2)]
            for row_cards in rows:
                cols = st.columns(2)
                for i, card in enumerate(row_cards):
                    with cols[i]:
                        st.markdown(f"""
                        <div class="glass-card" style="position:relative; overflow:hidden; margin-bottom:10px">
                            <div style="position:absolute; right:-10px; top:-10px; font-size:5rem; opacity:0.05; pointer-events:none">{card['icon']}</div>
                            <div class="hof-badge" style="color:{card['color']}; border:1px solid {card['color']}">{card['icon']} {card['title']}</div>
                            <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                                <div>
                                    <div class="hof-player">{card['player']}</div>
                                    <div style="font-size:0.8rem; color:#888; margin-top:4px">{card['desc']}</div>
                                </div>
                                <div>
                                    <div class="hof-stat" style="color:{card['color']}">{card['val']}</div>
                                    <div class="hof-unit">{card['unit']}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        elif menu == "Admin":
            section_title("ADMIN <span class='highlight'>PANEL</span>", "Accès Restreint")
            if "admin_access" not in st.session_state: st.session_state["admin_access"] = False
            if not st.session_state["admin_access"]:
                c1, c2, c3 = st.columns([1, 2, 1])
                with c2:
                    st.markdown("<div class='glass-card'><h4>🔒 ZONE SÉCURISÉE</h4>", unsafe_allow_html=True)
                    pwd = st.text_input("Mot de passe", type="password", key="admin_pwd")
                    if st.button("DÉVERROUILLER"):
                        if "ADMIN_PASSWORD" in st.secrets and pwd == st.secrets["ADMIN_PASSWORD"]:
                            st.session_state["admin_access"] = True; st.rerun()
                        else: st.error("⛔ Accès refusé")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div class='glass-card'><h4>🔄 DONNÉES</h4>", unsafe_allow_html=True)
                    if st.button("FORCER LA MISE À JOUR", type="secondary"): st.cache_data.clear(); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div class='glass-card'><h4>📡 DISCORD</h4>", unsafe_allow_html=True)
                    if st.button("🚀 ENVOYER RAPPORT", type="primary"):
                        res = send_discord_webhook(day_df, latest_pick, "https://dino-fant-tvewyye4t3dmqfeuvqsvmg.streamlit.app/")
                        if res == "success": st.success("✅ Envoyé !")
                        else: st.error(f"Erreur : {res}")
                    st.markdown("</div>", unsafe_allow_html=True)
                if st.button("🔒 VERROUILLER"): st.session_state["admin_access"] = False; st.rerun()

    else: st.warning("⚠️ Aucune donnée trouvée.")
except Exception as e: st.error(f"🔥 Critical Error: {e}")
