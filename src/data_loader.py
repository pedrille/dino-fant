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
        # 1. CHARGEMENT DU CSV
        if "GSHEET_ID" in st.secrets:
            SHEET_ID = st.secrets["GSHEET_ID"]
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Valeurs"
            # On lit tout en strings pour éviter les erreurs de conversion immédiates
            df_raw = pd.read_csv(url, header=None, dtype=str)
        else:
            return pd.DataFrame(), 0, {}, [], {}

        # 2. REPÉRAGE DES LIGNES (Scan intelligent)
        pick_row_idx = -1
        
        # On cherche la ligne qui contient le mot "Pick" dans la première colonne
        for i, row in df_raw.iterrows():
            first_cell = str(row[0])
            if "Pick" in first_cell:
                pick_row_idx = i
                break
        
        if pick_row_idx == -1:
            st.error("❌ Structure du fichier Excel non reconnue (Ligne 'Pick' introuvable).")
            return pd.DataFrame(), 0, {}, [], {}

        # La ligne des Decks est supposée être juste au-dessus
        deck_row_idx = pick_row_idx - 1

        # 3. EXTRACTION
        # Les joueurs sont après la ligne Pick
        players_start_row = pick_row_idx + 1
        players = df_raw.iloc[players_start_row:, 0].dropna().values
        
        data_list = []
        
        # --- PRÉ-TRAITEMENT DE LA LIGNE DECK (Fill Forward) ---
        # On récupère toute la ligne des decks pour boucher les trous avant la boucle
        deck_map = {} # col_idx -> deck_num
        if deck_row_idx >= 0:
            current_deck = 0
            for col in range(1, df_raw.shape[1]):
                val = df_raw.iloc[deck_row_idx, col]
                # Si c'est un chiffre, on met à jour le current_deck
                if pd.notna(val) and str(val).strip() != "":
                    try:
                        current_deck = int(float(str(val).replace(',', '.')))
                    except: pass
                deck_map[col] = current_deck

        # 4. BOUCLE SUR LES COLONNES (LES PICKS)
        for col_idx in range(1, df_raw.shape[1]):
            
            # Récupération du Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            # Si pas de pick valide, on passe
            if pd.isna(raw_pick) or str(raw_pick).strip() == "":
                continue
                
            try:
                pick_num = int(float(str(raw_pick).replace(',', '.')))
            except:
                continue # Ce n'est pas une colonne de jeu

            # Récupération du Deck (depuis notre map pré-calculée)
            deck_num = deck_map.get(col_idx, 0)
            
            # Calcul Date (Pour affichage et Weekly Report)
            # Pick 1 = 22 Octobre
            calculated_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)

            # Boucle sur les joueurs
            for i, player_name in enumerate(players):
                row_idx = players_start_row + i
                
                # Le score brut (ex: "44!", "56*")
                raw_score = df_raw.iloc[row_idx, col_idx]
                
                if pd.isna(raw_score) or str(raw_score).strip() == "":
                    continue
                
                score_str = str(raw_score).strip().replace(',', '.')
                if score_str.lower() == 'nan': continue
                
                # Détection Bonus
                is_bonus = '*' in score_str
                is_bp = '!' in score_str
                
                # Nettoyage
                clean_str = score_str.replace('*', '').replace('!', '')
                
                try:
                    score_val = float(clean_str)
                except:
                    continue
                
                final_score = score_val * 2 if is_bonus else score_val
                
                data_list.append({
                    'Pick': pick_num,
                    'Deck': deck_num, # Le Deck lu et propagé
                    'Date': calculated_date, # La Date calculée
                    'Player': player_name,
                    'Score': int(final_score),
                    'ScoreVal': int(score_val),
                    'IsBonus': is_bonus,
                    'IsBP': is_bp,
                    'Month': normalize_month(calculated_date.strftime("%B"))
                })

        # 5. CONSTRUCTION DATAFRAME
        df = pd.DataFrame(data_list)
        
        if df.empty:
            st.warning("⚠️ Aucune donnée extraite du fichier.")
            return pd.DataFrame(), 0, {}, [], {}

        # 6. CALCULS STATS (ZScore, etc.)
        if 'Score' in df.columns:
            df['ZScore'] = df.groupby('Pick')['Score'].transform(
                lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) > 0 else 0
            ).fillna(0)

        # Objets annexes pour l'app
        team_rank = 1 
        bp_map = df[df['IsBP'] == True].set_index('Pick')['Score'].to_dict()
        team_history = [1]
        daily_max_map = df.groupby('Pick')['Score'].max().to_dict()

        return df, team_rank, bp_map, team_history, daily_max_map

    except Exception as e:
        st.error(f"🔥 Erreur Data Loader : {e}")
        return pd.DataFrame(), 0, {}, [], {}
