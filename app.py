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
C_GREEN = "#10B981"
C_BLUE = "#3B82F6"

# --- 2. CSS PREMIUM (GLASSMORPHISM & TYPO) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Rajdhani:wght@500;700&display=swap');

    /* GLOBAL */
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    
    /* SIDEBAR FIX */
    section[data-testid="stSidebar"] {{ background-color: #000000; border-right: 1px solid #222; }}
    
    /* OPTION MENU HACK - NO WHITE BORDERS */
    .nav-link {{
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        margin: 5px 0 !important;
    }}
    .nav-link-selected {{
        background-color: {C_ACCENT} !important;
        color: #FFF !important;
    }}
    
    /* HEADINGS */
    h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    h1 {{ 
        font-size: 3rem; font-weight: 700; 
        background: linear-gradient(90deg, #FFF, #999); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    }}
    .highlight {{ color: {C_ACCENT}; }}
    .sub-header {{ font-size: 0.9rem; color: #666; letter-spacing: 2px; margin-bottom: 20px; }}

    /* CARDS (GLASSMORPHISM) */
    .glass-card {{
        background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }}
    .glass-card:hover {{ border-color: {C_ACCENT}; transform: translateY(-2px); box-shadow: 0 4px 20px rgba(206, 17, 65, 0.15); }}

    /* VERSUS CARDS FOR TRENDS */
    .vs-card {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    .vs-card:last-child {{ border-bottom: none; }}
    .vs-val {{ font-family: 'Rajdhani'; font-size: 1.5rem; font-weight: 700; }}
    
    /* KPI BLOCKS */
    .kpi-container {{ text-align: center; }}
    .kpi-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
    .kpi-value {{ font-family: 'Rajdhani'; font-size: 2.5rem; font-weight: 700; color: #FFF; line-height: 1; }}
    .kpi-sub {{ font-size: 0.8rem; color: {C_ACCENT}; font-weight: 600; margin-top: 4px; }}

    /* TABLEAUX & LISTES */
    .ranking-row {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 12px 15px; border-bottom: 1px solid rgba(255,255,255,0.05);
        font-family: 'Rajdhani'; font-size: 1.1rem;
    }}
    .ranking-row:last-child {{ border-bottom: none; }}

    /* BADGES HOF */
    .hof-badge {{
        display: inline-flex; align-items: center; padding: 4px 12px;
        border-radius: 20px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        margin-bottom: 8px; letter-spacing: 0.5px;
    }}
    
    /* CLEANUP STREAMLIT */
    .stPlotlyChart {{ width: 100% !important; }}
    div[data-testid="stDataFrame"] {{ border: none !important; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 0rem; }}
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return pd.DataFrame()
        df_raw = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", header=None)
        
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
            'Count40': len(scores[scores >= 40]), # NEW STAT pour HOF
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
    
    worst = day_df.iloc[-1]
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
                {"name": "🧱 LE MAÇON", "value": f"{worst['Player']} ({int(worst['Score'])} pts)", "inline": True},
                {"name": "🔗 LIEN RAPIDE", "value": f"[Accéder au Dashboard]({url_app})", "inline": True}
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
    <div class="glass-card kpi-container">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def section_title(title, subtitle):
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)

def comparison_html(title, icon, data_series, is_positive_good=True, unit="", is_rank=False):
    color = C_GREEN if is_positive_good else C_BLUE
    if not is_positive_good: color = C_ACCENT
    
    html = f"""
    <div class="glass-card" style="height:100%">
        <div style="display:flex; align-items:center; margin-bottom:15px; border-bottom:1px solid #333; padding-bottom:10px">
            <span style="font-size:1.5rem; margin-right:10px">{icon}</span>
            <span style="font-family:Rajdhani; font-weight:700; font-size:1.2rem; color:#FFF">{title}</span>
        </div>
    """
    if data_series.empty: html += "<div style='color:#666'>Données insuffisantes</div>"
    else:
        for player, val in data_series.items():
            val_fmt = f"{val:.1f}" if isinstance(val, float) else f"{int(val)}"
            if is_rank: val_fmt = f"+{int(val)}" if val > 0 else f"{int(val)}"
            elif val > 0 and not is_rank: val_fmt = f"+{val_fmt}"
            
            html += f"""<div class="vs-card"><span style="font-weight:600; color:#EEE">{player}</span><span class="vs-val" style="color:{color}">{val_fmt}<span style="font-size:0.8rem; margin-left:2px">{unit}</span></span></div>"""
    html += "</div>"
    return html

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
            st.markdown("<br>", unsafe_allow_html=True)
            st.image("raptors-ttfl-min.png", use_container_width=True) 
            st.markdown("<br>", unsafe_allow_html=True)
            
            menu = option_menu(
                menu_title=None,
                options=["Dashboard", "Team HQ", "Player Lab", "Trends", "Hall of Fame", "Admin"],
                icons=["grid-fill", "people-fill", "person-bounding-box", "activity", "trophy-fill", "shield-lock"],
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"color": C_ACCENT, "font-size": "1.2rem"}, 
                    "nav-link": {"background-color": "transparent", "margin": "0px", "--hover-color": "#222"},
                    "nav-link-selected": {"background-color": "transparent", "color": C_ACCENT, "border-right": f"4px solid {C_ACCENT}"},
                }
            )
            st.markdown(f"<div style='text-align:center; color:#444; font-size:11px; margin-top:50px; font-family:Rajdhani; border-top:1px solid #222; padding-top:10px'>DATA PICK #{int(latest_pick)}</div>", unsafe_allow_html=True)

        # --- DASHBOARD ---
        if menu == "Dashboard":
            section_title("RAPTORS <span class='highlight'>DASHBOARD</span>", f"Daily Briefing • Pick #{int(latest_pick)}")
            
            top = day_df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("MVP DU JOUR", top['Player'], f"{int(top['Score'])} PTS", C_GOLD)
            with c2: kpi_card("MOYENNE TEAM", int(day_df['Score'].mean()), "POINTS")
            with c3: kpi_card("TOTAL NUIT", int(day_df['Score'].sum()), "CUMULÉ")
            # MODIFICATION ICI : MAILLOT JAUNE -> LEADER SAISON
            with c4: kpi_card("LEADER SAISON", leader['Player'], f"TOTAL: {int(leader['Total'])}", C_ACCENT)
            
            col_chart, col_rank = st.columns([2, 1])
            with col_chart:
                st.markdown("<h3 style='margin-bottom:15px'>📊 PERFORMANCE LIVE</h3>", unsafe_allow_html=True)
                fig = px.bar(day_df, x='Player', y='Score', text='Score', color='Score', color_continuous_scale=[C_BG, C_ACCENT])
                fig.update_traces(textposition='outside', marker_line_width=0, textfont_size=14, textfont_family="Rajdhani")
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA', 'family': 'Inter'}, yaxis=dict(showgrid=True, gridcolor='#222', title=None), xaxis=dict(title=None), height=380, showlegend=False, coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            with col_rank:
                st.markdown("<h3 style='margin-bottom:15px'>📋 CLASSEMENT</h3>", unsafe_allow_html=True)
                html_rank = "<div class='glass-card' style='padding:0; overflow:hidden'>"
                for i, r in day_df.reset_index().iterrows():
                    color = C_ACCENT if i == 0 else ("#FFF" if i < 3 else "#888")
                    bg_row = "rgba(255,255,255,0.05)" if i % 2 == 0 else "transparent"
                    html_rank += f"<div class='ranking-row' style='background:{bg_row}'><span class='rank-pos' style='color:{color}'>{i+1}</span><span class='rank-name' style='color:{color if i==0 else '#EEE'}'>{r['Player']}</span><span class='rank-score'>{int(r['Score'])}</span></div>"
                html_rank += "</div>"
                st.markdown(html_rank, unsafe_allow_html=True)

        # --- TEAM HQ ---
        elif menu == "Team HQ":
            section_title("TEAM <span class='highlight'>HQ</span>", "Comparaison d'équipe")
            st.markdown("### 🎯 DENSITÉ DES SCORES")
            fig_dist = px.violin(df, x='Player', y='Score', box=True, points="all", color='Player', color_discrete_sequence=px.colors.qualitative.Bold)
            fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, showlegend=False, height=400, yaxis=dict(gridcolor='#222'))
            st.plotly_chart(fig_dist, use_container_width=True)
            st.markdown("### 📈 CLASSEMENT GÉNÉRAL")
            st.dataframe(full_stats[['Player', 'Total', 'Moyenne', 'Best', 'Nukes', 'Carottes']].sort_values('Total', ascending=False), hide_index=True, use_container_width=True, column_config={"Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()), "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f"), "Carottes": st.column_config.NumberColumn("🥕", help="Scores < 20")})

        # --- PLAYER LAB ---
        elif menu == "Player Lab":
            section_title("PLAYER <span class='highlight'>LAB</span>", "Analyse Profonde")
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
                c_a, c_b = st.columns(2)
                with c_a: kpi_card("BEST PICK", int(p_data['Best']), "RECORD")
                with c_b: kpi_card("WORST PICK", int(p_data['Worst']), "PIEUX")
                st.markdown("#### 🔥 FORME RÉCENTE"); last_5_scores = df[df['Player'] == sel_player].sort_values('Pick').tail(5)['Score'].values
                cols = st.columns(5)
                for i, s in enumerate(last_5_scores):
                    color = "#4ADE80" if s >= 30 else ("#F87171" if s < 20 else "#FFF")
                    cols[i].markdown(f"<div style='text-align:center; font-family:Rajdhani; font-weight:bold; color:{color}; border:1px solid #333; border-radius:8px; padding:5px'>{int(s)}</div>", unsafe_allow_html=True)

        # --- TRENDS ---
        elif menu == "Trends":
            section_title("MOMENTUM <span class='highlight'>TRACKER</span>", "Analyses comparatives sur 15 jours")
            delta_df = get_comparative_stats(df, latest_pick, lookback=15)
            df_15 = df[df['Pick'] > (latest_pick - 15)]
            
            avg_gain = delta_df['mean_diff'].sort_values(ascending=False).head(3)
            avg_loss = delta_df['mean_diff'].sort_values(ascending=True).head(3)
            rank_gain = delta_df['rank_diff'].sort_values(ascending=False).head(3)
            rank_loss = delta_df['rank_diff'].sort_values(ascending=True).head(3)
            nuke_cnt = df_15[df_15['Score'] >= 50].groupby('Player').size().sort_values(ascending=False).head(3)
            carrot_cnt = df_15[df_15['Score'] < 20].groupby('Player').size().sort_values(ascending=False).head(3)

            c1, c2 = st.columns(2)
            with c1: st.markdown(comparison_html("MOMENTUM (Pts Moy)", "🚀", avg_gain, True, " pts"), unsafe_allow_html=True)
            with c2: st.markdown(comparison_html("DOWNSWING (Pts Moy)", "📉", avg_loss, False, " pts"), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            c3, c4 = st.columns(2)
            with c3: st.markdown(comparison_html("LA REMONTADA (Places)", "🧗", rank_gain, True, " places", is_rank=True), unsafe_allow_html=True)
            with c4: st.markdown(comparison_html("LA CHUTE (Places)", "🪂", rank_loss, False, " places", is_rank=True), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            c5, c6 = st.columns(2)
            with c5: st.markdown(comparison_html("ATOMIC BOMBS (>50pts)", "☢️", nuke_cnt, True, " nukes"), unsafe_allow_html=True)
            with c6: st.markdown(comparison_html("CARROT FIELD (<20pts)", "🥕", carrot_cnt, False, " carottes"), unsafe_allow_html=True)

        # --- HALL OF FAME ---
        elif menu == "Hall of Fame":
            section_title("HALL OF <span class='highlight'>FAME</span>", "Les records de la saison")
            
            sniper = full_stats.sort_values('Moyenne', ascending=False).iloc[0]
            torche = full_stats.sort_values('Last15', ascending=False).iloc[0]
            fusee = full_stats.sort_values('Momentum', ascending=False).iloc[0]
            
            # MODIFICATION HOF 1: REMPLACEMENT DU NIGHT MVP par HEAVY HITTER
            heavy = full_stats.sort_values('Count40', ascending=False).iloc[0]
            
            peak = full_stats.sort_values('Best', ascending=False).iloc[0]
            intouch = full_stats.sort_values('Streak30', ascending=False).iloc[0]
            rock = full_stats.sort_values('Count30', ascending=False).iloc[0]
            nuke = full_stats.sort_values('Nukes', ascending=False).iloc[0]
            floor = full_stats.sort_values('Worst', ascending=True).iloc[0]
            lapin = full_stats.sort_values('Carottes', ascending=False).iloc[0]

            def hof_html(icon, color, title, p_name, value, unit, desc):
                border = f"1px solid {color}"; bg_badge = f"{color}20"
                return f"""<div class="glass-card" style="margin-bottom:15px; position:relative; overflow:hidden;"><div style="position:absolute; top:-10px; right:-10px; font-size:4rem; opacity:0.1; filter:grayscale(100%)">{icon}</div><div class="hof-badge" style="background:{bg_badge}; color:{color}; border:{border}">{icon} {title}</div><div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:10px"><div><div style="font-size:1.3rem; font-weight:700; line-height:1.2">{p_name}</div><div style="color:#888; font-size:0.8rem; margin-top:2px">{desc}</div></div><div style="text-align:right"><div style="font-family:Rajdhani; font-size:2rem; font-weight:700; color:{color}; line-height:1">{value}</div><div style="font-size:0.7rem; font-weight:bold; color:#666">{unit}</div></div></div></div>"""

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(hof_html("🏆", "#FFD700", "THE GOAT", sniper['Player'], f"{sniper['Moyenne']:.1f}", "PTS MOYENNE", "Meilleure moyenne générale"), unsafe_allow_html=True)
                st.markdown(hof_html("🔥", "#FF5252", "HUMAN TORCH", torche['Player'], f"{torche['Last15']:.1f}", "PTS / 15J", "Le plus chaud du mois"), unsafe_allow_html=True)
                
                # MODIFICATION HOF 2: RISING STAR EXPLICATIF
                st.markdown(hof_html("🚀", "#4ADE80", "RISING STAR", fusee['Player'], f"+{fusee['Momentum']:.1f}", "PTS DE GAIN", "Moyenne 5 derniers vs Saison"), unsafe_allow_html=True)
                
                st.markdown(hof_html("🏔️", "#A78BFA", "THE CEILING", peak['Player'], int(peak['Best']), "PTS MAX", "Record absolu en un match"), unsafe_allow_html=True)
                
                # MODIFICATION HOF 3: NOUVEAU BADGE HEAVY HITTER
                st.markdown(hof_html("🥊", "#64B5F6", "HEAVY HITTER", heavy['Player'], int(heavy['Count40']), "PICKS >40", "Total scores au dessus de 40pts"), unsafe_allow_html=True)
                
            with c2:
                st.markdown(hof_html("⚡", "#FBBF24", "UNSTOPPABLE", intouch['Player'], int(intouch['Streak30']), "SERIE", "Matchs consécutifs > 30pts"), unsafe_allow_html=True)
                st.markdown(hof_html("🛡️", "#34D399", "THE ROCK", rock['Player'], int(rock['Count30']), "MATCHS", "Total matchs > 30pts"), unsafe_allow_html=True)
                st.markdown(hof_html("☢️", "#EF4444", "NUCLEAR", nuke['Player'], int(nuke['Nukes']), "BOMBS", "Scores > 50pts"), unsafe_allow_html=True)
                st.markdown(hof_html("🧱", "#9CA3AF", "THE FLOOR", floor['Player'], int(floor['Worst']), "PTS MIN", "Pire score enregistré"), unsafe_allow_html=True)
                st.markdown(hof_html("🥕", "#F97316", "THE FARMER", lapin['Player'], int(lapin['Carottes']), "CAROTTES", "Scores < 20pts"), unsafe_allow_html=True)

        # --- ADMIN ---
        elif menu == "Admin":
            section_title("ADMIN <span class='highlight'>PANEL</span>", "Gestion des flux")
            if st.button("🚀 ENVOYER RAPPORT DISCORD", type="primary"):
                res = send_discord_webhook(day_df, latest_pick, "https://dino-fant-tvewyye4t3dmqfeuvqsvmg.streamlit.app/")
                if res == "success": st.success("✅ Envoyé !")
                else: st.error(f"Erreur : {res}")

    else: st.warning("⚠️ Aucune donnée.")
except Exception as e: st.error(f"🔥 Error: {e}")
