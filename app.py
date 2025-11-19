import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import numpy as np
import requests

# --- 1. CONFIGURATION & CORE SETTINGS ---
st.set_page_config(
    page_title="Raptors War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# --- 2. DESIGN SYSTEM (CSS ULTRA PREMIUM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700&display=swap');

    /* BASE */
    .stApp { background-color: #050505; font-family: 'Inter', sans-serif; color: #E5E7EB; }
    
    /* TYPOGRAPHIE */
    h1, h2, h3, h4 { font-family: 'Rajdhani', sans-serif; text-transform: uppercase; letter-spacing: 1px; }
    h1 { 
        font-size: 3rem; font-weight: 700; 
        background: linear-gradient(90deg, #FFFFFF 0%, #999999 100%); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        margin-bottom: 0rem;
    }
    h2 { 
        font-size: 1.5rem; color: #CE1141; margin-top: 2.5rem; margin-bottom: 1.5rem; 
        border-left: 4px solid #CE1141; padding-left: 15px;
    }
    .subtitle { color: #6B7280; font-size: 0.9rem; margin-bottom: 2rem; font-family: 'Inter', sans-serif; }

    /* COMPOSANTS UI (GLASSMORPHISM) */
    .card {
        background: linear-gradient(180deg, rgba(30, 30, 30, 0.6) 0%, rgba(10, 10, 10, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    /* KPI BOXES */
    .kpi-box {
        background: #0F0F0F;
        border: 1px solid #222;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-box:hover { border-color: #CE1141; transform: translateY(-3px); }
    .kpi-label { font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-val { font-family: 'Rajdhani'; font-size: 2rem; font-weight: 700; color: white; }
    .kpi-sub { font-size: 0.75rem; color: #CE1141; font-weight: 600; }

    /* BADGES */
    .badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600; margin-right: 5px; border: 1px solid;
    }
    .badge-fire { background: rgba(206, 17, 65, 0.15); border-color: #CE1141; color: #FCA5A5; }
    .badge-ice { background: rgba(59, 130, 246, 0.15); border-color: #3B82F6; color: #93C5FD; }
    .badge-gold { background: rgba(234, 179, 8, 0.15); border-color: #EAB308; color: #FDE047; }

    /* TABLES & PLOTS CLEANUP */
    div[data-testid="stDataFrame"] { border: none !important; }
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #020202; border-right: 1px solid #222; }
    
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE (ROBUSTE & COMPLET) ---
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return pd.DataFrame()
        df_raw = conn.read(spreadsheet=st.secrets["SPREADSHEET_URL"], worksheet="Valeurs", usecols=None, header=None)
        
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_raw.iloc[pick_row_idx, 1:], errors='coerce')
        data_start_idx = pick_row_idx + 1
        
        df_players = df_raw.iloc[data_start_idx:data_start_idx+50].copy()
        df_players = df_players.rename(columns={0: 'Player'})
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme", "0 et négatif"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)]
        df_players = df_players.dropna(subset=['Player'])

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
    """Calcul des stats complexes (Séries, Records, Forme)"""
    stats = []
    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        scores = d['Score'].values
        
        # Séries (Streaks)
        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
            
        # Briques & Bombes
        bricks = len(scores[scores < 20])
        nukes = len(scores[scores >= 50])
        
        stats.append({
            'Player': p,
            'Total': scores.sum(),
            'Moyenne': scores.mean(),
            'Best': scores.max(),
            'Worst': scores.min(),
            'Last5': scores[-5:].mean() if len(scores) >= 5 else scores.mean(),
            'Last10': scores[-10:].mean() if len(scores) >= 10 else scores.mean(),
            'Streak30': streak_30,
            'Bricks': bricks,
            'Nukes': nukes,
            'Games': len(scores)
        })
    return pd.DataFrame(stats)

# --- 4. AUTOMATION DISCORD ---
def send_discord_webhook(top_player, avg_score, pick_num, url_app):
    if "DISCORD_WEBHOOK" not in st.secrets: return "missing_secret"
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    
    data = {
        "username": "Raptors War Room",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png",
        "embeds": [{
            "title": f"🦖 RAPPORT TTFL • PICK #{int(pick_num)}",
            "description": "Les résultats de la nuit sont disponibles.",
            "color": 13504833,
            "fields": [
                {"name": "🔥 MVP", "value": f"**{top_player['Player']}**\n`{int(top_player['Score'])}` pts", "inline": True},
                {"name": "📊 Moyenne", "value": f"`{int(avg_score)}` pts", "inline": True},
                {"name": "🔗 Dashboard", "value": f"[Accéder à la War Room]({url_app})", "inline": False}
            ],
            "footer": {"text": "Raptors Elite System • We The North"}
        }]
    }
    try:
        result = requests.post(webhook_url, json=data)
        return "success" if result.status_code == 204 else f"error: {result.status_code}"
    except Exception as e: return f"error: {e}"

# --- 5. UI HELPERS ---
def kpi(label, value, sub=""):
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">{label}</div>
        <div class="kpi-val">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. MAIN APPLICATION ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        full_stats = compute_stats(df)
        leader = full_stats.sort_values('Total', ascending=False).iloc[0]
        
        # --- SIDEBAR ---
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png", width=130)
            menu = option_menu(
                menu_title=None,
                options=["Dashboard", "Team HQ", "Player Lab", "Momentum", "Hall of Fame", "Admin"],
                icons=["grid-fill", "people-fill", "person-bounding-box", "graph-up-arrow", "trophy-fill", "shield-lock"],
                default_index=0,
                styles={
                    "container": {"background-color": "transparent"},
                    "nav-link-selected": {"background-color": "#CE1141", "color": "white"},
                    "icon": {"color": "#CE1141"}
                }
            )
            st.markdown(f"<div style='text-align:center; color:#444; font-size:11px; margin-top:20px'>PICK #{int(latest_pick)}</div>", unsafe_allow_html=True)

        # --- 1. DASHBOARD (PICKS DE LA NUIT) ---
        if menu == "Dashboard":
            st.markdown(f"<h1>RAPTORS <span style='color:#CE1141'>DASHBOARD</span></h1>", unsafe_allow_html=True)
            st.markdown(f"<p class='subtitle'>Rapport du Pick #{int(latest_pick)}</p>", unsafe_allow_html=True)
            
            top = day_df.iloc[0]
            avg = day_df['Score'].mean()
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi("MVP DU JOUR", top['Player'], f"{int(top['Score'])} PTS")
            with c2: kpi("MOYENNE TEAM", int(avg), "POINTS")
            with c3: kpi("TOTAL NUIT", int(day_df['Score'].sum()), "POINTS CUMULÉS")
            with c4: kpi("MAILLOT JAUNE", leader['Player'], f"AVANCE: {int(leader['Total'] - full_stats.sort_values('Total', ascending=False).iloc[1]['Total'])}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            c_left, c_right = st.columns([2, 1])
            with c_left:
                st.markdown("### 📊 Performance du Soir")
                fig = px.bar(day_df, x='Player', y='Score', text='Score', color='Score', color_continuous_scale=['#333', '#CE1141'])
                fig.update_traces(textposition='outside', marker_line_width=0)
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#AAA'}, xaxis=dict(title=None), yaxis=dict(showgrid=True, gridcolor='#222'),
                    height=350, showlegend=False, coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with c_right:
                st.markdown("### 📋 Classement")
                html = "<div style='background:#0F0F0F; border-radius:8px; overflow:hidden; border:1px solid #222'>"
                for i, r in day_df.reset_index().iterrows():
                    color = "#CE1141" if i==0 else "#eee"
                    bg = "#1a1a1a" if i%2==0 else "#111"
                    html += f"<div style='padding:10px 15px; background:{bg}; display:flex; justify-content:space-between; border-bottom:1px solid #222'>"
                    html += f"<span style='font-weight:600; color:{color}'>#{i+1} {r['Player']}</span>"
                    html += f"<span style='font-family:Rajdhani; font-weight:700'>{int(r['Score'])}</span></div>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

        # --- 2. TEAM HQ (L'EQUIPE) ---
        elif menu == "Team HQ":
            st.markdown("<h1>TEAM <span style='color:#CE1141'>HEADQUARTERS</span></h1>", unsafe_allow_html=True)
            
            st.markdown("### 📈 La Course au Titre")
            df_sorted = df.sort_values('Pick')
            df_sorted['Cumul'] = df_sorted.groupby('Player')['Score'].cumsum()
            top5_total = full_stats.sort_values('Total', ascending=False).head(5)['Player'].tolist()
            
            # Filtre
            selected_players = st.multiselect("Comparer les joueurs", df['Player'].unique(), default=top5_total)
            if selected_players:
                fig = px.line(
                    df_sorted[df_sorted['Player'].isin(selected_players)], 
                    x='Pick', y='Cumul', color='Player', 
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#AAA'}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#222'),
                    height=450, hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 🎯 Distribution des Scores")
            fig_dist = px.box(df, x='Player', y='Score', color='Player', color_discrete_sequence=px.colors.qualitative.Bold)
            fig_dist.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font={'color': '#AAA'}, showlegend=False, yaxis=dict(gridcolor='#222')
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        # --- 3. PLAYER LAB (INDIVIDUEL) ---
        elif menu == "Player Lab":
            st.markdown("<h1>PLAYER <span style='color:#CE1141'>LAB</span></h1>", unsafe_allow_html=True)
            
            sel_player = st.selectbox("Sélectionner un joueur :", sorted(df['Player'].unique()))
            
            p_stats = full_stats[full_stats['Player'] == sel_player].iloc[0]
            p_history = df[df['Player'] == sel_player].sort_values('Pick')
            
            k1, k2, k3, k4 = st.columns(4)
            with k1: kpi("TOTAL SAISON", int(p_stats['Total']), f"Rank #{int(full_stats.sort_values('Total', ascending=False).reset_index()[full_stats.sort_values('Total', ascending=False).reset_index()['Player'] == sel_player].index[0] + 1)}")
            with k2: kpi("MOYENNE", f"{p_stats['Moyenne']:.1f}", f"vs Team: {df['Score'].mean():.1f}")
            with k3: kpi("MEILLEUR PICK", int(p_stats['Best']))
            with k4: kpi("BRIQUES (<20)", int(p_stats['Bricks']), "⚠️ Attention")
            
            st.markdown("---")
            
            c_graph, c_pie = st.columns([2, 1])
            with c_graph:
                st.markdown("### 📊 Historique & Tendance")
                p_history['MA5'] = p_history['Score'].rolling(5).mean()
                fig = go.Figure()
                fig.add_trace(go.Bar(x=p_history['Pick'], y=p_history['Score'], name='Score', marker_color='#333'))
                fig.add_trace(go.Scatter(x=p_history['Pick'], y=p_history['MA5'], name='Moy. 5j', line=dict(color='#CE1141', width=3)))
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#AAA'}, height=350, margin=dict(l=0, r=0, t=0, b=0),
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with c_pie:
                st.markdown("### 🍰 Répartition")
                bins = [0, 20, 30, 40, 150]
                labels = ['Brique (<20)', 'Moyen (20-30)', 'Bon (30-40)', 'Top (>40)']
                p_history['Cat'] = pd.cut(p_history['Score'], bins=bins, labels=labels)
                counts = p_history['Cat'].value_counts()
                fig_pie = px.pie(values=counts.values, names=counts.index, hole=0.6, color_discrete_sequence=px.colors.sequential.RdBu)
                fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', font={'color':'#fff'})
                st.plotly_chart(fig_pie, use_container_width=True)

        # --- 4. MOMENTUM (FORMES) ---
        elif menu == "Momentum":
            st.markdown("<h1>MOMENTUM <span style='color:#CE1141'>TRACKER</span></h1>", unsafe_allow_html=True)
            
            full_stats['Momentum_Score'] = full_stats['Last5'] - full_stats['Moyenne']
            hot = full_stats.sort_values('Last5', ascending=False).head(3)
            cold = full_stats.sort_values('Last5', ascending=True).head(3)
            
            c_hot, c_cold = st.columns(2)
            
            with c_hot:
                st.markdown("### 🔥 ON FIRE (Top Forme 5j)")
                for _, r in hot.iterrows():
                    st.markdown(f"""
                    <div class="card" style="border-left: 4px solid #CE1141; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:1.2rem; font-weight:bold;">{r['Player']}</span>
                            <span class="badge badge-fire">+{r['Momentum_Score']:.1f} pts vs Moy.</span>
                        </div>
                        <div style="font-family:Rajdhani; font-size:2rem; font-weight:700;">{r['Last5']:.1f} <span style="font-size:0.8rem; color:#666">MOYENNE 5j</span></div>
                    </div>""", unsafe_allow_html=True)

            with c_cold:
                st.markdown("### ❄️ ICE COLD (Dur dur...)")
                for _, r in cold.iterrows():
                    st.markdown(f"""
                    <div class="card" style="border-left: 4px solid #3B82F6; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:1.2rem; font-weight:bold;">{r['Player']}</span>
                            <span class="badge badge-ice">{r['Momentum_Score']:.1f} pts vs Moy.</span>
                        </div>
                        <div style="font-family:Rajdhani; font-size:2rem; font-weight:700;">{r['Last5']:.1f} <span style="font-size:0.8rem; color:#666">MOYENNE 5j</span></div>
                    </div>""", unsafe_allow_html=True)
            
            st.markdown("### 🌡️ Heatmap des 15 derniers jours")
            min_pick = max(1, latest_pick - 14)
            df_heat = df[df['Pick'] >= min_pick].pivot(index='Player', columns='Pick', values='Score')
            # Tri par score total récent
            df_heat['sum'] = df_heat.sum(axis=1)
            df_heat = df_heat.sort_values('sum', ascending=False).drop(columns='sum')
            
            fig_heat = px.imshow(df_heat, text_auto=True, aspect="auto", color_continuous_scale=['#111', '#CE1141'])
            fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'})
            fig_heat.update_coloraxes(showscale=False)
            st.plotly_chart(fig_heat, use_container_width=True)

        # --- 5. HALL OF FAME (INSOLITE) ---
        elif menu == "Hall of Fame":
            st.markdown("<h1>HALL OF <span style='color:#CE1141'>FAME</span></h1>", unsafe_allow_html=True)
            
            sniper = full_stats.sort_values('Moyenne', ascending=False).iloc[0]
            bricklayer = full_stats.sort_values('Bricks', ascending=False).iloc[0]
            streaker = full_stats.sort_values('Streak30', ascending=False).iloc[0]
            nuker = full_stats.sort_values('Nukes', ascending=False).iloc[0]
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f"""
                <div class="card" style="margin-bottom:20px;">
                    <div class="badge badge-gold">🏆 LE SNIPER</div>
                    <h3>{sniper['Player']}</h3>
                    <p style="color:#888">Meilleure moyenne de la saison.</p>
                    <div class="kpi-val">{sniper['Moyenne']:.1f} PTS</div>
                </div>
                <div class="card">
                    <div class="badge badge-fire">🔥 L'INTOUCHABLE</div>
                    <h3>{streaker['Player']}</h3>
                    <p style="color:#888">Série actuelle de matchs > 30 pts.</p>
                    <div class="kpi-val">{int(streaker['Streak30'])} MATCHS</div>
                </div>
                """, unsafe_allow_html=True)
                
            with c2:
                st.markdown(f"""
                <div class="card" style="margin-bottom:20px;">
                    <div class="badge badge-fire" style="border-color:#fff; color:#fff;">💣 ATOMIC BOMB</div>
                    <h3>{nuker['Player']}</h3>
                    <p style="color:#888">Le plus de scores > 50 pts.</p>
                    <div class="kpi-val">{int(nuker['Nukes'])} NUKES</div>
                </div>
                <div class="card">
                    <div class="badge badge-ice">🧱 LE MAÇON</div>
                    <h3>{bricklayer['Player']}</h3>
                    <p style="color:#888">Plus grand nombre de scores < 20.</p>
                    <div class="kpi-val">{int(bricklayer['Bricks'])} BRIQUES</div>
                </div>
                """, unsafe_allow_html=True)

        # --- 6. ADMIN ---
        elif menu == "Admin":
            st.markdown("<h1>ZONE <span style='color:#CE1141'>ADMIN</span></h1>", unsafe_allow_html=True)
            
            st.warning("⚠️ Attention : Cette action envoie une notification publique sur le serveur Discord.")
            
            col_btn, col_info = st.columns([1, 3])
            
            with col_btn:
                if st.button("🚀 LANCER LA NOTIF", type="primary"):
                    top_p = day_df.iloc[0]
                    avg_s = day_df['Score'].mean()
                    # Mettez l'URL de votre app ici
                    app_url = "https://ttfl-raptors.streamlit.app" 
                    
                    with st.spinner("Transmission au QG..."):
                        status = send_discord_webhook(top_p, avg_s, latest_pick, app_url)
                        
                    if status == "success":
                        st.success("✅ Rapport envoyé avec succès !")
                        st.balloons()
                    elif status == "missing_secret":
                        st.error("❌ Erreur : Le secret 'DISCORD_WEBHOOK' est manquant.")
                    else:
                        st.error(f"❌ Erreur lors de l'envoi : {status}")

    else:
        st.info("Chargement des données...")

except Exception as e:
    st.error("Erreur technique")
    st.write(e)
