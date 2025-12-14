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
            # On lit tout en texte (dtype=str) pour éviter les interprétations erronées
            df_raw = pd.read_csv(url, header=None, dtype=str)
        else:
            return pd.DataFrame(), 0, {}, [], {}

        # 2. REPÉRAGE DES LIGNES (SCAN)
        # On cherche la ligne qui contient exactement "Pick" dans la première colonne
        pick_row_idx = -1
        deck_row_idx = -1
        
        # Scan des 10 premières lignes pour trouver les repères
        for i, row in df_raw.head(10).iterrows():
            first_col = str(row[0]).strip()
            if first_col == "Pick":
                pick_row_idx = i
            elif first_col == "Deck":
                deck_row_idx = i
        
        # Sécurité si on ne trouve pas "Pick"
        if pick_row_idx == -1:
            # Fallback : Si structure standard, Pick est souvent en ligne 3 (index 2)
            pick_row_idx = 2
            deck_row_idx = 1

        # 3. LISTE DES JOUEURS
        # On commence après la ligne Pick
        players = []
        player_indices = []
        
        for i in range(pick_row_idx + 1, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            # Conditions d'arrêt (Fin du tableau)
            if val in ["nan", "", "None", "Team Raptors", "Score BP", "Classic", "Moyenne"]:
                break
            players.append(val)
            player_indices.append(i)

        if not players:
            st.error("Aucun joueur trouvé après la ligne Pick.")
            return pd.DataFrame(), 0, {}, [], {}

        # 4. EXTRACTION DES DONNÉES
        data_list = []
        
        # A. On prépare la map des Decks (Propagation des valeurs vers la droite)
        deck_map = {}
        current_deck = 0
        
        if deck_row_idx != -1:
            for col in range(1, df_raw.shape[1]):
                val = df_raw.iloc[deck_row_idx, col]
                if pd.notna(val) and str(val).strip() != "":
                    try:
                        # Nettoyage (ex: "1.0" -> 1)
                        current_deck = int(float(str(val).replace(',', '.')))
                    except: pass
                deck_map[col] = current_deck

        # B. Boucle sur les colonnes (Les Picks)
        for col_idx in range(1, df_raw.shape[1]):
            # Lecture du numéro de Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            # Si pas de pick valide, on saute la colonne
            if pd.isna(raw_pick) or str(raw_pick).strip() == "":
                continue
            
            try:
                pick_num = int(float(str(raw_pick).replace(',', '.')))
            except:
                continue # Ce n'est pas une colonne de jeu

            # Récupération Deck (ou 0 si pas trouvé)
            deck_num = deck_map.get(col_idx, 0)
            
            # Calcul Date
            calc_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)
            
            # C. Lecture des scores pour chaque joueur
            for player_name, row_idx in zip(players, player_indices):
                raw_score = df_raw.iloc[row_idx, col_idx]
                
                # Si vide ou NaN -> Joueur n'a pas joué ou DNP
                if pd.isna(raw_score) or str(raw_score).strip() == "":
                    continue
                
                score_str = str(raw_score).strip().replace(',', '.')
                if score_str.lower() == 'nan': continue
                
                # Détection Bonus (*) et Best Pick (!)
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

        # 5. FINALISATION DATAFRAME
        df = pd.DataFrame(data_list)
        
        if df.empty:
            # On renvoie vide mais sans erreur bloquante pour l'UI
            st.warning("⚠️ Données extraites vides. Vérifiez le format du Google Sheet.")
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
