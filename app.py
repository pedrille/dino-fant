import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- 1. CONFIGURATION PAGE (MODE WIDE OBLIGATOIRE) ---
st.set_page_config(
    page_title="Raptors Elite",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="collapsed" # Sidebar fermée par défaut sur mobile pour l'immersion
)

# --- 2. LE COEUR DU DESIGN (CSS RESPONSIVE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Oswald:wght@400;500;700&display=swap');

    /* --- RESET STREAMLIT --- */
    [data-testid="stAppViewContainer"] { background-color: #050505; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    [data-testid="stToolbar"] { display: none; } /* Cache le menu dev */
    div.block-container { padding-top: 2rem; padding-bottom: 5rem; max-width: 1200px; }

    /* --- TYPOGRAPHIE --- */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; }
    h1, h2, h3 { font-family: 'Oswald', sans-serif !important; text-transform: uppercase; }
    h1 { font-size: 3rem; background: linear-gradient(90deg, #FFFFFF, #999); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    h2 { font-size: 1.5rem; border-left: 4px solid #CE1141; padding-left: 10px; margin-top: 30px; margin-bottom: 20px; }
    
    /* --- KPI CARDS RESPONSIVE (GRID SYSTEM) --- */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 15px;
        margin-bottom: 30px;
    }
    .kpi-card {
        background: #111111;
        border: 1px solid #222;
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover { transform: translateY(-3px); border-color: #CE1141; box-shadow: 0 10px 20px rgba(206, 17, 65, 0.15); }
    .kpi-card::after {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 4px;
        background: linear-gradient(90deg, #CE1141, #000);
    }
    .kpi-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-value { font-family: 'Oswald'; font-size: 2.2rem; font-weight: 700; color: white; line-height: 1; }
    .kpi-sub { font-size: 0.85rem; color: #CE1141; margin-top: 5px; font-weight: 600; }

    /* --- TABLEAUX PREMIUM --- */
    [data-testid="stDataFrame"] { border: none; }
    [data-testid="stDataFrame"] table { background-color: #111 !important; }
    
    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #222; }
    
    /* --- BOUTONS --- */
    .stButton button {
        background-color: #CE1141; color: white; border: none; border-radius: 6px;
        font-family: 'Oswald'; text-transform: uppercase; letter-spacing: 1px;
        transition: 0.3s; width: 100%;
    }
    .stButton button:hover { background-color: #ff1e50; box-shadow: 0 0 15px #CE1141; }

</style>
""", unsafe_allow_html=True)

# --- DATA LOADER (ROBUSTE) ---
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets: return pd.DataFrame()
        url = st.secrets["SPREADSHEET_URL"]
        df_raw = conn.read(spreadsheet=url, worksheet="Valeurs", usecols=None, header=None)
        
        pick_row_idx = 2
        picks_series = pd.to_numeric(df_raw.iloc[pick_row_idx, 1:], errors='coerce')
        data_start_idx = pick_row_idx + 1
        df_players = df_raw.iloc[data_start_idx:data_start_idx+50].copy()
        df_players = df_players.rename(columns={0: 'Player'})
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme", "0 et négatif"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)]
        df_players = df_players.dropna(subset=['Player'])

        valid_cols_map = {}
        for col_idx, pick_num in picks_series.items():
            if pd.notna(pick_num) and pick_num > 0:
                valid_cols_map[col_idx] = int(pick_num)
        
        cols_to_keep = ['Player'] + list(valid_cols_map.keys())
        cols_to_keep = [c for c in cols_to_keep if c in df_players.columns]
        df_clean = df_players[cols_to_keep].copy()
        df_clean = df_clean.rename(columns=valid_cols_map)
        
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        return df_long.dropna(subset=['Score', 'Pick'])
    except: return pd.DataFrame()

def get_player_stats(df, player_name):
    p_data = df[df['Player'] == player_name].sort_values('Pick')
    last_5 = p_data.tail(5)['Score'].mean() if len(p_data) >= 5 else p_data['Score'].mean()
    return p_data['Score'].sum(), p_data['Score'].mean(), p_data['Score'].max(), last_5

# --- APP LOGIC ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        
        # --- SIDEBAR NAVIGATION ---
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png", width=140)
            st.markdown("<br>", unsafe_allow_html=True)
            
            selected = option_menu(
                menu_title=None,
                options=["Dashboard", "Classement", "Versus", "Admin"],
                icons=["grid-fill", "trophy-fill", "lightning-charge-fill", "gear-fill"],
                default_index=0,
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "#CE1141", "font-size": "16px"}, 
                    "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "color": "#888"},
                    "nav-link-selected": {"background-color": "#1A1A1A", "color": "white", "border-left": "3px solid #CE1141"},
                }
            )
            
            st.markdown(f"<div style='position:fixed; bottom:20px; color:#444; font-size:10px; padding-left:10px;'>PICK #{int(latest_pick)} EN COURS</div>", unsafe_allow_html=True)

        # --- PAGE 1: DASHBOARD ---
        if selected == "Dashboard":
            st.markdown(f"<h1>RAPTORS <span style='color:#CE1141'>ELITE</span></h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#666; margin-top:-15px; margin-bottom:30px'>Rapport de performance • Journée {int(latest_pick)}</p>", unsafe_allow_html=True)

            # KPI GRID (HTML/CSS RESPONSIVE)
            top = day_df.iloc[0]
            avg = day_df['Score'].mean()
            leader = df.groupby('Player')['Score'].sum().sort_values(ascending=False).index[0]
            leader_score = df.groupby('Player')['Score'].sum().max()
            
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-card">
                    <div class="kpi-label">🔥 MVP du Jour</div>
                    <div class="kpi-value">{top['Player']}</div>
                    <div class="kpi-sub">{int(top['Score'])} PTS</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">📊 Moyenne Équipe</div>
                    <div class="kpi-value">{int(avg)}</div>
                    <div class="kpi-sub">POINTS</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">👑 Leader Saison</div>
                    <div class="kpi-value">{leader}</div>
                    <div class="kpi-sub">{int(leader_score)} PTS</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">📈 Joueurs Actifs</div>
                    <div class="kpi-value">{len(day_df)}</div>
                    <div class="kpi-sub">PARTICIPANTS</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # CHART & TOP 5
            c1, c2 = st.columns([2, 1]) # Sur mobile, ça va stacker automatiquement grâce au layout 'wide' un peu forcé
            
            with c1:
                st.markdown("## Dynamique")
                df_sorted = df.sort_values('Pick')
                df_sorted['Cumul'] = df_sorted.groupby('Player')['Score'].cumsum()
                top5 = df.groupby('Player')['Score'].sum().nlargest(5).index
                
                fig = px.line(
                    df_sorted[df_sorted['Player'].isin(top5)], 
                    x='Pick', y='Cumul', color='Player',
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    height=400
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#888'}, margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#222'),
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            with c2:
                st.markdown("## Top Performance")
                # Custom HTML Table pour le look "Widget"
                html_table = """<table style='width:100%; border-collapse:collapse; color:#eee;'>"""
                for i, row in day_df.head(7).reset_index().iterrows():
                    rank_color = "#CE1141" if i==0 else "#444"
                    html_table += f"""
                    <tr style='border-bottom:1px solid #222; height:45px;'>
                        <td style='width:30px; color:{rank_color}; font-weight:bold;'>#{i+1}</td>
                        <td style='font-weight:500;'>{row['Player']}</td>
                        <td style='text-align:right; font-family:Oswald; font-size:1.1em;'>{int(row['Score'])}</td>
                    </tr>"""
                html_table += "</table>"
                st.markdown(f"<div style='background:#111; padding:15px; border-radius:10px; border:1px solid #222'>{html_table}</div>", unsafe_allow_html=True)

        # --- PAGE 2: CLASSEMENT ---
        elif selected == "Classement":
            st.markdown("<h2>CLASSEMENT GÉNÉRAL</h2>", unsafe_allow_html=True)
            
            total = df.groupby('Player')['Score'].sum().sort_values(ascending=False).reset_index()
            total.index += 1
            total.columns = ['Joueur', 'Total Points']
            
            # Configuration du tableau natif Streamlit mais stylisé
            st.dataframe(
                total, 
                use_container_width=True, 
                height=600,
                column_config={
                    "Total Points": st.column_config.ProgressColumn(
                        "Score", format="%d", min_value=0, max_value=int(total['Total Points'].max()),
                    )
                }
            )

        # --- PAGE 3: VERSUS ---
        elif selected == "Versus":
            st.markdown("<h2>FACE À FACE</h2>", unsafe_allow_html=True)
            players = sorted(df['Player'].unique())
            
            col_sel1, col_sel2 = st.columns(2)
            p1 = col_sel1.selectbox("Joueur A", players, index=0, label_visibility="collapsed")
            p2 = col_sel2.selectbox("Joueur B", players, index=1, label_visibility="collapsed")
            
            if p1 and p2:
                t1, a1, b1, f1 = get_player_stats(df, p1)
                t2, a2, b2, f2 = get_player_stats(df, p2)
                
                # Comparaison visuelle (HTML Grid)
                st.markdown(f"""
                <div style='display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-top:20px;'>
                    <div style='background:#111; padding:20px; border-radius:10px; border-left:4px solid #CE1141; text-align:center;'>
                        <h3 style='margin:0; color:white;'>{p1}</h3>
                        <div style='font-size:2.5em; font-family:Oswald; color:#CE1141; margin:10px 0;'>{int(t1)}</div>
                        <div style='color:#666; font-size:0.9em;'>TOTAL POINTS</div>
                    </div>
                    <div style='background:#111; padding:20px; border-radius:10px; border-right:4px solid #fff; text-align:center;'>
                        <h3 style='margin:0; color:white;'>{p2}</h3>
                        <div style='font-size:2.5em; font-family:Oswald; color:white; margin:10px 0;'>{int(t2)}</div>
                        <div style='color:#666; font-size:0.9em;'>TOTAL POINTS</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Comparaison détaillée
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                c1.metric("Moyenne", f"{a1:.1f}", f"{a1-a2:.1f}")
                c2.metric("Record", f"{int(b1)}", f"{int(b1-b2)}")
                c3.metric("Forme (5j)", f"{f1:.1f}", f"{f1-f2:.1f}")

        # --- PAGE 4: ADMIN ---
        elif selected == "Admin":
            st.markdown("<h2>ZONE ADMIN</h2>", unsafe_allow_html=True)
            st.warning("⚠️ Cette section envoie une notification à toute l'équipe.")
            if st.button("📢 ENVOYER LE RÉCAP DISCORD"):
                st.success("Simulation d'envoi effectuée.")

    else:
        st.info("Initialisation de la base de données...")

except Exception as e:
    st.error(f"Erreur: {e}")
