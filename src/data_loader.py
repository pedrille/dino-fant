import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import datetime
from src.utils import normalize_month

# --- CONFIGURATION ---
SEASON_START_DATE = datetime.datetime(2024, 10, 22)

@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    try:
        # 1. CONNEXION VIA ST-GSHEETS-CONNECTION (VOTRE MÉTHODE QUI MARCHAIT)
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # On lit le fichier "Valeurs"
        # Note : Assurez-vous que le secret s'appelle bien "SPREADSHEET_URL" ou "GSHEET_ID" dans votre TOML
        # Dans votre ancien code c'était "SPREADSHEET_URL". Je vais gérer les deux cas.
        
        url = st.secrets.get("SPREADSHEET_URL") or f"https://docs.google.com/spreadsheets/d/{st.secrets.get('GSHEET_ID')}"
        
        df_valeurs = conn.read(spreadsheet=url, worksheet="Valeurs", header=None, ttl=0).astype(str)

        # 2. LOGIQUE DE PARSING (VOTRE ANCIEN CODE ADAPTÉ)
        # On cherche la ligne Pick (souvent ligne 2, index 2)
        pick_row_idx = 2
        
        # Sécurité : on vérifie si la ligne 2 contient bien des chiffres
        # Sinon on scanne
        if not str(df_valeurs.iloc[pick_row_idx, 1]).replace('.','').isdigit():
            for i, row in df_valeurs.iterrows():
                if str(row[0]) == "Pick":
                    pick_row_idx = i
                    break

        # Extraction de la série des Picks
        picks_series = pd.to_numeric(df_valeurs.iloc[pick_row_idx, 1:], errors='coerce')
        
        # Gestion des Dates/Mois (Ligne 0)
        month_row = df_valeurs.iloc[0]
        pick_to_month = {}
        current_month = "Inconnu"
        
        # Mapping Pick -> Mois
        for col_idx in range(1, len(month_row)):
            val_month = str(month_row[col_idx]).strip()
            if val_month and val_month.lower() != 'nan': 
                current_month = val_month
            
            pick_val = pd.to_numeric(df_valeurs.iloc[pick_row_idx, col_idx], errors='coerce')
            if pd.notna(pick_val) and pick_val > 0:
                pick_to_month[int(pick_val)] = normalize_month(current_month)

        # Gestion des Decks (Ligne 1) - AJOUT POUR WEEKLY REPORT
        deck_row = df_valeurs.iloc[1] # Ligne Deck
        pick_to_deck = {}
        current_deck = 0
        
        for col_idx in range(1, len(deck_row)):
            val_deck = str(deck_row[col_idx]).strip()
            if val_deck and val_deck.lower() != 'nan':
                try:
                    current_deck = int(float(val_deck.replace(',', '.')))
                except: pass
            
            pick_val = pd.to_numeric(df_valeurs.iloc[pick_row_idx, col_idx], errors='coerce')
            if pd.notna(pick_val) and pick_val > 0:
                pick_to_deck[int(pick_val)] = current_deck

        # 3. EXTRACTION JOUEURS
        # On prend tout ce qui est sous la ligne Pick jusqu'à 50 lignes plus bas
        df_players = df_valeurs.iloc[pick_row_idx+1:pick_row_idx+50].copy().rename(columns={0: 'Player'})
        
        # Nettoyage des lignes parasites
        stop_words = ["Team Raptors", "Score BP", "Classic", "BP", "nan", "Moyenne", "Somme", "None"]
        df_players = df_players[~df_players['Player'].isin(stop_words)].dropna(subset=['Player'])
        df_players = df_players[df_players['Player'].str.strip() != ""]
        df_players['Player'] = df_players['Player'].str.strip()

        # 4. TRANSFORMATION (PIVOT)
        # On ne garde que les colonnes qui correspondent à des Picks valides
        valid_map = {idx: int(val) for idx, val in picks_series.items() if pd.notna(val) and val > 0}
        
        cols = [0] + list(valid_map.keys()) # 0 = Player
        cols = [c for c in cols if c in df_players.columns]
        
        df_clean = df_players[cols].copy()
        # On renomme les colonnes (Index Excel -> Numéro Pick)
        df_clean.rename(columns=valid_map, inplace=True)
        
        # Passage en format Long (Pick, Player, Score)
        df_long = df_clean.melt(id_vars=['Player'], var_name='Pick', value_name='ScoreRaw')

        # 5. NETTOYAGE SCORES
        df_long['IsBP'] = df_long['ScoreRaw'].str.contains('!', na=False)
        df_long['IsBonus'] = df_long['ScoreRaw'].str.contains(r'\*', na=False)
        df_long['ScoreClean'] = df_long['ScoreRaw'].str.replace(r'[\*!]', '', regex=True)
        
        df_long['ScoreVal'] = pd.to_numeric(df_long['ScoreClean'], errors='coerce')
        # Calcul Score Final (x2 si Bonus)
        df_long['Score'] = np.where(df_long['IsBonus'], df_long['ScoreVal'] * 2, df_long['ScoreVal'])
        
        # Nettoyage final
        final_df = df_long.dropna(subset=['Score', 'Pick'])
        final_df['Pick'] = final_df['Pick'].astype(int)
        
        # Ajout des métadonnées (Mois, Deck, Date)
        final_df['Month'] = final_df['Pick'].map(pick_to_month).fillna("Inconnu")
        final_df['Deck'] = final_df['Pick'].map(pick_to_deck).fillna(0).astype(int)
        
        # Calcul Date (Simulé) pour l'affichage
        final_df['Date'] = final_df['Pick'].apply(lambda x: SEASON_START_DATE + datetime.timedelta(days=x-1))

        # 6. OBJETS ANNEXES
        # Z-Score
        daily_stats = final_df.groupby('Pick')['Score'].agg(['mean', 'std']).reset_index()
        daily_stats.rename(columns={'mean': 'DailyMean', 'std': 'DailyStd'}, inplace=True)
        final_df = pd.merge(final_df, daily_stats, on='Pick', how='left')
        final_df['ZScore'] = np.where(final_df['DailyStd'] > 0, 
                                      (final_df['Score'] - final_df['DailyMean']) / final_df['DailyStd'], 0)

        # BP Map (Pour stats.py)
        # On cherche la ligne "Score BP" dans le fichier d'origine pour être précis
        bp_row = df_valeurs[df_valeurs[0].str.contains("Score BP", na=False)]
        if not bp_row.empty:
            bp_series_raw = pd.to_numeric(bp_row.iloc[0, 1:], errors='coerce')
            bp_map = {int(picks_series[idx]): val for idx, val in bp_series_raw.items() if idx in valid_map}
        else:
            # Fallback : Max du jour
            bp_map = final_df.groupby('Pick')['Score'].max().to_dict()

        team_rank = 1 # Placeholder
        team_history = [1] # Placeholder
        daily_max_map = final_df.groupby('Pick')['Score'].max().to_dict()

        return final_df, team_rank, bp_map, team_history, daily_max_map

    except Exception as e:
        # Affiche l'erreur explicite si ça plante encore
        st.error(f"🔥 Erreur Chargement (GSheetsConnection) : {str(e)}")
        return pd.DataFrame(), 0, {}, [], {}
