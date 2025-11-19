import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Raptors FR - TTFL", layout="wide", page_icon="🦖")

# --- FONCTION : CHARGER LES DONNÉES ---
@st.cache_data(ttl=600) # Mise à jour toutes les 10 min
def load_data():
    # On récupère le lien CSV depuis les secrets
    if "GOOGLE_SHEET_URL" in st.secrets:
        csv_url = st.secrets["GOOGLE_SHEET_URL"]
    else:
        st.error("Lien Google Sheet manquant dans les Secrets !")
        st.stop()
    
    try:
        # Lecture du CSV
        df = pd.read_csv(csv_url, header=None)
        
        # Le fichier Excel a une structure complexe, on s'adapte :
        # La ligne 2 (index 2) contient les numéros de Pick [nan, 1, 2, 3...]
        picks_row = df.iloc[2, 1:] 
        
        # On cherche où s'arrêtent les joueurs (avant "Team Raptors" ou "Score BP")
        # On prend large, on filtrera après
        players_data = df.iloc[3:20].copy()
        
        # On renomme : Colonne 0 = Player, les autres = les Picks
        cols = ['Player'] + list(picks_row)
        # On s'assure qu'on a le même nombre de colonnes
        players_data = players_data.iloc[:, :len(cols)]
        players_data.columns = cols
        
        # On ne garde que les lignes qui ont un nom de joueur valide
        # (On exclut les lignes vides ou les totaux comme "Team Raptors")
        # Liste des mots clés à exclure
        exclude_list = ["Team Raptors", "Score BP", "Classic", "0 et négatif", "BP", "nan"]
        players_data = players_data[~players_data['Player'].isin(exclude_list)]
        players_data = players_data.dropna(subset=['Player'])

        # Transformation en format long
        df_long = players_data.melt(id_vars=['Player'], var_name='Pick', value_name='Score')
        
        # Nettoyage des types
        df_long['Score'] = pd.to_numeric(df_long['Score'], errors='coerce')
        df_long['Pick'] = pd.to_numeric(df_long['Pick'], errors='coerce')
        
        # On garde seulement les scores existants (pas les futurs) et valides (>0 ou 0)
        df_clean = df_long.dropna(subset=['Score', 'Pick'])
        
        return df_clean
        
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return pd.DataFrame()

# --- FONCTION : ENVOYER SUR DISCORD ---
def send_discord_summary(top_player, avg_score, pick_num):
    if "DISCORD_WEBHOOK" not in st.secrets:
        st.error("Webhook Discord manquant dans les Secrets !")
        return False

    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    
    message = {
        "username": "Raptors Bot 🦖",
        "embeds": [{
            "title": f"🏀 Récap TTFL - Pick {int(pick_num)}",
            "color": 13504833, # Rouge Raptors
            "fields": [
                {"name": "🔥 MVP du Jour", "value": f"**{top_player['Player']}** avec {int(top_player['Score'])} pts", "inline": True},
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

# --- INTERFACE PRINCIPALE ---
try:
    df = load_data()
    
    if not df.empty:
        latest_pick = df['Pick'].max()
        
        # Filtrer les données du dernier jour
        day_df = df[df['Pick'] == latest_pick].sort_values('Score', ascending=False)
        
        if not day_df.empty:
            top_player = day_df.iloc[0]
            team_avg = day_df['Score'].mean()

            # Titre
            st.title(f"🦖 RAPTORS FR | PICK {int(latest_pick)}")

            # KPIS
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("MVP du Jour", top_player['Player'], f"{int(top_player['Score'])} pts")
            kpi2.metric("Moyenne Équipe", f"{int(team_avg)} pts")
            
            # Calcul Leader Saison
            total_scores = df.groupby('Player')['Score'].sum().sort_values(ascending=False)
            leader = total_scores.index[0]
            kpi3.metric("Leader Saison", leader, f"{int(total_scores.iloc[0])} pts")

            st.divider()

            # Graphique d'évolution
            st.subheader("📈 Évolution de la Saison")
            
            # Calcul du cumulatif
            df = df.sort_values('Pick')
            df['Cumul'] = df.groupby('Player')['Score'].cumsum()
            
            # Filtre Joueurs
            players_list = df['Player'].unique()
            selection = st.multiselect("Comparer les joueurs :", players_list, default=players_list[:min(5, len(players_list))])
            
            if selection:
                chart_data = df[df['Player'].isin(selection)]
                fig = px.line(chart_data, x='Pick', y='Cumul', color='Player', markers=True, title="Course au score total")
                st.plotly_chart(fig, use_container_width=True)

            # --- SECTION ADMIN (SIDEBAR) ---
            with st.sidebar:
                st.header("⚙️ Admin Zone")
                st.info("Une fois le Excel rempli le matin, clique ici pour notifier l'équipe.")
                
                if st.button("📢 Envoyer Récap Discord"):
                    with st.spinner("Envoi en cours..."):
                        success = send_discord_summary(top_player, team_avg, latest_pick)
                        if success:
                            st.success("Envoyé sur Discord !")
                        else:
                            st.error("Erreur d'envoi.")
        else:
            st.warning("Aucune donnée trouvée pour le dernier pick.")
    else:
        st.info("En attente de données...")

except Exception as e:
    st.error("Une erreur est survenue.")
    st.expander("Détails techniques").write(e)
