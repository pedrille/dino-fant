import streamlit as st
import pandas as pd
import datetime
from src.utils import normalize_month

# --- CONFIGURATION ---
SEASON_START_DATE = datetime.datetime(2024, 10, 22)

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    try:
        # 1. CHARGEMENT
        if "GSHEET_ID" in st.secrets:
            SHEET_ID = st.secrets["GSHEET_ID"]
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Valeurs"
            # On lit tout en texte (dtype=str) pour éviter les erreurs de format
            df_raw = pd.read_csv(url, header=None, dtype=str)
        else:
            return pd.DataFrame(), 0, {}, [], {}

        # 2. IDENTIFICATION STRICTE DES LIGNES (Basé sur votre fichier)
        # On cherche la ligne qui contient "Pick" dans la première colonne
        pick_row_idx = -1
        for i, row in df_raw.iterrows():
            if str(row[0]).strip() == "Pick":
                pick_row_idx = i
                break
        
        if pick_row_idx == -1:
            st.error("❌ Structure invalide : Ligne 'Pick' introuvable.")
            return pd.DataFrame(), 0, {}, [], {}

        deck_row_idx = pick_row_idx - 1 # La ligne juste au-dessus

        # 3. IDENTIFICATION DES JOUEURS
        # On commence après la ligne Pick
        # On s'arrête si on tombe sur "Team Raptors", "Score BP", ou vide
        players = []
        player_indices = []
        
        for i in range(pick_row_idx + 1, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            if val in ["nan", "", "None", "Team Raptors", "Score BP", "Classic"]:
                break # On arrête de lire les joueurs ici
            players.append(val)
            player_indices.append(i)

        # 4. EXTRACTION DES DONNÉES
        data_list = []
        
        # On prépare la map des Decks (Fill Forward)
        # On lit la ligne des Decks et on bouche les trous
        deck_map = {}
        current_deck = 0
        
        if deck_row_idx >= 0:
            for col in range(1, df_raw.shape[1]):
                val = df_raw.iloc[deck_row_idx, col]
                if pd.notna(val) and str(val).strip() != "":
                    try:
                        # On nettoie la valeur (ex: "1" ou "1.0")
                        current_deck = int(float(str(val).replace(',', '.')))
                    except: pass
                deck_map[col] = current_deck

        # On parcourt les colonnes (Les Picks)
        for col_idx in range(1, df_raw.shape[1]):
            # Lecture du Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            # Si pas de pick, on saute
            if pd.isna(raw_pick) or str(raw_pick).strip() == "":
                continue
            
            try:
                pick_num = int(float(str(raw_pick).replace(',', '.')))
            except:
                continue # Ce n'est pas une colonne de jeu

            # Récupération Deck & Date
            deck_num = deck_map.get(col_idx, 0)
            calc_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)
            
            # Lecture des scores pour chaque joueur identifié
            for player_name, row_idx in zip(players, player_indices):
                raw_score = df_raw.iloc[row_idx, col_idx]
                
                # Si vide ou NaN
                if pd.isna(raw_score) or str(raw_score).strip() == "":
                    continue
                
                score_str = str(raw_score).strip().replace(',', '.')
                if score_str.lower() == 'nan': continue
                
                # Détection Bonus / BP
                is_bonus = '*' in score_str
                is_bp = '!' in score_str
                
                # Nettoyage pour conversion
                clean_str = score_str.replace('*', '').replace('!', '')
                
                try:
                    score_val = float(clean_str)
                except:
                    continue # Score illisible
                
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

        # 5. FINALISATION
        df = pd.DataFrame(data_list)
        
        if df.empty:
            # On renvoie vide mais sans erreur bloquante pour l'UI
            return pd.DataFrame(), 0, {}, [], {}

        # Calcul Z-Score
        if 'Score' in df.columns:
            df['ZScore'] = df.groupby('Pick')['Score'].transform(
                lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) > 0 else 0
            ).fillna(0)

        # Objets annexes
        team_rank = 1 
        bp_map = df[df['IsBP'] == True].set_index('Pick')['Score'].to_dict()
        team_history = [1]
        daily_max_map = df.groupby('Pick')['Score'].max().to_dict()

        return df, team_rank, bp_map, team_history, daily_max_map

    except Exception as e:
        st.error(f"🔥 Erreur critique Data Loader : {e}")
        return pd.DataFrame(), 0, {}, [], {}
