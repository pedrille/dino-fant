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

    /* --- TRENDS HOT/COLD --- */
    .trend-container {{
        border-radius: 16px; padding: 20px; margin-bottom: 20px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
    }}
    
    .hot-header {{ border-bottom: 1px solid rgba(206, 17, 65, 0.3); padding-bottom: 10px; margin-bottom: 15px; }}
    .cold-header {{ border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding-bottom: 10px; margin-bottom: 15px; }}

    .trend-title {{ font-family: 'Rajdhani'; font-weight: 800; font-size: 1.4rem; display: flex; align-items: center; gap: 8px; }}
    .trend-desc {{ font-family: 'Inter'; font-size: 0.75rem; color: #888; margin-top: 2px; font-weight: 400; }}
    
    .trend-row {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .trend-row:last-child {{ border-bottom: none; }}
    .trend-val-block {{ text-align: right; }}
    .trend-val-main {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.3rem; line-height: 1; }}
    .trend-val-sub {{ font-size: 0.7rem; color: #666; display: block; margin-top: 2px; }}

    /* --- HALL OF FAME --- */
    .hof-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
        background: rgba(255,255,255,0.05);
    }}
    .hof-player {{ font-family: 'Rajdhani'; font-size: 1.6rem; font-weight: 700; color: #FFF; }}
    .hof-stat {{ font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 800; text-align: right; line-height: 1; }}
    .hof-unit {{ font-size: 0.7rem; color: #666; text-align: right; font-weight: 600; text-transform: uppercase; }}

    /* --- DASHBOARD RANKING --- */
    .rank-row {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 4px;
        transition: background 0.2s;
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

# --- 3. DATA ENGINE (OPTIMISÉ CACHE 60s) ---
@st.cache_data(ttl=60) # Remis à 60s pour éviter la lenteur extrême
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return pd.DataFrame()
        
        # Lecture avec petit cache
        df_raw = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", header=None, ttl=0)
        
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_raw.iloc[pick_row_idx, 1:], errors='coerce')
        data_start_idx = pick_row_idx + 1
        
        df_players = df_raw.iloc[data_start_idx:data_start_idx+50].copy()
        df_players = df_players.rename(columns={0: 'Player'})
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)].dropna(subset=['Player'])

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
        
        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
            
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        
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
def send_discord_webhook(day_df, pick_num, url_app):
    if "DISCORD_WEBHOOK" not in st.secrets: return "missing_secret"
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    
    top_3 = day_df.head(3).reset_index(drop=True)
    podium_text = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, row in top_3.iterrows():
        podium_text += f"{medals[i]} **{row['Player']}** • {int(row['Score'])} pts\n"
    
    avg_score = int(day_df['Score'].mean())

    data = {
        "username": "Raptors Intelligence",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2592/2592242.png", 
        "embeds": [{
            "title": f"🦖 DEBRIEF • PICK #{int(pick_num)}",
            "description": f"La nuit est terminée. Voici le rapport officiel.\n\n**MOYENNE TEAM :** `{avg_score} pts`",
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
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        full_stats = compute_stats(df)
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
                    War Room v3.0
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
            with c3: kpi_card("TOTAL NUIT", int(day_df['Score'].sum()), "CUMULÉ")
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
                
                # --- FIX DU BUG D'AFFICHAGE HTML ---
                medals = {0: "🥇", 1: "🥈", 2: "🥉"}
                rows_html = ""
                for i, r in day_df.reset_index().iterrows():
                    pos_disp = medals.get(i, f"<span style='color:#666; font-size:0.9rem'>{i+1}</span>")
                    hl_style = f"border-left: 3px solid {C_ACCENT}; background: rgba(255,255,255,0.03);" if i == 0 else "border-left: 3px solid transparent;"
                    score_col = C_ACCENT if i == 0 else "#FFF"
                    
                    # Attention à l'indentation ici ! Tout doit être collé à gauche dans la f-string pour Markdown
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
            st.dataframe(full_stats[['Player', 'Total', 'Moyenne', 'Best', 'Nukes', 'Carottes']].sort_values('Total', ascending=False), hide_index=True, use_container_width=True, column_config={
                "Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()), 
                "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f"),
                "Carottes": st.column_config.NumberColumn("🥕", help="Scores < 20"),
                "Nukes": st.column_config.NumberColumn("☢️", help="Scores > 50")
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

        # --- TRENDS (CORRECTION HTML BUG) ---
        elif menu == "Trends":
            section_title("MARKET <span class='highlight'>WATCH</span>", "Analyse des tendances sur 15 jours")
            
            lookback_days = 15
            df_recent = df[df['Pick'] > (latest_pick - lookback_days)]
            
            recent_stats = df_recent.groupby('Player').agg({
                'Score': ['mean', 'count', lambda x: (x >= 40).sum(), lambda x: (x < 20).sum()]
            })
            recent_stats.columns = ['Mean15', 'Count', 'Highs', 'Lows']
            season_avg = df.groupby('Player')['Score'].mean().rename('SeasonAvg')
            delta_df = get_comparative_stats(df, latest_pick, lookback=lookback_days)
            merged = recent_stats.join(delta_df).join(season_avg)
            merged['PctDiff'] = ((merged['Mean15'] - merged['SeasonAvg']) / merged['SeasonAvg']) * 100
            
            def render_trend_block(title, desc, icon, color, data_rows, type_metric):
                # Début du bloc
                html = f"""
                <div class="trend-container">
                    <div class="{'hot' if color==C_ACCENT else 'cold'}-header">
                        <div class="trend-title" style="color:{color}">{icon} {title}</div>
                        <div class="trend-desc">{desc}</div>
                    </div>
                """
                if data_rows.empty: 
                    html += "<div style='color:#666; font-style:italic'>Aucune donnée significative.</div>"
                else:
                    for p_name, row in data_rows.iterrows():
                        val_html = ""
                        sub_html = ""
                        
                        if type_metric == 'avg':
                            diff = row['Mean15'] - row['SeasonAvg']
                            sign = "+" if diff > 0 else ""
                            c_val = C_GREEN if diff > 0 else "#F87171"
                            val_html = f"{row['Mean15']:.1f} <span style='font-size:0.8rem'>pts</span>"
                            sub_html = f"{sign}{diff:.1f} pts ({sign}{row['PctDiff']:.0f}%) vs saison"
                        elif type_metric == 'mom':
                            val = row['mean_diff']
                            sign = "+" if val > 0 else ""
                            c_val = C_GREEN if val > 0 else "#F87171"
                            val_html = f"{sign}{val:.1f} <span style='font-size:0.8rem'>pts</span>"
                            sub_html = f"Évolution moyenne sur 15j"
                        elif type_metric == 'rank':
                            val = int(row['rank_diff'])
                            sign = "+" if val > 0 else ""
                            c_val = "#FFF"
                            val_html = f"{sign}{val} <span style='font-size:0.8rem'>places</span>"
                            sub_html = "au classement général"
                        elif type_metric == 'count':
                            val = int(row['Highs'] if 'Highs' in row else row['Lows'])
                            pct = (val/row['Count'])*100
                            c_val = "#FFF"
                            val_html = f"{val} <span style='font-size:0.8rem'>{'picks' if 'Highs' in row else 'carottes'}</span>"
                            sub_html = f"soit {pct:.0f}% des matchs"

                        # Construction ligne par ligne sans indentation pour éviter le bug Markdown
                        html += f"""<div class="trend-row"><div class="trend-name">{p_name}</div><div class="trend-val-block"><div class="trend-val-main" style="color:{c_val}">{val_html}</div><div class="trend-val-sub">{sub_html}</div></div></div>"""
                
                html += "</div>"
                return html

            c_hot, c_cold = st.columns(2, gap="large")

            with c_hot:
                st.markdown(f"<h3 style='color:{C_ACCENT}; margin-bottom:20px'>🔥 HOT LIST</h3>", unsafe_allow_html=True)
                
                top_avg = merged.sort_values('Mean15', ascending=False).head(3)
                st.markdown(render_trend_block("FORME OLYMPIQUE", "Meilleure moyenne sur la quinzaine.", "📈", C_ACCENT, top_avg, 'avg'), unsafe_allow_html=True)
                
                top_mom = merged[merged['mean_diff'] > 0].sort_values('mean_diff', ascending=False).head(3)
                st.markdown(render_trend_block("GROSSE PROGRESSION", "Hausse significative des scores récents.", "🚀", C_ACCENT, top_mom, 'mom'), unsafe_allow_html=True)

                top_rank = merged[merged['rank_diff'] > 0].sort_values('rank_diff', ascending=False).head(3)
                st.markdown(render_trend_block("CLIMBING THE LADDER", "Gains de places au classement général.", "🧗", C_ACCENT, top_rank, 'rank'), unsafe_allow_html=True)
                
                top_highs = merged[merged['Highs'] > 0].sort_values('Highs', ascending=False).head(3)
                st.markdown(render_trend_block("HEAVY HITTERS", "Joueurs enchaînant les scores > 40pts.", "💣", C_ACCENT, top_highs, 'count'), unsafe_allow_html=True)

            with c_cold:
                st.markdown(f"<h3 style='color:{C_BLUE}; margin-bottom:20px'>❄️ COLD LIST</h3>", unsafe_allow_html=True)
                
                bot_avg = merged.sort_values('Mean15', ascending=True).head(3)
                st.markdown(render_trend_block("ICE COLD", "Moyenne en berne sur la quinzaine.", "🥶", C_BLUE, bot_avg, 'avg'), unsafe_allow_html=True)
                
                bot_mom = merged[merged['mean_diff'] < 0].sort_values('mean_diff', ascending=True).head(3)
                st.markdown(render_trend_block("DOWNSWING", "Baisse de régime vs moyenne saison.", "📉", C_BLUE, bot_mom, 'mom'), unsafe_allow_html=True)

                bot_rank = merged[merged['rank_diff'] < 0].sort_values('rank_diff', ascending=True).head(3)
                st.markdown(render_trend_block("FREE FALLING", "Chute au classement général.", "🪂", C_BLUE, bot_rank, 'rank'), unsafe_allow_html=True)

                top_lows = merged[merged['Lows'] > 0].sort_values('Lows', ascending=False).head(3)
                st.markdown(render_trend_block("CARROT FARMERS", "Accumulation de scores < 20pts.", "🥕", C_BLUE, top_lows, 'count'), unsafe_allow_html=True)

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

        # --- ADMIN ---
        elif menu == "Admin":
            section_title("ADMIN <span class='highlight'>PANEL</span>", "Gestion des flux")
            
            col_refresh, col_discord = st.columns(2)
            
            with col_refresh:
                st.markdown("#### 🔄 DONNÉES")
                st.info("Utiliser ce bouton si les scores ne semblent pas à jour.")
                if st.button("FORCER LA MISE À JOUR (PURGE CACHE)", type="secondary"):
                    st.cache_data.clear()
                    st.rerun()
            
            with col_discord:
                st.markdown("#### 📡 DISCORD")
                st.write("Envoi du rapport quotidien.")
                if st.button("🚀 ENVOYER RAPPORT DISCORD", type="primary"):
                    res = send_discord_webhook(day_df, latest_pick, "https://dino-fant-tvewyye4t3dmqfeuvqsvmg.streamlit.app/")
                    if res == "success": st.success("✅ Envoyé !")
                    else: st.error(f"Erreur : {res}")

    else: st.warning("⚠️ Aucune donnée trouvée dans la Spreadsheet. Vérifiez l'URL et le format.")
except Exception as e: st.error(f"🔥 Critical Error: {e}")
