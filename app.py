import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import numpy as np
import requests

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(
    page_title="Raptors War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

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
C_ALPHA = "#F472B6" # Rose/Rouge pour l'Alpha Dog

# --- 2. CSS PREMIUM ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');

    /* GLOBAL */
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    div[data-testid="stSidebarNav"] {{ display: none; }} 
    
    /* MENU */
    .nav-link {{ font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }}

    /* TYPO */
    h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    h1 {{ font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #FFF, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub-header {{ font-size: 0.9rem; color: #666; letter-spacing: 1.5px; margin-bottom: 25px; font-weight: 500; }}

    /* CARDS */
    .glass-card {{
        background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%);
        backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px; padding: 24px; margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }}

    /* TRENDS */
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

    /* HOF */
    .hof-badge {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; background: rgba(255,255,255,0.05); }}
    .hof-player {{ font-family: 'Rajdhani'; font-size: 1.6rem; font-weight: 700; color: #FFF; }}
    .hof-stat {{ font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 800; text-align: right; line-height: 1; }}
    .hof-unit {{ font-size: 0.7rem; color: #666; text-align: right; font-weight: 600; text-transform: uppercase; }}

    /* RANKING */
    .rank-row {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 15px; border-radius: 8px; margin-bottom: 4px; transition: background 0.2s; }}
    .rank-row:hover {{ background: rgba(255,255,255,0.03); }}
    .rank-pos {{ font-family: 'Rajdhani'; font-weight: 700; width: 30px; font-size: 1.1rem; }}
    .rank-name {{ flex-grow: 1; font-weight: 500; font-size: 1rem; padding-left: 10px; }}
    .rank-score {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.3rem; color: #FFF; }}
    
    /* KPI */
    .kpi-label {{ color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
    .kpi-num {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 2.8rem; line-height: 1; color: #FFF; }}

    /* CLEANUP */
    .stPlotlyChart {{ width: 100% !important; }}
    div[data-testid="stDataFrame"] {{ border: none !important; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 2rem; }}
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return None, None, None, None, []

        # --- A. VALEURS ---
        df_valeurs = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", header=None, ttl=0)
        
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_valeurs.iloc[pick_row_idx, 1:], errors='coerce')
        
        bp_row = df_valeurs[df_valeurs[0].astype(str).str.contains("Score BP", na=False)]
        bp_series = pd.to_numeric(bp_row.iloc[0, 1:], errors='coerce') if not bp_row.empty else pd.Series()
        
        df_players = df_valeurs.iloc[pick_row_idx+1:pick_row_idx+50].copy().rename(columns={0: 'Player'})
        stop = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop)].dropna(subset=['Player'])
        
        valid_map = {idx: int(val) for idx, val in picks_series.items() if pd.notna(val) and val > 0}
        cols = ['Player'] + list(valid_map.keys())
        cols = [c for c in cols if c in df_players.columns]
        
        df_clean = df_players[cols].copy().rename(columns=valid_map)
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        final_df = df_long.dropna(subset=['Score', 'Pick'])
        
        bp_map = {int(picks_series[idx]): val for idx, val in bp_series.items() if idx in valid_map}
        
        # Pre-calcul du max score par pick pour le badge Alpha Dog
        daily_max_map = final_df.groupby('Pick')['Score'].max().to_dict()

        # --- B. STATS ---
        df_stats = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Stats_Raptors_FR", header=None, ttl=0)
        
        ranks_map = {}
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
            for i in range(start_row_rank+1, start_row_rank+20):
                if i >= len(df_stats): break
                p_name = str(df_stats.iloc[i, col_start_rank])
                hist_vals = df_stats.iloc[i, col_start_rank+1:].values
                nums = [x for x in hist_vals if isinstance(x, (int, float, np.number)) and not pd.isna(x) and x > 0]
                
                if nums:
                    last_rank = nums[-1]
                    if p_name == "Team Raptors":
                        team_current_rank = last_rank
                        team_rank_history = nums
                    else:
                        ranks_map[p_name] = last_rank

        return final_df, team_current_rank, bp_map, ranks_map, team_rank_history, daily_max_map

    except: return pd.DataFrame(), 0, {}, {}, [], {}

def compute_stats(df, bp_map, ranks_map, daily_max_map):
    stats = []
    latest_pick = df['Pick'].max()
    season_avgs = df.groupby('Player')['Score'].mean()
    
    df_15 = df[df['Pick'] > (latest_pick - 15)]
    avg_15 = df_15.groupby('Player')['Score'].mean()

    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        scores = d['Score'].values
        picks = d['Pick'].values
        
        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
            
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        
        bp_count = 0
        alpha_count = 0 # Leader count
        
        for pick_num, score in zip(picks, scores):
            # Best Pick Global check
            if pick_num in bp_map and score >= bp_map[pick_num] and score > 0:
                bp_count += 1
            # Team Leader check
            if pick_num in daily_max_map and score >= daily_max_map[pick_num] and score > 0:
                alpha_count += 1
        
        s_avg = season_avgs.get(p, 0)
        l15_avg = avg_15.get(p, s_avg)
        progression_15 = l15_avg - s_avg

        stats.append({
            'Player': p,
            'Total': scores.sum(),
            'Moyenne': scores.mean(),
            'StdDev': scores.std(), 
            'Best': scores.max(),
            'Worst': scores.min(),
            'Last': scores[-1], 
            'Last5': last5_avg, 
            'Last15': scores[-15:].mean() if len(scores) >= 15 else scores.mean(),
            'Streak30': streak_30,
            'Count30': len(scores[scores >= 30]), 
            'Count40': len(scores[scores >= 40]),
            'Carottes': len(scores[scores < 20]),
            'Nukes': len(scores[scores >= 50]),
            'BP_Count': bp_count,
            'Alpha_Count': alpha_count, # NEW
            'Momentum': momentum,
            'Games': len(scores),
            'Progression15': progression_15,
            'GeneralRank': ranks_map.get(p, 9999)
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
def send_discord_webhook(day_df, pick_num, url_app, team_rank):
    if "DISCORD_WEBHOOK" not in st.secrets: return "missing_secret"
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    top_3 = day_df.head(3).reset_index(drop=True)
    podium_text = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, row in top_3.iterrows():
        podium_text += f"{medals[i]} **{row['Player']}** • {int(row['Score'])} pts\n"
    avg_score = int(day_df['Score'].mean())
    rank_txt = f"#{int(team_rank)}" if team_rank > 0 else "N/A"
    data = {
        "username": "Raptors Intelligence",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2592/2592242.png", 
        "embeds": [{
            "title": f"🦖 DEBRIEF • PICK #{int(pick_num)}",
            "description": f"Rapport officiel.\n\n**MOYENNE TEAM :** `{avg_score} pts`\n**CLASSEMENT :** `{rank_txt}`",
            "color": 13504833,
            "fields": [{"name": "🏆 PODIUM", "value": podium_text, "inline": False}, {"name": "🔗 LIEN", "value": f"[Dashboard]({url_app})", "inline": False}],
            "footer": {"text": "Raptors Elite System"}
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
    df, team_rank, bp_map, ranks_map, team_history, daily_max_map = load_data()
    
    if df is not None and not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        full_stats = compute_stats(df, bp_map, ranks_map, daily_max_map)
        leader = full_stats.sort_values('Total', ascending=False).iloc[0]
        
        with st.sidebar:
            st.markdown("<div style='text-align:center; margin-bottom: 30px;'>", unsafe_allow_html=True)
            st.image("raptors-ttfl-min.png", use_container_width=True) 
            st.markdown("</div>", unsafe_allow_html=True)
            menu = option_menu(menu_title=None, options=["Dashboard", "Team HQ", "Player Lab", "Trends", "Hall of Fame", "Admin"], icons=["grid-fill", "people-fill", "person-bounding-box", "fire", "trophy-fill", "shield-lock"], default_index=0, styles={"container": {"padding": "0!important", "background-color": "#000000"}, "icon": {"color": "#666", "font-size": "1.1rem"}, "nav-link": {"font-family": "Rajdhani, sans-serif", "font-weight": "700", "font-size": "15px", "text-transform": "uppercase", "color": "#AAA", "text-align": "left", "margin": "5px 0px", "--hover-color": "#111"}, "nav-link-selected": {"background-color": C_ACCENT, "color": "#FFF", "icon-color": "#FFF", "box-shadow": "0px 4px 20px rgba(206, 17, 65, 0.4)"}})
            st.markdown(f"""<div style='position: fixed; bottom: 30px; width: 100%; padding-left: 20px;'><div style='color:#444; font-size:10px; font-family:Rajdhani; letter-spacing:2px; text-transform:uppercase'>Data Pick #{int(latest_pick)}<br>War Room v5.2</div></div>""", unsafe_allow_html=True)

        if menu == "Dashboard":
            section_title("RAPTORS <span class='highlight'>DASHBOARD</span>", f"Daily Briefing • Pick #{int(latest_pick)}")
            top = day_df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("MVP DU JOUR", top['Player'], f"{int(top['Score'])} PTS", C_GOLD)
            with c2: kpi_card("MOYENNE TEAM", int(day_df['Score'].mean()), "POINTS")
            r_disp = f"#{int(team_rank)}" if team_rank > 0 else "N/A"
            c_rank = C_GOLD if team_rank > 0 and team_rank <= 20 else (C_GREEN if team_rank <= 100 else "#FFF")
            with c3: kpi_card("CLASSEMENT TEAM", r_disp, "GENERAL", c_rank)
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
                    rows += f"""<div class='rank-row' style='{style}'><div class='rank-pos'>{pos}</div><div class='rank-name' style='color:{'#FFF' if i < 3 else '#AAA'}'>{r['Player']}</div><div class='rank-score' style='color:{col}'>{int(r['Score'])}</div></div>"""
                st.markdown(f"<div style='display:flex; flex-direction:column; gap:5px'>{rows}</div></div>", unsafe_allow_html=True)

        elif menu == "Team HQ":
            section_title("TEAM <span class='highlight'>HQ</span>", "Vue d'ensemble de l'effectif")
            if len(team_history) > 1:
                st.markdown("### 📈 ÉVOLUTION DU CLASSEMENT")
                hist_df = pd.DataFrame({'Deck': range(1, len(team_history)+1), 'Rank': team_history})
                fig_h = px.line(hist_df, x='Deck', y='Rank', markers=True)
                fig_h.update_traces(line_color=C_ACCENT, line_width=3, marker_size=8)
                fig_h.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, yaxis=dict(autorange="reversed", gridcolor='#222'), xaxis=dict(showgrid=False))
                st.plotly_chart(fig_h, use_container_width=True)

            st.markdown("### 🎯 RÉPARTITION DES SCORES")
            fig_dist = px.violin(df, x='Player', y='Score', box=True, points="all", color='Player', color_discrete_sequence=px.colors.qualitative.Prism)
            fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, showlegend=False, height=400, yaxis=dict(gridcolor='#222'))
            st.plotly_chart(fig_dist, use_container_width=True)
            
            st.markdown("### 📊 DATA ROOM")
            st.dataframe(full_stats[['Player', 'Total', 'Moyenne', 'GeneralRank', 'BP_Count', 'Alpha_Count', 'Nukes', 'Carottes']].sort_values('Total', ascending=False), hide_index=True, use_container_width=True, column_config={
                "Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()), 
                "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f"),
                "GeneralRank": st.column_config.NumberColumn("Class. Gén.", format="#%d"),
                "Carottes": st.column_config.NumberColumn("🥕", help="Scores < 20"),
                "Nukes": st.column_config.NumberColumn("☢️", help="Scores > 50"),
                "BP_Count": st.column_config.NumberColumn("🎯", help="Best Picks Global"),
                "Alpha_Count": st.column_config.NumberColumn("🐺", help="Best Team Score")
            })

        elif menu == "Player Lab":
            section_title("PLAYER <span class='highlight'>LAB</span>", "Deep Dive Analytics")
            sel_player = st.selectbox("Sélectionner un joueur", sorted(df['Player'].unique()))
            col_radar, col_stats = st.columns([1, 1])
            p_data = full_stats[full_stats['Player'] == sel_player].iloc[0]
            
            with col_radar:
                max_avg = full_stats['Moyenne'].max(); max_best = full_stats['Best'].max(); max_last5 = full_stats['Last5'].max(); max_nukes = full_stats['Nukes'].max()
                reg_score = 100 - ((p_data['StdDev'] / full_stats['StdDev'].max()) * 100)
                r_vals = [(p_data['Moyenne'] / max_avg) * 100, (p_data['Best'] / max_best) * 100, (p_data['Last5'] / max_last5) * 100, reg_score, (p_data['Nukes'] / (max_nukes if max_nukes > 0 else 1)) * 100]
                r_cats = ['SCORING', 'EXPLOSIVITÉ', 'FORME', 'RÉGULARITÉ', 'CLUTCH']
                fig_radar = go.Figure(data=go.Scatterpolar(r=r_vals + [r_vals[0]], theta=r_cats + [r_cats[0]], fill='toself', line_color=C_ACCENT, fillcolor="rgba(206, 17, 65, 0.3)"))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=12, family="Rajdhani"), margin=dict(t=20, b=20))
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True); st.plotly_chart(fig_radar, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
            
            with col_stats:
                kpi_card("MOYENNE SAISON", f"{p_data['Moyenne']:.1f}", "PTS")
                c1, c2 = st.columns(2)
                with c1: kpi_card("CLASSEMENT GÉNÉRAL", f"#{p_data['GeneralRank']}", "TTFL INDIV", C_GOLD)
                with c2: kpi_card("BEST PICK", int(p_data['Best']), "RECORD")
                st.markdown("#### 🔥 DERNIERS MATCHS")
                last_5 = df[df['Player'] == sel_player].sort_values('Pick').tail(5)['Score'].values
                cols = st.columns(5)
                for i, s in enumerate(last_5):
                    c = "#4ADE80" if s >= 40 else ("#F87171" if s < 20 else "#FFF")
                    cols[i].markdown(f"<div style='text-align:center; font-family:Rajdhani; font-size:1.2rem; font-weight:800; color:{c}; background:rgba(255,255,255,0.05); border-radius:8px; padding:10px'>{int(s)}</div>", unsafe_allow_html=True)

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
                            vf = f"{v:.1f}" if isinstance(v, float) else str(int(v))
                            if metric == "diff": vf = f"+{vf}"
                            if metric == "pct": vf = f"+{vf}%"
                            h += f"<div class='t-row'><span class='t-name'>{p}</span><span class='t-val' style='color:{C_GREEN}'>{vf} <span style='font-size:0.8rem; color:#888'>{unit}</span></span></div>"
                    st.markdown(h+"</div>", unsafe_allow_html=True)
                with c2:
                    h = f"<div class='trend-box'><div class='cold-header'>❄️ COLD STREAK</div>"
                    if cold.empty: h += "<div style='color:#666'>Aucune donnée</div>"
                    else:
                        for p, v in cold.head(3).items():
                            vf = f"{v:.1f}" if isinstance(v, float) else str(int(v))
                            if metric == "pct": vf = f"{vf}%"
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
            progression = full_stats.sort_values('Progression15', ascending=False).iloc[0]
            heavy = full_stats.sort_values('Count40', ascending=False).iloc[0]
            peak = full_stats.sort_values('Best', ascending=False).iloc[0]
            intouch = full_stats.sort_values('Streak30', ascending=False).iloc[0]
            rock = full_stats.sort_values('Count30', ascending=False).iloc[0]
            nuke = full_stats.sort_values('Nukes', ascending=False).iloc[0]
            floor = full_stats.sort_values('Worst', ascending=True).iloc[0]
            lapin = full_stats.sort_values('Carottes', ascending=False).iloc[0]
            sniper_bp = full_stats.sort_values('BP_Count', ascending=False).iloc[0]
            alpha_dog = full_stats.sort_values('Alpha_Count', ascending=False).iloc[0]

            def hof_card(title, icon, color, p_name, val, unit, desc):
                return f"""<div class="glass-card" style="position:relative; overflow:hidden"><div style="position:absolute; right:-10px; top:-10px; font-size:5rem; opacity:0.05; pointer-events:none">{icon}</div><div class="hof-badge" style="color:{color}; border:1px solid {color}">{icon} {title}</div><div style="display:flex; justify-content:space-between; align-items:flex-end;"><div><div class="hof-player">{p_name}</div><div style="font-size:0.8rem; color:#888; margin-top:4px">{desc}</div></div><div><div class="hof-stat" style="color:{color}">{val}</div><div class="hof-unit">{unit}</div></div></div></div>"""

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(hof_card("THE GOAT", "🏆", C_GOLD, sniper['Player'], f"{sniper['Moyenne']:.1f}", "PTS MOY", "Meilleure moyenne générale"), unsafe_allow_html=True)
                st.markdown(hof_card("THE SNIPER", "🎯", C_PURPLE, sniper_bp['Player'], int(sniper_bp['BP_Count']), "BEST PICKS", "A trouvé le meilleur score TTFL le plus souvent"), unsafe_allow_html=True)
                st.markdown(hof_card("HUMAN TORCH", "🔥", "#FF5252", torche['Player'], f"{torche['Last15']:.1f}", "PTS / 15J", "Le plus chaud du mois"), unsafe_allow_html=True)
                st.markdown(hof_card("RISING STAR", "🚀", C_GREEN, progression['Player'], f"+{progression['Progression15']:.1f}", "PTS GAIN", "Progression Moyenne 15j vs Saison"), unsafe_allow_html=True)
                st.markdown(hof_card("THE CEILING", "🏔️", "#A78BFA", peak['Player'], int(peak['Best']), "PTS MAX", "Record absolu en un match"), unsafe_allow_html=True)
                st.markdown(hof_card("HEAVY HITTER", "🥊", "#64B5F6", heavy['Player'], int(heavy['Count40']), "PICKS >40", "Volume de gros scores"), unsafe_allow_html=True)
            with c2:
                st.markdown(hof_card("ALPHA DOG", "🐺", C_ALPHA, alpha_dog['Player'], int(alpha_dog['Alpha_Count']), "TOPS TEAM", "Le plus souvent meilleur scoreur de l'équipe"), unsafe_allow_html=True)
                st.markdown(hof_card("UNSTOPPABLE", "⚡", "#FBBF24", intouch['Player'], int(intouch['Streak30']), "SERIE", "Matchs consécutifs > 30pts"), unsafe_allow_html=True)
                st.markdown(hof_card("THE ROCK", "🛡️", C_GREEN, rock['Player'], int(rock['Count30']), "MATCHS", "Total matchs > 30pts"), unsafe_allow_html=True)
                st.markdown(hof_card("NUCLEAR", "☢️", "#EF4444", nuke['Player'], int(nuke['Nukes']), "BOMBS", "Scores > 50pts"), unsafe_allow_html=True)
                st.markdown(hof_card("THE FLOOR", "🧱", "#9CA3AF", floor['Player'], int(floor['Worst']), "PTS MIN", "Pire score enregistré"), unsafe_allow_html=True)
                st.markdown(hof_card("THE FARMER", "🥕", "#F97316", lapin['Player'], int(lapin['Carottes']), "CAROTTES", "Scores < 20pts"), unsafe_allow_html=True)

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
                        res = send_discord_webhook(day_df, latest_pick, "https://dino-fant-tvewyye4t3dmqfeuvqsvmg.streamlit.app/", team_rank)
                        if res == "success": st.success("✅ Envoyé !")
                        else: st.error(f"Erreur : {res}")
                    st.markdown("</div>", unsafe_allow_html=True)
                if st.button("🔒 VERROUILLER"): st.session_state["admin_access"] = False; st.rerun()

    else: st.warning("⚠️ Aucune donnée trouvée.")
except Exception as e: st.error(f"🔥 Critical Error: {e}")
