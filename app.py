import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Raptors FR - TTFL", layout="wide", page_icon="🦖")

# --- FONCTION : CHARGER LES DONNÉES ---
@st.cache_data(ttl=600)
def load_data():
    # 1. Récupération du lien
    if "GOOGLE_SHEET_URL" in st.secrets:
        csv_url = st.secrets["GOOGLE_SHEET_URL"]
    else:
        st.error("Lien Google Sheet manquant dans les Secrets !")
        st.stop()
    
    try:
        # 2. Lecture brute du fichier pour trouver les repères
        df_raw = pd.read_csv(csv_url, header=None)
        
        # --- LOGIQUE INTELLIGENTE ---
        # On cherche la ligne qui contient le mot "Pick" dans la première colonne
        # C'est notre point de repère pour les entêtes
        start_row_index = df_raw[df_raw[0].astype(str).str.contains("Pick", case=False, na=False)].index[0]
        
        # La ligne des Picks (1, 2, 3...) est celle juste trouvée
        # On nettoie les valeurs pour qu'elles soient numériques
        picks_row = pd.to_numeric(df_raw.iloc[start_row_index, 1:], errors='coerce')
        
        # Les joueurs commencent à la ligne suivante
        data_start_index = start_row_index + 1
        
        # On cherche la fin (quand on tombe sur "Team Raptors" ou "Score BP")
        # On coupe large par sécurité (50 lignes max après le début)
        df_players = df_raw.iloc[data_start_index:data_start_index+50].copy()
        
        # On nettoie la première colonne (Noms des joueurs)
        df_players = df_players.rename(columns={0: 'Player'})
        
        # Liste des mots qui signalent la fin du tableau des joueurs
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne"]
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)]
        df_players = df_players.dropna(subset=['Player']) # Enlève les lignes vides
        
        # --- RECONSTRUCTION ---
        # On mappe les colonnes des joueurs avec les numéros de Pick trouvés plus haut
        # On crée un dictionnaire {Index_Colonne: Numéro_Pick}
        valid_cols = {}
        for idx, pick_num in picks_row.items():
            if pd.notna(pick_num): # Si c'est un vrai numéro de pick
                valid_cols[idx] = pick_num
                
        # On ne garde que les colonnes valides dans le dataframe des joueurs
        # Colonne 0 (Player) + les colonnes identifiées
        cols_to_keep = [0] + list(valid_cols.keys())
        df_final = df_players.loc[:, cols_to_keep]
        
        # On renomme les colonnes avec les vrais numéros de Pick
        new_col_names = {0: 'Player'}
        new_col_names.update(valid_cols)
        df_final = df_final.rename(columns=new_col_names)

        # Transformation en format long (Player | Pick | Score)
        df_long = df_final.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        
        # Nettoyage final des types
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        
        # On supprime les lignes sans score (futur)
        df_clean = df_long.dropna(subset=['Score', 'Pick'])
        
        return df_clean
        
    except Exception as e:
        st.error(f"Erreur lors de l'analyse du fichier : {e}")
        return pd.DataFrame()

# --- FONCTION : DISCORD ---
def send_discord_summary(top_player, avg_score, pick_num):
    if "DISCORD_WEBHOOK" not in st.secrets:
        st.error("Webhook manquant !")
        return False

    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    message = {
        "username": "Raptors Bot 🦖",
        "embeds": [{
            "title": f"🏀 Récap Pick {int(pick_num)}",
            "color": 13504833,
            "fields": [
                {"name": "🔥 MVP", "value": f"{top_player['Player']} ({int(top_player['Score'])})", "inline": True},
                {"name": "📊 Moyenne", "value": f"{int(avg_score)} pts", "inline": True},
                {"name": "🔗 Lien", "value": "[Voir Dashboard](https://ttfl-raptors.streamlit.app)", "inline": False}
            ]
        }]
    }
    try:
        requests.post(webhook_url, json=message)
        return True
    except:
        return False

# --- INTERFACE ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        
        if not day_df.empty:
            top_player = day_df.iloc[0]
            team_avg = day_df['Score'].mean()

            st.title(f"🦖 RAPTORS FR | PICK {int(latest_pick)}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("MVP", top_player['Player'], f"{int(top_player['Score'])}")
            c2.metric("Moyenne", f"{int(team_avg)}")
            
            total = df.groupby('Player')['Score'].sum().sort_values(ascending=False)
            c3.metric("Leader", total.index[0], f"{int(total.iloc[0])}")
            
            st.divider()
            
            # Graphique
            df = df.sort_values('Pick')
            df['Cumul'] = df.groupby('Player')['Score'].cumsum()
            players = df['Player'].unique()
            sel = st.multiselect("Joueurs", players, default=players[:5])
            if sel:
                st.plotly_chart(px.line(df[df['Player'].isin(sel)], x='Pick', y='Cumul', color='Player'))

            # Admin
            with st.sidebar:
                st.header("Admin")
                if st.button("Envoyer Discord"):
                    if send_discord_summary(top_player, team_avg, latest_pick):
                        st.success("Envoyé !")
        else:
            st.warning("Pas de scores pour ce pick.")
    else:
        st.info("Impossible de lire les données. Vérifiez le lien Secret.")

except Exception as e:
    st.error(f"Erreur globale : {e}")
