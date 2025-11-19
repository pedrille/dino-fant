import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import requests
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.let_it_rain import rain

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Raptors FR - War Room",
    layout="wide",
    page_icon="🦖",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ (LOOK RAPTORS) ---
st.markdown("""
<style>
    /* Fond sombre et accents rouges */
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: #CE1141 !important; font-family: 'Impact', sans-serif; }
    .stMetricValue { color: #FFFFFF !important; }
    
    /* Style des cartes de stats */
    div[data-testid="metric-container"] {
        background-color: #1F2937;
        border: 1px solid #374151;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Badge Styles */
    .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
    .badge-gold { background-color: #FFD700; color: black; }
    .badge-brick { background-color: #5c2a2a; color: white; }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---

def get_medal(rank):
    if rank == 1: return "🥇"
    if rank == 2: return "🥈"
    if rank == 3: return "🥉"
    return f"{rank}."

def calculate_advanced_stats(df):
    """Calcule des stats avancées pour chaque joueur."""
    stats = []
    players = df['Player'].unique()
    
    for player in players:
        p_data = df[df['Player'] == player]
        scores = p_data['Score']
        
        total_score = scores.sum()
        avg_score = scores.mean()
        matches_played = len(scores)
        best_score = scores.max()
        worst_score = scores.min()
        
        # Stats funs
        bricks = len(scores[scores < 20]) # Nombre de fois sous 20 pts
        bombs = len(scores[scores >= 45]) # Nombre de fois au dessus de 45 pts
        
        stats.append({
            'Joueur': player,
            'Total Pts': int(total_score),
            'Moyenne': round(avg_score, 1),
            'Matchs': matches_played,
            'Best': int(best_score),
            'Worst': int(worst_score),
            '🧱 Briques': bricks,
            '💣 Bombes': bombs
        })
        
    return pd.DataFrame(stats).sort_values('Total Pts', ascending=False).reset_index(drop=True)

# --- CHARGEMENT DES DONNÉES (Même logique robuste) ---
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

# --- FONCTION DISCORD ---
def send_discord_summary(top_player, avg_score, pick_num, total_points):
    if "DISCORD_WEBHOOK" not in st.secrets:
        st.error("Webhook manquant")
        return False
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    message = {
        "username": "Raptors Bot 🦖",
        "embeds": [{
            "title": f"🦖 DEBRIEF - Pick {int(pick_num)}",
            "description": "Les résultats sont tombés !",
            "color": 13504833,
            "fields": [
                {"name": "👑 MVP", "value": f"**{top_player['Player']}**\nScore: `{int(top_player['Score'])}`", "inline": True},
                {"name": "📊 Équipe", "value": f"Moyenne: `{int(avg_score)}`\nTotal: `{int(total_points)}`", "inline": True},
                {"name": "🔗 War Room", "value": "[Voir le Dashboard Complet](https://ttfl-raptors.streamlit.app)", "inline": False}
            ],
            "footer": {"text": "We The North!"}
        }]
    }
    try:
        requests.post(webhook_url, json=message)
        return True
    except:
        return False

# --- MAIN APP ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        
        # Calcul des stats globales
        global_stats = calculate_advanced_stats(df)
        leader_season = global_stats.iloc[0]
        
        # --- SIDEBAR (Navigation) ---
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/36/Toronto_Raptors_logo.svg/1200px-Toronto_Raptors_logo.svg.png", width=100)
            st.title(f"Pick #{int(latest_pick)}")
            
            st.write("---")
            st.header("🛠️ Admin")
            if st.button("📢 Envoyer Rapport Discord"):
                with st.spinner("Transmission..."):
                    total_day_score = day_df['Score'].sum()
                    if send_discord_summary(day_df.iloc[0], day_df['Score'].mean(), latest_pick, total_day_score):
                        st.success("Envoyé !")
                    else:
                        st.error("Échec")

        # --- ONGLET 1 : DAILY RECAP (L'Essentiel) ---
        tab1, tab2, tab3 = st.tabs(["🔥 Daily Recap", "📊 Stats Avancées", "🏆 Hall of Fame"])
        
        with tab1:
            # Header dynamique
            if not day_df.empty:
                top_player = day_df.iloc[0]
                
                # Animation Confettis si score > 50
                if top_player['Score'] >= 50:
                    rain(emoji="🔥", font_size=54, falling_speed=5, animation_length="1s")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Meilleur Score", f"{int(top_player['Score'])}", f"{top_player['Player']}")
                col2.metric("Moyenne Équipe", f"{int(day_df['Score'].mean())}")
                col3.metric("Total Équipe", f"{int(day_df['Score'].sum())}")
                col4.metric("Leader Saison", f"{leader_season['Joueur']}", f"{int(leader_season['Total Pts'])}")
                style_metric_cards(background_color="#1F2937", border_left_color="#CE1141")
                
                st.write("---")
                
                # Podium du jour
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.subheader("Le Podium du Jour")
                    podium_df = day_df.head(3).copy()
                    podium_df['Rang'] = ["🥇", "🥈", "🥉"]
                    st.dataframe(
                        podium_df[['Rang', 'Player', 'Score']].set_index('Rang'),
                        use_container_width=True,
                        column_config={"Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100)}
                    )
                
                with c2:
                    st.subheader("🧱 Le Mur des Briques")
                    flops = day_df[day_df['Score'] < 25].sort_values('Score')
                    if not flops.empty:
                        for _, row in flops.iterrows():
                            st.error(f"**{row['Player']}** : {int(row['Score'])} pts")
                    else:
                        st.success("Aucune brique aujourd'hui ! 💪")

        # --- ONGLET 2 : STATS AVANCÉES (Pour les nerds) ---
        with tab2:
            st.subheader("Analyse de l'Équipe")
            
            # Graphique de course
            df_sorted = df.sort_values('Pick')
            df_sorted['Cumul'] = df_sorted.groupby('Player')['Score'].cumsum()
            
            players_list = df['Player'].unique()
            selected_players = st.multiselect("Comparer les joueurs :", players_list, default=players_list[:5])
            
            if selected_players:
                fig = px.line(
                    df_sorted[df_sorted['Player'].isin(selected_players)], 
                    x='Pick', y='Cumul', color='Player', markers=True,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#333")
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.write("---")
            
            # Tableau détaillé
            st.subheader("Tableau de Bord Complet")
            
            # On utilise le dataframe calculé plus haut
            st.dataframe(
                global_stats,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total Pts": st.column_config.NumberColumn(format="%d pts"),
                    "Moyenne": st.column_config.NumberColumn(format="%.1f pts"),
                    "🧱 Briques": st.column_config.NumberColumn(help="Scores inférieurs à 20"),
                    "💣 Bombes": st.column_config.NumberColumn(help="Scores supérieurs à 45"),
                }
            )

        # --- ONGLET 3 : HALL OF FAME (Awards) ---
        with tab3:
            st.subheader("🏆 Les Trophées de la Saison")
            
            # Calcul des awards
            sniper = global_stats.sort_values('Moyenne', ascending=False).iloc[0]
            macon = global_stats.sort_values('🧱 Briques', ascending=False).iloc[0]
            bomber = global_stats.sort_values('💣 Bombes', ascending=False).iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"🎯 **Le Sniper**\n\n**{sniper['Joueur']}**\n\nMeilleure Moyenne : {sniper['Moyenne']}")
            
            with col2:
                st.warning(f"💣 **L'Artificier**\n\n**{bomber['Joueur']}**\n\n{bomber['💣 Bombes']} scores > 45")
                
            with col3:
                st.error(f"🧱 **Le Maçon**\n\n**{macon['Joueur']}**\n\n{macon['🧱 Briques']} scores < 20")
            
            st.write("---")
            st.markdown("*Les trophées sont calculés automatiquement sur l'ensemble des picks joués.*")

    else:
        st.warning("En attente de données...")

except Exception as e:
    st.error("Erreur critique")
    st.expander("Logs").write(e)
