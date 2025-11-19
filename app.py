import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Raptors FR - TTFL", layout="wide", page_icon="🦖")

# --- FONCTION DE CHARGEMENT DES DONNÉES (CONNEXION NATIVE) ---
@st.cache_data(ttl=600) # Mise à jour du cache toutes les 10 min
def load_data():
    # Création de la connexion sécurisée avec le robot
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        # Récupération de l'URL depuis les secrets
        if "SPREADSHEET_URL" not in st.secrets:
            st.error("L'URL du Google Sheet manque dans les Secrets Streamlit !")
            st.stop()
            
        url = st.secrets["SPREADSHEET_URL"]

        # Lecture de la feuille "Valeurs" (Nom exact de l'onglet)
        # On lit tout sans header pour scanner le fichier nous-mêmes
        df_raw = conn.read(spreadsheet=url, worksheet="Valeurs", usecols=None, header=None)
        
        # --- ALGORITHME DE NETTOYAGE ROBUSTE ---
        
        # 1. Trouver la ligne des Picks (1, 2, 3...)
        # On cherche la première ligne qui contient le chiffre 1, 2 et 3 dans les colonnes
        # Généralement c'est la ligne index 2 (3ème ligne du fichier)
        pick_row_idx = 2
        
        # On récupère cette ligne pour avoir les numéros de Picks
        picks_series = pd.to_numeric(df_raw.iloc[pick_row_idx, 1:], errors='coerce')
        
        # 2. Isoler les joueurs
        # Les joueurs commencent juste après la ligne des picks
        data_start_idx = pick_row_idx + 1
        
        # On prend une tranche large (50 lignes) pour être sûr d'avoir tout le monde
        df_players = df_raw.iloc[data_start_idx:data_start_idx+50].copy()
        
        # On renomme la première colonne "Player"
        df_players = df_players.rename(columns={0: 'Player'})
        
        # 3. Filtrer les lignes inutiles (Totaux, Scores BP, Lignes vides)
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme", "0 et négatif"]
        # On garde seulement les lignes où 'Player' n'est pas dans la liste interdite
        df_players = df_players[~df_players['Player'].astype(str).isin(stop_words)]
        df_players = df_players.dropna(subset=['Player']) # Enlève les lignes vides

        # 4. Reconstruire le tableau propre
        # On crée un dictionnaire {Index_Colonne: Numéro_Pick}
        valid_cols_map = {}
        for col_idx, pick_num in picks_series.items():
            if pd.notna(pick_num) and pick_num > 0:
                valid_cols_map[col_idx] = int(pick_num)
        
        # On ne garde que les colonnes utiles dans le dataframe joueurs
        cols_to_keep = ['Player'] + list(valid_cols_map.keys())
        # Petite sécurité : vérifier que les colonnes existent bien
        cols_to_keep = [c for c in cols_to_keep if c in df_players.columns]
        
        df_clean = df_players[cols_to_keep].copy()
        
        # On renomme les colonnes (Ex: Colonne 5 devient "Pick 4")
        df_clean = df_clean.rename(columns=valid_cols_map)

        # 5. Transformer en format long (Base de données)
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        
        # Conversion finale des types
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        
        # On supprime les lignes sans score (les jours futurs)
        df_final = df_long.dropna(subset=['Score', 'Pick'])
        
        return df_final

    except Exception as e:
        st.error(f"Erreur lors de la lecture du Google Sheet : {e}")
        return pd.DataFrame()

# --- FONCTION : ENVOI DISCORD ---
def send_discord_summary(top_player, avg_score, pick_num):
    if "DISCORD_WEBHOOK" not in st.secrets:
        st.error("Webhook Discord manquant !")
        return False

    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    
    message = {
        "username": "Raptors Bot 🦖",
        "embeds": [{
            "title": f"🏀 Récap TTFL - Pick {int(pick_num)}",
            "color": 13504833, # Rouge Raptors
            "fields": [
                {"name": "🔥 MVP du Jour", "value": f"**{top_player['Player']}** ({int(top_player['Score'])})", "inline": True},
                {"name": "📊 Moyenne Équipe", "value": f"{int(avg_score)} pts", "inline": True},
                {"name": "🔗 Dashboard", "value": "[Voir les stats complètes](https://ttfl-raptors.streamlit.app)", "inline": False}
            ]
        }]
    }
    
    try:
        requests.post(webhook_url, json=message)
        return True
    except:
        return False

# --- APPLICATION PRINCIPALE ---
try:
    df = load_data()
    
    if not df.empty:
        # Trouver le dernier pick joué
        latest_pick = df['Pick'].max()
        
        # Données du jour
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        
        if not day_df.empty:
            top_player = day_df.iloc[0]
            team_avg = day_df['Score'].mean()
            
            # --- HEADER ---
            st.title(f"🦖 RAPTORS FR | PICK {int(latest_pick)}")
            st.markdown(f"**Mise à jour :** {latest_pick}ème journée")

            # --- KPIs ---
            kpi1, kpi2, kpi3 = st.columns(3)
            
            kpi1.metric("🔥 MVP du Jour", top_player['Player'], f"{int(top_player['Score'])} pts")
            kpi2.metric("📊 Moyenne Équipe", f"{int(team_avg)} pts")
            
            # Calcul Leader Saison
            total_scores = df.groupby('Player')['Score'].sum().sort_values(ascending=False)
            leader_name = total_scores.index[0]
            leader_score = total_scores.iloc[0]
            
            kpi3.metric("👑 Leader Saison", leader_name, f"{int(leader_score)} pts")

            st.divider()

            # --- GRAPHIQUE ---
            st.subheader("📈 La Course au Titre")
            
            # Préparation des données cumulées
            df_sorted = df.sort_values('Pick')
            df_sorted['Cumul'] = df_sorted.groupby('Player')['Score'].cumsum()
            
            # Sélecteur de joueurs
            players_list = df['Player'].unique()
            default_selection = players_list[:5] if len(players_list) > 0 else []
            selection = st.multiselect("Comparer les joueurs :", players_list, default=default_selection)
            
            if selection:
                chart_data = df_sorted[df_sorted['Player'].isin(selection)]
                fig = px.line(chart_data, x='Pick', y='Cumul', color='Player', markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            # --- TABLEAUX ---
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("Classement Général")
                st.dataframe(total_scores, use_container_width=True)
            with c2:
                st.subheader("Scores du Jour")
                st.dataframe(day_df[['Player', 'Score']].set_index('Player'), use_container_width=True)

            # --- SIDEBAR ADMIN ---
            with st.sidebar:
                st.header("⚙️ Zone Admin")
                st.info("Clique ci-dessous une fois le fichier Excel rempli.")
                if st.button("📢 Envoyer sur Discord"):
                    with st.spinner("Envoi en cours..."):
                        if send_discord_summary(top_player, team_avg, latest_pick):
                            st.success("Envoyé avec succès !")
                        else:
                            st.error("Erreur lors de l'envoi.")

        else:
            st.warning("Aucun score trouvé pour le dernier pick.")
    else:
        st.info("Connexion réussie, mais le tableau semble vide ou mal formaté.")

except Exception as e:
    st.error("Une erreur critique est survenue.")
    st.expander("Voir l'erreur").write(e)
