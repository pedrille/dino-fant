import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import numpy as np

# --- 1. CONFIGURATION (FULL IMMERSION) ---
st.set_page_config(
    page_title="Raptors Infinity",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS "PIXEL PERFECT" (CLEAN & AIRY) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700&display=swap');

    /* RESET & BASE */
    .stApp {
        background-color: #050505;
        font-family: 'Inter', sans-serif;
        color: #F3F4F6;
    }
    
    /* ESPACEMENT & STRUCTURE */
    .block-container { padding-top: 2rem; padding-bottom: 5rem; max-width: 1400px; }
    div[data-testid="column"] { gap: 1rem; }
    
    /* TYPOGRAPHIE */
    h1, h2, h3 { font-family: 'Rajdhani', sans-serif; letter-spacing: 0.5px; text-transform: uppercase; }
    h1 { font-size: 3.5rem; font-weight: 700; background: linear-gradient(to right, #fff, #666); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
    h2 { font-size: 1.4rem; color: #CE1141; margin-top: 3rem; margin-bottom: 1.5rem; display: flex; align-items: center; }
    h2::before { content: ''; display: inline-block; width: 6px; height: 24px; background: #CE1141; margin-right: 12px; border-radius: 2px; }
    
    /* CARTES KPI (GLASSMORPHISM V2 - PLUS SUBTIL) */
    .kpi-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover { border-color: #CE1141; transform: translateY(-2px); }
    .kpi-label { font-size: 0.8rem; color: #9CA3AF; font-weight: 500; letter-spacing: 1px; }
    .kpi-val { font-family: 'Rajdhani'; font-size: 2.8rem; font-weight: 700; color: white; line-height: 1; }
    .kpi-sub { font-size: 0.85rem; color: #CE1141; font-weight: 600; }

    /* TABLES CLEAN */
    div[data-testid="stDataFrame"] { border: none !important; }
    div[data-testid="stDataFrame"] table { background: transparent !important; }
    
    /* CUSTOM WIDGETS */
    .stSelectbox > div > div { background-color: #111; border: 1px solid #333; }
    .stMultiSelect > div > div { background-color: #111; border: 1px solid #333; }
    
    /* PLOTLY CLEANUP */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }

</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
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

def get_stats(df):
    stats = []
    for p in df['Player'].unique():
        d = df[df['Player'] == p]
        scores = d['Score']
        stats.append({
            'Player': p,
            'Total': scores.sum(),
            'Moyenne': scores.mean(),
            'Best': scores.max(),
            'Last5': scores.tail(5).mean() if len(scores) >= 5 else scores.mean(),
            'Regularity': 100 - scores.std() # Metric simple inverse écart type
        })
    return pd.DataFrame(stats)

# --- 4. UI COMPONENTS ---
def card(label, value, sub):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-val">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APP ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        all_stats = get_stats(df)
        leader = all_stats.sort_values('Total', ascending=False).iloc[0]

        # --- SIDEBAR ---
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png", width=120)
            selected = option_menu(
                menu_title=None,
                options=["Dashboard", "Analytics", "Admin"],
                icons=["grid-1x2", "graph-up", "gear"],
                default_index=0,
                styles={
                    "container": {"background-color": "transparent"},
                    "nav-link-selected": {"background-color": "#CE1141", "color": "white"}
                }
            )
            st.markdown(f"<div style='text-align:center; color:#555; font-size:12px; margin-top:20px'>PICK #{int(latest_pick)}</div>", unsafe_allow_html=True)

        if selected == "Dashboard":
            # HEADER
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"<h1>RAPTORS <span style='color:#CE1141'>INFINITY</span></h1>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#888; margin-top:-10px'>Live Performance Tracking • Pick {int(latest_pick)}</p>", unsafe_allow_html=True)
            
            # KPI ROW
            k1, k2, k3, k4 = st.columns(4)
            top_p = day_df.iloc[0]
            with k1: card("MVP DU JOUR", f"{top_p['Player']}", f"{int(top_p['Score'])} PTS")
            with k2: card("MOYENNE TEAM", f"{int(day_df['Score'].mean())}", "POINTS")
            with k3: card("MAILLOT JAUNE", f"{leader['Player']}", f"{int(leader['Total'])} PTS")
            with k4: card("RECORD SAISON", f"{int(df['Score'].max())}", "POINTS")

            # --- SECTION 1: DYNAMIQUE (CHART AVEC ZOOM) ---
            st.markdown("<h2>📈 DYNAMIQUE & COURBES</h2>", unsafe_allow_html=True)
            
            # Controls
            col_ctrl1, col_ctrl2 = st.columns([1, 3])
            with col_ctrl1:
                time_range = st.radio("Période", ["7 Derniers Jours", "Saison Complète"], horizontal=True, label_visibility="collapsed")
            with col_ctrl2:
                # Select All Logic
                all_players = df['Player'].unique().tolist()
                container = st.container()
                all_selected = st.checkbox("Sélectionner tout le monde", value=False)
                
                if all_selected:
                    default_sel = all_players
                else:
                    # Par défaut Top 5 du classement général
                    default_sel = all_stats.sort_values('Total', ascending=False).head(5)['Player'].tolist()
                
                selection = st.multiselect("Joueurs", all_players, default=default_sel, label_visibility="collapsed")

            # Data Filter
            df_chart = df.sort_values('Pick').copy()
            df_chart['Cumul'] = df_chart.groupby('Player')['Score'].cumsum()
            
            if time_range == "7 Derniers Jours":
                min_pick = max(1, latest_pick - 6)
                df_chart = df_chart[df_chart['Pick'] >= min_pick]
                # Pour le graphique 7 jours, on montre le score brut, pas le cumul, c'est plus pertinent pour la forme
                y_axis = 'Score'
                title_chart = "Scores par Match (7 derniers jours)"
            else:
                y_axis = 'Cumul'
                title_chart = "Course au Total (Saison)"

            if selection:
                fig = px.line(
                    df_chart[df_chart['Player'].isin(selection)], 
                    x='Pick', y=y_axis, color='Player',
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    markers=True
                )
                fig.update_layout(
                    height=450,
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#9CA3AF', family='Inter'),
                    xaxis=dict(showgrid=False, gridcolor='#222', title=None),
                    yaxis=dict(showgrid=True, gridcolor='#222', title=None),
                    legend=dict(orientation="h", y=1.1, x=0, title=None),
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

            # --- SECTION 2: HEATMAP & RADAR ---
            c_heat, c_radar = st.columns([2, 1])
            
            with c_heat:
                st.markdown("<h2>🔥 HEATMAP DE FORME (LAST 10)</h2>", unsafe_allow_html=True)
                # Préparation Data Heatmap
                min_pick_heat = max(1, latest_pick - 9)
                df_heat = df[df['Pick'] >= min_pick_heat].pivot(index='Player', columns='Pick', values='Score')
                # Sort by Total recent
                df_heat['Total'] = df_heat.sum(axis=1)
                df_heat = df_heat.sort_values('Total', ascending=True).drop('Total', axis=1)
                
                fig_heat = px.imshow(
                    df_heat, 
                    text_auto=True, 
                    aspect="auto",
                    color_continuous_scale=['#1a1a1a', '#CE1141'], # Noir vers Rouge Raptors
                    origin='lower'
                )
                fig_heat.update_layout(
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#9CA3AF'),
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(side="top")
                )
                fig_heat.update_traces(showscale=False) # Cacher la barre de couleur pour le clean
                st.plotly_chart(fig_heat, use_container_width=True)

            with c_radar:
                st.markdown("<h2>⚡ PROFILS (TOP 5)</h2>", unsafe_allow_html=True)
                # Radar Chart pour le Top 5
                top5_stats = all_stats.sort_values('Total', ascending=False).head(5)
                
                # Normalisation pour le radar (0-1)
                categories = ['Moyenne', 'Best', 'Last5', 'Regularity']
                
                fig_radar = go.Figure()
                
                for i, row in top5_stats.iterrows():
                    # Simple normalisation maison pour l'exemple visuel
                    values = [
                        row['Moyenne']/60, 
                        row['Best']/80, 
                        row['Last5']/60, 
                        row['Regularity']/100
                    ]
                    
                    fig_radar.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name=row['Player'],
                        opacity=0.4
                    ))

                fig_radar.update_layout(
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, range=[0, 1], showticklabels=False, linecolor='#333'),
                        angularaxis=dict(color='#888')
                    ),
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#ccc'),
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.1)
                )
                st.plotly_chart(fig_radar, use_container_width=True)

        elif selected == "Analytics":
            st.markdown("<h2>📊 DONNÉES BRUTES</h2>", unsafe_allow_html=True)
            
            # Tableau avec Highlight et barres
            st.dataframe(
                all_stats.sort_values('Total', ascending=False),
                use_container_width=True,
                height=800,
                column_config={
                    "Player": "Joueur",
                    "Total": st.column_config.ProgressColumn("Total", format="%d", min_value=0, max_value=int(all_stats['Total'].max())),
                    "Moyenne": st.column_config.NumberColumn("Moy.", format="%.1f"),
                    "Best": st.column_config.NumberColumn("Best", format="%d"),
                    "Last5": st.column_config.LineChartColumn("Forme (5j)"),
                    "Regularity": st.column_config.NumberColumn("Régularité", format="%.0f")
                }
            )

        elif selected == "Admin":
            st.markdown("<h2>⚙️ ZONE ADMIN</h2>", unsafe_allow_html=True)
            st.info("Envoyer le rapport quotidien sur Discord.")
            if st.button("📢 ENVOYER"):
                st.success("Envoyé (Simulation)")

    else:
        st.info("Chargement des données...")

except Exception as e:
    st.error("Erreur technique")
    st.expander("Log").write(e)
