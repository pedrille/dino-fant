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
    p_df = df[(df['Player'] == player) & (df['Pick'] <= current_pick_limit)].sort_values('Pick')
    scores = p_df['Score'].values
    
    # 1. Série Sans Carotte (> 20)
    curr_no_carrot = 0
    max_no_carrot = 0
    temp_nc = 0
    
    # Historique
    for s in scores:
        if s >= 20:
            temp_nc += 1
            max_no_carrot = max(max_no_carrot, temp_nc)
        else:
            temp_nc = 0
            
    # Active (depuis la fin)
    for s in reversed(scores):
        if s >= 20: curr_no_carrot += 1
        else: break
        
    # 2. Série > 30
    curr_30 = 0
    max_30 = 0
    temp_30 = 0
    
    for s in scores:
        if s >= 30:
            temp_30 += 1
            max_30 = max(max_30, temp_30)
        else:
            temp_30 = 0
            
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
    """
    if df_full.empty: return None

    # Conversion et préparation
    df = df_full.copy()
    # On s'assure d'avoir des dates
    # (Supposons que df a une colonne 'Date' ou qu'on peut déduire les semaines via les picks si séquentiels)
    # Pour être robuste, on va utiliser les semaines ISO via une fausse date si pas de date réelle, 
    # mais ici on suppose que le fichier source a des dates ou on groupe par 7 picks.
    # Mieux : On utilise la colonne 'Date' du GSheet si chargée, sinon on simule.
    # HYPOTHESE FORTE : df a une colonne 'Date' au format datetime.
    
    # Si 'Date' n'est pas datetime, on convertit
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['WeekNum'] = df['Date'].dt.isocalendar().week
        df['Weekday'] = df['Date'].dt.weekday # 0=Lundi, 6=Dimanche
    else:
        return {"error": "Pas de colonne Date trouvée."}

    # 1. Identifier la dernière semaine COMPLÈTE ou EN COURS
    # On prend le dernier pick joué
    last_pick = df.sort_values('Pick').iloc[-1]
    target_week_num = last_pick['WeekNum']
    
    # Data de la semaine cible
    week_df = df[df['WeekNum'] == target_week_num].copy()
    
    # Check si Dimanche est joué
    has_sunday = 6 in week_df['Weekday'].values
    
    # 2. CALCUL HISTORIQUE ROTW (Raptor of the Week)
    # On parcourt toutes les semaines précédentes pour compter les titres
    rotw_history = {} # {Player: Nb_Titres}
    all_weeks = sorted(df['WeekNum'].unique())
    
    for w in all_weeks:
        if w >= target_week_num: continue # On s'arrête avant la semaine actuelle pour l'historique
        
        w_data = df[df['WeekNum'] == w]
        if w_data.empty: continue
        
        # Somme des scores de la semaine w
        w_scores = w_data.groupby('Player')['Score'].sum()
        if w_scores.empty: continue
        
        max_score = w_scores.max()
        winners = w_scores[w_scores == max_score].index.tolist()
        
        for p in winners:
            rotw_history[p] = rotw_history.get(p, 0) + 1

    # 3. PODIUM DE LA SEMAINE ACTUELLE
    weekly_scores = week_df.groupby('Player')['Score'].sum().sort_values(ascending=False)
    weekly_podium = []
    
    # Top 3 (avec gestion ex-aequo implicite par l'ordre, mais on va raffiner l'affichage plus tard)
    for i, (player, score) in enumerate(weekly_scores.head(3).items()):
        nb_titles = rotw_history.get(player, 0)
        # Si le joueur est 1er cette semaine, on lui ajoute virtuellement son titre pour l'affichage
        if i == 0: 
            # Attention s'il y a ex-aequo pour la 1ere place
            if score == weekly_scores.iloc[0]:
                nb_titles += 1
        
        weekly_podium.append({
            'rank': i+1,
            'player': player,
            'score': int(score),
            'titles': nb_titles
        })

    # 4. CLASSEMENT ROTW SAISON (Top 3)
    # On met à jour l'historique avec la semaine actuelle pour le classement final
    current_winners = get_winners_list(weekly_scores, maximize=True)
    for p, _ in current_winners:
        rotw_history[p] = rotw_history.get(p, 0) + 1
        
    sorted_rotw = sorted(rotw_history.items(), key=lambda x: x[1], reverse=True)[:3]

    # 5. SNIPER HEBDO (Max BP cette semaine)
    weekly_bp = week_df.groupby('Player')['IsBP'].sum()
    snipers = get_winners_list(weekly_bp, maximize=True)
    
    # 6. LA MURAILLE (Min Carottes cette semaine)
    # On ne considère que ceux qui ont joué au moins 4 matchs cette semaine pour éviter les absents
    games_played = week_df.groupby('Player')['Score'].count()
    active_players = games_played[games_played >= 4].index
    
    if not active_players.empty:
        weekly_carrots = week_df[week_df['Player'].isin(active_players)]
        # Compter les scores < 20
        carrot_counts = weekly_carrots[weekly_carrots['Score'] < 20].groupby('Player')['Score'].count()
        # Ceux qui n'ont pas de carottes ne sont pas dans le groupby, il faut les ajouter à 0
        for p in active_players:
            if p not in carrot_counts.index:
                carrot_counts[p] = 0
        
        murailles = get_winners_list(carrot_counts, maximize=False) # On cherche le min
    else:
        murailles = []

    # 7. REMONTADA (Progression Moyenne vs Semaine Précédente)
    prev_week_num = all_weeks[all_weeks.index(target_week_num) - 1] if all_weeks.index(target_week_num) > 0 else None
    remontada_winners = []
    
    if prev_week_num:
        prev_df = df[df['WeekNum'] == prev_week_num]
        
        # On calcule les moyennes
        curr_avg = week_df.groupby('Player')['Score'].mean()
        prev_avg = prev_df.groupby('Player')['Score'].mean()
        
        # On garde ceux qui ont joué assez de matchs les 2 semaines
        progression = {}
        for p in curr_avg.index:
            if p in prev_avg.index:
                # Check volume matchs (ex: min 3 matchs)
                nb_curr = len(week_df[week_df['Player'] == p])
                nb_prev = len(prev_df[prev_df['Player'] == p])
                
                if nb_curr >= 3 and nb_prev >= 3:
                    delta = curr_avg[p] - prev_avg[p]
                    if delta > 0:
                        progression[p] = delta
                        
        if progression:
            # On prend le max
            max_prog = max(progression.values())
            remontada_winners = [(p, v) for p, v in progression.items() if v == max_prog]

    # 8. SUNDAY CLUTCH (MVP Dimanche)
    sunday_winners = []
    if has_sunday:
        sunday_df = week_df[week_df['Weekday'] == 6]
        if not sunday_df.empty:
            sunday_scores = sunday_df.groupby('Player')['Score'].max() # Max au cas où bug doublon
            sunday_winners = get_winners_list(sunday_scores, maximize=True)

    # 9. SÉRIES & DYNAMIQUES
    # On scanne les joueurs du podium + quelques randoms pour trouver des séries intéressantes
    streaks_info = []
    # On regarde tout le monde
    current_pick_num = week_df['Pick'].max()
    
    # Record Team pour comparaison
    team_records = {
        'nc': 0, '30': 0
    }
    # On scanne vite fait les records team
    # (Simplification : on prend des valeurs hardcodées ou on ferait un scan complet, 
    #  ici on va calculer pour chaque joueur et prendre le max)
    
    players_streaks = {}
    for p in df['Player'].unique():
        s = calculate_streaks(df, p, current_pick_num)
        players_streaks[p] = s
        team_records['nc'] = max(team_records['nc'], s['record_nc'])
        team_records['30'] = max(team_records['30'], s['record_30'])
        
    # Filtrage des séries intéressantes à afficher
    for p, s in players_streaks.items():
        # Série No-Carrot significative (> 10)
        if s['active_nc'] >= 10:
            status = "🔥"
            if s['active_nc'] >= s['record_nc']: status = "🚨 RECORD PERSO !"
            if s['active_nc'] >= team_records['nc']: status = "👑 RECORD TEAM !"
            streaks_info.append({
                'player': p, 'type': 'Carotte Free', 'val': s['active_nc'], 
                'record': s['record_nc'], 'msg': status
            })
            
        # Série > 30 significative (> 4)
        if s['active_30'] >= 4:
            status = "🔥"
            if s['active_30'] >= s['record_30']: status = "🚨 RECORD PERSO !"
            streaks_info.append({
                'player': p, 'type': 'Série > 30pts', 'val': s['active_30'], 
                'record': s['record_30'], 'msg': status
            })

    # 10. TEAM PULSE (Chiffres clés)
    team_avg_curr = week_df['Score'].mean()
    team_avg_prev = prev_df['Score'].mean() if prev_week_num else 0
    diff_team = team_avg_curr - team_avg_prev
    
    total_carrots_team = len(week_df[week_df['Score'] < 20])
    total_bp_team = week_df['IsBP'].sum()
    
    # Min score equipe (Clean Sheet check)
    min_score_team = week_df['Score'].min()
    clean_sheet = min_score_team >= 25 # Seuil arbitraire clean sheet

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
