import streamlit as st
import pandas as pd
import datetime
from src.utils import normalize_month

# --- CONFIGURATION ---
SEASON_START_DATE = datetime.datetime(2024, 10, 22)

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    try:
        # =================================================================================
        # ID RECUPÉRÉ DE VOTRE LIEN :
        SHEET_ID = "1wUzU5EcwMQMPcdJsS8r_yM5U0uoF2N8GHCZIEerAYlQ"
        # =================================================================================

        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Valeurs"
        
        # Lecture brute
        df_raw = pd.read_csv(url, header=None, dtype=str)

        # 2. REPÉRAGE DES LIGNES (SCAN)
        pick_row_idx = -1
        deck_row_idx = -1
        
        # On cherche "Pick" et "Deck" dans la première colonne
        for i, row in df_raw.head(20).iterrows():
            val = str(row[0]).strip()
            if val == "Pick":
                pick_row_idx = i
            elif val == "Deck":
                deck_row_idx = i
        
        # Sécurité
        if pick_row_idx == -1:
            # Fallback sur les positions standards de votre fichier (Ligne 3 = index 2)
            pick_row_idx = 2
            deck_row_idx = 1

        # 3. LISTE DES JOUEURS
        players = []
        player_indices = []
        
        # Lecture sous la ligne Pick
        for i in range(pick_row_idx + 1, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            # Stop words pour s'arrêter avant les totaux
            if val in ["nan", "", "None", "Team Raptors", "Score BP", "Classic", "Moyenne"]:
                break
            players.append(val)
            player_indices.append(i)

        if not players:
            st.error("❌ Fichier lu mais aucun joueur trouvé.")
            return pd.DataFrame(), 0, {}, [], {}

        # 4. EXTRACTION DES DONNÉES
        data_list = []
        
        # A. Map des Decks (Fill Forward)
        deck_map = {}
        current_deck = 0
        
        if deck_row_idx != -1:
            for col in range(1, df_raw.shape[1]):
                val = df_raw.iloc[deck_row_idx, col]
                if pd.notna(val) and str(val).strip() != "":
                    try:
                        current_deck = int(float(str(val).replace(',', '.')))
                    except: pass
                deck_map[col] = current_deck

        # B. Boucle sur les colonnes (Picks)
        for col_idx in range(1, df_raw.shape[1]):
            # Lecture Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            if pd.isna(raw_pick) or str(raw_pick).strip() == "":
                continue
            
            try:
                pick_num = int(float(str(raw_pick).replace(',', '.')))
            except:
                continue

            # Deck & Date
            deck_num = deck_map.get(col_idx, 0)
            calc_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)
            
            # C. Lecture Scores
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

        # 5. FINALISATION
        df = pd.DataFrame(data_list)
        
        if df.empty:
            st.warning("⚠️ Données vides après extraction.")
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
        st.error(f"🔥 Erreur critique : {e}")
        return pd.DataFrame(), 0, {}, [], {}
