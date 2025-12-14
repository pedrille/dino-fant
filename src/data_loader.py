import streamlit as st
import pandas as pd
import datetime
from src.utils import normalize_month

# --- CONFIGURATION ---
SEASON_START_DATE = datetime.datetime(2024, 10, 22)

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    # Initialisation des variables de retour par défaut (vides)
    empty_res = (pd.DataFrame(), 0, {}, [], {})

    try:
        # 1. CHARGEMENT BRUT
        if "GSHEET_ID" not in st.secrets:
            st.error("❌ Secret GSHEET_ID manquant.")
            return empty_res

        SHEET_ID = st.secrets["GSHEET_ID"]
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Valeurs"
        
        # Lecture sans header, tout en string pour éviter les erreurs de type
        df_raw = pd.read_csv(url, header=None, dtype=str)

        # 2. SCANNER INTELLIGENT (Cherche "Pick" et "Deck")
        pick_row_idx = -1
        deck_row_idx = -1

        # On scanne les 20 premières lignes
        for i, row in df_raw.head(20).iterrows():
            first_col_val = str(row[0]).strip().lower() # On met tout en minuscule et sans espace
            
            if "pick" in first_col_val:
                pick_row_idx = i
            
            if "deck" in first_col_val:
                deck_row_idx = i

        # Si on n'a pas trouvé la ligne Pick, on arrête et on affiche l'erreur
        if pick_row_idx == -1:
            st.error(f"❌ Impossible de trouver la ligne 'Pick' dans les 20 premières lignes du fichier. Contenu ligne 1 : {df_raw.iloc[0,0]}")
            return empty_res

        # Si on n'a pas trouvé Deck, on suppose qu'il est juste au-dessus
        if deck_row_idx == -1:
            deck_row_idx = pick_row_idx - 1

        # 3. EXTRACTION
        players = []
        player_indices = []
        
        # On lit les joueurs sous la ligne Pick
        for i in range(pick_row_idx + 1, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            # Stop words : mots qui signalent la fin du tableau joueurs
            if val.lower() in ["nan", "", "none", "team raptors", "score bp", "classic", "moyenne"]:
                break
            players.append(val)
            player_indices.append(i)

        if not players:
            st.error("❌ La ligne 'Pick' a été trouvée, mais aucun joueur n'a été détecté en dessous.")
            return empty_res

        # 4. BOUCLE SUR LES COLONNES
        data_list = []
        
        # Pré-lecture des Decks pour boucher les trous (Fill Forward)
        deck_map = {}
        current_deck = 0
        
        # On scanne la ligne des decks si elle existe
        if deck_row_idx >= 0:
            for col in range(1, df_raw.shape[1]):
                val = df_raw.iloc[deck_row_idx, col]
                if pd.notna(val) and str(val).strip() != "":
                    try:
                        # On nettoie "1.0" ou "1" ou "Deck 1"
                        clean_val = str(val).lower().replace('deck', '').strip()
                        current_deck = int(float(clean_val))
                    except: pass
                deck_map[col] = current_deck

        # On parcourt les colonnes de données (Picks)
        for col_idx in range(1, df_raw.shape[1]):
            # Lecture Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            if pd.isna(raw_pick) or str(raw_pick).strip() == "":
                continue
                
            try:
                pick_num = int(float(str(raw_pick).replace(',', '.')))
            except:
                continue # Ce n'est pas une colonne de Pick

            # Récupération Deck & Date
            deck_num = deck_map.get(col_idx, 0)
            calc_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)

            # Lecture Score Joueurs
            for player_name, row_idx in zip(players, player_indices):
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

        # 5. CONSTRUCTION FINAL
        df = pd.DataFrame(data_list)
        
        if df.empty:
            st.warning("⚠️ Fichier lu, joueurs trouvés, mais aucune donnée de score extraite.")
            return empty_res

        # Stats annexes
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
        st.error(f"🔥 CRASH CRITIQUE DATA LOADER : {str(e)}")
        return empty_res
