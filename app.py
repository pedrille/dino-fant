import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import numpy as np

# --- 1. CONFIGURATION & DESIGN SYSTEM ---
st.set_page_config(
    page_title="Raptors Dynasty",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="collapsed"
)

# CSS AVANCÉ (GLASSMORPHISM & NEON)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');

    /* GLOBAL */
    .stApp {
        background-color: #050505;
        background-image: 
            radial-gradient(at 0% 0%, rgba(206, 17, 65, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(255, 255, 255, 0.05) 0px, transparent 50%);
        font-family: 'Inter', sans-serif;
        color: #EDEDED;
    }
    
    /* TYPO */
    h1, h2, h3 { font-family: 'Rajdhani', sans-serif; text-transform: uppercase; letter-spacing: 1px; }
    h1 { font-weight: 700; font-size: 3rem; background: -webkit-linear-gradient(#fff, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    h2 { color: #CE1141; border-left: 4px solid #CE1141; padding-left: 12px; font-size: 1.8rem; margin-top: 40px; }
    
    /* KPI CARDS */
    .stat-box {
        background: rgba(20, 20, 20, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        text-align: center;
        transition: 0.3s;
    }
    .stat-box:hover { border-color: #CE1141; box-shadow: 0 0 20px rgba(206, 17, 65, 0.2); }
    .stat-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-family: 'Rajdhani'; font-size: 2.5rem; font-weight: 700; color: white; line-height: 1.1; }
    .stat-delta { font-size: 0.8rem; font-weight: 600; margin-top: 5px; }
    .positive { color: #4ade80; }
    .negative { color: #f87171; }

    /* HOT & COLD CARDS */
    .player-card {
        background: #0F0F0F;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid #444;
    }
    .card-hot { border-left-color: #CE1141; background: linear-gradient(90deg, rgba(206, 17, 65, 0.1), transparent); }
    .card-cold { border-left-color: #3b82f6; background: linear-gradient(90deg, rgba(59, 130, 246, 0.1), transparent); }
    
    .p-name { font-weight: 700; font-size: 1.1rem; font-family: 'Rajdhani'; }
    .p-stat { font-weight: 700; font-size: 1.2rem; }
    .p-sub { font-size: 0.75rem; color: #666; }

    /* INSIGHTS */
    .insight-pill {
        display: inline-block;
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 20px;
        padding: 5px 15px;
        font-size: 0.85rem;
        margin-right: 10px;
        margin-bottom: 10px;
        color: #ccc;
    }
    .pill-highlight { border-color: #CE1141; color: white; background: rgba(206, 17, 65, 0.1); }

    /* PLOTLY FIX */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }

</style>
""", unsafe_allow_html=True)

# --- 2. ENGINE (DATA & LOGIC) ---

@st.cache_data(ttl=600)
def load_data():
    """Chargement robuste et nettoyage des données"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return pd.DataFrame()
        df_raw = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", usecols=None, header=None)
        
        # Logique de repérage
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_raw.iloc[pick_row_idx, 1:], errors='coerce')
        data_start_idx = pick_row_idx + 1
        
        # Extraction Joueurs
        df_players = df_raw.iloc[data_start_idx:data_start_idx+50].copy()
        df_players = df_players.rename(columns={0: 'Player'})
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme", "0 et négatif"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)]
        df_players = df_players.dropna(subset=['Player'])

        # Mapping Colonnes
        valid_cols_map = {idx: int(val) for idx, val in picks_series.items() if pd.notna(val) and val > 0}
        cols_to_keep = ['Player'] + list(valid_cols_map.keys())
        cols_to_keep = [c for c in cols_to_keep if c in df_players.columns]
        
        df_clean = df_players[cols_to_keep].copy().rename(columns=valid_cols_map)
        
        # Format Long
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        
        return df_long.dropna(subset=['Score', 'Pick'])
    except: return pd.DataFrame()

def get_advanced_stats(df):
    """Calcule les métriques avancées pour chaque joueur"""
    players = df['Player'].unique()
    stats_list = []
    
    for p in players:
        p_data = df[df['Player'] == p].sort_values('Pick')
        scores = p_data['Score'].values
        
        # Stats de base
        total = scores.sum()
        avg = scores.mean()
        count = len(scores)
        best = scores.max()
        
        # Forme (5 derniers matchs)
        last_5 = scores[-5:] if len(scores) >= 5 else scores
        avg_last_5 = last_5.mean()
        
        # Dynamique (Différence Forme vs Saison)
        momentum = avg_last_5 - avg
        
        # Séries (Streak > 30)
        current_streak = 0
        for s in reversed(scores):
            if s >= 30: current_streak += 1
            else: break
            
        stats_list.append({
            'Player': p,
            'Total': total,
            'Avg': avg,
            'Last5_Avg': avg_last_5,
            'Momentum': momentum,
            'Streak_30': current_streak,
            'Best': best,
            'Count': count
        })
        
    return pd.DataFrame(stats_list)

# --- 3. UI COMPONENTS ---

def kpi_card(label, value, delta=None, sub=""):
    delta_html = ""
    if delta is not None:
        color = "positive" if delta >= 0 else "negative"
        sign = "+" if delta >= 0 else ""
        delta_html = f"<div class='stat-delta {color}'>{sign}{delta}</div>"
        
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
        {delta_html}
        <div style="font-size:0.7rem; color:#555; margin-top:5px;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def player_row(rank, name, score, max_score, is_mvp=False):
    width = (score / max_score) * 100
    color = "#CE1141" if is_mvp else "#333"
    crown = "👑" if is_mvp else f"#{rank}"
    
    st.markdown(f"""
    <div style="margin-bottom: 8px; display:flex; align-items:center;">
        <div style="width:30px; font-weight:bold; color:{'#CE1141' if is_mvp else '#666'}">{crown}</div>
        <div style="flex-grow:1;">
            <div style="display:flex; justify-content:space-between; font-size:0.9rem; margin-bottom:2px;">
                <span style="font-weight:600;">{name}</span>
                <span style="font-family:'Rajdhani'; font-weight:700;">{int(score)}</span>
            </div>
            <div style="width:100%; background:#1a1a1a; height:6px; border-radius:3px;">
                <div style="width:{width}%; background:{color}; height:100%; border-radius:3px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def hot_cold_widget(stats_df):
    # Trier par Momentum pour Hot/Cold
    hot = stats_df.sort_values('Last5_Avg', ascending=False).head(3)
    cold = stats_df.sort_values('Last5_Avg', ascending=True).head(3)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("##### 🔥 ON FIRE (LAST 5)")
        for _, row in hot.iterrows():
            st.markdown(f"""
            <div class="player-card card-hot">
                <div>
                    <div class="p-name">{row['Player']}</div>
                    <div class="p-sub">Momentum: <span style="color:#4ade80">+{row['Momentum']:.1f}</span></div>
                </div>
                <div class="p-stat">{row['Last5_Avg']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
            
    with c2:
        st.markdown("##### ❄️ DANS LE DUR (LAST 5)")
        for _, row in cold.iterrows():
            st.markdown(f"""
            <div class="player-card card-cold">
                <div>
                    <div class="p-name">{row['Player']}</div>
                    <div class="p-sub">Momentum: <span style="color:#f87171">{row['Momentum']:.1f}</span></div>
                </div>
                <div class="p-stat">{row['Last5_Avg']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

# --- 4. MAIN APP LOGIC ---

try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        stats_df = get_advanced_stats(df)
        
        leader_row = stats_df.sort_values('Total', ascending=False).iloc[0]
        
        # SIDEBAR
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png", width=140)
            selected = option_menu(
                menu_title=None,
                options=["Dashboard", "Stats Center", "Admin"],
                icons=["grid", "bar-chart-line", "shield-lock"],
                default_index=0,
                styles={
                    "container": {"background-color": "transparent"},
                    "nav-link-selected": {"background-color": "#CE1141", "color": "white"},
                    "icon": {"color": "#CE1141"}
                }
            )
            st.markdown("---")
            st.markdown(f"<div style='text-align:center; color:#666'>Pick #{int(latest_pick)}<br>Season 2025</div>", unsafe_allow_html=True)

        # --- DASHBOARD VIEW ---
        if selected == "Dashboard":
            
            # HEADER
            st.markdown(f"<h1>RAPTORS <span style='color:#CE1141'>DYNASTY</span></h1>", unsafe_allow_html=True)
            
            # TOP KPIS
            top_p = day_df.iloc[0]
            avg_team = day_df['Score'].mean()
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("MVP DU JOUR", top_p['Player'], int(top_p['Score']), "POINTS")
            with c2: kpi_card("MOYENNE TEAM", int(avg_team), None, f"Pick #{int(latest_pick)}")
            with c3: kpi_card("LEADER SAISON", leader_row['Player'], int(leader_row['Total']), "TOTAL POINTS")
            with c4: kpi_card("PICK RATE", len(day_df), None, "JOUEURS ACTIFS")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # MAIN CONTENT GRID
            col_left, col_right = st.columns([2, 1.2])
            
            with col_left:
                st.markdown("## 📈 DYNAMIQUE DE L'ÉQUIPE")
                
                # Graphique "Clean"
                df_sorted = df.sort_values('Pick')
                df_sorted['Cumul'] = df_sorted.groupby('Player')['Score'].cumsum()
                
                # Top 5 seulement pour lisibilité
                top5_names = stats_df.sort_values('Total', ascending=False).head(5)['Player'].tolist()
                
                fig = px.line(
                    df_sorted[df_sorted['Player'].isin(top5_names)], 
                    x='Pick', y='Cumul', color='Player',
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(
                    height=350,
                    margin=dict(l=0, r=0, t=0, b=0),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#888', 'family': 'Inter'},
                    xaxis=dict(showgrid=False, title=None),
                    yaxis=dict(showgrid=True, gridcolor='#222', title=None),
                    legend=dict(orientation="h", y=1.1, x=0, title=None)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                st.markdown("## 🔥 ÉTAT DE FORME")
                hot_cold_widget(stats_df)

            with col_right:
                st.markdown("## 📊 CLASSEMENT DU JOUR")
                st.markdown("<div style='background:#111; padding:15px; border-radius:12px; border:1px solid #222;'>", unsafe_allow_html=True)
                
                max_s = day_df['Score'].max()
                for i, (idx, row) in enumerate(day_df.iterrows()):
                    player_row(i+1, row['Player'], row['Score'], max_s, is_mvp=(i==0))
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("## 💡 INSIGHTS")
                # Génération automatique d'insights
                insights_html = ""
                
                # Série de victoires
                streaks = stats_df[stats_df['Streak_30'] >= 2].sort_values('Streak_30', ascending=False)
                for _, s in streaks.iterrows():
                    insights_html += f"<span class='insight-pill pill-highlight'>🔥 <b>{s['Player']}</b>: {int(s['Streak_30'])} matchs > 30pts</span>"
                
                # Record battu ?
                if top_p['Score'] > 50:
                     insights_html += f"<span class='insight-pill pill-highlight'>💣 <b>{top_p['Player']}</b> a explosé le compteur !</span>"
                
                # Régularité
                sniper = stats_df.sort_values('Avg', ascending=False).iloc[0]
                insights_html += f"<span class='insight-pill'>🎯 <b>{sniper['Player']}</b> est le plus régulier ({sniper['Avg']:.1f} moy)</span>"
                
                st.markdown(insights_html, unsafe_allow_html=True)

        # --- STATS CENTER ---
        elif selected == "Stats Center":
            st.markdown("<h2>STATS CENTER</h2>", unsafe_allow_html=True)
            
            st.dataframe(
                stats_df.sort_values('Total', ascending=False),
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "Player": "Joueur",
                    "Total": st.column_config.ProgressColumn("Total Points", format="%d", min_value=0, max_value=int(stats_df['Total'].max())),
                    "Avg": st.column_config.NumberColumn("Moyenne", format="%.1f"),
                    "Last5_Avg": st.column_config.NumberColumn("Forme (5j)", format="%.1f"),
                    "Momentum": st.column_config.NumberColumn("Dyn.", format="%.1f"),
                    "Streak_30": st.column_config.NumberColumn("Série >30", format="%d 🔥"),
                }
            )

        # --- ADMIN ---
        elif selected == "Admin":
            st.markdown("<h2>ZONE ADMIN</h2>", unsafe_allow_html=True)
            if st.button("📢 ENVOYER RAPPORT DISCORD", type="primary"):
                st.success("Rapport envoyé au QG.")

    else:
        st.info("Chargement des données en cours...")

except Exception as e:
    st.error("Erreur technique.")
    st.expander("Détails").write(e)
