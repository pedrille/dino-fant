import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import numpy as np
import requests
import streamlit.components.v1 as components

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(
    page_title="Raptors War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# ✅ LIEN DE L'IMAGE DISCORD (RAW)
DISCORD_AVATAR_URL = "https://raw.githubusercontent.com/pedrille/dino-fant/main/basketball_discord.png"

# Palette de couleurs
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

# --- 2. CSS PREMIUM ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    /* LOGO NON CLIQUABLE */
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
    .rank-row {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 15px; border-radius: 8px; margin-bottom: 4px; transition: background 0.2s; }}
    .rank-row:hover {{ background: rgba(255,255,255,0.03); }}
    .rank-pos {{ font-family: 'Rajdhani'; font-weight: 700; width: 30px; font-size: 1.1rem; }}
    .rank-name {{ flex-grow: 1; font-weight: 500; font-size: 1rem; padding-left: 10px; }}
    .rank-score {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.3rem; color: #FFF; }}
    .kpi-label {{ color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
    .kpi-num {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 2.8rem; line-height: 1; color: #FFF; }}
    .stat-box-mini {{ background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:10px; text-align:center; height:100%; display:flex; flex-direction:column; justify-content:center; }}
    .stat-mini-val {{ font-family:'Rajdhani'; font-weight:700; font-size:1.6rem; color:#FFF; line-height:1; }}
    .stat-mini-lbl {{ font-size:0.7rem; color:#888; text-transform:uppercase; margin-top:5px; letter-spacing:0.5px; }}
    .stat-mini-sub {{ font-size:0.7rem; font-weight:600; margin-top:2px; }}
    .stPlotlyChart {{ width: 100% !important; }}
    div[data-testid="stDataFrame"] {{ border: none !important; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 2rem; }}
    /* SPECIAL HQ CARDS */
    .hq-card-row {{ display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.1); }}
    .hq-card-row:last-child {{ border-bottom:none; }}
    .hq-val {{ font-family:'Rajdhani'; font-weight:800; font-size:1.8rem; color:#FFF; }}
    .hq-lbl {{ font-size:0.8rem; color:#AAA; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
    /* CHART DESC */
    .chart-desc {{ font-size:0.8rem; color:#888; margin-bottom:10px; font-style:italic; }}
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return None, None, None, None, []

        # A. VALEURS
        df_valeurs = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", header=None, ttl=0).astype(str)
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_valeurs.iloc[pick_row_idx, 1:], errors='coerce')
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
        # LOGIQUE BONUS
        df_long['IsBonus'] = df_long['ScoreRaw'].str.contains(r'\*', na=False)
        df_long['ScoreClean'] = df_long['ScoreRaw'].str.replace(r'\*', '', regex=True)
        df_long['ScoreVal'] = pd.to_numeric(df_long['ScoreClean'], errors='coerce')
        # IMPORTANT : Score = Valeur lue * 2 si bonus
        df_long['Score'] = np.where(df_long['IsBonus'], df_long['ScoreVal'] * 2, df_long['ScoreVal'])
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        final_df = df_long.dropna(subset=['Score', 'Pick'])
        final_df['Player'] = final_df['Player'].str.strip()
        bp_map = {int(picks_series[idx]): val for idx, val in bp_series.items() if idx in valid_map}
        daily_max_map = final_df.groupby('Pick')['Score'].max().to_dict()

        # --- AJOUT: CALCUL Z-SCORE POUR ANALYSE CONTEXTUELLE ---
        daily_stats = final_df.groupby('Pick')['Score'].agg(['mean', 'std']).reset_index()
        daily_stats.rename(columns={'mean': 'DailyMean', 'std': 'DailyStd'}, inplace=True)
        final_df = pd.merge(final_df, daily_stats, on='Pick', how='left')
        final_df['ZScore'] = np.where(final_df['DailyStd'] > 0, 
                                      (final_df['Score'] - final_df['DailyMean']) / final_df['DailyStd'], 0)

        # B. STATS
        df_stats = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Stats_Raptors_FR", header=None, ttl=0)
        team_rank_history = []
        team_current_rank = 0
        start_row_rank = -1
        col_start_rank = -1
        for r_idx, row in df_stats.iterrows():
            for c_idx, val in enumerate(row):
                if str(val).strip() == "Classement":
                    start_row_rank = r_idx
                    col_start_rank = c_idx
                    break
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
        return final_df, team_current_rank, bp_map, team_rank_history, daily_max_map

    except: return pd.DataFrame(), 0, {}, [], {}

def compute_stats(df, bp_map, daily_max_map):
    stats = []
    latest_pick = df['Pick'].max()
    season_avgs = df.groupby('Player')['Score'].mean()
    season_avgs_raw = df.groupby('Player')['ScoreVal'].mean()
    df_15 = df[df['Pick'] > (latest_pick - 15)]
    avg_15 = df_15.groupby('Player')['Score'].mean()
    df_10 = df[df['Pick'] > (latest_pick - 10)]
    avg_10 = df_10.groupby('Player')['Score'].mean()

    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        scores = d['Score'].values
        scores_raw = d['ScoreVal'].values
        picks = d['Pick'].values
        bonuses = d['IsBonus'].values
        z_scores = d['ZScore'].values
        
        # --- AJOUT: DONNÉES POUR SPARKLINES ---
        trend_data = scores[-20:].tolist() # 20 derniers matchs pour la courbe

        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        bp_count = 0
        alpha_count = 0
        bonus_points_gained = 0
        bonus_scores_list = []
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
        if s_avg > 0: progression_pct = ((l15_avg - s_avg) / s_avg) * 100
        else: progression_pct = 0
        reliability_pct = ((len(scores) - len(scores[scores < 20])) / len(scores)) * 100
        
        # Moyenne Z-Score
        avg_z = np.mean(z_scores) if len(z_scores) > 0 else 0

        stats.append({
            'Player': p,
            'Total': scores.sum(),
            'Moyenne': scores.mean(),
            'Moyenne_Raw': s_avg_raw,
            'StdDev': scores.std(),
            'Best': scores.max(),
            'Best_Raw': scores_raw.max(),
            'Worst': scores.min(),
            'Worst_Raw': scores_raw.min(),
            'Last': scores[-1],
            'LastIsBonus': bonuses[-1] if len(bonuses) > 0 else False,
            'Last5': last5_avg,
            'Last10': l10_avg,
            'Last15': l15_avg,
            'Streak30': streak_30,
            'Count30': len(scores[scores >= 30]),
            'Count40': len(scores[scores >= 40]),
            'Carottes': len(scores[scores < 20]),
            'Nukes': len(scores[scores >= 50]),
            'BP_Count': bp_count,
            'Alpha_Count': alpha_count,
            'Bonus_Gained': bonus_points_gained,
            'Best_Bonus': best_bonus,
            'Worst_Bonus': worst_bonus,
            'Avg_Bonus': avg_bonus_score,
            'Momentum': momentum,
            'Games': len(scores),
            'ProgressionPct': progression_pct,
            'ReliabilityPct': reliability_pct,
            'AvgZ': avg_z,        # AJOUT
            'Trend': trend_data   # AJOUT
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

# --- 4. DISCORD ---
def send_discord_webhook(day_df, pick_num, url_app):
    if "DISCORD_WEBHOOK" not in st.secrets: return "missing_secret"
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    top_3 = day_df.head(3).reset_index(drop=True)
    podium_text = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, row in top_3.iterrows():
        bonus_mark = " 🔥(x2)" if row['IsBonus'] else ""
        podium_text += f"{medals[i]} **{row['Player']}** • {int(row['Score'])} pts{bonus_mark}\n"
    avg_score = int(day_df['Score'].mean())
    data = {
        "username": "RaptorsTTFL Dashboard",
        "avatar_url": DISCORD_AVATAR_URL,
        "embeds": [{
            "title": f"🏀 RECAP DU PICK #{int(pick_num)}",
            "description": f"Les matchs sont terminés, voici les scores de l'équipe !\n\n📊 **MOYENNE TEAM :** {avg_score} pts",
            "color": 13504833,
            "fields": [{"name": "🏆 LE PODIUM", "value": podium_text, "inline": False}, {"name": "", "value": f"👉 [Voir tous les détails sur le Dashboard]({url_app})", "inline": False}],
            "footer": {"text": "Raptors TTFL • We The North"}
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
    df, team_rank, bp_map, team_history, daily_max_map = load_data()
    if df is not None and not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        full_stats = compute_stats(df, bp_map, daily_max_map)
        leader = full_stats.sort_values('Total', ascending=False).iloc[0]
        with st.sidebar:
            st.markdown("<div style='text-align:center; margin-bottom: 30px;'>", unsafe_allow_html=True)
            st.image("raptors-ttfl-min.png", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            menu = option_menu(menu_title=None, options=["Dashboard", "Team HQ", "Player Lab", "Bonus x2", "Trends", "Hall of Fame", "Admin"], icons=["grid-fill", "people-fill", "person-bounding-box", "lightning-charge-fill", "fire", "trophy-fill", "shield-lock"], default_index=0, styles={"container": {"padding": "0!important", "background-color": "#000000"}, "icon": {"color": "#666", "font-size": "1.1rem"}, "nav-link": {"font-family": "Rajdhani, sans-serif", "font-weight": "700", "font-size": "15px", "text-transform": "uppercase", "color": "#AAA", "text-align": "left", "margin": "5px 0px", "--hover-color": "#111"}, "nav-link-selected": {"background-color": C_ACCENT, "color": "#FFF", "icon-color": "#FFF", "box-shadow": "0px 4px 20px rgba(206, 17, 65, 0.4)"}})
            st.markdown(f"""<div style='position: fixed; bottom: 30px; width: 100%; padding-left: 20px;'><div style='color:#444; font-size:10px; font-family:Rajdhani; letter-spacing:2px; text-transform:uppercase'>Data Pick #{int(latest_pick)}<br>War Room v12.0 (Enhanced)</div></div>""", unsafe_allow_html=True)
            # SCRIPT JS POUR FERMER SIDEBAR
            components.html("""<script>const options = window.parent.document.querySelectorAll('.nav-link'); options.forEach((option) => { option.addEventListener('click', () => { const sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]'); if (sidebar) {} }); });</script>""", height=0, width=0)

        if menu == "Dashboard":
            section_title("RAPTORS <span class='highlight'>DASHBOARD</span>", f"Daily Briefing • Pick #{int(latest_pick)}")
            top = day_df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("MVP DU JOUR", top['Player'], f"{int(top['Score'])} PTS", C_GOLD)
            total_day = day_df['Score'].sum()
            with c2: kpi_card("TOTAL TEAM JOUR", int(total_day), "POINTS")
            team_daily_avg = day_df['Score'].mean()
            team_season_avg = df['Score'].mean()
            diff_perf = ((team_daily_avg - team_season_avg) / team_season_avg) * 100
            perf_col = C_GREEN if diff_perf > 0 else "#F87171"
            with c3: kpi_card("PERF. TEAM JOUR", f"{diff_perf:+.1f}%", "VS MOY. SAISON", perf_col)
            with c4: kpi_card("LEADER SAISON", leader['Player'], f"TOTAL: {int(leader['Total'])}", C_ACCENT)
            col_chart, col_rank = st.columns([2, 1])
            with col_chart:
                st.markdown("<div class='glass-card' style='height:100%'>", unsafe_allow_html=True)
                st.markdown("<h3 style='margin-bottom:20px'>📊 PERFORMANCE LIVE</h3>", unsafe_allow_html=True)
                fig = px.bar(day_df, x='Player', y='Score', text='Score', color='Score', color_continuous_scale=[C_BG, C_ACCENT])
                fig.update_traces(textposition='outside', marker_line_width=0, textfont_size=14, textfont_family="Rajdhani", cliponaxis=False)
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA', 'family': 'Inter'}, yaxis=dict(showgrid=False, visible=False), xaxis=dict(title=None, tickfont=dict(size=14, family='Rajdhani', weight=600)), height=350, showlegend=False, coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_rank:
                st.markdown("<div class='glass-card' style='height:100%'>", unsafe_allow_html=True)
                st.markdown("<h3 style='margin-bottom:20px'>📋 CLASSEMENT</h3>", unsafe_allow_html=True)
                medals = {0: "🥇", 1: "🥈", 2: "🥉"}
                rows = ""
                for i, r in day_df.reset_index().iterrows():
                    pos = medals.get(i, f"<span style='color:#666; font-size:0.9rem'>{i+1}</span>")
                    style = f"border-left: 3px solid {C_ACCENT}; background: rgba(255,255,255,0.03);" if i == 0 else "border-left: 3px solid transparent;"
                    col = C_ACCENT if i == 0 else "#FFF"
                    bonus_icon = " 🔥" if r['IsBonus'] else ""
                    rows += f"""<div class='rank-row' style='{style}'><div class='rank-pos'>{pos}</div><div class='rank-name' style='color:{'#FFF' if i < 3 else '#AAA'}'>{r['Player']}{bonus_icon}</div><div class='rank-score' style='color:{col}'>{int(r['Score'])}</div></div>"""
                st.markdown(f"<div style='display:flex; flex-direction:column; gap:5px'>{rows}</div></div>", unsafe_allow_html=True)

            # --- DASHBOARD FOOTER ---
            st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)
            st.markdown("### 🏆 LEADERS & FORME DU MOMENT")
            c_podium, c_forme = st.columns(2)
            with c_podium:
                st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_ACCENT}; font-family:Rajdhani; font-weight:700; margin-bottom:15px'>🏆 LEADERS SAISON (TOTAL PTS)</div>", unsafe_allow_html=True)
                top_3_season = full_stats.sort_values('Total', ascending=False).head(3).reset_index()
                for i, r in top_3_season.iterrows():
                    medal = medals.get(i, f"{i+1}")
                    st.markdown(f"""
                    <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:8px'>
                    <div style='display:flex; align-items:center; gap:15px'>
                    <div style='font-size:1.5rem'>{medal}</div>
                    <div style='font-family:Rajdhani; font-weight:700; font-size:1.2rem; color:#FFF'>{r['Player']}</div>
                    </div>
                    <div style='font-family:Rajdhani; font-weight:700; font-size:1.5rem; color:{C_ACCENT if i==0 else "#FFF"}'>{int(r['Total'])}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c_forme:
                st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_GREEN}; font-family:Rajdhani; font-weight:700; margin-bottom:15px'>🔥 FORME DU MOMENT (MOY. 15J)</div>", unsafe_allow_html=True)
                top_3_form = full_stats.sort_values('Last15', ascending=False).head(3).reset_index()
                for i, r in top_3_form.iterrows():
                    medal = medals.get(i, f"{i+1}")
                    st.markdown(f"""
                    <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:8px'>
                    <div style='display:flex; align-items:center; gap:15px'>
                    <div style='font-size:1.5rem'>{medal}</div>
                    <div style='font-family:Rajdhani; font-weight:700; font-size:1.2rem; color:#FFF'>{r['Player']}</div>
                    </div>
                    <div style='font-family:Rajdhani; font-weight:700; font-size:1.5rem; color:{C_GREEN if i==0 else "#FFF"}'>{r['Last15']:.1f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        elif menu == "Team HQ":
            section_title("TEAM <span class='highlight'>HQ</span>", "Vue d'ensemble de l'effectif")
            total_pts_season = df['Score'].sum()
            daily_agg = df.groupby('Pick')['Score'].sum()
            best_night = daily_agg.max()
            worst_night = daily_agg.min()
            avg_night = daily_agg.mean()
            total_nukes_team = len(df[df['Score'] >= 50])
            total_carrots_team = len(df[df['Score'] < 20])
            total_bonus_played = len(df[df['IsBonus'] == True])
            total_picks_played = len(df)
            current_rank_disp = f"#{int(team_rank)}" if team_rank > 0 else "-"
            best_rank_ever = f"#{min(team_history)}" if len(team_history) > 0 else "-"
            bonus_df = df[df['IsBonus'] == True]
            avg_bonus_team = bonus_df['Score'].mean() if not bonus_df.empty else 0

            nb_matchs_joues = latest_pick
            daily_totals = df.groupby('Pick')['Score'].sum()
            if len(daily_totals) > 15:
                avg_team_15 = daily_totals[daily_totals.index > (latest_pick - 15)].mean()
            else:
                avg_team_15 = daily_totals.mean()
            avg_team_season = daily_totals.mean()
            diff_team = avg_team_15 - avg_team_season
            col_dyn = C_GREEN if diff_team > 0 else C_ORANGE
            # Calcul Moyenne Score Indiv
            team_avg_per_pick = df['Score'].mean()

            team_daily_totals = df.groupby('Pick')['Score'].sum().reset_index()
            last_15_team = team_daily_totals[team_daily_totals['Pick'] > (latest_pick - 15)]
            team_season_avg_total = team_daily_totals['Score'].mean()

            c_stats, c_info = st.columns([3, 2])

            with c_stats:
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>{int(total_pts_season)}</div><div class='stat-mini-lbl'>TOTAL SAISON</div><div class='stat-mini-sub'>Points Cumulés</div></div>", unsafe_allow_html=True)
                with r1c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BONUS}'>{total_bonus_played}</div><div class='stat-mini-lbl'>BONUS JOUÉS</div><div class='stat-mini-sub'>Total Équipe</div></div>", unsafe_allow_html=True)
                with r1c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{avg_bonus_team:.1f}</div><div class='stat-mini-lbl'>EFFICIENCE</div><div class='stat-mini-sub'>Moyenne sous Bonus</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                r2c1, r2c2, r2c3 = st.columns(3)
                with r2c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_ACCENT}'>{total_nukes_team}</div><div class='stat-mini-lbl'>TOTAL NUKES</div><div class='stat-mini-sub'>Sur {total_picks_played} picks</div></div>", unsafe_allow_html=True)
                with r2c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_ORANGE}'>{total_carrots_team}</div><div class='stat-mini-lbl'>TOTAL CAROTTES</div><div class='stat-mini-sub'>Sur {total_picks_played} picks</div></div>", unsafe_allow_html=True)
                with r2c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(nb_matchs_joues)}</div><div class='stat-mini-lbl'>MATCHS JOUÉS</div><div class='stat-mini-sub'>Jours de compétition</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                r3c1, r3c2, r3c3 = st.columns(3)
                with r3c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{best_rank_ever}</div><div class='stat-mini-lbl'>MEILLEUR RANG</div><div class='stat-mini-sub'>Historique (Maj Hebdo)</div></div>", unsafe_allow_html=True)
                # --- CHANGEMENT ICI : SCORE MOYEN INDIVIDUEL GLOBAL ---
                with r3c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{team_avg_per_pick:.1f}</div><div class='stat-mini-lbl'>MOY. / PICK</div><div class='stat-mini-sub'>Global Saison</div></div>", unsafe_allow_html=True)
                with r3c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{col_dyn}'>{int(avg_team_15)}</div><div class='stat-mini-lbl'>DYNAMIQUE (15J)</div><div class='stat-mini-sub'>vs {int(avg_team_season)} (Saison)</div></div>", unsafe_allow_html=True)

            with c_info:
                html_content = f"""
                <div class="glass-card" style="height:100%; display:flex; flex-direction:column; justify-content:space-around; padding:20px;">
                <div style="text-align:center; margin-bottom:15px; font-family:Rajdhani; font-weight:700; font-size:1.2rem; color:#AAA; letter-spacing:2px; border-bottom:1px solid #333; padding-bottom:10px;">PERFORMANCES COLLECTIVES</div>
                <div class="hq-card-row">
                <div class="hq-lbl">🚀 PLAFOND <span style="font-size:0.6rem; color:#666">(RECORD)</span></div>
                <div class="hq-val" style="color:{C_GREEN}">{int(best_night)}</div>
                </div>
                <div class="hq-card-row">
                <div class="hq-lbl">⚖️ MOYENNE <span style="font-size:0.6rem; color:#666">(SAISON)</span></div>
                <div class="hq-val">{int(avg_night)}</div>
                </div>
                <div class="hq-card-row">
                <div class="hq-lbl">🧱 PLANCHER <span style="font-size:0.6rem; color:#666">(PIRE SOIR)</span></div>
                <div class="hq-val" style="color:{C_ACCENT}">{int(worst_night)}</div>
                </div>
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)

            if len(team_history) > 1:
                st.markdown("### 📈 ÉVOLUTION DU CLASSEMENT")
                hist_df = pd.DataFrame({'Deck': range(1, len(team_history)+1), 'Rank': team_history})
                fig_h = px.line(hist_df, x='Deck', y='Rank', markers=True)
                fig_h.update_traces(line_color=C_ACCENT, line_width=3, marker_size=8)
                fig_h.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, yaxis=dict(autorange="reversed", gridcolor='#222'), xaxis=dict(showgrid=False))
                st.plotly_chart(fig_h, use_container_width=True)
            
            st.markdown("### 📈 DYNAMIQUE TEAM (15 DERNIERS MATCHS)")
            st.markdown("<div class='chart-desc'>Cumul des points de toute l'équipe soir après soir vs la moyenne habituelle.</div>", unsafe_allow_html=True)
            fig_team_trend = px.line(last_15_team, x='Pick', y='Score', markers=True)
            fig_team_trend.update_traces(line_color=C_ACCENT, line_width=3, marker_size=8)
            fig_team_trend.add_hline(y=team_season_avg_total, line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Totaux Saison", annotation_position="bottom right")
            fig_team_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, yaxis=dict(gridcolor='#222'), xaxis=dict(showgrid=False))
            st.plotly_chart(fig_team_trend, use_container_width=True)

            # --- AJOUT: HEATMAP ---
            st.markdown("### 🔥 HEATMAP DE LA SAISON (Ajout v12.0)")
            st.markdown("<div class='chart-desc'>Vue thermique pour repérer les séries (rouge = bas, vert = haut).</div>", unsafe_allow_html=True)
            heatmap_data = df.pivot_table(index='Player', columns='Pick', values='Score', aggfunc='sum')
            fig_heat = px.imshow(heatmap_data, labels=dict(x="Pick", y="Player", color="Score"), x=heatmap_data.columns, y=heatmap_data.index, color_continuous_scale=[[0.0, '#EF4444'], [0.3, '#1F2937'], [0.5, '#374151'], [0.7, '#10B981'], [1.0, '#CE1141']], aspect="auto")
            fig_heat.update_traces(xgap=1, ygap=1)
            fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=500, xaxis={'showgrid': False}, yaxis={'showgrid': False})
            st.plotly_chart(fig_heat, use_container_width=True)
            
            # --- AJOUT: CONTRIBUTION ---
            st.markdown("### 🍰 CONTRIBUTION COLLECTIVE (Ajout v12.0)")
            st.markdown("<div class='chart-desc'>Part de chaque joueur dans le score total de l'équipe (15 derniers jours).</div>", unsafe_allow_html=True)
            contrib_df = df[df['Pick'] > (latest_pick - 15)]
            fig_area = px.area(contrib_df, x='Pick', y='Score', color='Player', groupnorm='percent', line_shape='spline')
            fig_area.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=400, yaxis=dict(showgrid=False), xaxis=dict(showgrid=False))
            st.plotly_chart(fig_area, use_container_width=True)

            st.markdown("### 🎯 RÉPARTITION DES SCORES")
            st.markdown("<div class='chart-desc'>Dispersion des performances individuelles : permet de voir qui est régulier (boîte étroite) et qui est instable (boîte large).</div>", unsafe_allow_html=True)
            fig_dist = px.violin(df, x='Player', y='Score', box=True, points="all", color='Player', color_discrete_sequence=px.colors.qualitative.Prism)
            fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, showlegend=False, height=400, yaxis=dict(gridcolor='#222'))
            st.plotly_chart(fig_dist, use_container_width=True)
            
            st.markdown("### 📊 DATA ROOM")
            st.markdown("<div class='chart-desc'>Tableau de bord détaillé de tous les joueurs.</div>", unsafe_allow_html=True)
            
            # --- MODIFICATION: AJOUT SPARKLINES SANS SUPPRIMER LES AUTRES COLONNES ---
            st.dataframe(full_stats[['Player', 'Trend', 'Total', 'Moyenne', 'BP_Count', 'Nukes', 'Carottes', 'Bonus_Gained']].sort_values('Total', ascending=False), hide_index=True, use_container_width=True, column_config={
                "Player": st.column_config.TextColumn("Joueur"),
                "Trend": st.column_config.LineChartColumn("Forme (20j)", width="medium", y_min=0, y_max=80), # AJOUTÉ
                "Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()),
                "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f"),
                "Carottes": st.column_config.NumberColumn("🥕", help="Scores < 20"),
                "Nukes": st.column_config.NumberColumn("☢️", help="Scores > 50"),
                "BP_Count": st.column_config.NumberColumn("🎯", help="Best Picks"),
                "Bonus_Gained": st.column_config.NumberColumn("⚗️", help="Pts Bonus Gagnés")
            })

        elif menu == "Player Lab":
            section_title("PLAYER <span class='highlight'>LAB</span>", "Deep Dive Analytics")
            sel_player = st.selectbox("Sélectionner un joueur", sorted(df['Player'].unique()))
            col_radar, col_stats = st.columns([1, 1])
            p_data = full_stats[full_stats['Player'] == sel_player].iloc[0]
            sorted_team = full_stats.sort_values('Total', ascending=False).reset_index(drop=True)
            internal_rank = sorted_team[sorted_team['Player'] == sel_player].index[0] + 1
            nb_players = len(sorted_team)
            sniper_pct = (p_data['BP_Count'] / p_data['Games']) * 100
            form_10 = p_data['Last10']
            diff_form = form_10 - p_data['Moyenne']
            sign = "+" if diff_form > 0 else ""
            color_diff = C_GREEN if diff_form > 0 else "#F87171"
            
            # --- MODIFICATION: 5 COLONNES POUR INCLURE LE Z-SCORE ---
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: kpi_card("TOTAL POINTS", int(p_data['Total']), "SAISON")
            with c2: kpi_card("MOYENNE", f"{p_data['Moyenne']:.1f}", "PTS / PICK")
            
            z_val = p_data['AvgZ']
            z_col = C_GREEN if z_val > 0.5 else (C_RED if z_val < -0.5 else "#DDD")
            with c3: kpi_card("IMPACT (Z)", f"{z_val:+.2f}", "VS TEAM", z_col) # AJOUT
            
            rank_col = C_GOLD if internal_rank == 1 else (C_SILVER if internal_rank == 2 else (C_BRONZE if internal_rank == 3 else "#FFF"))
            with c4: kpi_card("CLASSEMENT", f"#{internal_rank}", f"SUR {nb_players}", rank_col)
            with c5: kpi_card("BEST SCORE", int(p_data['Best']), "RECORD", C_GOLD)

            # --- LAST 10 PICKS ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🔥 10 DERNIERS MATCHS")
            p_hist_all = df[df['Player'] == sel_player]
            p_hist = p_hist_all.sort_values('Pick').tail(10)
            cols = st.columns(10)
            for i, (idx, r) in enumerate(p_hist.iterrows()):
                s = r['Score']; is_b = r['IsBonus']; c = "#4ADE80" if s >= 40 else ("#F87171" if s < 20 else "#FFF")
                border = f"2px solid {C_BONUS}" if is_b else "1px solid rgba(255,255,255,0.1)"
                cols[i].markdown(f"<div style='text-align:center; font-family:Rajdhani; font-size:0.9rem; font-weight:800; color:{c}; background:rgba(255,255,255,0.05); border:{border}; border-radius:6px; padding:6px 2px'>{int(s)}</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # --- MAIN GRID ---
            col_radar, col_stats = st.columns([1, 2])
            with col_radar:
                st.markdown("<div class='glass-card' style='height:100%; display:flex; flex-direction:column; justify-content:center;'>", unsafe_allow_html=True)
                max_avg = full_stats['Moyenne'].max(); max_best = full_stats['Best'].max(); max_last5 = full_stats['Last5'].max(); max_nukes = full_stats['Nukes'].max()
                reg_score = 100 - ((p_data['StdDev'] / full_stats['StdDev'].max()) * 100)
                r_vals = [(p_data['Moyenne'] / max_avg) * 100, (p_data['Best'] / max_best) * 100, (p_data['Last5'] / max_last5) * 100, reg_score, (p_data['Nukes'] / (max_nukes if max_nukes > 0 else 1)) * 100]
                r_cats = ['SCORING', 'EXPLOSIVITÉ', 'FORME', 'RÉGULARITÉ', 'CLUTCH']
                fig_radar = go.Figure(data=go.Scatterpolar(r=r_vals + [r_vals[0]], theta=r_cats + [r_cats[0]], fill='toself', line_color=C_ACCENT, fillcolor="rgba(206, 17, 65, 0.3)"))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=12, family="Rajdhani"), margin=dict(t=20, b=20, l=20, r=20), height=280)
                st.plotly_chart(fig_radar, use_container_width=True)
                st.markdown("""<div style='font-size:0.7rem; color:#888; text-align:center; margin-top:5px; line-height:1.4;'><span style='color:#FFF'>SCORING</span>: Moyenne Saison<br><span style='color:#FFF'>EXPLOSIVITÉ</span>: Record de points<br><span style='color:#FFF'>FORME</span>: 5 derniers matchs<br><span style='color:#FFF'>RÉGULARITÉ</span>: Stabilité (Ecart-type)<br><span style='color:#FFF'>CLUTCH</span>: Scores > 50pts</div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_stats:
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['ReliabilityPct'])}%</div><div class='stat-mini-lbl'>FIABILITÉ</div><div class='stat-mini-sub'>% Picks > 20pts</div></div>", unsafe_allow_html=True)
                with r1c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Nukes'])}</div><div class='stat-mini-lbl'>NUKES</div><div class='stat-mini-sub'>Scores > 50pts</div></div>", unsafe_allow_html=True)
                with r1c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_RED}'>{int(p_data['Carottes'])}</div><div class='stat-mini-lbl'>CAROTTES</div><div class='stat-mini-sub'>Scores < 20pts</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                r2c1, r2c2, r2c3 = st.columns(3)
                with r2c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(sniper_pct)}%</div><div class='stat-mini-lbl'>SNIPER RATE</div><div class='stat-mini-sub'>% Best Pick</div></div>", unsafe_allow_html=True)
                with r2c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Avg_Bonus']:.1f}</div><div class='stat-mini-lbl'>BONUS EFF.</div><div class='stat-mini-sub'>Moyenne sous x2</div></div>", unsafe_allow_html=True)
                with r2c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Count40'])}</div><div class='stat-mini-lbl'>HEAVY HITS</div><div class='stat-mini-sub'>Scores > 40pts</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                r3c1, r3c2, r3c3 = st.columns(3)
                with r3c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Last10']:.1f}</div><div class='stat-mini-lbl'>FORME (10j)</div><div class='stat-mini-sub'>Moyenne récente</div></div>", unsafe_allow_html=True)
                with r3c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{color_diff}'>{sign}{diff_form:.1f}</div><div class='stat-mini-lbl'>DYNAMIQUE</div><div class='stat-mini-sub'>vs Moy. Saison</div></div>", unsafe_allow_html=True)
                with r3c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Worst'])}</div><div class='stat-mini-lbl'>FLOOR</div><div class='stat-mini-sub'>Pire Score</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

                # NEW: 4TH ROW
                r4c1, r4c2, r4c3 = st.columns(3)
                alpha_rate = (p_data['Alpha_Count'] / p_data['Games']) * 100 if p_data['Games'] > 0 else 0
                with r4c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>{int(alpha_rate)}%</div><div class='stat-mini-lbl'>ALPHA %</div><div class='stat-mini-sub'>Leader Team</div></div>", unsafe_allow_html=True)
                with r4c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Moyenne_Raw']:.1f}</div><div class='stat-mini-lbl'>MOY. PURE</div><div class='stat-mini-sub'>Sans Bonus</div></div>", unsafe_allow_html=True)
                with r4c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Count30'])}</div><div class='stat-mini-lbl'>SAFE ZONE</div><div class='stat-mini-sub'>Scores > 30pts</div></div>", unsafe_allow_html=True)

            # --- CHARTS ---
            c_dist, c_trend = st.columns(2)
            with c_dist:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("#### 📊 DISTRIBUTION DES SCORES", unsafe_allow_html=True)
                st.markdown("<div class='chart-desc'>Fréquence des scores par tranches de points.</div>", unsafe_allow_html=True)
                fig_hist = px.histogram(p_hist_all, x="Score", nbins=15, color_discrete_sequence=[C_ACCENT])
                fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=30, b=0), height=200, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_hist, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c_trend:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("#### 📈 TENDANCE (15 DERNIERS MATCHS)", unsafe_allow_html=True)
                st.markdown("<div class='chart-desc'>Dynamique récente (Points) comparée à la moyenne saison (Ligne).</div>", unsafe_allow_html=True)
                last_15_data = p_hist_all.sort_values('Pick').tail(15)
                if not last_15_data.empty:
                    fig_trend = px.line(last_15_data, x="Pick", y="Score", markers=True)
                    fig_trend.update_traces(line_color=C_GOLD, marker_color=C_ACCENT, marker_size=8)
                    # ADD PLAYER AVERAGE LINE
                    fig_trend.add_hline(y=p_data['Moyenne'], line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Saison", annotation_position="bottom right")
                    fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=30, b=0), height=200, xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig_trend, use_container_width=True)
                else: st.info("Pas assez de données")
                st.markdown("</div>", unsafe_allow_html=True)

            # --- NEW: FULL SEASON EVOLUTION ---
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("#### 🏔️ PARCOURS SAISON COMPLÈTE", unsafe_allow_html=True)
            st.markdown("<div class='chart-desc'>Vue d'ensemble de tous les picks de la saison.</div>", unsafe_allow_html=True)
            # PREPARE DATA FOR TEAM AVG LINE
            team_season_avg = df['Score'].mean()

            fig_evol = px.line(p_hist_all, x="Pick", y="Score", markers=True)
            fig_evol.update_traces(line_color=C_BLUE, line_width=2, marker_size=4)
            # PLAYER AVG LINE (Left)
            fig_evol.add_hline(y=p_data['Moyenne'], line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Joueur", annotation_position="top left")
            # TEAM AVG LINE (Right, Orange)
            fig_evol.add_hline(y=team_season_avg, line_dash="dash", line_color=C_ORANGE, annotation_text="Moy. Team", annotation_position="bottom right", annotation_font_color=C_ORANGE)

            fig_evol.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=30, b=0), height=300, xaxis_title="Pick #", yaxis_title="Points TTFL")
            st.plotly_chart(fig_evol, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        elif menu == "Bonus x2":
            section_title("BONUS <span class='highlight'>ZONE</span>", "Analyse des Jokers x2")
            df_bonus = df[df['IsBonus'] == True].copy()
            if df_bonus.empty: st.info("Aucun bonus utilisé pour le moment.")
            else:
                nb_bonus = len(df_bonus); avg_bonus = df_bonus['Score'].mean(); best_bonus = df_bonus['Score'].max()
                k1, k2, k3 = st.columns(3)
                with k1: kpi_card("BONUS JOUÉS", nb_bonus, "TOTAL SAISON", C_BONUS)
                with k2: kpi_card("MOYENNE BONUS", f"{avg_bonus:.1f}", "POINTS DOUBLÉS", "#FFF")
                with k3: kpi_card("MEILLEUR BONUS", int(best_bonus), "RECORD", C_GOLD)
                st.markdown("### 💰 RENTABILITÉ DES BONUS (Points Gagnés)")
                df_bonus['Gain'] = df_bonus['Score'] / 2
                profit_df = df_bonus.groupby('Player')['Gain'].sum().sort_values(ascending=False).reset_index()
                fig = px.bar(profit_df, x='Gain', y='Player', orientation='h', text='Gain', color='Gain', color_continuous_scale='Teal')
                fig.update_traces(texttemplate='%{text:.0f} pts', textposition='outside')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, xaxis=dict(showgrid=False, visible=False))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("### 📜 HISTORIQUE DÉTAILLÉ")
                st.dataframe(df_bonus[['Player', 'Pick', 'Score', 'Gain']].sort_values('Pick', ascending=False), hide_index=True, use_container_width=True, column_config={"Score": st.column_config.NumberColumn("Score Final (x2)", format="%d pts"), "Gain": st.column_config.NumberColumn("Gain Réel", format="+%d pts")})

        elif menu == "Trends":
            section_title("MARKET <span class='highlight'>WATCH</span>", "Analyse des tendances sur 15 jours")
            df_15 = df[df['Pick'] > (latest_pick - 15)]; df_7 = df[df['Pick'] > (latest_pick - 7)]
            avg_15 = df_15.groupby('Player')['Score'].mean().sort_values(ascending=False)
            season_avg = df.groupby('Player')['Score'].mean()
            avg_7 = df_7.groupby('Player')['Score'].mean()
            diff_7 = (avg_7 - season_avg).dropna().sort_values(ascending=False)
            pct_15 = ((avg_15 - season_avg) / season_avg * 100).dropna().sort_values(ascending=False)
            nukes_15 = df_15[df_15['Score'] >= 50].groupby('Player').size().sort_values(ascending=False)
            carrots_15 = df_15[df_15['Score'] < 20].groupby('Player').size().sort_values(ascending=False)
            delta_rank = get_comparative_stats(df, latest_pick, 15)['rank_diff']
            def render_row(title, sub, hot, cold, metric, unit=""):
                st.markdown(f"<div class='trend-section-title'>{title}</div><div class='trend-section-desc'>{sub}</div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    h = f"<div class='trend-box'><div class='hot-header'>🔥 TOP PERFORMERS</div>"
                    if hot.empty: h += "<div style='color:#666'>Aucune donnée</div>"
                    else:
                        for p, v in hot.head(3).items():
                            val = float(v)
                            if metric in ["diff", "pct"]:
                                if val > 0: vf = f"+{val:.1f}"
                                else: vf = f"{val:.1f}"
                            else:
                                vf = f"{val:.1f}" if metric == "raw" else str(int(val))
                            if metric == "pct": vf += "%"
                            h += f"<div class='t-row'><span class='t-name'>{p}</span><span class='t-val' style='color:{C_GREEN}'>{vf} <span style='font-size:0.8rem; color:#888'>{unit}</span></span></div>"
                    st.markdown(h+"</div>", unsafe_allow_html=True)
                with c2:
                    h = f"<div class='trend-box'><div class='cold-header'>❄️ COLD STREAK</div>"
                    if cold.empty: h += "<div style='color:#666'>Aucune donnée</div>"
                    else:
                        for p, v in cold.head(3).items():
                            val = float(v)
                            if metric in ["diff", "pct"]:
                                vf = f"{val:.1f}"
                            else:
                                vf = f"{val:.1f}" if metric == "raw" else str(int(val))

                            if metric == "pct": vf += "%"
                            h += f"<div class='t-row'><span class='t-name'>{p}</span><span class='t-val' style='color:#F87171'>{vf} <span style='font-size:0.8rem; color:#888'>{unit}</span></span></div>"
                    st.markdown(h+"</div>", unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)
            render_row("MOYENNE GÉNÉRALE (15 JOURS)", "Les joueurs les plus réguliers vs ceux en difficulté sur la quinzaine.", avg_15, avg_15.sort_values(), "raw", "pts")
            render_row("EXPLOSIVITÉ (7 JOURS VS SAISON)", "Écart de points entre la semaine passée et la moyenne habituelle.", diff_7, diff_7.sort_values(), "diff", "pts diff")
            render_row("DYNAMIQUE DE FORME (15J VS SAISON)", "Pourcentage de progression ou régression sur la quinzaine.", pct_15, pct_15.sort_values(), "pct", "")
            render_row("PICKS MARQUANTS (15 JOURS)", "Accumulation de scores > 50pts (Nukes) vs scores < 20pts (Carottes).", nukes_15, carrots_15, "int", "picks")
            render_row("MOUVEMENTS AU CLASSEMENT", "Gains et pertes de places au général sur 15 jours.", delta_rank.sort_values(ascending=False), delta_rank.sort_values(), "diff", "places")

        elif menu == "Hall of Fame":
            section_title("HALL OF <span class='highlight'>FAME</span>", "Records & Trophées de la saison")
            sniper = full_stats.sort_values('Moyenne', ascending=False).iloc[0]
            torche = full_stats.sort_values('Last15', ascending=False).iloc[0]
            progression = full_stats.sort_values('ProgressionPct', ascending=False).iloc[0]
            heavy = full_stats.sort_values('Count40', ascending=False).iloc[0]
            peak = full_stats.sort_values('Best', ascending=False).iloc[0]
            intouch = full_stats.sort_values('Streak30', ascending=False).iloc[0]
            rock = full_stats.sort_values('Count30', ascending=False).iloc[0]
            nuke = full_stats.sort_values('Nukes', ascending=False).iloc[0]
            floor = full_stats.sort_values('Worst', ascending=True).iloc[0]
            lapin = full_stats.sort_values('Carottes', ascending=False).iloc[0]
            sniper_bp = full_stats.sort_values('BP_Count', ascending=False).iloc[0]
            alpha_dog = full_stats.sort_values('Alpha_Count', ascending=False).iloc[0]
            alchemist = full_stats.sort_values('Bonus_Gained', ascending=False).iloc[0]
            bad_business = full_stats.sort_values('Bonus_Gained', ascending=True).iloc[0]
            has_bonus = full_stats[full_stats['Worst_Bonus'] > 0]
            crash_test = has_bonus.sort_values('Worst_Bonus', ascending=True).iloc[0] if not has_bonus.empty else full_stats.iloc[0]
            pure_peak = full_stats.sort_values('Best_Raw', ascending=False).iloc[0]
            pure_avg = full_stats.sort_values('Moyenne_Raw', ascending=False).iloc[0]
            zen_master = full_stats.sort_values('ReliabilityPct', ascending=False).iloc[0]
            brick_layer = full_stats.sort_values('Worst_Raw', ascending=True).iloc[0]

            def hof_card(title, icon, color, p_name, val, unit, desc):
                return f"""<div class="glass-card" style="position:relative; overflow:hidden"><div style="position:absolute; right:-10px; top:-10px; font-size:5rem; opacity:0.05; pointer-events:none">{icon}</div><div class="hof-badge" style="color:{color}; border:1px solid {color}">{icon} {title}</div><div style="display:flex; justify-content:space-between; align-items:flex-end;"><div><div class="hof-player">{p_name}</div><div style="font-size:0.8rem; color:#888; margin-top:4px">{desc}</div></div><div><div class="hof-stat" style="color:{color}">{val}</div><div class="hof-unit">{unit}</div></div></div></div>"""

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(hof_card("THE GOAT", "🏆", C_GOLD, sniper['Player'], f"{sniper['Moyenne']:.1f}", "PTS MOY", "Meilleure moyenne générale de la saison"), unsafe_allow_html=True)
                st.markdown(hof_card("REAL MVP", "💎", C_PURE, pure_avg['Player'], f"{pure_avg['Moyenne_Raw']:.1f}", "PTS MOY (BRUT)", "Meilleure moyenne sans compter les bonus"), unsafe_allow_html=True)
                st.markdown(hof_card("THE SNIPER", "🎯", C_PURPLE, sniper_bp['Player'], int(sniper_bp['BP_Count']), "BEST PICKS", "Plus grand nombre de 'Best Pick' TTFL trouvés"), unsafe_allow_html=True)
                st.markdown(hof_card("ALPHA DOG", "🐺", C_ALPHA, alpha_dog['Player'], int(alpha_dog['Alpha_Count']), "TOPS TEAM", "Plus grand nombre de fois meilleur scoreur de l'équipe"), unsafe_allow_html=True)
                st.markdown(hof_card("HUMAN TORCH", "🔥", "#FF5252", torche['Player'], f"{torche['Last15']:.1f}", "PTS / 15J", "Meilleure moyenne sur les 15 derniers jours"), unsafe_allow_html=True)
                st.markdown(hof_card("RISING STAR", "🚀", C_GREEN, progression['Player'], f"+{progression['ProgressionPct']:.1f}%", "PROGRESSION", "Plus forte hausse (Moy. 15j vs Saison)"), unsafe_allow_html=True)
                st.markdown(hof_card("THE CEILING", "🏔️", "#A78BFA", peak['Player'], int(peak['Best']), "PTS MAX", "Record de points sur un seul match (Bonus inclus)"), unsafe_allow_html=True)
                st.markdown(hof_card("PURE SCORER", "🏀", "#F472B6", pure_peak['Player'], int(pure_peak['Best_Raw']), "PTS MAX (BRUT)", "Plus gros score réalisé sans bonus"), unsafe_allow_html=True)
                st.markdown(hof_card("THE ALCHEMIST", "⚗️", C_BONUS, alchemist['Player'], int(alchemist['Bonus_Gained']), "PTS BONUS", "Plus grand nombre de points gagnés grâce aux bonus"), unsafe_allow_html=True)

            with c2:
                st.markdown(hof_card("BAD BUSINESS", "💸", "#666", bad_business['Player'], int(bad_business['Bonus_Gained']), "PTS BONUS", "Le moins de points gagnés grâce aux bonus"), unsafe_allow_html=True)
                st.markdown(hof_card("ZEN MASTER", "🧘", "#EAB308", zen_master['Player'], f"{int(zen_master['ReliabilityPct'])}%", "FIABILITÉ", "Plus haut % de matchs sans carotte"), unsafe_allow_html=True)
                st.markdown(hof_card("HEAVY HITTER", "🥊", "#64B5F6", heavy['Player'], int(heavy['Count40']), "PICKS >40", "Nombre de scores supérieurs à 40 points"), unsafe_allow_html=True)
                st.markdown(hof_card("NUCLEAR", "☢️", "#EF4444", nuke['Player'], int(nuke['Nukes']), "BOMBS", "Nombre de scores supérieurs à 50 points"), unsafe_allow_html=True)
                st.markdown(hof_card("THE ROCK", "🛡️", C_GREEN, rock['Player'], int(rock['Count30']), "MATCHS", "Nombre de scores > 30 pts (Assurance tous risques)"), unsafe_allow_html=True)
                st.markdown(hof_card("UNSTOPPABLE", "⚡", "#FBBF24", intouch['Player'], int(intouch['Streak30']), "SERIE", "Plus longue série de matchs consécutifs > 30 pts"), unsafe_allow_html=True)
                st.markdown(hof_card("THE BRICK", "🏗️", "#71717A", brick_layer['Player'], int(brick_layer['Worst_Raw']), "PTS MIN (BRUT)", "Score le plus bas enregistré sans bonus"), unsafe_allow_html=True)
                st.markdown(hof_card("CRASH TEST", "💥", C_ORANGE, crash_test['Player'], int(crash_test['Worst_Bonus']), "PTS MIN (X2)", "Le pire score réalisé avec un bonus"), unsafe_allow_html=True)
                st.markdown(hof_card("THE FARMER", "🥕", "#F97316", lapin['Player'], int(lapin['Carottes']), "CAROTTES", "Nombre de scores inférieurs à 20 points"), unsafe_allow_html=True)

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
