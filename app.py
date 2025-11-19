import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- CONFIGURATION DE LA PAGE (FULL SCREEN) ---
st.set_page_config(
    page_title="Raptors War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# --- DESIGN SYSTEM (CSS ULTRA PREMIUM) ---
st.markdown("""
<style>
    /* Importation Font Sportive 'Oswald' & 'Inter' */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Oswald:wght@400;500;700&display=swap');

    /* RESET & BACKGROUND */
    .stApp {
        background-color: #09090b; /* Noir Profond */
        background-image: radial-gradient(circle at 50% 0%, #1f050a 0%, #09090b 40%);
        font-family: 'Inter', sans-serif;
        color: #E4E4E7;
    }

    /* TYPOGRAPHIE */
    h1, h2, h3 {
        font-family: 'Oswald', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
    }
    
    h1 { color: #FFFFFF; font-size: 3.5rem; text-shadow: 0 0 20px rgba(206, 17, 65, 0.6); }
    h2 { color: #CE1141; border-bottom: 2px solid #CE1141; padding-bottom: 10px; margin-top: 40px; }
    h3 { color: #A1A1AA; font-size: 1.2rem; }

    /* CUSTOM KPI CARDS (LE SECRET DU DESIGN) */
    .kpi-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px -10px rgba(206, 17, 65, 0.5);
        border-color: #CE1141;
    }
    .kpi-title { font-size: 0.9rem; color: #71717A; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 5px; }
    .kpi-value { font-family: 'Oswald', sans-serif; font-size: 2.5rem; font-weight: 700; color: #FFFFFF; }
    .kpi-sub { font-size: 0.8rem; color: #CE1141; font-weight: 600; }

    /* TABLEAUX STYLISÉS */
    .dataframe { font-family: 'Inter', sans-serif; font-size: 0.9rem; }
    div[data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #27272A;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #27272A;
    }
    
    /* PLOTLY CHARTS TRANSPARENTS */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS (HTML INJECTION) ---
def display_kpi(title, value, subtext=""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
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
    except:
        return pd.DataFrame()

# --- MAIN APP ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        leader_name = df.groupby('Player')['Score'].sum().idxmax()
        leader_score = df.groupby('Player')['Score'].sum().max()
        
        # --- SIDEBAR NAVIGATION ---
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png", width=180)
            st.markdown("### RAPTORS ELITE")
            
            selected = option_menu(
                menu_title=None,
                options=["War Room", "Analytics", "Roster", "Admin"],
                icons=["speedometer", "graph-up-arrow", "people", "shield-lock"],
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"color": "#CE1141", "font-size": "18px"}, 
                    "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#1F1F23"},
                    "nav-link-selected": {"background-color": "#1F1F23", "border-left": "4px solid #CE1141"},
                }
            )
            st.markdown(f"<br><div style='text-align:center; color:#555; font-size:12px'>Pick #{int(latest_pick)}</div>", unsafe_allow_html=True)

        # --- PAGE: WAR ROOM (DASHBOARD) ---
        if selected == "War Room":
            # HERO SECTION
            st.markdown(f"""
            <div style="padding: 20px 0;">
                <h1>RAPTORS <span style="color:#CE1141">WAR ROOM</span></h1>
                <p style="color:#A1A1AA; font-size: 1.2rem;">Performance Report • Pick #{int(latest_pick)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # KPI CARDS (HTML INJECTION)
            top_player = day_df.iloc[0]
            avg_score = day_df['Score'].mean()
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: display_kpi("MVP du Jour", f"{top_player['Player']}", f"{int(top_player['Score'])} PTS")
            with c2: display_kpi("Moyenne Équipe", f"{int(avg_score)}", "POINTS")
            with c3: display_kpi("Maillot Jaune", f"{leader_name}", f"{int(leader_score)} PTS")
            with c4: display_kpi("Pick Rate", f"{len(day_df)}", "JOUEURS ACTIFS")
            
            st.markdown("---")
            
            # MAIN CHART & TABLE
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                st.markdown("## 📈 DYNAMIQUE DE SAISON")
                df_sorted = df.sort_values('Pick')
                df_sorted['Cumul'] = df_sorted.groupby('Player')['Score'].cumsum()
                
                # Default selection: Top 5 overall
                top_5_players = df.groupby('Player')['Score'].sum().nlargest(5).index.tolist()
                
                fig = px.line(
                    df_sorted[df_sorted['Player'].isin(top_5_players)], 
                    x='Pick', y='Cumul', color='Player',
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    height=450
                )
                # Styling Plotly to match Dark Theme
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#A1A1AA', family="Inter"),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor='#27272A'),
                    legend=dict(orientation="h", y=1.1, x=0)
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_table:
                st.markdown("## 📊 TOP DU JOUR")
                # Stylized table
                podium = day_df[['Player', 'Score']].head(10).reset_index(drop=True)
                podium.index += 1
                st.dataframe(
                    podium, 
                    use_container_width=True,
                    column_config={
                        "Score": st.column_config.ProgressColumn(
                            "Score", format="%d", min_value=0, max_value=int(podium['Score'].max() * 1.1),
                            width="medium"
                        )
                    },
                    height=450
                )

        # --- PAGE: ANALYTICS (STATS AVANCEES) ---
        elif selected == "Analytics":
            st.markdown("## 🧠 DEEP DIVE ANALYTICS")
            
            # Scatter Plot: Moyenne vs Régularité
            stats = df.groupby('Player')['Score'].agg(['mean', 'std', 'sum', 'count']).reset_index()
            stats.columns = ['Joueur', 'Moyenne', 'Volatilité', 'Total', 'Matchs']
            
            fig = px.scatter(
                stats, x='Moyenne', y='Volatilité', size='Total', color='Joueur',
                hover_name='Joueur', text='Joueur', size_max=40,
                title="Performance vs Régularité (Taille = Score Total)",
                height=600
            )
            fig.update_traces(textposition='top center')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#A1A1AA'),
                xaxis=dict(showgrid=True, gridcolor='#27272A', title="Moyenne de points"),
                yaxis=dict(showgrid=True, gridcolor='#27272A', title="Volatilité (Ecart-Type)"),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- PAGE: ROSTER (FACE A FACE) ---
        elif selected == "Roster":
            st.markdown("## ⚔️ HEAD TO HEAD")
            
            players = sorted(df['Player'].unique())
            c1, c2 = st.columns(2)
            p1 = c1.selectbox("Joueur A", players, index=0)
            p2 = c2.selectbox("Joueur B", players, index=1)
            
            if p1 and p2:
                # Get Stats
                s1 = df[df['Player'] == p1]['Score']
                s2 = df[df['Player'] == p2]['Score']
