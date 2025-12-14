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
            # On lit tout pour ne rien rater
            df_raw = pd.read_csv(url, header=None)
        else:
            return pd.DataFrame(), 0, {}, [], {}

        # 2. REPÉRAGE MANUEL (Plus sûr)
        # On sait que la ligne Pick est la ligne 3 (index 2) dans votre fichier
        # On sait que la ligne Deck est la ligne 2 (index 1)
        pick_row_idx = 2
        deck_row_idx = 1
        
        # Vérification de sécurité
        if len(df_raw) < 5: 
            st.error("Fichier trop court.")
            return pd.DataFrame(), 0, {}, [], {}

        # 3. EXTRACTION
        players_start_row = 3 # Les joueurs commencent ligne 4 (index 3)
        players = df_raw.iloc[players_start_row:, 0].dropna().values
        
        data_list = []
        
        # Pré-lecture des Decks pour boucher les trous (Fill Forward)
        deck_map = {}
        current_deck = 0
        for col_idx in range(1, df_raw.shape[1]):
            val = df_raw.iloc[deck_row_idx, col_idx]
            # Si on trouve un chiffre, c'est un nouveau deck
            if pd.notna(val):
                try:
                    # On convertit en float puis int pour gérer "1.0" ou "1"
                    current_deck = int(float(str(val).replace(',', '.')))
                except: pass
            deck_map[col_idx] = current_deck

        # Boucle principale sur les colonnes (Picks)
        for col_idx in range(1, df_raw.shape[1]):
            
            # Récupération du Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            # On ignore si pas de pick
            if pd.isna(raw_pick) or str(raw_pick).strip() == "":
                continue
                
            try:
                pick_num = int(float(str(raw_pick).replace(',', '.')))
            except:
                continue

            # Récupération du Deck mémorisé
            deck_num = deck_map.get(col_idx, 0)
            
            # Calcul Date (Pour affichage)
            calc_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)

            # Parcours des joueurs
            for i, player_name in enumerate(players):
                row_idx = players_start_row + i
                
                # Check si on ne dépasse pas
                if row_idx >= len(df_raw): break
                
                raw_score = df_raw.iloc[row_idx, col_idx]
                
                if pd.isna(raw_score) or str(raw_score).strip() == "":
                    continue
                
                score_str = str(raw_score).strip().replace(',', '.')
                if score_str.lower() == 'nan': continue
                
                is_bonus = '*' in score_str
                is_bp = '!' in score_str
                clean_str = score_str.replace('*', '').replace('!', '')
                
                try:
                    score_val = float(clean_str)
                except:
                    continue
                
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

        # 4. FINALISATION
        df = pd.DataFrame(data_list)
        
        if df.empty:
            # Fallback ultime pour ne pas crasher
            return pd.DataFrame(), 0, {}, [], {}

        # Z-Score
        if 'Score' in df.columns:
            df['ZScore'] = df.groupby('Pick')['Score'].transform(
                lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) > 0 else 0
            ).fillna(0)

        team_rank = 1
        bp_map = df[df['IsBP'] == True].set_index('Pick')['Score'].to_dict()
        team_history = [1]
        daily_max_map = df.groupby('Pick')['Score'].max().to_dict()

        return df, team_rank, bp_map, team_history, daily_max_map

    except Exception as e:
        # Affiche l'erreur pour débugger
        st.error(f"Erreur Data Loader : {e}")
        return pd.DataFrame(), 0, {}, [], {}
