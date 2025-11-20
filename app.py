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

# --- 2. CSS PREMIUM (DESIGN SYSTEM) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');

    /* GLOBAL */
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    div[data-testid="stSidebarNav"] {{ display: none; }} 
    
    /* MENU */
    .nav-link {{
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }}

    /* TYPOGRAPHY */
    h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    h1 {{ 
        font-size: 3rem; font-weight: 800; 
        background: linear-gradient(90deg, #FFF, #888); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    }}
    .highlight {{ color: {C_ACCENT}; }}
    .sub-header {{ font-size: 0.9rem; color: #666; letter-spacing: 1.5px; margin-bottom: 25px; font-weight: 500; }}

    /* GLASS CARDS */
    .glass-card {{
        background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }}

    /* --- TRENDS LAYOUT --- */
    .trend-section-title {{
        font-family: 'Rajdhani'; font-size: 1.2rem; font-weight: 700; color: #FFF; margin-bottom: 5px; border-left: 4px solid #555; padding-left: 10px;
    }}
    .trend-section-desc {{
        font-size: 0.8rem; color: #888; margin-bottom: 15px; padding-left: 14px; font-style: italic;
    }}
    
    .trend-box {{
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(255,255,255,0.05);
        height: 100%;
    }}
    
    .hot-header {{ color: {C_ACCENT}; border-bottom: 1px solid rgba(206, 17, 65, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .cold-header {{ color: {C_BLUE}; border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}

    .t-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .t-row:last-child {{ border-bottom: none; }}
    .t-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.2rem; text-align: right; }}
    .t-sub {{ font-size: 0.7rem; color: #666; display: block; margin-top: 2px; text-align: right; }}
    .t-name {{ font-weight: 500; color: #DDD; font-size: 0.95rem; }}

    /* --- HALL OF FAME --- */
    .hof-badge {{
        display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; background: rgba(255,255,255,0.05);
    }}
    .hof-player {{ font-family: 'Rajdhani'; font-size: 1.6rem; font-weight: 700; color: #FFF; }}
    .hof-stat {{ font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 800; text-align: right; line-height: 1; }}
    .hof-unit {{ font-size: 0.7rem; color: #666; text-align: right; font-weight: 600; text-transform: uppercase; }}

    /* --- DASHBOARD RANKING --- */
    .rank-row {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 15px; border-radius: 8px; margin-bottom: 4px; transition: background 0.2s;
    }}
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

# --- 3. DATA ENGINE (V4 - INTELLIGENT PARSING) ---
@st.cache_data(ttl=60) 
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return pd.DataFrame(), 0, pd.Series()
        
        # 1. LECTURE ONGLET VALEURS (Joueurs)
        # On lit tout pour attraper la ligne "Score BP" qui est souvent ligne 16 (index 15)
        df_raw = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", header=None, ttl=0)
        
        # Extraction Ligne Pick
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_raw.iloc[pick_row_idx, 1:], errors='coerce')
        
        # Extraction Ligne Score BP (Best Pick) - Ligne 16 dans le CSV fourni
        # On cherche la ligne qui commence par "Score BP"
        bp_row_data = df_raw[df_raw[0].astype(str).str.contains("Score BP", na=False)]
        if not bp_row_data.empty:
            bp_series = pd.to_numeric(bp_row_data.iloc[0, 1:], errors='coerce')
        else:
            bp_series = pd.Series(index=picks_series.index, data=0)

        # Nettoyage Joueurs
        data_start_idx = pick_row_idx + 1
        df_players = df_raw.iloc[data_start_idx:data_start_idx+50].copy()
        df_players = df_players.rename(columns={0: 'Player'})
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)].dropna(subset=['Player'])

        # Mapping des colonnes valides
        valid_cols_map = {idx: int(val) for idx, val in picks_series.items() if pd.notna(val) and val > 0}
        
        # Dataframe Clean
        cols_to_keep = ['Player'] + list(valid_cols_map.keys())
        cols_to_keep = [c for c in cols_to_keep if c in df_players.columns]
        df_clean = df_players[cols_to_keep].copy().rename(columns=valid_cols_map)
        
        # Dataframe Long (Pour les calculs)
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        final_df = df_long.dropna(subset=['Score', 'Pick'])

        # Mapping BP (Best Pick) pour comparaison
        # On crée un dictionnaire {Pick_Num : Score_BP}
        bp_map = {int(picks_series[idx]): val for idx, val in bp_series.items() if idx in valid_cols_map}

        # 2. LECTURE ONGLET STATS (Pour le Team Rank)
        # Le classement est dans le bloc de droite "Classement" (colonne AK environ)
        team_rank = 0
        try:
            df_stats = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Stats_Raptors_FR", header=None, ttl=0)
            # Recherche de "Team Raptors" dans la colonne AJ (35) ou AK (36)
            # Selon le CSV, "Team Raptors" est en ligne 14, Col AK (36), et le rang est en fin de ligne
            
            # On scanne la zone pour trouver "Team Raptors" et prendre la dernière valeur non nulle de sa ligne
            for idx, row in df_stats.iterrows():
                # On convertit la ligne en string pour chercher
                row_str = row.astype(str).values
                if "Team Raptors" in row_str:
                    # On cherche des nombres dans cette ligne
                    numeric_values = [x for x in row if isinstance(x, (int, float, np.number)) and not pd.isna(x)]
                    if numeric_values:
                        team_rank = numeric_values[-1] # Le dernier chiffre est le classement actuel
                    break
        except:
            team_rank = 0

        return final_df, int(team_rank), bp_map
    except: return pd.DataFrame(), 0, {}

def compute_stats(df, bp_map):
    stats = []
    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        scores = d['Score'].values
        picks = d['Pick'].values
        
        # Streak 30
        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
            
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        
        # Calcul des Best Picks (BP)
        # On compare le score du joueur au score BP du pick correspondant
        bp_count = 0
        for pick_num, score in zip(picks, scores):
            if pick_num in bp_map and score >= bp_map[pick_num] and score > 0:
                bp_count += 1

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
            'Zeros': len(scores[scores == 0]), # Nouveau Stat Ghost
            'BP_Count': bp_count, # Nouveau Stat Sniper
            'Momentum': momentum,
            'Games': len(scores)
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
    rank_txt = f"#{team_rank}" if team_rank > 0 else "N/A"

    data = {
        "username": "Raptors Intelligence",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2592/2592242.png", 
        "embeds": [{
            "title": f"🦖 DEBRIEF • PICK #{int(pick_num)}",
            "description": f"La nuit est terminée. Voici le rapport officiel.\n\n**MOYENNE TEAM :** `{avg_score} pts`\n**CLASSEMENT :** `{rank_txt}`",
            "color": 13504833,
            "fields": [
                {"name": "🏆 PODIUM", "value": podium_text, "inline": False},
                {"name": "🔗 LIEN RAPIDE", "value": f"[Accéder au Dashboard]({url_app})", "inline": False}
            ],
            "footer": {"text": "Raptors Elite System • Data is Power"}
        }]
    }
    try:
        requests.post(webhook_url, json=data)
        return "success"
    except Exception as e: return str(e)

# --- 5. COMPOSANTS UI ---
def kpi_card(label, value, sub, color="#FFF"):
    st.markdown(f"""
    <div class="glass-card" style="text-align:center">
        <div class="kpi-label">{label}</div>
        <div class="kpi-num" style="color:{color}">{value}</div>
        <div class="kpi-sub" style="color:{C_ACCENT}">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def section_title(title, subtitle):
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)

# --- 6. MAIN APP ---
try:
    df, team_rank, bp_map = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        full_stats = compute_stats(df, bp_map)
        leader = full_stats.sort_values('Total', ascending=False).iloc[0]
        
        # --- SIDEBAR ---
        with st.sidebar:
            st.markdown("<div style='text-align:center; margin-bottom: 30px;'>", unsafe_allow_html=True)
            st.image("raptors-ttfl-min.png", use_container_width=True) 
            st.markdown("</div>", unsafe_allow_html=True)
            
            menu = option_menu(
                menu_title=None,
                options=["Dashboard", "Team HQ", "Player Lab", "Trends", "Hall of Fame", "Admin"],
                icons=["grid-fill", "people-fill", "person-bounding-box", "fire", "trophy-fill", "shield-lock"],
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#000000"},
                    "icon": {"color": "#666", "font-size": "1.1rem"}, 
                    "nav-link": {
                        "font-family": "Rajdhani, sans-serif",
                        "font-weight": "700",
                        "font-size": "15px",
                        "text-transform": "uppercase",
                        "color": "#AAA",
                        "text-align": "left",
                        "margin": "5px 0px",
                        "--hover-color": "#111"
                    },
                    "nav-link-selected": {
                        "background-color": C_ACCENT, 
                        "color": "#FFF",
                        "icon-color": "#FFF",
                        "box-shadow": "0px 4px 20px rgba(206, 17, 65, 0.4)"
                    },
                }
            )
            
            st.markdown(f"""
            <div style='position: fixed; bottom: 30px; width: 100%; padding-left: 20px;'>
                <div style='color:#444; font-size:10px; font-family:Rajdhani; letter-spacing:2px; text-transform:uppercase'>
                    Data Pick #{int(latest_pick)}<br>
                    War Room v4.0
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- DASHBOARD ---
        if menu == "Dashboard":
            section_title("RAPTORS <span class='highlight'>DASHBOARD</span>", f"Daily Briefing • Pick #{int(latest_pick)}")
            
            top = day_df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("MVP DU JOUR", top['Player'], f"{int(top['Score'])} PTS", C_GOLD)
            with c2: kpi_card("MOYENNE TEAM", int(day_df['Score'].mean()), "POINTS")
            
            # Affichage CLASSEMENT TEAM récupéré dynamiquement
            rank_display = f"#{int(team_rank)}" if team_rank > 0 else "N/A"
            rank_color = C_GOLD if team_rank > 0 and team_rank <= 20 else (C_GREEN if team_rank <= 100 else "#FFF")
            
            with c3: kpi_card("CLASSEMENT TEAM", rank_display, "GENERAL", rank_color)
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
                rows_html = ""
                for i, r in day_df.reset_index().iterrows():
                    pos_disp = medals.get(i, f"<span style='color:#666; font-size:0.9rem'>{i+1}</span>")
                    hl_style = f"border-left: 3px solid {C_ACCENT}; background: rgba(255,255,255,0.03);" if i == 0 else "border-left: 3px solid transparent;"
                    score_col = C_ACCENT if i == 0 else "#FFF"
                    rows_html += f"""<div class='rank-row' style='{hl_style}'><div class='rank-pos'>{pos_disp}</div><div class='rank-name' style='color:{'#FFF' if i < 3 else '#AAA'}'>{r['Player']}</div><div class='rank-score' style='color:{score_col}'>{int(r['Score'])}</div></div>"""
                
                st.markdown(f"<div style='display:flex; flex-direction:column; gap:5px'>{rows_html}</div></div>", unsafe_allow_html=True)

        # --- TEAM HQ ---
        elif menu == "Team HQ":
            section_title("TEAM <span class='highlight'>HQ</span>", "Vue d'ensemble de l'effectif")
            st.markdown("### 🎯 RÉPARTITION DES SCORES")
            fig_dist = px.violin(df, x='Player', y='Score', box=True, points="all", color='Player', color_discrete_sequence=px.colors.qualitative.Prism)
            fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, showlegend=False, height=400, yaxis=dict(gridcolor='#222'))
            st.plotly_chart(fig_dist, use_container_width=True)
            
            st.markdown("### 📈 CLASSEMENT GÉNÉRAL")
            st.dataframe(full_stats[['Player', 'Total', 'Moyenne', 'BP_Count', 'Nukes', 'Carottes', 'Zeros']].sort_values('Total', ascending=False), hide_index=True, use_container_width=True, column_config={
                "Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()), 
                "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f"),
                "Carottes": st.column_config.NumberColumn("🥕", help="Scores < 20"),
                "Nukes": st.column_config.NumberColumn("☢️", help="Scores > 50"),
                "BP_Count": st.column_config.NumberColumn("🎯", help="Best Picks"),
                "Zeros": st.column_config.NumberColumn("👻", help="Bulles (0 pts)")
            })

        # --- PLAYER LAB ---
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
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'), bgcolor='rgba(0,0,0,0)'), 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='white', size=12, family="Rajdhani"), 
                    margin=dict(t=20, b=20)
                )
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True); st.plotly_chart(fig_radar, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
            
            with col_stats:
                kpi_card("MOYENNE SAISON", f"{p_data['Moyenne']:.1f}", "PTS")
                c_a, c_b = st.columns(2)
                with c_a: kpi_card("BEST PICK", int(p_data['Best']), "RECORD")
                with c_b: kpi_card("WORST PICK", int(p_data['Worst']), "PIEUX")
                
                st.markdown("#### 🔥 DERNIERS MATCHS")
                last_5_scores = df[df['Player'] == sel_player].sort_values('Pick').tail(5)['Score'].values
                cols = st.columns(5)
                for i, s in enumerate(last_5_scores):
                    color = "#4ADE80" if s >= 40 else ("#F87171" if s < 20 else "#FFF")
                    cols[i].markdown(f"<div style='text-align:center; font-family:Rajdhani; font-size:1.2rem; font-weight:800; color:{color}; background:rgba(255,255,255,0.05); border-radius:8px; padding:10px'>{int(s)}</div>", unsafe_allow_html=True)

        # --- TRENDS ---
        elif menu == "Trends":
            section_title("MARKET <span class='highlight'>WATCH</span>", "Analyse des tendances sur 15 jours")
            
            # PREP DATA
            df_15 = df[df['Pick'] > (latest_pick - 15)] # 15 jours
            df_7 = df[df['Pick'] > (latest_pick - 7)]   # 7 jours
            
            # 1. GENERAL AVG 15D
            avg_15 = df_15.groupby('Player')['Score'].mean().sort_values(ascending=False)
            top_hot_avg = avg_15.head(3)
            top_cold_avg = avg_15.tail(3).sort_values(ascending=True)
            
            # 2. BURST 7D vs SEASON
            season_avg = df.groupby('Player')['Score'].mean()
            avg_7 = df_7.groupby('Player')['Score'].mean()
            diff_7 = (avg_7 - season_avg).dropna().sort_values(ascending=False)
            top_hot_7 = diff_7.head(3)
            top_cold_7 = diff_7.tail(3).sort_values(ascending=True)
            
            # 3. % EVOLUTION 15D
            pct_15 = ((avg_15 - season_avg) / season_avg * 100).dropna().sort_values(ascending=False)
            top_hot_pct = pct_15.head(3)
            top_cold_pct = pct_15.tail(3).sort_values(ascending=True)
            
            # 4. EXTREMES
            nukes_15 = df_15[df_15['Score'] >= 50].groupby('Player').size().sort_values(ascending=False).head(3)
            carrots_15 = df_15[df_15['Score'] < 20].groupby('Player').size().sort_values(ascending=False).head(3)

            # 5. RANK EVOLUTION
            delta_rank = get_comparative_stats(df, latest_pick, lookback=15)['rank_diff']
            top_hot_rank = delta_rank.sort_values(ascending=False).head(3)
            top_cold_rank = delta_rank.sort_values(ascending=True).head(3) # Negative

            # --- RENDER FUNCTION (ROW SPLIT) ---
            def render_comparison_row(title, subtitle, hot_data, cold_data, type_metric, unit=""):
                st.markdown(f"<div class='trend-section-title'>{title}</div><div class='trend-section-desc'>{subtitle}</div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                
                # HOT SIDE
                with c1:
                    html = f"<div class='trend-box'><div class='hot-header'>🔥 TOP PERFORMERS</div>"
                    if hot_data.empty: html += "<div style='color:#666'>Aucune donnée</div>"
                    else:
                        for p, val in hot_data.items():
                            val_fmt = f"{val:.1f}" if isinstance(val, float) else str(int(val))
                            if type_metric == "diff": val_fmt = f"+{val_fmt}"
                            if type_metric == "pct": val_fmt = f"+{val_fmt}%"
                            
                            html += f"<div class='t-row'><span class='t-name'>{p}</span><span class='t-val' style='color:{C_GREEN}'>{val_fmt} <span style='font-size:0.8rem; color:#888'>{unit}</span></span></div>"
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                
                # COLD SIDE
                with c2:
                    html = f"<div class='trend-box'><div class='cold-header'>❄️ COLD STREAK</div>"
                    if cold_data.empty: html += "<div style='color:#666'>Aucune donnée</div>"
                    else:
                        for p, val in cold_data.items():
                            val_fmt = f"{val:.1f}" if isinstance(val, float) else str(int(val))
                            if type_metric == "pct": val_fmt = f"{val_fmt}%" # Deja negatif
                            
                            html += f"<div class='t-row'><span class='t-name'>{p}</span><span class='t-val' style='color:#F87171'>{val_fmt} <span style='font-size:0.8rem; color:#888'>{unit}</span></span></div>"
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                
                st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True) # Spacer

            # --- DISPLAY BLOCKS ---
            render_comparison_row("MOYENNE GÉNÉRALE (15 JOURS)", "Les joueurs les plus réguliers vs ceux en difficulté sur la quinzaine.", top_hot_avg, top_cold_avg, "raw", "pts")
            render_comparison_row("EXPLOSIVITÉ (7 JOURS VS SAISON)", "Écart de points entre la semaine passée et la moyenne habituelle.", top_hot_7, top_cold_7, "diff", "pts diff")
            render_comparison_row("DYNAMIQUE DE FORME (15J VS SAISON)", "Pourcentage de progression ou régression sur la quinzaine.", top_hot_pct, top_cold_pct, "pct", "")
            render_comparison_row("PICKS MARQUANTS (15 JOURS)", "Accumulation de scores > 50pts (Nukes) vs scores < 20pts (Carottes).", nukes_15, carrots_15, "int", "picks")
            render_comparison_row("MOUVEMENTS AU CLASSEMENT", "Gains et pertes de places au général sur 15 jours.", top_hot_rank[top_hot_rank>0], top_cold_rank[top_cold_rank<0], "diff", "places")


        # --- HALL OF FAME ---
        elif menu == "Hall of Fame":
            section_title("HALL OF <span class='highlight'>FAME</span>", "Records & Trophées de la saison")
            
            sniper = full_stats.sort_values('Moyenne', ascending=False).iloc[0]
            torche = full_stats.sort_values('Last15', ascending=False).iloc[0]
            fusee = full_stats.sort_values('Momentum', ascending=False).iloc[0]
            heavy = full_stats.sort_values('Count40', ascending=False).iloc[0]
            peak = full_stats.sort_values('Best', ascending=False).iloc[0]
            intouch = full_stats.sort_values('Streak30', ascending=False).iloc[0]
            rock = full_stats.sort_values('Count30', ascending=False).iloc[0]
            nuke = full_stats.sort_values('Nukes', ascending=False).iloc[0]
            floor = full_stats.sort_values('Worst', ascending=True).iloc[0]
            lapin = full_stats.sort_values('Carottes', ascending=False).iloc[0]
            # NOUVEAUX STATS
            best_picker = full_stats.sort_values('BP_Count', ascending=False).iloc[0]
            ghost = full_stats.sort_values('Zeros', ascending=False).iloc[0]

            def hof_card(title, icon, color, p_name, val, unit, desc):
                return f"""
                <div class="glass-card" style="position:relative; overflow:hidden">
                    <div style="position:absolute; right:-10px; top:-10px; font-size:5rem; opacity:0.05; pointer-events:none">{icon}</div>
                    <div class="hof-badge" style="color:{color}; border:1px solid {color}">{icon} {title}</div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <div class="hof-player">{p_name}</div>
                            <div style="font-size:0.8rem; color:#888; margin-top:4px">{desc}</div>
                        </div>
                        <div>
                            <div class="hof-stat" style="color:{color}">{val}</div>
                            <div class="hof-unit">{unit}</div>
                        </div>
                    </div>
                </div>
                """

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(hof_card("THE GOAT", "🏆", C_GOLD, sniper['Player'], f"{sniper['Moyenne']:.1f}", "PTS MOY", "Meilleure moyenne générale"), unsafe_allow_html=True)
                st.markdown(hof_card("THE SNIPER", "🎯", C_PURPLE, best_picker['Player'], int(best_picker['BP_Count']), "BEST PICKS", "A trouvé le meilleur score le plus souvent"), unsafe_allow_html=True)
                st.markdown(hof_card("HUMAN TORCH", "🔥", "#FF5252", torche['Player'], f"{torche['Last15']:.1f}", "PTS / 15J", "Le plus chaud du mois"), unsafe_allow_html=True)
                st.markdown(hof_card("RISING STAR", "🚀", C_GREEN, fusee['Player'], f"+{fusee['Momentum']:.1f}", "PTS GAIN", "Progression vs Saison"), unsafe_allow_html=True)
                st.markdown(hof_card("THE CEILING", "🏔️", "#A78BFA", peak['Player'], int(peak['Best']), "PTS MAX", "Record absolu en un match"), unsafe_allow_html=True)
                st.markdown(hof_card("HEAVY HITTER", "🥊", "#64B5F6", heavy['Player'], int(heavy['Count40']), "PICKS >40", "Volume de gros scores"), unsafe_allow_html=True)

            with c2:
                st.markdown(hof_card("UNSTOPPABLE", "⚡", "#FBBF24", intouch['Player'], int(intouch['Streak30']), "SERIE", "Matchs consécutifs > 30pts"), unsafe_allow_html=True)
                st.markdown(hof_card("THE ROCK", "🛡️", C_GREEN, rock['Player'], int(rock['Count30']), "MATCHS", "Total matchs > 30pts"), unsafe_allow_html=True)
                st.markdown(hof_card("NUCLEAR", "☢️", "#EF4444", nuke['Player'], int(nuke['Nukes']), "BOMBS", "Scores > 50pts"), unsafe_allow_html=True)
                st.markdown(hof_card("THE FLOOR", "🧱", "#9CA3AF", floor['Player'], int(floor['Worst']), "PTS MIN", "Pire score enregistré"), unsafe_allow_html=True)
                st.markdown(hof_card("THE FARMER", "🥕", "#F97316", lapin['Player'], int(lapin['Carottes']), "CAROTTES", "Scores < 20pts"), unsafe_allow_html=True)
                st.markdown(hof_card("THE GHOST", "👻", "#888", ghost['Player'], int(ghost['Zeros']), "BULLES", "Scores à 0 point"), unsafe_allow_html=True)

        # --- ADMIN ---
        elif menu == "Admin":
            section_title("ADMIN <span class='highlight'>PANEL</span>", "Accès Restreint")
            
            if "admin_access" not in st.session_state: st.session_state["admin_access"] = False

            if not st.session_state["admin_access"]:
                c1, c2, c3 = st.columns([1, 2, 1])
                with c2:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("#### 🔒 ZONE SÉCURISÉE")
                    pwd = st.text_input("Mot de passe", type="password", key="admin_pwd")
                    if st.button("DÉVERROUILLER"):
                        if "ADMIN_PASSWORD" in st.secrets and pwd == st.secrets["ADMIN_PASSWORD"]:
                            st.session_state["admin_access"] = True
                            st.rerun()
                        else: st.error("⛔ Accès refusé")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                col_refresh, col_discord = st.columns(2)
                with col_refresh:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("#### 🔄 DONNÉES")
                    st.info("Utiliser si les données ne sont pas à jour.")
                    if st.button("FORCER LA MISE À JOUR (PURGE)", type="secondary"):
                        st.cache_data.clear()
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with col_discord:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("#### 📡 DISCORD")
                    st.write("Envoi du rapport quotidien.")
                    if st.button("🚀 ENVOYER RAPPORT DISCORD", type="primary"):
                        res = send_discord_webhook(day_df, latest_pick, "https://dino-fant-tvewyye4t3dmqfeuvqsvmg.streamlit.app/", team_rank)
                        if res == "success": st.success("✅ Envoyé !")
                        else: st.error(f"Erreur : {res}")
                    st.markdown("</div>", unsafe_allow_html=True)
                if st.button("🔒 VERROUILLER L'ACCÈS"):
                    st.session_state["admin_access"] = False
                    st.rerun()

    else: st.warning("⚠️ Aucune donnée trouvée dans la Spreadsheet. Vérifiez l'URL et le format.")
except Exception as e: st.error(f"🔥 Critical Error: {e}")
