import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import datetime
from src.utils import normalize_month

# --- CONFIGURATION ---
# Date du Pick #1 (22 Octobre 2024)
SEASON_START_DATE = datetime.datetime(2024, 10, 22)

@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    try:
        # 1. CONNEXION SÉCURISÉE (Via vos secrets [connections.gsheets])
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Récupération de l'URL depuis les secrets
        url = st.secrets["SPREADSHEET_URL"]
        
        # Lecture complète de l'onglet "Valeurs" sans en-tête (header=None)
        # On lit tout en string pour éviter les erreurs de conversion
        df_raw = conn.read(spreadsheet=url, worksheet="Valeurs", header=None).astype(str)

        # 2. REPÉRAGE DES LIGNES (Basé sur votre structure Excel)
        # Ligne 1 (index 0) = Mois
        # Ligne 2 (index 1) = Deck
        # Ligne 3 (index 2) = Pick
        pick_row_idx = 2
        deck_row_idx = 1
        players_start_row = 3

        # Vérification de sécurité basique
        first_col_val = str(df_raw.iloc[pick_row_idx, 0]).strip()
        if "Pick" not in first_col_val:
            # Fallback : on scanne si jamais ça a bougé
            for i, row in df_raw.head(10).iterrows():
                if "Pick" in str(row[0]):
                    pick_row_idx = i
                    deck_row_idx = i - 1
                    players_start_row = i + 1
                    break

        # 3. EXTRACTION DES JOUEURS
        players = []
        player_indices = []
        
        for i in range(players_start_row, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            # Stop words
            if val in ["nan", "None", "", "Team Raptors", "Score BP", "Classic", "Moyenne"]:
                break
            players.append(val)
            player_indices.append(i)

        if not players:
            return pd.DataFrame(), 0, {}, [], {}

        # 4. EXTRACTION DES DONNÉES
        data_list = []
        
        # --- MAP DES DECKS (Gestion des trous) ---
        deck_map = {}
        current_deck = 0
        
        # On parcourt la ligne des Decks
        for col_idx in range(1, df_raw.shape[1]):
            val = df_raw.iloc[deck_row_idx, col_idx]
            # Si on a une valeur (ex: "1" ou "1.0"), on met à jour le deck courant
            if pd.notna(val) and val != "nan" and val.strip() != "":
                try:
                    current_deck = int(float(val.replace(',', '.')))
                except: pass
            deck_map[col_idx] = current_deck

        # --- PARCOURS DES PICKS ---
        for col_idx in range(1, df_raw.shape[1]):
            # Lecture du Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            if pd.isna(raw_pick) or raw_pick == "nan" or raw_pick.strip() == "":
                continue
            
            try:
                pick_num = int(float(raw_pick.replace(',', '.')))
            except:
                continue # Colonne invalide

            # Récupération Deck & Calcul Date
            deck_num = deck_map.get(col_idx, 0)
            calc_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)

            # Lecture des scores joueurs
            for player_name, row_idx in zip(players, player_indices):
                raw_score = df_raw.iloc[row_idx, col_idx]
                
                # Si vide -> DNP
                if pd.isna(raw_score) or raw_score == "nan" or raw_score.strip() == "":
                    continue
                
                score_str = raw_score.strip().replace(',', '.')
                
                # Attributs
                is_bonus = '*' in score_str
                is_bp = '!' in score_str
                
                # Nettoyage pour valeur numérique
                clean_str = score_str.replace('*', '').replace('!', '')
                
                try:
                    score_val = float(clean_str)
                except:
                    continue # Score illisible
                
                # Calcul Score Final
                final_score = score_val * 2 if is_bonus else score_val
                
                data_list.append({
                    'Pick': pick_num,
                    'Deck': deck_num,
                    'Date': calc_date,
                    'Player': player_name,
                    'Score': int(final_score),
                    'ScoreVal': int(score_val),
                    'IsBonus': is_bonus,
                    'IsBP': is_bp,
                    'Month': normalize_month(calc_date.strftime("%B"))
                })

        # 5. DATAFRAME FINAL
        df = pd.DataFrame(data_list)
        
        if df.empty:
            return pd.DataFrame(), 0, {}, [], {}

        # 6. CALCULS STATS (Z-Score, etc.)
        df['ZScore'] = df.groupby('Pick')['Score'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) > 0 else 0
        ).fillna(0)

        # Objets annexes (Placeholders simplifiés pour éviter les erreurs de référence)
        team_rank = 1 
        # On essaie de récupérer les BP depuis les données extraites
        bp_map = df[df['IsBP'] == True].set_index('Pick')['Score'].to_dict()
        if not bp_map: # Fallback si les "!" ne sont pas détectés
             bp_map = df.groupby('Pick')['Score'].max().to_dict()
             
        team_history = [1]
        daily_max_map = df.groupby('Pick')['Score'].max().to_dict()

        return df, team_rank, bp_map, team_history, daily_max_map

    except Exception as e:
        st.error(f"🔥 Erreur Data Loader : {str(e)}")
        return pd.DataFrame(), 0, {}, [], {}
