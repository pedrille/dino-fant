import streamlit as st
import pandas as pd
import datetime
from src.utils import normalize_month

# --- CONFIGURATION ---
# Date théorique de début de saison pour l'affichage (Ajustable)
SEASON_START_DATE = datetime.datetime(2024, 10, 22)

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    try:
        # 1. ID GOOGLE SHEET (C'est le vôtre)
        SHEET_ID = "1wUzU5EcwMQMPcdJsS8r_yM5U0uoF2N8GHCZIEerAYlQ"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Valeurs"
        
        # Lecture brute (tout en string)
        df_raw = pd.read_csv(url, header=None, dtype=str)

        # 2. REPÉRAGE DES LIGNES CLÉS (Scan vertical colonne A)
        pick_row_idx = -1
        deck_row_idx = -1
        
        for i, row in df_raw.iterrows():
            val = str(row[0]).strip()
            if val == "Pick":
                pick_row_idx = i
            elif val == "Deck":
                deck_row_idx = i
            # On s'arrête si on a trouvé les deux ou si on va trop loin
            if pick_row_idx != -1 and deck_row_idx != -1:
                break
        
        # Sécurité absolue : si pas trouvé, on force les index standards de votre fichier
        if pick_row_idx == -1: pick_row_idx = 2
        if deck_row_idx == -1: deck_row_idx = 1

        # 3. LISTE DES JOUEURS (Scan vertical sous 'Pick')
        players = []
        player_indices = []
        
        # On commence juste après la ligne Pick
        for i in range(pick_row_idx + 1, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            
            # CONDITIONS D'ARRÊT STRICTES (Fin du tableau)
            if val in ["Team Raptors", "Score BP", "Classic", "Moyenne", "None"]:
                break
            
            # On ignore les lignes vides, mais ON NE S'ARRETE PAS (c'est ça qui cassait avant)
            if val == "" or val == "nan":
                continue
                
            players.append(val)
            player_indices.append(i)

        if not players:
            st.error("❌ Aucun joueur détecté dans la colonne A.")
            return pd.DataFrame(), 0, {}, [], {}

        # 4. EXTRACTION DES DONNÉES (Scan horizontal)
        data_list = []
        
        # Map des Decks (pour boucher les trous "1, , , , 2")
        deck_map = {}
        current_deck = 0
        
        if deck_row_idx >= 0:
            for col in range(1, df_raw.shape[1]):
                val = df_raw.iloc[deck_row_idx, col]
                if pd.notna(val) and str(val).strip() != "":
                    try:
                        current_deck = int(float(str(val).replace(',', '.')))
                    except: pass
                deck_map[col] = current_deck

        # Boucle sur les colonnes (Picks)
        for col_idx in range(1, df_raw.shape[1]):
            # Lecture du Pick
            raw_pick = df_raw.iloc[pick_row_idx, col_idx]
            
            if pd.isna(raw_pick) or str(raw_pick).strip() == "":
                continue
            
            try:
                pick_num = int(float(str(raw_pick).replace(',', '.')))
            except:
                continue 

            deck_num = deck_map.get(col_idx, 0)
            calc_date = SEASON_START_DATE + datetime.timedelta(days=pick_num - 1)

            # Lecture des scores pour chaque joueur
            for player_name, row_idx in zip(players, player_indices):
                raw_score = df_raw.iloc[row_idx, col_idx]
                
                # Si vide -> Le joueur n'a pas joué ce pick
                if pd.isna(raw_score) or str(raw_score).strip() == "":
                    continue
                
                score_str = str(raw_score).strip().replace(',', '.')
                if score_str.lower() == 'nan': continue
                
                # Gestion Bonus / Best Pick
                is_bonus = '*' in score_str
                is_bp = '!' in score_str
                
                # Nettoyage pour avoir la valeur numérique
                clean_str = score_str.replace('*', '').replace('!', '')
                
                try:
                    score_val = float(clean_str)
                except:
                    continue # Valeur non numérique (ex: "DNP")
                
                # Le score final inclut le bonus x2
                final_score = score_val * 2 if is_bonus else score_val
                
                data_list.append({
                    'Pick': pick_num,
                    'Deck': deck_num,
                    'Date': calc_date,
                    'Player': player_name,
                    'Score': int(final_score),
                    'ScoreVal': int(score_val), # Score brut sans bonus
                    'IsBonus': is_bonus,
                    'IsBP': is_bp,
                    'Month': normalize_month(calc_date.strftime("%B"))
                })

        # 5. RETOUR
        df = pd.DataFrame(data_list)
        
        if df.empty:
            st.warning("⚠️ Aucune donnée de score extraite.")
            return pd.DataFrame(), 0, {}, [], {}

        # Calculs stats
        if 'Score' in df.columns:
            df['ZScore'] = df.groupby('Pick')['Score'].transform(
                lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) > 0 else 0
            ).fillna(0)

        # Placeholders pour compatibilité
        team_rank = 1 
        bp_map = df[df['IsBP'] == True].set_index('Pick')['Score'].to_dict()
        team_history = [1]
        daily_max_map = df.groupby('Pick')['Score'].max().to_dict()

        return df, team_rank, bp_map, team_history, daily_max_map

    except Exception as e:
        st.error(f"🔥 Erreur critique : {e}")
        return pd.DataFrame(), 0, {}, [], {}
