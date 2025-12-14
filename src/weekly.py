import pandas as pd
import numpy as np
import datetime

def get_winners_list(series, maximize=True):
    """
    Retourne une liste de tuples (Joueur, Valeur) pour gérer les égalités.
    maximize=True -> On cherche les plus grands scores (ex: Points)
    maximize=False -> On cherche les plus petits scores (ex: Carottes)
    """
    if series.empty:
        return []
    
    target_val = series.max() if maximize else series.min()
    winners = series[series == target_val]
    
    return [(player, val) for player, val in winners.items()]

def calculate_streaks(df, player, current_pick_limit):
    """
    Calcule la série active et le record historique pour un joueur donné.
    """
    # On filtre sur le joueur et jusqu'au pick actuel (pour ne pas lire le futur)
    p_df = df[(df['Player'] == player) & (df['Pick'] <= current_pick_limit)].sort_values('Pick')
    
    if p_df.empty:
        return {'active_nc': 0, 'record_nc': 0, 'active_30': 0, 'record_30': 0}

    scores = p_df['Score'].values
    
    # --- 1. SÉRIE SANS CAROTTE (>= 20) ---
    curr_no_carrot = 0
    max_no_carrot = 0
    temp_nc = 0
    
    # Historique (Record)
    for s in scores:
        if s >= 20:
            temp_nc += 1
            max_no_carrot = max(max_no_carrot, temp_nc)
        else:
            temp_nc = 0
            
    # Active (en remontant depuis la fin)
    for s in reversed(scores):
        if s >= 20: curr_no_carrot += 1
        else: break
        
    # --- 2. SÉRIE > 30 ---
    curr_30 = 0
    max_30 = 0
    temp_30 = 0
    
    # Historique
    for s in scores:
        if s >= 30:
            temp_30 += 1
            max_30 = max(max_30, temp_30)
        else:
            temp_30 = 0
            
    # Active
    for s in reversed(scores):
        if s >= 30: curr_30 += 1
        else: break
        
    return {
        'active_nc': curr_no_carrot, 'record_nc': max_no_carrot,
        'active_30': curr_30, 'record_30': max_30
    }

def generate_weekly_report_data(df_full):
    """
    Fonction principale qui génère toutes les données pour le rapport.
    Retourne None si les données sont insuffisantes (pas de dates).
    """
    if df_full.empty: return None

    df = df_full.copy()
    
    # --- SÉCURITÉ DATE ---
    # On vérifie si la colonne 'Date' existe, sinon on ne peut pas faire de rapport hebdo
    if 'Date' not in df.columns:
        return None

    # Conversion robuste des dates (ignore les erreurs)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # On supprime les lignes où la date n'a pas pu être convertie (NaT)
    df = df.dropna(subset=['Date'])
    
    if df.empty: return None

    # Ajout des infos temporelles
    df['WeekNum'] = df['Date'].dt.isocalendar().week
    df['Weekday'] = df['Date'].dt.weekday # 0=Lundi, ..., 6=Dimanche

    # 1. IDENTIFIER LA SEMAINE CIBLE (La dernière présente dans les données)
    # On trie par date pour avoir la dernière
    df_sorted = df.sort_values('Date')
    last_entry = df_sorted.iloc[-1]
    target_week_num = last_entry['WeekNum']
    
    # Isolation des données de la semaine cible
    week_df = df[df['WeekNum'] == target_week_num].copy()
    
    if week_df.empty: return None
    
    # Check si Dimanche est joué (Weekday == 6)
    has_sunday = 6 in week_df['Weekday'].values
    
    # 2. CALCUL HISTORIQUE ROTW (Raptor of the Week)
    rotw_history = {} # {Player: Nb_Titres}
    all_weeks = sorted(df['WeekNum'].unique())
    
    for w in all_weeks:
        if w >= target_week_num: continue # On ne compte pas la semaine en cours dans l'historique "passé"
        
        w_data = df[df['WeekNum'] == w]
        if w_data.empty: continue
        
        # On calcule les scores totaux de cette semaine passée
        w_scores = w_data.groupby('Player')['Score'].sum()
        if w_scores.empty: continue
        
        max_score = w_scores.max()
        # Gestion ex-aequo historique
        winners = w_scores[w_scores == max_score].index.tolist()
        
        for p in winners:
            rotw_history[p] = rotw_history.get(p, 0) + 1

    # 3. PODIUM SEMAINE ACTUELLE
    weekly_scores = week_df.groupby('Player')['Score'].sum().sort_values(ascending=False)
    weekly_podium = []
    
    # On itère sur le Top 3
    # Note : Le calcul des rangs doit gérer les ex-aequo pour l'affichage
    current_rank = 1
    for i, (player, score) in enumerate(weekly_scores.head(3).items()):
        nb_titles = rotw_history.get(player, 0)
        
        # Si c'est le 1er (ou ex-aequo 1er), on lui ajoute le titre virtuel pour l'affichage
        if score == weekly_scores.iloc[0]:
            nb_titles += 1
            rank_disp = 1
        elif i > 0 and score == weekly_scores.iloc[i-1]:
            # Cas ex-aequo (même score que le précédent) -> même rang
            rank_disp = weekly_podium[-1]['rank']
        else:
            rank_disp = i + 1
        
        weekly_podium.append({
            'rank': rank_disp,
            'player': player,
            'score': int(score),
            'titles': nb_titles
        })

    # 4. CLASSEMENT ROTW SAISON (Mis à jour avec cette semaine)
    # On identifie les vainqueurs de la semaine actuelle
    current_winners_list = get_winners_list(weekly_scores, maximize=True)
    
    # On met à jour le dict historique temporairement pour le classement
    temp_history = rotw_history.copy()
    for p, _ in current_winners_list:
        temp_history[p] = temp_history.get(p, 0) + 1
        
    # Tri décroissant et Top 3
    sorted_rotw = sorted(temp_history.items(), key=lambda x: x[1], reverse=True)[:3]

    # 5. SNIPER HEBDO (Max BP)
    weekly_bp = week_df.groupby('Player')['IsBP'].sum()
    snipers = get_winners_list(weekly_bp[weekly_bp > 0], maximize=True) # Uniquement si > 0
    
    # 6. LA MURAILLE (Min Carottes)
    # Filtre : Joueurs ayant joué au moins 4 matchs cette semaine
    games_count = week_df.groupby('Player')['Score'].count()
    active_players = games_count[games_count >= 4].index
    
    murailles = []
    if not active_players.empty:
        # On regarde les carottes uniquement pour ces joueurs
        subset = week_df[week_df['Player'].isin(active_players)]
        
        # On compte les carottes (<20)
        carrots = subset[subset['Score'] < 20].groupby('Player')['Score'].count()
        
        # Astuce : ceux qui n'ont PAS de carottes ne sont pas dans "carrots".
        # On doit créer une série complète avec 0 par défaut
        full_carrots = pd.Series(0, index=active_players)
        full_carrots = full_carrots.add(carrots, fill_value=0)
        
        murailles = get_winners_list(full_carrots, maximize=False)

    # 7. REMONTADA (Progression vs Semaine précédente)
    # Trouver la semaine précédente dans la liste des semaines existantes
    try:
        idx_curr = all_weeks.index(target_week_num)
        prev_week_num = all_weeks[idx_curr - 1] if idx_curr > 0 else None
    except ValueError:
        prev_week_num = None

    remontada_winners = []
    team_avg_prev = 0
    
    if prev_week_num:
        prev_df = df[df['WeekNum'] == prev_week_num]
        team_avg_prev = prev_df['Score'].mean()
        
        # Moyennes par joueur
        curr_avg = week_df.groupby('Player')['Score'].mean()
        prev_avg = prev_df.groupby('Player')['Score'].mean()
        
        progression = {}
        for p in curr_avg.index:
            if p in prev_avg.index:
                # Filtre : Avoir joué au moins 3 matchs sur les deux semaines
                n_curr = len(week_df[week_df['Player'] == p])
                n_prev = len(prev_df[prev_df['Player'] == p])
                
                if n_curr >= 3 and n_prev >= 3:
                    delta = curr_avg[p] - prev_avg[p]
                    if delta > 0: # On ne garde que les progressions positives
                        progression[p] = delta
        
        if progression:
            # Conversion en Série pour utiliser get_winners_list
            s_prog = pd.Series(progression)
            # On prend les meilleurs et on formate (Joueur, +Val)
            raw_winners = get_winners_list(s_prog, maximize=True)
            # Petit formatage pour l'affichage (+X.X)
            remontada_winners = [(p, f"+{v:.1f}") for p, v in raw_winners]

    # 8. SUNDAY CLUTCH
    sunday_winners = []
    if has_sunday:
        sunday_df = week_df[week_df['Weekday'] == 6]
        if not sunday_df.empty:
            # On prend le max score du dimanche
            s_scores = sunday_df.groupby('Player')['Score'].max()
            sunday_winners = get_winners_list(s_scores, maximize=True)

    # 9. SÉRIES & DYNAMIQUES
    streaks_info = []
    current_pick_num = week_df['Pick'].max()
    
    # Calcul des records d'équipe (approximatif basé sur le max des joueurs actuels pour simplifier)
    # Dans l'idéal on scannerait tout l'historique, mais c'est coûteux.
    # On va comparer aux records PERSONNELS calculés.
    
    for p in week_df['Player'].unique():
        s = calculate_streaks(df, p, current_pick_num)
        
        # Logique de notification
        # Série No-Carrot (> 10)
        if s['active_nc'] >= 10:
            msg = "🔥"
            # Si on est proche du record perso (ou battu)
            if s['active_nc'] >= s['record_nc']: msg = "🚨 RECORD BATTU !"
            
            streaks_info.append({
                'player': p, 'type': 'Carotte Free', 'val': s['active_nc'], 
                'record': s['record_nc'], 'msg': msg
            })
            
        # Série > 30pts (> 4)
        if s['active_30'] >= 4:
            msg = "🔥"
            if s['active_30'] >= s['record_30']: msg = "🚨 RECORD BATTU !"
            
            streaks_info.append({
                'player': p, 'type': 'Série > 30pts', 'val': s['active_30'], 
                'record': s['record_30'], 'msg': msg
            })

    # 10. TEAM PULSE
    team_avg_curr = week_df['Score'].mean()
    diff_team = team_avg_curr - team_avg_prev
    
    total_carrots_team = len(week_df[week_df['Score'] < 20])
    total_bp_team = week_df['IsBP'].sum()
    
    # Clean Sheet (Score min >= 25)
    min_score = week_df['Score'].min()
    clean_sheet = min_score >= 25

    return {
        "meta": {
            "week_num": target_week_num,
            "has_sunday": has_sunday,
            "start_date": week_df['Date'].min().strftime('%d/%m'),
            "end_date": week_df['Date'].max().strftime('%d/%m')
        },
        "podium": weekly_podium,
        "rotw_leaderboard": sorted_rotw,
        "sniper": snipers,
        "muraille": murailles,
        "remontada": remontada_winners,
        "sunday_clutch": sunday_winners,
        "streaks": streaks_info,
        "team_stats": {
            "avg": team_avg_curr,
            "diff": diff_team,
            "carrots": total_carrots_team,
            "bp": total_bp_team,
            "clean_sheet": clean_sheet
        }
    }
