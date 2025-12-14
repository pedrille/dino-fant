import streamlit as st
import pandas as pd
import datetime
from src.utils import normalize_month

# --- CONFIGURATION ---
# Date du Pick #1 (Opening Night NBA 2024-25)
SEASON_START_DATE = datetime.datetime(2024, 10, 22)

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    try:
        # 1. CHARGEMENT DU CSV GOOGLE SHEET
        if "GSHEET_ID" in st.secrets:
            SHEET_ID = st.secrets["GSHEET_ID"]
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Valeurs"
            df_raw = pd.read_csv(url, header=None)
        else:
            return pd.DataFrame(), 0, {}, [], {}

        # 2. REPÉRAGE DES LIGNES CLÉS (SCAN)
        pick_row_idx = -1
        deck_row_idx = -1
        
        # On scanne les 10 premières lignes pour trouver "Deck" et "Pick"
        for i, row in df_raw.head(10).iterrows():
            first_cell = str(row[0])
            if "Pick" in first_cell:
                pick_row_idx = i
            if "Deck" in first_cell:
                deck_row_idx = i
        
        if pick_row_idx == -1:
            st.error("Structure du fichier non reconnue (Ligne 'Pick' introuvable).")
            return pd.DataFrame(), 0, {}, [], {}

        # 3. EXTRACTION DES DONNÉES
        players_start_row = pick_row_idx + 1
        players = df_raw.iloc[players_start_row:, 0].dropna().values
        
        data_list = []
        
        # Variable pour mémoriser le Deck en cours (Fill Forward)
        current_deck_num = 0
        
        # On parcourt les colonnes (à partir de la colonne B)
        for col_idx in range(1, df_raw.shape[1]):
            
            # --- A. GESTION DU DECK ---
            # Si on a trouvé une ligne Deck, on regarde ce qu'il y a dedans
            if deck_row_idx != -1:
                raw_deck_val = df_raw.iloc[deck_row_idx, col_idx]
                try:
                    # Si c'est un chiffre, c'est le début d'un nouveau Deck
                    deck_val = int(float(raw_deck_val))
                    current_deck_num = deck_val
                except (ValueError, TypeError):
                    # Si c'est vide, on reste sur le Deck précédent (c'est normal en Excel)
                    pass
            
            # --- B. RECUPERATION DU PICK ---
            raw_pick_val = df_raw.iloc[pick_row_idx, col_idx]
            try:
                pick_num = int(float(raw_pick_val))
            except (ValueError, TypeError):
                continue # Ce n'est pas une colonne de jeu (ex: colonne vide)

            # Calcul Date (Esthétique uniquement, le Weekly se basera sur le Deck)
            calculated_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)
            
            # --- C. PARCOURS DES JOUEURS ---
            for i, player_name in enumerate(players):
                row_idx = players_start_row + i
                raw_score = df_raw.iloc[row_idx, col_idx]
                
                # Nettoyage
                if pd.isna(raw_score) or str(raw_score).strip() == "":
                    continue
                    
                score_str = str(raw_score).strip().replace(',', '.')
                if score_str.lower() == 'nan': continue
                
                is_bonus = '*' in score_str
                is_bp = '!' in score_str
                clean_str = score_str.replace('*', '').replace('!', '')
                
                try:
                    score_val = float(clean_str)
                except ValueError:
                    continue 
                
                final_score = score_val * 2 if is_bonus else score_val
                
                data_list.append({
                    'Deck': current_deck_num, # Le vrai Deck lu dans le Excel
                    'Pick': pick_num,
                    'Date': calculated_date,
                    'Player': player_name,
                    'Score': int(final_score),
                    'ScoreVal': int(score_val),
                    'IsBonus': is_bonus,
                    'IsBP': is_bp,
                    'Month': normalize_month(calculated_date.strftime("%B")) 
                })

        # 4. DATAFRAME FINAL
        df = pd.DataFrame(data_list)
        if df.empty: return pd.DataFrame(), 0, {}, [], {}

        # 5. CALCULS ADDITIONNELS
        df['ZScore'] = df.groupby('Pick')['Score'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) > 0 else 0
        ).fillna(0)
        
        team_rank = 1 
        bp_map = df[df['IsBP'] == True].set_index('Pick')['Score'].to_dict()
        team_history = [1] 
        daily_max_map = df.groupby('Pick')['Score'].max().to_dict()

        return df, team_rank, bp_map, team_history, daily_max_map

    except Exception as e:
        st.error(f"Erreur Data Loader: {e}")
        return pd.DataFrame(), 0, {}, [], {}
