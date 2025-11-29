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

# --- CONFIG COULEURS JOUEURS ---
PLAYER_COLORS = {
    "Pedrille": "#CE1141", "Tomus06": "#FFD700", "Mims22": "#10B981",
    "MadDawgs": "#3B82F6", "Gabeur": "#8B5CF6", "HoodieRigone": "#F97316",
    "iAmDjuu25": "#06B6D4", "Luoshtgin": "#EC4899", "Mendosaaaa": "#84CC16",
    "Duduge21": "#6366F1", "Inconnu": "#9CA3AF"
}

# --- CONFIG COULEURS SCORES (STRICT) ---
C_CARROT = "#EF4444"  # 0-19 (Rouge)
C_AVG    = "#374151"  # 20-39 (Gris Foncé)
C_GOOD   = "#10B981"  # 40+ (Vert)
C_GOLD   = "#FFD700"  # Bonus x2

# --- CONFIG SAISONS ---
SEASONS_CONFIG = {
    "🏆 SAISON COMPLÈTE": (1, 165),
    "🍂 PART 1: THE OPENING RUN (Oct - Thanksgiving)": (1, 37),
    "❄️ PART 2: WINTER WAR (Nov - NYE)": (38, 70),
    "🎆 PART 3: NEW YEAR BATTLE (Jan - All-Star)": (71, 113),
    "💍 PART 4: THE FINAL PUSH (Post All-Star)": (114, 165)
}

# Palette Globale
C_BG = "#050505"
C_ACCENT = "#CE1141"
C_TEXT = "#E5E7EB"
C_BLUE = "#3B82F6"
C_PURPLE = "#8B5CF6"
C_BONUS = "#06B6D4"
C_ALPHA = "#F472B6"
C_IRON = "#A1A1AA"
C_ALIEN = "#84CC16"

PACERS_PUNCHLINES = [
    "Un bon Pacer est un Pacer sous carotte 🥕",
    "PACERS : Petit Animal Chétif Et Rarement Stylé 🐁",
    "Les Pacers gèrent leur avance comme Doc Rivers gère un 3-1 📉",
    "Stat du jour : 100% des Pacers portent des chaussettes avec des sandales 🧦",
    "Définition de Pacers : 'Groupe de personnes ayant beaucoup de chance' 🍀",
    "Le classement est formel : Les Pacers trichent (source : tkt) 🕵️‍♂️",
    "Ball Don't Lie : Les Pacers vont finir par payer l'addition 🗣️",
    "Les Pacers sont aussi aimés que Dillon Brooks 🐻",
    "Les Pacers font plus de briques que Westbrook un soir de pleine lune 🌕",
    "Un Pacer ne fait pas de Best Pick, il fait un 'Pick par erreur' 🤷‍♂️",
    "Le QI Basket des Pacers est inférieur au temps de jeu de Thanasis 🇬🇷"
]

# --- 2. CSS PREMIUM ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    .glass-card {{ background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 24px; margin-bottom: 20px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3); }}
    
    /* TICKER */
    .ticker-wrap {{ position: fixed; top: 0; left: 0; width: 100%; overflow: hidden; height: 30px; background-color: #CE1141; padding-left: 100%; box-sizing: content-box; z-index: 9999; }}
    .ticker {{ display: inline-block; height: 30px; line-height: 30px; white-space: nowrap; padding-right: 100%; box-sizing: content-box; animation: ticker 30s linear infinite; }}
    .ticker__item {{ display: inline-block; padding: 0 2rem; font-size: 0.9rem; color: white; font-family: 'Rajdhani'; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }}
    @keyframes ticker {{ 0% {{ transform: translate3d(0, 0, 0); }} 100% {{ transform: translate3d(-100%, 0, 0); }} }}

    h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    .kpi-num {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 2.8rem; line-height: 1; color: #FFF; }}
    .kpi-label {{ color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
    .kpi-dashboard-fixed {{ height: 190px; display: flex; flex-direction: column; justify-content: center; }}
    
    /* TEAM HQ / GRID */
    .stat-box-mini {{ background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:12px; padding: 20px 10px; text-align:center; height:100%; display:flex; flex-direction:column; justify-content:center; }}
    .stat-mini-val {{ font-family:'Rajdhani'; font-weight:700; font-size:1.8rem; color:#FFF; line-height:1; }}
    .stat-mini-lbl {{ font-size:0.75rem; color:#888; text-transform:uppercase; margin-top:8px; letter-spacing:1px; }}
    
    /* MATCH PILLS */
    .match-pill {{ flex: 0 0 auto; min-width: 40px; height: 48px; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: 'Rajdhani'; font-weight: 700; font-size: 0.9rem; color: #FFF; margin: 0 2px; line-height: 1; padding-top: 2px; }}
    .match-row {{ display: flex; flex-direction: row-reverse; overflow-x: auto; gap: 4px; padding-bottom: 8px; width: 100%; justify-content: flex-start; }}
    
    /* TRENDS */
    .trend-box {{ background: rgba(255,255,255,0.03); border-radius: 12px; padding: 15px; border: 1px solid rgba(255,255,255,0.05); height: 100%; }}
    .hot-header {{ color: {C_ACCENT}; border-bottom: 1px solid rgba(206, 17, 65, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .cold-header {{ color: {C_BLUE}; border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .trend-card-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .trend-name {{ font-weight: 500; color: #DDD; }}
    .trend-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.1rem; }}
    .trend-delta {{ font-size: 0.8rem; margin-left: 8px; font-weight: 600; }}
    
    /* HOF */
    .hof-badge {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; background: rgba(255,255,255,0.05); }}
    .hof-player {{ font-family: 'Rajdhani'; font-size: 1.6rem; font-weight: 700; color: #FFF; }}
    .hof-stat {{ font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 800; text-align: right; line-height: 1; }}
    .hof-unit {{ font-size: 0.7rem; color: #666; text-align: right; font-weight: 600; text-transform: uppercase; }}
    
    /* COMPARATOR */
    .h2h-row {{ display:flex; justify-content:space-between; align-items:center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .h2h-label {{ font-size: 0.8rem; color: #888; text-transform:uppercase; letter-spacing:1px; }}
    .h2h-val {{ font-family:'Rajdhani'; font-weight:700; font-size:1.2rem; color:#FFF; width:80px; text-align:center; }}
    .h2h-val.win {{ color: {C_GOOD}; }}
    .h2h-val.lose {{ color: {C_CARROT}; opacity:0.6; }}
    
    /* TOP 5 PICKS STYLING */
    .top-pick-card {{ display: flex; align-items: center; background: linear-gradient(90deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%); border: 1px solid rgba(255,255,255,0.05); padding: 10px 15px; margin-bottom: 8px; border-radius: 8px; }}
    .tp-rank-badge {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 1rem; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: #222; border: 2px solid #444; color: #FFF; margin-right: 12px; flex-shrink: 0; }}
    .tp-score-big {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 1.8rem; color: #FFF; line-height: 1; margin-left: 15px; flex-shrink: 0; min-width: 60px; text-align: right; }}
    .tp-content {{ flex-grow: 1; overflow: hidden; }}
    .tp-date {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }}
    .tp-tags {{ font-size: 0.7rem; color: {C_BONUS}; font-weight: 600; }}
    
    /* RADAR LEGEND */
    .legend-box {{ display: flex; flex-direction: column; justify-content: center; height: 100%; padding-left: 20px; border-left: 1px solid #333; }}
    .legend-item {{ margin-bottom: 15px; }}
    .legend-title {{ color: {C_ACCENT}; font-family: 'Rajdhani'; font-weight: 700; font-size: 1rem; margin-bottom: 2px; }}
    .legend-desc {{ color: #888; font-size: 0.8rem; line-height: 1.3; }}
    
    .chart-desc {{ font-size:0.8rem; color:#888; margin-bottom:10px; font-style:italic; }}
    .stSelectbox label {{ color: #E5E7EB !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem; }}
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=0, show_spinner=False) 
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return None, None, None, None, [], 0, {}
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
        
        df_long['IsBP'] = df_long['ScoreRaw'].str.contains('!', na=False)
        df_long['IsBonus'] = df_long['ScoreRaw'].str.contains(r'\*', na=False)
        df_long['ScoreClean'] = df_long['ScoreRaw'].str.replace(r'[\*!]', '', regex=True)
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

        # B. STATS (Correction v22.0)
        df_stats = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Stats_Raptors_FR", header=None, ttl=0)
        team_rank_history = []
        team_current_rank = 0
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
                    hist_vals = df_stats.iloc[i, col_start_rank+1:df_stats.shape[1]].values
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
        return final_df, team_current_rank, bp_map, team_rank_history, daily_max_map
    except: return pd.DataFrame(), 0, {}, [], {}

@st.cache_data(ttl=300, show_spinner=False) 
def compute_stats(df, bp_map, daily_max_map):
    stats = []
    if df.empty: return pd.DataFrame()
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
        
        # --- PHOENIX CALCULATION (V23) ---
        max_phoenix = 0
        for i in range(len(scores) - 1):
            if scores[i] < 20: # Carrot
                rebound = scores[i+1]
                if rebound > max_phoenix: max_phoenix = rebound

        # --- BEST DECK (Rolling 7 days) (V23) ---
        max_rolling_7 = 0
        if len(scores) >= 7:
            for i in range(len(scores) - 6):
                total_7 = sum(scores[i:i+7])
                if total_7 > max_rolling_7: max_rolling_7 = total_7
        else:
            max_rolling_7 = sum(scores) if len(scores) > 0 else 0

        current_no_carrot_streak = 0
        for s in reversed(scores):
            if s >= 20: current_no_carrot_streak += 1
            else: break
            
        max_no_carrot = 0
        current_count = 0
        for s in scores:
            if s >= 20:
                current_count += 1
                if current_count > max_no_carrot: max_no_carrot = current_count
            else:
                current_count = 0
        
        max_alien_streak = 0
        current_alien = 0
        for s in scores:
            if s >= 60:
                current_alien += 1
                if current_alien > max_alien_streak: max_alien_streak = current_alien
            else:
                current_alien = 0
        
        try:
            vals, counts = np.unique(scores, return_counts=True)
            max_count_idx = np.argmax(counts)
            mode_score = vals[max_count_idx]
            mode_count = counts[max_count_idx]
        except: mode_score = 0; mode_count = 0

        spread = scores.max() - scores.min()
        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        
        # Trend Arrow for Tables
        trend_arrow = "➡️"
        if momentum > 2: trend_arrow = "↗️"
        elif momentum < -2: trend_arrow = "↘️"

        bp_count = d['IsBP'].sum()
        alpha_count = 0; bonus_points_gained = 0; bonus_scores_list = []
        for i, (pick_num, score) in enumerate(zip(picks, scores)):
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
            'MaxAlien': max_alien_streak,
            'MaxRolling7': max_rolling_7, # Added for HOF
            'MaxPhoenix': max_phoenix, # Added for HOF
            'TrendArrow': trend_arrow # Added for Table
        })
    return pd.DataFrame(stats)

def kpi_card(label, value, sub, color="#FFF", is_fixed=False):
    style_class = "glass-card kpi-dashboard-fixed" if is_fixed else "glass-card"
    st.markdown(f"""<div class="{style_class}" style="text-align:center"><div class="kpi-label">{label}</div><div class="kpi-num" style="color:{color}">{value}</div><div class="kpi-sub" style="color:{C_ACCENT}">{sub}</div></div>""", unsafe_allow_html=True)

def section_title(title, subtitle):
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)

# V23: NEW HELPER FOR COLORS
def get_color_for_score(score):
    if score < 20: return C_CARROT
    elif score < 40: return C_AVG
    else: return C_GOOD

# --- 6. MAIN APP ---
try:
    # UX BOOSTER
    components.html("""<script>window.parent.document.querySelector('.main').scrollTo(0, 0);</script>""", height=0, width=0)
    
    with st.spinner('🦖 Analyse des données en cours...'):
        # LOAD DATA
        df, team_rank, bp_map, team_history, daily_max_map = load_data()
    
    # --- V23: NEWS TICKER ---
    if df is not None and not df.empty:
        latest_pick_ticker = df['Pick'].max()
        ticker_day = df[df['Pick'] == latest_pick_ticker].sort_values('Score', ascending=False)
        top_ticker = ticker_day.iloc[0]
        team_avg_ticker = int(ticker_day['Score'].mean())
        ticker_text = f"🔥 FLASH RAPTORS : {top_ticker['Player']} domine la soirée avec {int(top_ticker['Score'])} pts !  ---  📊 Moyenne équipe : {team_avg_ticker} pts  ---  ⚔️ Winter War en cours..."
        st.markdown(f"""<div class="ticker-wrap"><div class="ticker"><div class="ticker__item">{ticker_text}</div></div></div>""", unsafe_allow_html=True)

    # --- SÉLECTEUR TEMPOREL (SIDEBAR) ---
    with st.sidebar:
        st.markdown("<div style='text-align:center; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.image("raptors-ttfl-min.png", use_container_width=True) 
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='font-family:Rajdhani; font-weight:700; color:#AAA; margin-bottom:5px; font-size:0.9rem; letter-spacing:1px'>📅 PÉRIODE ACTIVE</div>", unsafe_allow_html=True)
        options_saisons = list(SEASONS_CONFIG.keys())
        selected_season_name = st.selectbox("Période", options_saisons, index=0, label_visibility="collapsed", key="season_selector")
        start_pick, end_pick = SEASONS_CONFIG[selected_season_name]
        df_full_history = df.copy() if df is not None else pd.DataFrame()

        if df is not None and not df.empty:
            df = df[(df['Pick'] >= start_pick) & (df['Pick'] <= end_pick)].copy()
            if df.empty and selected_season_name != "🏆 SAISON COMPLÈTE":
                st.warning(f"⏳ La période '{selected_season_name}' n'a pas encore commencé."); st.stop()
            else: latest_pick = df['Pick'].max() if not df.empty else 0

        menu = option_menu(menu_title=None, options=["Dashboard", "Team HQ", "Player Lab", "Bonus x2", "No-Carrot", "Trends", "Hall of Fame", "Admin"], icons=["grid-fill", "people-fill", "person-bounding-box", "lightning-charge-fill", "shield-check", "fire", "trophy-fill", "shield-lock"], default_index=0, styles={"container": {"padding": "0!important", "background-color": "#000000"}, "icon": {"color": "#666", "font-size": "1.1rem"}, "nav-link": {"font-family": "Rajdhani, sans-serif", "font-weight": "700", "font-size": "15px", "text-transform": "uppercase", "color": "#AAA", "text-align": "left", "margin": "5px 0px", "--hover-color": "#111"}, "nav-link-selected": {"background-color": C_ACCENT, "color": "#FFF", "icon-color": "#FFF", "box-shadow": "0px 4px 20px rgba(206, 17, 65, 0.4)"}})
        st.markdown(f"""<div style='position: fixed; bottom: 30px; width: 100%; padding-left: 20px;'><div style='color:#444; font-size:10px; font-family:Rajdhani; letter-spacing:2px; text-transform:uppercase'>Pick Actuel #{int(latest_pick)}<br>War Room v23.1</div></div>""", unsafe_allow_html=True)

    # --- BANDEAU UI ---
    if selected_season_name != "🏆 SAISON COMPLÈTE":
        season_color = C_ACCENT 
        if "WINTER" in selected_season_name: season_color = C_BLUE 
        elif "NEW YEAR" in selected_season_name: season_color = C_GOLD 
        elif "FINAL" in selected_season_name: season_color = C_GOOD 
        st.markdown(f"""<div style="background: linear-gradient(90deg, {season_color} 0%, rgba(0,0,0,0) 100%); padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; border-left: 6px solid #FFF; box-shadow: 0 4px 20px rgba(0,0,0,0.5);"><div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="color: #FFF; font-family: 'Rajdhani'; font-weight: 800; font-size: 1.5rem; text-transform: uppercase; letter-spacing: 2px;">{selected_season_name.split('(')[0]}</div><div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; font-weight: 600; text-transform:uppercase; letter-spacing:1px; margin-top:2px;">🎯 PICKS #{start_pick} à #{end_pick}</div></div><div style="background:rgba(0,0,0,0.4); padding:5px 15px; border-radius:20px; color:#FFF; font-weight:700; font-size:0.8rem; border:1px solid rgba(255,255,255,0.2)">MODE TOURNOI ACTIF</div></div></div>""", unsafe_allow_html=True)
    
    if df is not None and not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False).copy()
        full_stats = compute_stats(df, bp_map, daily_max_map)
        leader = full_stats.sort_values('Total', ascending=False).iloc[0]
        team_avg_per_pick = df['Score'].mean()
        total_bp_team = full_stats['BP_Count'].sum()
        team_streak_nc = 0
        for p_id in sorted(df['Pick'].unique(), reverse=True):
            if df[df['Pick'] == p_id]['Score'].min() >= 20: team_streak_nc += 1
            else: break
            
        if menu == "Dashboard":
            section_title("RAPTORS <span class='highlight'>DASHBOARD</span>", f"Daily Briefing • Pick #{int(latest_pick)}")
            top = day_df.iloc[0]
            val_suffix = ""
            if 'IsBonus' in top and top['IsBonus']: val_suffix += " 🌟x2"
            if 'IsBP' in top and top['IsBP']: val_suffix += " 🎯BP"
            badges_html = val_suffix if val_suffix else "&nbsp;"
            sub_html = f"<div><div style='font-size:1.4rem; font-weight:800'>{int(top['Score'])} PTS</div><div style='font-size:0.9rem; color:#999; font-weight:600; margin-top:4px'>{badges_html}</div></div>"

            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: st.markdown(f"""<div class="glass-card kpi-dashboard-fixed" style="text-align:center"><div class="kpi-label">MVP DU SOIR</div><div class="kpi-num" style="color:{C_GOLD}">{top['Player']}</div><div class="kpi-sub" style="color:{C_ACCENT}">{sub_html}</div></div>""", unsafe_allow_html=True)
            with c2: kpi_card("TOTAL TEAM SOIR", int(day_df['Score'].sum()), "POINTS", is_fixed=True)
            diff_perf = ((day_df['Score'].mean() - team_avg_per_pick) / team_avg_per_pick) * 100
            perf_col = C_GOOD if diff_perf > 0 else C_CARROT
            with c3: kpi_card("PERF. TEAM SOIR", f"{diff_perf:+.1f}%", "VS MOY. PÉRIODE", perf_col, is_fixed=True)
            col_streak = C_GOOD if team_streak_nc > 0 else C_CARROT
            with c4: kpi_card("SÉRIE TEAM NO-CARROT", f"{team_streak_nc}", "JOURS CONSÉCUTIFS", col_streak, is_fixed=True)
            with c5: kpi_card("LEADER PÉRIODE", leader['Player'], f"TOTAL: {int(leader['Total'])}", C_ACCENT, is_fixed=True)
            
            day_df['BarColor'] = day_df['Score'].apply(get_color_for_score)
            c_perf, c_clutch = st.columns([2, 1])
            with c_perf:
                st.markdown("<h3 style='margin-bottom:10px; margin-top:0; color:#FFF; font-family:Rajdhani; font-weight:700'>📊 SCORES DU SOIR</h3>", unsafe_allow_html=True)
                fig = px.bar(day_df, x='Player', y='Score', text='Score', color='BarColor', color_discrete_map="identity")
                fig.update_traces(textposition='outside', marker_line_width=0, textfont_size=14, textfont_family="Rajdhani", cliponaxis=False)
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA', 'family': 'Inter'}, yaxis=dict(showgrid=False, visible=False), xaxis=dict(title=None, tickfont=dict(size=14, family='Rajdhani', weight=600)), height=350, showlegend=False, coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            
            with c_clutch:
                st.markdown("<h3 style='margin-bottom:10px; margin-top:0; color:#FFF; font-family:Rajdhani; font-weight:700'>⚡ CLUTCH DU SOIR</h3>", unsafe_allow_html=True)
                day_merged = pd.merge(day_df, full_stats[['Player', 'Moyenne']], on='Player')
                day_merged['Delta'] = day_merged['Score'] - day_merged['Moyenne']
                for i, row in enumerate(day_merged.sort_values('Delta', ascending=False).head(3).itertuples()):
                    st.markdown(f"""<div class='glass-card' style='margin-bottom:10px; padding:12px'><div style='display:flex; justify-content:space-between; align-items:center'><div><div style='font-weight:700; color:{C_TEXT}'>{row.Player}</div><div style='font-size:0.75rem; color:#666'>Moy: {row.Moyenne:.1f}</div></div><div style='text-align:right'><div style='font-size:1.2rem; font-weight:800; color:{C_GOOD}'>+{row.Delta:.1f}</div><div style='font-size:0.8rem; color:#888'>{int(row.Score)} pts</div></div></div></div>""", unsafe_allow_html=True)

            c_gen, c_form, c_text = st.columns(3)
            with c_gen:
                st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_ACCENT}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🏆 TOP 5 PÉRIODE</div>", unsafe_allow_html=True)
                for i, r in full_stats.sort_values('Total', ascending=False).head(5).reset_index().iterrows():
                    st.markdown(f"<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px'><div style='display:flex; align-items:center; gap:10px'><div style='font-size:1.2rem; width:20px'>#{i+1}</div><div style='font-family:Rajdhani; font-weight:600; font-size:1rem; color:#FFF'>{r['Player']}</div></div><div style='text-align:right'><span style='font-family:Rajdhani; font-weight:700; color:{C_ACCENT}'>{int(r['Total'])}</span> <span style='font-size:0.8rem'>{r['TrendArrow']}</span></div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c_form:
                st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_GOOD}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🔥 TOP 5 FORME (15J)</div>", unsafe_allow_html=True)
                for i, r in full_stats.sort_values('Last15', ascending=False).head(5).reset_index().iterrows():
                    st.markdown(f"<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px'><div style='display:flex; align-items:center; gap:10px'><div style='font-size:1.2rem; width:20px'>#{i+1}</div><div style='font-family:Rajdhani; font-weight:600; font-size:1rem; color:#FFF'>{r['Player']}</div></div><div style='font-family:Rajdhani; font-weight:700; color:{C_GOOD}'>{r['Last15']:.1f}</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c_text:
                st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_TEXT}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🎨 TEXTURE DES PICKS</div>", unsafe_allow_html=True)
                day_df['RangeV23'] = pd.cut(day_df['Score'], bins=[-1, 19, 39, 200], labels=['Carotte', 'Moyen', 'Top'])
                dist_counts = day_df['RangeV23'].value_counts().reset_index()
                dist_counts.columns = ['Range', 'Count']
                fig_donut = px.pie(dist_counts, values='Count', names='Range', hole=0.4, color='Range', color_discrete_map={'Carotte': C_CARROT, 'Moyen': C_AVG, 'Top': C_GOOD})
                fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=220, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_donut, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)

        elif menu == "Team HQ":
            section_title("TEAM <span class='highlight'>HQ</span>", "Vue d'ensemble de l'effectif")
            total_pts_season = df['Score'].sum()
            daily_agg = df.groupby('Pick')['Score'].sum()
            avg_night = daily_agg.mean()
            
            k1, k2, k3, k4 = st.columns(4)
            with k1: kpi_card("TOTAL PÉRIODE", int(total_pts_season), "POINTS CUMULÉS", C_GOLD)
            with k2: kpi_card("MOYENNE / PICK", f"{team_avg_per_pick:.1f}", "PAR JOUEUR", "#FFF")
            with k3: kpi_card("MOYENNE ÉQUIPE / SOIR", f"{int(avg_night)}", "TOTAL COLLECTIF", C_BLUE)
            
            avg_team_15 = daily_agg[daily_agg.index > (latest_pick - 15)].mean() if len(daily_agg) > 15 else daily_agg.mean()
            diff_dyn_team = ((avg_team_15 - avg_night) / avg_night) * 100
            with k4: kpi_card("DYNAMIQUE 15J", f"{diff_dyn_team:+.1f}%", "VS MOY. PÉRIODE", C_GOOD if diff_dyn_team > 0 else C_CARROT)

            st.markdown("<br>", unsafe_allow_html=True)
            c_grid, c_extra = st.columns([2, 1], gap="medium")
            
            with c_grid:
                # FULL GRID 3x3 FROM V21.7
                g1, g2, g3 = st.columns(3, gap="small")
                with g1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(latest_pick)}</div><div class='stat-mini-lbl'>MATCHS JOUÉS</div></div>", unsafe_allow_html=True)
                with g2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_ACCENT}'>#{int(team_rank)}</div><div class='stat-mini-lbl'>CLASSEMENT</div></div>", unsafe_allow_html=True)
                with g3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>#{min(team_history)}</div><div class='stat-mini-lbl'>BEST RANK</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
                g4, g5, g6 = st.columns(3, gap="small")
                with g4: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BLUE}'>{len(df[df['Score']>35])}</div><div class='stat-mini-lbl'>SAFE ZONE</div></div>", unsafe_allow_html=True)
                with g5: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOOD}'>{len(df[df['Score']>=50])}</div><div class='stat-mini-lbl'>NUKES</div></div>", unsafe_allow_html=True)
                with g6: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_CARROT}'>{len(df[df['Score']<20])}</div><div class='stat-mini-lbl'>CAROTTES</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
                g7, g8, g9 = st.columns(3, gap="small")
                with g7: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_PURPLE}'>{total_bp_team}</div><div class='stat-mini-lbl'>BEST PICKS</div></div>", unsafe_allow_html=True)
                with g8: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BONUS}'>{total_bonus_played}</div><div class='stat-mini-lbl'>BONUS JOUÉS</div></div>", unsafe_allow_html=True)
                with g9: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(daily_agg.max())}</div><div class='stat-mini-lbl'>RECORD TEAM</div></div>", unsafe_allow_html=True)

            with c_extra:
                st.markdown("### 🏁 LA COURSE AU TITRE")
                st.markdown("<div class='chart-desc'>Évolution du classement (Cumulatif).</div>", unsafe_allow_html=True)
                df_sorted = df.sort_values('Pick')
                df_cumul = df_sorted.groupby(['Player', 'Pick'])['Score'].sum().groupby(level=0).cumsum().reset_index()
                df_cumul.rename(columns={'Score': 'Total'}, inplace=True)
                df_race = df_cumul[df_cumul['Pick'] % 2 == 0].copy() if df_cumul['Pick'].nunique() > 50 else df_cumul.copy()
                fig_race = px.bar(df_race, x="Total", y="Player", orientation='h', text="Total", animation_frame="Pick", range_x=[0, df_race['Total'].max()*1.1])
                fig_race.update_traces(marker_color=C_ACCENT, textposition='outside')
                fig_race.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, yaxis={'categoryorder':'total ascending'}, height=350, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig_race, use_container_width=True)

            st.markdown("### 🔥 HEATMAP UNIFIÉE")
            heat_filter = st.selectbox("📅 Filtrer la Heatmap", ["VUE GLOBALE"] + list(df['Month'].unique()), key='heat_filter')
            df_heat = df if heat_filter == "VUE GLOBALE" else df[df['Month'] == heat_filter]
            heatmap_data = df_heat.pivot_table(index='Player', columns='Pick', values='Score', aggfunc='sum')
            # V23: STRICT COLOR SCALE
            colorscale = [[0.0, C_CARROT], [0.25, C_CARROT], [0.25, C_AVG], [0.5, C_AVG], [0.5, C_GOOD], [1.0, "#00FF00"]]
            fig_heat = px.imshow(heatmap_data, labels=dict(x="Pick", y="Player", color="Score"), x=heatmap_data.columns, y=heatmap_data.index, color_continuous_scale="RdYlGn", zmin=0, zmax=60, aspect="auto")
            fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=500, xaxis={'showgrid': False}, yaxis={'showgrid': False})
            st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("### 📊 DATA ROOM")
            st.dataframe(full_stats[['Player', 'TrendArrow', 'Total', 'Moyenne', 'BP_Count', 'Nukes', 'Carottes', 'Bonus_Gained']].sort_values('Total', ascending=False), hide_index=True, use_container_width=True, column_config={"Player": st.column_config.TextColumn("Joueur", width="medium"), "Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()), "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f")})

        elif menu == "Player Lab":
            section_title("PLAYER <span class='highlight'>LAB</span>", "Deep Dive Analytics")
            
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                st.markdown("<div class='widget-title'>👤 JOUEUR PRINCIPAL</div>", unsafe_allow_html=True)
                sel_player = st.selectbox("Recherche", sorted(df['Player'].unique()), label_visibility="collapsed")
            with col_sel2:
                st.markdown("<div class='widget-title'>🆚 COMPARER AVEC (OPTIONNEL)</div>", unsafe_allow_html=True)
                compare_list = ["Aucun"] + [p for p in sorted(df['Player'].unique()) if p != sel_player]
                comp_player = st.selectbox("Adversaire", compare_list, label_visibility="collapsed")
            
            p_data = full_stats[full_stats['Player'] == sel_player].iloc[0]
            p_hist_all = df[df['Player'] == sel_player]
            
            if comp_player != "Aucun":
                comp_data = full_stats[full_stats['Player'] == comp_player].iloc[0]
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    st.markdown(f"<div style='text-align:center; font-family:Rajdhani; font-size:1.5rem; color:{C_GOLD}'>VS</div>", unsafe_allow_html=True)
                    metrics = [("TOTAL POINTS", 'Total', 'int'), ("MOYENNE", 'Moyenne', 'float'), ("RECORD", 'Best', 'int'), ("NUKES (>50)", 'Nukes', 'int'), ("CAROTTES (<20)", 'Carottes', 'int'), ("FORME (15J)", 'Last15', 'float')]
                    for label, key, fmt in metrics:
                        v1 = p_data[key]; v2 = comp_data[key]
                        win1 = v1 > v2 if key != 'Carottes' else v1 < v2
                        col1 = C_GOOD if win1 else (C_CARROT if v1 != v2 else "#FFF")
                        col2 = C_GOOD if not win1 and v1 != v2 else (C_CARROT if v1 != v2 else "#FFF")
                        val1 = int(v1) if fmt == 'int' else f"{v1:.1f}"
                        val2 = int(v2) if fmt == 'int' else f"{v2:.1f}"
                        st.markdown(f"<div class='h2h-row'><div class='h2h-val' style='color:{col1}'>{val1}</div><div class='h2h-label'>{label}</div><div class='h2h-val' style='color:{col2}'>{val2}</div></div>", unsafe_allow_html=True)
                with c2:
                    max_avg = full_stats['Moyenne'].max(); max_best = full_stats['Best'].max()
                    def get_radar_vals(d): return [(d['Moyenne']/max_avg)*100, (d['Best']/max_best)*100, (d['Last10']/full_stats['Last10'].max())*100, 100-((d['StdDev']/full_stats['StdDev'].max())*100), (d['Nukes']/(full_stats['Nukes'].max() if full_stats['Nukes'].max()>0 else 1))*100]
                    fig_rad = go.Figure()
                    fig_rad.add_trace(go.Scatterpolar(r=get_radar_vals(p_data)+[get_radar_vals(p_data)[0]], theta=['SCORING', 'CEILING', 'FORME', 'RÉGULARITÉ', 'CLUTCH']*2, fill='toself', name=sel_player, line_color=PLAYER_COLORS.get(sel_player, C_ACCENT)))
                    fig_rad.add_trace(go.Scatterpolar(r=get_radar_vals(comp_data)+[get_radar_vals(comp_data)[0]], theta=['SCORING', 'CEILING', 'FORME', 'RÉGULARITÉ', 'CLUTCH']*2, fill='toself', name=comp_player, line_color=PLAYER_COLORS.get(comp_player, C_BLUE), opacity=0.5))
                    fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(t=20, b=20, l=40, r=40), height=400)
                    st.plotly_chart(fig_rad, use_container_width=True)
            else:
                c1, c2, c3, c4, c5 = st.columns(5)
                sorted_team = full_stats.sort_values('Total', ascending=False).reset_index(drop=True)
                rank = sorted_team[sorted_team['Player'] == sel_player].index[0] + 1
                with c1: kpi_card("TOTAL POINTS", int(p_data['Total']), "PÉRIODE")
                with c2: kpi_card("MOYENNE", f"{p_data['Moyenne']:.1f}", "PTS / PICK")
                with c3: kpi_card("SÉRIE NO-CAROTTE", f"{int(p_data['CurrentNoCarrot'])}", "MATCHS", C_GOOD if p_data['CurrentNoCarrot'] > 3 else C_CARROT)
                with c4: kpi_card("CLASSEMENT", f"#{rank}", "PÉRIODE", C_GOLD if rank==1 else "#FFF")
                with c5: kpi_card("BEST SCORE", int(p_data['Best']), "RECORD PÉRIODE", C_GOLD)

                st.markdown("<div style='margin-top:20px; text-align:center; color:#888; font-size:0.8rem; margin-bottom:5px'>HISTORIQUE MATCHS</div>", unsafe_allow_html=True)
                if not p_hist_all.empty:
                    html_picks = "<div class='match-row' style='width:100%'>"
                    desc_picks = p_hist_all.sort_values('Pick', ascending=False)
                    for _, r in desc_picks.iterrows():
                        sc = r['Score']; bg = get_color_for_score(sc); txt = "#FFF"; border = "1px solid rgba(255,255,255,0.1)"
                        if r['IsBonus']: bg = C_GOLD; txt = "#000"; border = "2px solid #FFF"
                        pill_content = f"<div class='mp-score'>{int(sc)}</div>"
                        if r.get('IsBP', False): pill_content += "<div class='mp-icon'>🎯</div>"
                        html_picks += f"<div class='match-pill' style='background:{bg}; color:{txt}; border:{border}' title='Pick #{r['Pick']}'>{pill_content}</div>"
                    html_picks += "</div>"
                    st.markdown(html_picks, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                # FULL GRID KPI FROM V21.7
                col_grid, col_top5 = st.columns([3, 1], gap="medium")
                with col_grid:
                    r1c1, r1c2, r1c3 = st.columns(3, gap="small")
                    with r1c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['ReliabilityPct'])}%</div><div class='stat-mini-lbl'>FIABILITÉ</div></div>", unsafe_allow_html=True)
                    with r1c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Last15']:.1f}</div><div class='stat-mini-lbl'>MOYENNE 15J</div></div>", unsafe_allow_html=True)
                    with r1c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Best_Raw'])}</div><div class='stat-mini-lbl'>BEST SCORE SEC</div></div>", unsafe_allow_html=True)
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    r2c1, r2c2, r2c3 = st.columns(3, gap="small")
                    with r2c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BLUE}'>{int(p_data['Count35'])}</div><div class='stat-mini-lbl'>SAFE ZONE</div></div>", unsafe_allow_html=True)
                    with r2c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOOD}'>{int(p_data['Nukes'])}</div><div class='stat-mini-lbl'>NUKES</div></div>", unsafe_allow_html=True)
                    with r2c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_CARROT}'>{int(p_data['Carottes'])}</div><div class='stat-mini-lbl'>CAROTTES</div></div>", unsafe_allow_html=True)
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    r3c1, r3c2, r3c3 = st.columns(3, gap="small")
                    with r3c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_PURPLE}'>{int(p_data['BP_Count'])}</div><div class='stat-mini-lbl'>BEST PICKS</div></div>", unsafe_allow_html=True)
                    with r3c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>{int(p_data['Alpha_Count'])}</div><div class='stat-mini-lbl'>MVP</div></div>", unsafe_allow_html=True)
                    with r3c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BONUS}'>{p_data['Avg_Bonus']:.1f}</div><div class='stat-mini-lbl'>MOYENNE BONUS</div></div>", unsafe_allow_html=True)

                with col_top5:
                    st.markdown("#### 🌟 TOP 5 PICKS")
                    top_5 = p_hist_all.sort_values('Score', ascending=False).head(5)
                    for i, r in top_5.reset_index().iterrows():
                        rank_num = i + 1
                        border_col = C_GOLD if rank_num == 1 else (C_SILVER if rank_num == 2 else (C_BRONZE if rank_num == 3 else "#444"))
                        html_card = f"""<div class="top-pick-card" style="border-left: 4px solid {border_col}"><div class="tp-rank-badge" style="border-color:{border_col}; color:{border_col}">{rank_num}</div><div class="tp-content"><div class="tp-date">Pick #{r['Pick']}</div></div><div class="tp-score-big">{int(r['Score'])}</div></div>"""
                        st.markdown(html_card, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                c_radar_graph, c_radar_legend = st.columns([2, 1], gap="large")
                with c_radar_graph:
                    max_avg = full_stats['Moyenne'].max(); max_best = full_stats['Best'].max()
                    reg_score = 100 - ((p_data['StdDev'] / full_stats['StdDev'].max()) * 100)
                    r_vals = [(p_data['Moyenne']/max_avg)*100, (p_data['Best']/max_best)*100, (p_data['Last10']/full_stats['Last10'].max())*100, reg_score, (p_data['Nukes']/(full_stats['Nukes'].max() if full_stats['Nukes'].max()>0 else 1))*100]
                    fig_radar = go.Figure(data=go.Scatterpolar(r=r_vals + [r_vals[0]], theta=['SCORING', 'CEILING', 'FORME', 'RÉGULARITÉ', 'CLUTCH']*2, fill='toself', line_color=C_ACCENT, fillcolor="rgba(206, 17, 65, 0.3)"))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=14, family="Rajdhani"), margin=dict(t=20, b=20, l=40, r=40), height=400)
                    st.plotly_chart(fig_radar, use_container_width=True)
                with c_radar_legend:
                    st.markdown("""<div class='legend-box'><div class='legend-item'><div class='legend-title'>SCORING</div><div class='legend-desc'>Volume de points moyen.</div></div><div class='legend-item'><div class='legend-title'>CEILING</div><div class='legend-desc'>Potentiel max.</div></div><div class='legend-item'><div class='legend-title'>FORME</div><div class='legend-desc'>Dynamique 10j.</div></div></div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                c_dist, c_trend = st.columns(2, gap="medium")
                with c_dist:
                    st.markdown("#### 📊 DISTRIBUTION", unsafe_allow_html=True)
                    fig_hist = px.histogram(p_hist_all, x="Score", nbins=15, color_discrete_sequence=[C_ACCENT], text_auto=True)
                    fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=10, b=0), height=250, xaxis_title=None, yaxis_title=None, bargap=0.1)
                    st.plotly_chart(fig_hist, use_container_width=True)
                with c_trend:
                    st.markdown("#### 📈 TENDANCE", unsafe_allow_html=True)
                    last_15_data = p_hist_all.sort_values('Pick').tail(15)
                    fig_trend = px.line(last_15_data, x="Pick", y="Score", markers=True)
                    fig_trend.update_traces(line_color=C_GOLD, marker_color=C_ACCENT)
                    fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=10, b=0), height=250)
                    st.plotly_chart(fig_trend, use_container_width=True)

        elif menu == "Bonus x2":
            section_title("BONUS <span class='highlight'>ZONE</span>", "Analyse de Rentabilité")
            df_bonus = df[df['IsBonus'] == True].copy()
            df_bonus['RealGain'] = df_bonus['Score'] - df_bonus['ScoreVal']
            available_months = df['Month'].unique().tolist()
            sel_month = st.selectbox("Filtrer par Mois", ["Tous"] + [m for m in available_months if m != "Inconnu"])
            if sel_month != "Tous": df_bonus_disp = df_bonus[df_bonus['Month'] == sel_month]
            else: df_bonus_disp = df_bonus

            if df_bonus_disp.empty: st.info("Aucun bonus trouvé.")
            else:
                k1, k2, k3, k4, k5 = st.columns(5)
                with k1: kpi_card("TOTAL", len(df_bonus_disp), "BONUS JOUÉS 🌟", C_BONUS)
                with k2: kpi_card("MOYENNE", f"{df_bonus_disp['Score'].mean():.1f}", "PTS / BONUS", "#FFF")
                with k3: kpi_card("GAIN RÉEL", f"+{int(df_bonus_disp['RealGain'].sum())}", "PTS AJOUTÉS", C_GOOD)
                success_rate = (len(df_bonus_disp[df_bonus_disp['Score'] >= 50]) / len(df_bonus_disp) * 100)
                with k4: kpi_card("RENTABILITÉ", f"{int(success_rate)}%", "SCORES > 50 PTS", C_PURPLE)
                with k5: kpi_card("RECORD", int(df_bonus_disp['Score'].max()), "MAX SCORE", C_GOLD)
                
                st.markdown("<br>", unsafe_allow_html=True)
                c_ch1, c_ch2 = st.columns([2, 3])
                with c_ch1:
                    st.markdown("#### 💰 GAINS MENSUELS")
                    monthly_gain = df_bonus.groupby('Month')['RealGain'].sum().reset_index()
                    fig_m = px.bar(monthly_gain, x='Month', y='RealGain', text='RealGain', color='RealGain', color_continuous_scale='Teal')
                    fig_m.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=300)
                    st.plotly_chart(fig_m, use_container_width=True)
                with c_ch2:
                    st.markdown("#### 🎯 SCORES BONUS")
                    fig_strip = px.strip(df_bonus_disp, x="Player", y="Score", color="Player", color_discrete_map=PLAYER_COLORS, stripmode='overlay')
                    fig_strip.update_traces(marker=dict(size=12, line=dict(width=1, color='White'), opacity=0.9))
                    fig_strip.add_hline(y=50, line_dash="dash", line_color="#666")
                    fig_strip.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=300)
                    st.plotly_chart(fig_strip, use_container_width=True)

                st.markdown("### 📜 HISTORIQUE DÉTAILLÉ")
                st.dataframe(df_bonus_disp[['Pick', 'Player', 'Month', 'ScoreVal', 'Score', 'RealGain']].sort_values('Pick', ascending=False), hide_index=True, use_container_width=True)

        elif menu == "No-Carrot":
            section_title("ANTI <span class='highlight'>CARROTE</span>", "Objectif Fiabilité")
            max_streak_team = 0
            curr_str = 0
            for p_id in sorted(df['Pick'].unique()):
                if df[df['Pick'] == p_id]['Score'].min() >= 20: curr_str += 1
                else:
                    if curr_str > max_streak_team: max_streak_team = curr_str
                    curr_str = 0
            if curr_str > max_streak_team: max_streak_team = curr_str
            iron_man_curr = full_stats.sort_values('CurrentNoCarrot', ascending=False).iloc[0]
            
            k1, k2, k3 = st.columns(3)
            with k1: kpi_card("SÉRIE TEAM", f"{team_streak_nc}", "JOURS SANS CAROTTE", C_GOOD if team_streak_nc > 0 else C_CARROT)
            with k2: kpi_card("RECORD PÉRIODE", f"{max_streak_team}", "JOURS CONSÉCUTIFS", C_GOLD)
            with k3: kpi_card("IRON MAN", iron_man_curr['Player'], f"{int(iron_man_curr['CurrentNoCarrot'])} MATCHS SUITE", C_BLUE)
            
            st.markdown("<br>", unsafe_allow_html=True)
            c_graph, c_list = st.columns([2, 1], gap="large")
            with c_graph:
                st.markdown("#### 📉 ZONE DE DANGER")
                carrot_counts = df[df['Score'] < 20].groupby('Pick').size().reset_index(name='Carottes')
                all_picks = pd.DataFrame({'Pick': sorted(df['Pick'].unique())})
                carrot_chart = pd.merge(all_picks, carrot_counts, on='Pick', how='left').fillna(0)
                # FIX V23.1 : GREEN if 0 carrots, RED if > 0
                carrot_chart['Color'] = np.where(carrot_chart['Carottes'] > 0, C_CARROT, C_GOOD)
                fig_car = px.bar(carrot_chart, x='Pick', y='Carottes', color='Color', color_discrete_map="identity")
                fig_car.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#222'), showlegend=False, height=350)
                st.plotly_chart(fig_car, use_container_width=True)
            with c_list:
                st.markdown("#### 🛡️ SÉRIES EN COURS")
                sorted_reliability = full_stats.sort_values('CurrentNoCarrot', ascending=False)[['Player', 'CurrentNoCarrot']]
                for i, r in sorted_reliability.iterrows():
                    val = int(r['CurrentNoCarrot'])
                    col_bar = C_GOOD if val >= 10 else (C_BLUE if val >= 5 else C_TEXT)
                    width = min(100, val * 2)
                    st.markdown(f"<div style='margin-bottom:8px;'><div style='display:flex; justify-content:space-between; font-size:0.9rem; font-weight:600; color:{C_TEXT}'><span>{r['Player']}</span><span style='color:{col_bar}'>{val}</span></div><div style='width:100%; background:#222; height:6px; border-radius:3px; margin-top:2px;'><div style='width:{width}%; background:{col_bar}; height:100%; border-radius:3px;'></div></div></div>", unsafe_allow_html=True)

        elif menu == "Trends":
            section_title("TENDANCES", "Analyse de la forme (15j)")
            df_15 = df[df['Pick'] > (latest_pick - 15)]
            team_daily_15 = df_15.groupby('Pick')['Score'].sum()
            avg_15_team = team_daily_15.mean()
            season_avg_team = df.groupby('Pick')['Score'].sum().mean()
            team_trend_diff = ((avg_15_team - season_avg_team) / season_avg_team) * 100
            best_form = df_15.groupby('Player')['Score'].mean().idxmax()
            best_val = df_15.groupby('Player')['Score'].mean().max()
            
            k1, k2, k3, k4, k5 = st.columns(5)
            with k1: kpi_card("MOYENNE TEAM (15J)", f"{avg_15_team:.0f}", "POINTS / SOIR", C_BLUE)
            with k2: kpi_card("MOYENNE / PICK", f"{df_15['Score'].mean():.1f}", "INDIVIDUEL", "#FFF")
            with k3: kpi_card("DYNAMIQUE", f"{team_trend_diff:+.1f}%", "VS SAISON", C_GOOD if team_trend_diff > 0 else C_CARROT)
            with k4: kpi_card("PLAFOND TEAM", int(team_daily_15.max()), "MEILLEUR SOIR", C_GOLD)
            with k5: kpi_card("MVP (15J)", best_form, f"{best_val:.1f} PTS", C_ACCENT)
            
            st.markdown("<br>", unsafe_allow_html=True)
            # RESTORED HOT/COLD COLUMNS V21.7
            player_season_avg = df.groupby('Player')['Score'].mean()
            player_15_avg = df[df['Pick'] > (latest_pick - 15)].groupby('Player')['Score'].mean()
            delta_df = pd.DataFrame({'Season': player_season_avg, 'Last15': player_15_avg})
            delta_df['Delta'] = delta_df['Last15'] - delta_df['Season']
            delta_df = delta_df.dropna()
            hot_players = delta_df[delta_df['Delta'] > 0].sort_values('Delta', ascending=False).head(5)
            cold_players = delta_df[delta_df['Delta'] < 0].sort_values('Delta', ascending=True).head(5)

            c_hot, c_cold = st.columns(2, gap="large")
            with c_hot:
                st.markdown(f"<div class='trend-box'><div class='hot-header'>🔥 EN FEU (SUR-PERFORMANCE)</div><div style='font-size:0.8rem; color:#888; margin-bottom:10px'>Joueurs au-dessus de leur moyenne période sur les 15 derniers matchs.</div>", unsafe_allow_html=True)
                for p, row in hot_players.iterrows():
                    st.markdown(f"<div class='trend-card-row'><div class='trend-name'>{p}</div><div style='text-align:right'><div class='trend-val' style='color:{C_GOOD}'>{row['Last15']:.1f}</div><div class='trend-delta' style='color:{C_GOOD}'>+{row['Delta']:.1f}</div></div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c_cold:
                st.markdown(f"<div class='trend-box'><div class='cold-header'>❄️ DANS LE DUR (SOUS-PERFORMANCE)</div><div style='font-size:0.8rem; color:#888; margin-bottom:10px'>Joueurs en-dessous de leur moyenne période sur les 15 derniers matchs.</div>", unsafe_allow_html=True)
                for p, row in cold_players.iterrows():
                    st.markdown(f"<div class='trend-card-row'><div class='trend-name'>{p}</div><div style='text-align:right'><div class='trend-val' style='color:{C_CARROT}'>{row['Last15']:.1f}</div><div class='trend-delta' style='color:{C_CARROT}'>{row['Delta']:.1f}</div></div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📉 MOMENTUM")
            active = df_15['Player'].unique()
            mom_data = df_15[df_15['Player'].isin(active)].sort_values('Pick')
            fig_mom = px.line(mom_data, x='Pick', y='Score', color='Player', markers=True, color_discrete_map=PLAYER_COLORS)
            fig_mom.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=500, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_mom, use_container_width=True)

        elif menu == "Hall of Fame":
            section_title("HALL OF <span class='highlight'>FAME</span>", "Records & Trophées de la saison")
            
            st.markdown("<h3 style='margin-bottom:15px; font-family:Rajdhani; color:#AAA;'>🏆 RAPTORS SEASON TROPHIES</h3>", unsafe_allow_html=True)
            trophy_cols = st.columns(4)
            season_keys = [k for k in SEASONS_CONFIG.keys() if "SAISON COMPLÈTE" not in k]
            real_latest = df_full_history['Pick'].max() if not df_full_history.empty else 0
            
            for i, s_name in enumerate(season_keys):
                s_start, s_end = SEASONS_CONFIG[s_name]
                short_name = s_name.split(':')[0].replace("PART ", "P")
                full_title = s_name.split(':')[1].split('(')[0].strip()
                is_finished = real_latest > s_end
                is_active = s_start <= real_latest <= s_end
                
                card_bg = "rgba(255,255,255,0.02)"; border_col = "#333"; title_col = "#666"; icon = "🔒"; player_name = "VERROUILLÉ"; score_val = "-"
                
                if not (real_latest < s_start):
                    df_part = df_full_history[(df_full_history['Pick'] >= s_start) & (df_full_history['Pick'] <= s_end)]
                    if not df_part.empty:
                        leader = df_part.groupby('Player')['Score'].sum().sort_values(ascending=False).head(1)
                        if not leader.empty: player_name = leader.index[0]; score_val = f"{int(leader.values[0])} pts"
                    if is_finished:
                        card_bg = "linear-gradient(145deg, rgba(255, 215, 0, 0.1) 0%, rgba(0,0,0,0.4) 100%)"; border_col = C_GOLD; title_col = C_GOLD; icon = "👑"
                    elif is_active:
                        card_bg = "linear-gradient(145deg, rgba(59, 130, 246, 0.1) 0%, rgba(0,0,0,0.4) 100%)"; border_col = C_BLUE; title_col = C_BLUE; icon = "🔥"; short_name += " (EN COURS)"

                with trophy_cols[i]:
                    st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border_col}; border-radius:10px; padding:15px; text-align:center; height:100%;"><div style="font-size:0.7rem; color:#888; text-transform:uppercase; margin-bottom:5px;">{short_name}</div><div style="font-family:Rajdhani; font-weight:700; color:{title_col}; font-size:0.9rem; text-transform:uppercase; height:35px; margin-bottom:10px;">{full_title}</div><div style="font-size:1.5rem; margin-bottom:5px;">{icon}</div><div style="font-family:Rajdhani; font-weight:800; color:#FFF; font-size:1.1rem;">{player_name}</div><div style="font-size:0.8rem; color:{title_col}; font-weight:600;">{score_val}</div></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom:10px; font-family:Rajdhani; color:#AAA;'>🏛️ RECORDS GLOBAUX SAISON</h3>", unsafe_allow_html=True)
            
            full_stats_global = compute_stats(df_full_history, bp_map, daily_max_map)
            def get_hof(metric, asc=False): return full_stats_global.sort_values(metric, ascending=asc).iloc[0]
            
            # V23.1: RESTORED ORIGINAL DESCRIPTIONS
            hof_list = [
                {"title": "THE GOAT", "icon": "🏆", "color": C_GOLD, "p": get_hof('Moyenne'), "v": f"{get_hof('Moyenne')['Moyenne']:.1f}", "u": "PTS MOY", "d": "Meilleure moyenne générale de la saison (Bonus incl.)"},
                {"title": "REAL MVP", "icon": "💎", "color": C_PURE, "p": get_hof('Moyenne_Raw'), "v": f"{get_hof('Moyenne_Raw')['Moyenne_Raw']:.1f}", "u": "PTS BRUT", "d": "Meilleure moyenne sans compter les bonus"},
                {"title": "KING OF DECKS", "icon": "🃏", "color": "#E11D48", "p": get_hof('MaxRolling7'), "v": int(get_hof('MaxRolling7')['MaxRolling7']), "u": "PTS / 7J", "d": "Meilleure série de 7 jours glissants"},
                {"title": "THE PHOENIX", "icon": "🐣", "color": "#F43F5E", "p": get_hof('MaxPhoenix'), "v": int(get_hof('MaxPhoenix')['MaxPhoenix']), "u": "REBOND", "d": "Meilleur score le lendemain d'une carotte"},
                {"title": "THE SNIPER", "icon": "🎯", "color": C_PURPLE, "p": get_hof('BP_Count'), "v": int(get_hof('BP_Count')['BP_Count']), "u": "BEST PICKS", "d": "Le plus de Best Picks trouvés"},
                {"title": "ALPHA DOG", "icon": "🐺", "color": C_ALPHA, "p": get_hof('Alpha_Count'), "v": int(get_hof('Alpha_Count')['Alpha_Count']), "u": "TOPS TEAM", "d": "Le plus souvent meilleur scoreur de l'équipe"},
                {"title": "THE CEILING", "icon": "🏔️", "color": "#FB7185", "p": get_hof('Best'), "v": int(get_hof('Best')['Best']), "u": "MAX SCORE", "d": "Record absolu sur un match (Bonus inclus)"},
                {"title": "PURE SCORER", "icon": "🏀", "color": "#7C3AED", "p": get_hof('Best_Raw'), "v": int(get_hof('Best_Raw')['Best_Raw']), "u": "MAX BRUT", "d": "Record absolu sur un match (Sans bonus)"},
                {"title": "THE ALCHEMIST", "icon": "⚗️", "color": C_BONUS, "p": get_hof('Bonus_Gained'), "v": int(get_hof('Bonus_Gained')['Bonus_Gained']), "u": "PTS BONUS", "d": "Le plus de points gagnés grâce aux bonus"},
                {"title": "NUCLEAR", "icon": "☢️", "color": C_ACCENT, "p": get_hof('Nukes'), "v": int(get_hof('Nukes')['Nukes']), "u": "BOMBS", "d": "Le plus de scores > 50 pts"},
                {"title": "HEAVY HITTER", "icon": "🥊", "color": "#DC2626", "p": get_hof('Count40'), "v": int(get_hof('Count40')['Count40']), "u": "PICKS > 40", "d": "Le plus de scores > 40 pts"},
                {"title": "THE ROCK", "icon": "🛡️", "color": C_GOOD, "p": get_hof('Count30'), "v": int(get_hof('Count30')['Count30']), "u": "MATCHS", "d": "Le plus de scores dans la Safe Zone (> 30 pts)"},
                {"title": "HUMAN TORCH", "icon": "🔥", "color": "#BE123C", "p": get_hof('Last15'), "v": f"{get_hof('Last15')['Last15']:.1f}", "u": "PTS / 15J", "d": "Meilleure forme actuelle (Moyenne 15j)"},
                {"title": "RISING STAR", "icon": "🚀", "color": "#34D399", "p": get_hof('ProgressionPct'), "v": f"+{get_hof('ProgressionPct')['ProgressionPct']:.1f}%", "u": "PROGRESSION", "d": "Plus grosse progression (Moyenne 15j vs Saison)"},
                {"title": "ZEN MASTER", "icon": "🧘", "color": "#38BDF8", "p": get_hof('ReliabilityPct'), "v": f"{int(get_hof('ReliabilityPct')['ReliabilityPct'])}%", "u": "FIABILITÉ", "d": "Plus haut taux de fiabilité (Moins de carottes)"},
                {"title": "UNSTOPPABLE", "icon": "⚡", "color": "#F59E0B", "p": get_hof('Streak30'), "v": int(get_hof('Streak30')['Streak30']), "u": "SERIE", "d": "Plus longue série consécutive > 30 pts"},
                {"title": "METRONOME", "icon": "⏰", "color": C_IRON, "p": get_hof('StdDev', True), "v": f"{get_hof('StdDev', True)['StdDev']:.1f}", "u": "ECART TYPE", "d": "Le joueur le plus régulier (Faible variation)"},
                {"title": "THE MANIAC", "icon": "🤪", "color": "#D946EF", "p": get_hof('ModeCount'), "v": f"{get_hof('ModeCount')['ModeScore']}", "u": "REPETITION", "d": "Score le plus souvent répété par ce joueur"},
                {"title": "IRON WALL", "icon": "🧱", "color": "#78350F", "p": get_hof('Worst'), "v": int(get_hof('Worst')['Worst']), "u": "PIRE SCORE", "d": "Le 'Pire score' le plus élevé (Plancher haut)"},
                {"title": "ALBATROSS", "icon": "🦅", "color": "#2DD4BF", "p": get_hof('Spread'), "v": int(get_hof('Spread')['Spread']), "u": "AMPLITUDE", "d": "Plus grand écart entre le record et le pire score"},
                {"title": "IRON MAN", "icon": "🤖", "color": "#4F46E5", "p": get_hof('MaxNoCarrot'), "v": int(get_hof('MaxNoCarrot')['MaxNoCarrot']), "u": "MATCHS", "d": "Plus longue série historique sans carotte (< 20 pts)"},
                {"title": "THE ALIEN", "icon": "👽", "color": C_ALIEN, "p": get_hof('MaxAlien'), "v": int(get_hof('MaxAlien')['MaxAlien']), "u": "MATCHS", "d": "Plus longue série de matchs consécutifs à +60 pts"},
                {"title": "CRASH TEST", "icon": "💥", "color": C_CARROT, "p": get_hof('Worst_Bonus', True), "v": int(get_hof('Worst_Bonus', True)['Worst_Bonus']), "u": "MIN (X2)", "d": "Le pire score réalisé avec un bonus actif"},
                {"title": "BAD BUSINESS", "icon": "💸", "color": "#9CA3AF", "p": get_hof('Bonus_Gained', True), "v": int(get_hof('Bonus_Gained', True)['Bonus_Gained']), "u": "GAINS", "d": "Le moins de points gagnés grâce aux bonus"},
                {"title": "THE BRICK", "icon": "🏗️", "color": "#6B7280", "p": get_hof('Worst_Raw', True), "v": int(get_hof('Worst_Raw', True)['Worst_Raw']), "u": "MIN BRUT", "d": "Le pire score brut enregistré"},
                {"title": "THE FARMER", "icon": "🥕", "color": "#F97316", "p": get_hof('Carottes'), "v": int(get_hof('Carottes')['Carottes']), "u": "CAROTTES", "d": "Le plus grand nombre de carottes (< 20 pts)"}
            ]

            rows = [hof_list[i:i+2] for i in range(0, len(hof_list), 2)]
            for row_cards in rows:
                cols = st.columns(2)
                for i, c in enumerate(row_cards):
                    with cols[i]:
                        st.markdown(f"""<div class="glass-card" style="position:relative; overflow:hidden; margin-bottom:10px"><div style="position:absolute; right:-10px; top:-10px; font-size:5rem; opacity:0.05; pointer-events:none">{c['icon']}</div><div class="hof-badge" style="color:{c['color']}; border:1px solid {c['color']}">{c['icon']} {c['title']}</div><div style="display:flex; justify-content:space-between; align-items:flex-end;"><div><div class="hof-player">{c['p']['Player']}</div><div style="font-size:0.8rem; color:#888; margin-top:4px">{c['d']}</div></div><div><div class="hof-stat" style="color:{c['color']}">{c['v']}</div><div class="hof-unit">{c['u']}</div></div></div></div>""", unsafe_allow_html=True)

        elif menu == "Admin":
            section_title("ADMIN", "Zone Sécurisée")
            if "admin_access" not in st.session_state: st.session_state["admin_access"] = False
            if st.session_state["admin_access"]:
                c1, c2 = st.columns(2)
                with c1: 
                    if st.button("🔄 REFRESH DATA"): st.cache_data.clear(); st.rerun()
                with c2: 
                    if st.button("📡 PUSH DISCORD"): send_discord_webhook(day_df, latest_pick, "https://raptorsttfl-dashboard.streamlit.app/")
            else:
                pwd = st.text_input("Password", type="password")
                if st.button("Unlock") and "ADMIN_PASSWORD" in st.secrets and pwd == st.secrets["ADMIN_PASSWORD"]: st.session_state["admin_access"] = True; st.rerun()

    else: st.warning("⚠️ Data unavailable.")
except Exception as e: st.error(f"🔥 System Error: {e}")
