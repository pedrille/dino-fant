import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_extras.metric_cards import style_metric_cards

# --- CONFIGURATION DE LA PAGE (FULL SCREEN) ---
st.set_page_config(
    page_title="Raptors Elite",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (LE DESIGN "ULTRA PRO") ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&family=Roboto:wght@300;400;700&display=swap');

    /* Structure Principale */
    .stApp {
        background-color: #0E0E0E;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Titres style Sportif */
    h1, h2, h3, h4 {
        font-family: 'Oswald', sans-serif !important;
        text-transform: uppercase;
        color: #FFFFFF;
        letter-spacing: 1px;
    }
    
    /* Couleur Raptors */
    .highlight { color: #CE1141; }
    
    /* Cartes Métriques Custom */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #1a1a1a, #222222);
        border-left: 5px solid #CE1141;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: scale(1.02);
    }
    
    /* Tableaux Pro */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #050505;
    }
    
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS DATA (ROBUSTES) ---
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        if "SPREADSHEET_URL" not in st.secrets:
            st.error("URL manquante")
            st.stop()
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

    except Exception as e:
        st.error(f"Erreur data : {e}")
        return pd.DataFrame()

def get_player_stats(df, player_name):
    p_data = df[df['Player'] == player_name].sort_values('Pick')
    if len(p_data) >= 5:
        last_5 = p_data.tail(5)['Score'].mean()
    else:
        last_5 = p_data['Score'].mean()
    total = p_data['Score'].sum()
    avg = p_data['Score'].mean()
    best = p_data['Score'].max()
    return total, avg, best, last_5

# --- FONCTIONS UI ---

def show_dashboard(df, latest_pick, day_df, leader_season):
    st.markdown(f"## 🦖 DASHBOARD <span class='highlight'>PICK {int(latest_pick)}</span>", unsafe_allow_html=True)
    
    # Top KPI Row
    top_player = day_df.iloc[0]
    avg_score = day_df['Score'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("MVP DU JOUR", f"{top_player['Player']}", f"{int(top_player['Score'])} pts")
    col2.metric("MOYENNE ÉQUIPE", f"{int(avg_score)}", delta=None)
    col3.metric("LEADER SAISON", f"{leader_season['Player']}", f"{int(leader_season['Total'])}")
    col4.metric("RECORD SAISON", f"{int(df['Score'].max())}", "Points")
    style_metric_cards(background_color="#1A1A1A", border_left_color="#CE1141")
    
    st.write("---")

    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("📈 PERFORMANCE DU JOUR")
        # Bar chart stylisé
        fig = px.bar(
            day_df, x='Score', y='Player', orientation='h', text='Score',
            color='Score', color_continuous_scale=['#5c2a2a', '#CE1141']
        )
        fig.update_traces(textposition='outside', marker_line_width=0)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='white', xaxis=dict(showgrid=False, visible=False),
            yaxis=dict(autorange="reversed"), height=500, margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("🔥 HOT & COLD")
        # Forme sur 5 matchs
        df_sorted = df.sort_values('Pick')
        last_5_avg = df_sorted.groupby('Player').tail(5).groupby('Player')['Score'].mean().sort_values(ascending=False)
        
        st.markdown("**En Feu (Moy. 5 derniers)**")
        for p, score in last_5_avg.head(3).items():
            st.markdown(f"🔥 **{p}** : `{score:.1f}`")
            
        st.markdown("---")
        st.markdown("**Dans le Dur**")
        for p, score in last_5_avg.tail(3).items():
            st.markdown(f"❄️ **{p}** : `{score:.1f}`")

def show_standings(df):
    st.markdown("## 🏆 CLASSEMENT GÉNÉRAL")
    
    total_scores = df.groupby('Player')['Score'].sum().sort_values(ascending=False).reset_index()
    total_scores.columns = ['Joueur', 'Total Points']
    
    # On ajoute des stats
    stats = df.groupby('Player')['Score'].agg(['mean', 'max', 'count']).reset_index()
    stats.columns = ['Joueur', 'Moyenne', 'Best', 'Matchs']
    
    final_table = pd.merge(total_scores, stats, on='Joueur')
    final_table['Rang'] = final_table.index + 1
    
    # Reorder columns
    final_table = final_table[['Rang', 'Joueur', 'Total Points', 'Moyenne', 'Best', 'Matchs']]

    st.dataframe(
        final_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total Points": st.column_config.ProgressColumn(
                "Total Points", format="%d", min_value=0, max_value=final_table['Total Points'].max(),
            ),
            "Moyenne": st.column_config.NumberColumn(format="%.1f"),
            "Rang": st.column_config.NumberColumn(format="#%d", width="small")
        },
        height=600
    )

def show_versus(df):
    st.markdown("## ⚔️ FACE À FACE")
    
    players = sorted(df['Player'].unique())
    col1, col2 = st.columns(2)
    
    with col1:
        p1 = st.selectbox("Joueur A", players, index=0)
    with col2:
        p2 = st.selectbox("Joueur B", players, index=1)
        
    if p1 and p2:
        df_p1 = df[df['Player'] == p1].sort_values('Pick')
        df_p2 = df[df['Player'] == p2].sort_values('Pick')
        
        # Stats Comparatives
        t1, a1, b1, f1 = get_player_stats(df, p1)
        t2, a2, b2, f2 = get_player_stats(df, p2)
        
        # Radar Chart ou KPI cote a cote
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", int(t1), delta=int(t1-t2))
        c2.metric("Moyenne", round(a1, 1), delta=round(a1-a2, 1))
        c3.metric("Best Pick", int(b1), delta=int(b1-b2))
        c4.metric("Forme (5j)", round(f1, 1), delta=round(f1-f2, 1))
        
        st.write("---")
        
        # Graphique comparatif
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_p1['Pick'], y=df_p1['Score'], mode='lines+markers', name=p1, line=dict(color='#CE1141', width=3)))
        fig.add_trace(go.Scatter(x=df_p2['Pick'], y=df_p2['Score'], mode='lines+markers', name=p2, line=dict(color='#FFFFFF', width=2, dash='dot')))
        
        fig.update_layout(
            title="Historique des Scores",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='white', xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#333')
        )
        st.plotly_chart(fig, use_container_width=True)

# --- APP PRINCIPALE ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        leader_name = df.groupby('Player')['Score'].sum().idxmax()
        leader_score = df.groupby('Player')['Score'].sum().max()
        leader = {'Player': leader_name, 'Total': leader_score}

        # --- SIDEBAR NAVIGATION ---
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png", width=150)
            
            selected = option_menu(
                "Raptors Elite",
                ["Dashboard", "Classement", "Face-à-Face", "Admin"],
                icons=['speedometer2', 'trophy', 'people', 'gear'],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#050505"},
                    "icon": {"color": "white", "font-size": "18px"}, 
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#333"},
                    "nav-link-selected": {"background-color": "#CE1141"},
                }
            )
            
            st.markdown(f"<div style='text-align: center; color: grey; font-size: 12px;'>Last Pick: {int(latest_pick)}</div>", unsafe_allow_html=True)

        # --- ROUTING ---
        if selected == "Dashboard":
            show_dashboard(df, latest_pick, day_df, leader)
            
        elif selected == "Classement":
            show_standings(df)
            
        elif selected == "Face-à-Face":
            show_versus(df)
            
        elif selected == "Admin":
            st.title("⚙️ ADMINISTRATION")
            st.info("Utilisez ce bouton uniquement lorsque le fichier Excel est complet pour la journée.")
            if st.button("📢 Diffuser sur Discord"):
                # (Insérer la fonction d'envoi Discord ici si besoin)
                st.success("Fonctionnalité prête")

    else:
        st.warning("Chargement des données...")

except Exception as e:
    st.error("Erreur Critique")
    st.expander("Détails").write(e)
