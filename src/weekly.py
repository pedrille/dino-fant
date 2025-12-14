import pandas as pd
import numpy as np

def get_winners_list(series, maximize=True):
    """ Gestion des égalités """
    if series.empty: return []
    target_val = series.max() if maximize else series.min()
    winners = series[series == target_val]
    return [(player, val) for player, val in winners.items()]

def calculate_streaks(df, player, current_pick_limit):
    """ Calcul des séries jusqu'au pick actuel """
    p_df = df[(df['Player'] == player) & (df['Pick'] <= current_pick_limit)].sort_values('Pick')
    if p_df.empty: return {'active_nc': 0, 'record_nc': 0, 'active_30': 0, 'record_30': 0}

    scores = p_df['Score'].values
    
    # Série No Carrot
    curr_nc, max_nc, temp_nc = 0, 0, 0
    for s in scores:
        if s >= 20: temp_nc += 1; max_nc = max(max_nc, temp_nc)
        else: temp_nc = 0
    for s in reversed(scores):
        if s >= 20: curr_nc += 1
        else: break
        
    # Série > 30
    curr_30, max_30, temp_30 = 0, 0, 0
    for s in scores:
        if s >= 30: temp_30 += 1; max_30 = max(max_30, temp_30)
        else: temp_30 = 0
    for s in reversed(scores):
        if s >= 30: curr_30 += 1
        else: break
        
    return {'active_nc': curr_nc, 'record_nc': max_nc, 'active_30': curr_30, 'record_30': max_30}

def generate_weekly_report_data(df_full):
    """
    Génère le rapport basé sur les DECKS (Semaines TTFL).
    """
    # Vérification colonne Deck
    if df_full.empty or 'Deck' not in df_full.columns:
        return None

    df = df_full.copy()
    
    # 1. IDENTIFIER LE DECK CIBLE (Le dernier joué ou en cours)
    target_deck = df['Deck'].max()
    
    # Sécurité si Deck 0 ou inexistant
    if pd.isna(target_deck) or target_deck == 0: return None
    
    # Données de la semaine (Deck)
    week_df = df[df['Deck'] == target_deck].copy()
    if week_df.empty: return None
    
    # Dates esthétiques (basées sur le pick min/max du deck)
    start_date = week_df['Date'].min().strftime('%d/%m')
    end_date = week_df['Date'].max().strftime('%d/%m')
    
    # 2. HISTORIQUE ROTW (Decks passés)
    rotw_history = {}
    all_decks = sorted(df['Deck'].unique())
    
    for d in all_decks:
        if d >= target_deck: continue
        if d == 0: continue
        
        d_data = df[df['Deck'] == d]
        if d_data.empty: continue
        
        d_scores = d_data.groupby('Player')['Score'].sum()
        if d_scores.empty: continue
        
        max_s = d_scores.max()
        winners = d_scores[d_scores == max_s].index.tolist()
        for p in winners:
            rotw_history[p] = rotw_history.get(p, 0) + 1

    # 3. PODIUM SEMAINE
    weekly_scores = week_df.groupby('Player')['Score'].sum().sort_values(ascending=False)
    weekly_podium = []
    
    for i, (player, score) in enumerate(weekly_scores.head(3).items()):
        nb_titles = rotw_history.get(player, 0)
        # Gestion du rang affiché (ex-aequo)
        rank_disp = i + 1
        if i == 0:
            if score == weekly_scores.iloc[0]: nb_titles += 1
        elif i > 0 and score == weekly_scores.iloc[i-1]:
            rank_disp = weekly_podium[-1]['rank']
            
        weekly_podium.append({'rank': rank_disp, 'player': player, 'score': int(score), 'titles': nb_titles})

    # 4. CLASSEMENT ROTW
    current_winners = get_winners_list(weekly_scores, maximize=True)
    temp_hist = rotw_history.copy()
    for p, _ in current_winners: temp_hist[p] = temp_hist.get(p, 0) + 1
    sorted_rotw = sorted(temp_hist.items(), key=lambda x: x[1], reverse=True)[:3]

    # 5. STATS INDIV (Sniper / Muraille)
    weekly_bp = week_df.groupby('Player')['IsBP'].sum()
    snipers = get_winners_list(weekly_bp[weekly_bp > 0], maximize=True)
    
    # Muraille : min 4 matchs joués dans le deck pour être éligible (ou max possible)
    max_games = week_df.groupby('Player')['Score'].count().max()
    threshold = max(4, max_games - 1) # Tolérance de 1 match manqué
    eligible = week_df.groupby('Player')['Score'].count()
    eligible = eligible[eligible >= threshold].index
    
    murailles = []
    if not eligible.empty:
        sub = week_df[week_df['Player'].isin(eligible)]
        carrots = sub[sub['Score'] < 20].groupby('Player')['Score'].count()
        full_carrots = pd.Series(0, index=eligible).add(carrots, fill_value=0)
        murailles = get_winners_list(full_carrots, maximize=False)

    # 6. REMONTADA
    remontada_winners = []
    team_avg_prev = 0
    prev_deck = target_deck - 1
    
    if prev_deck > 0:
        prev_df = df[df['Deck'] == prev_deck]
        if not prev_df.empty:
            team_avg_prev = prev_df['Score'].mean()
            curr_avg = week_df.groupby('Player')['Score'].mean()
            prev_avg = prev_df.groupby('Player')['Score'].mean()
            
            progression = {}
            for p in curr_avg.index:
                if p in prev_avg.index:
                    delta = curr_avg[p] - prev_avg[p]
                    if delta > 0: progression[p] = delta
            
            if progression:
                s_prog = pd.Series(progression)
                raw_winners = get_winners_list(s_prog, maximize=True)
                remontada_winners = [(p, f"+{v:.1f}") for p, v in raw_winners]

    # 7. SUNDAY CLUTCH (Dernier Pick du Deck)
    last_pick_of_deck = week_df['Pick'].max()
    sunday_df = week_df[week_df['Pick'] == last_pick_of_deck]
    sunday_winners = get_winners_list(sunday_df.groupby('Player')['Score'].max(), maximize=True)

    # 8. SÉRIES
    streaks_info = []
    current_pick_num = week_df['Pick'].max()
    for p in week_df['Player'].unique():
        s = calculate_streaks(df, p, current_pick_num)
        if s['active_nc'] >= 10:
            msg = "🔥"
            if s['active_nc'] >= s['record_nc']: msg = "🚨 RECORD BATTU !"
            streaks_info.append({'player': p, 'type': 'Carotte Free', 'val': s['active_nc'], 'record': s['record_nc'], 'msg': msg})
        if s['active_30'] >= 4:
            msg = "🔥"
            if s['active_30'] >= s['record_30']: msg = "🚨 RECORD BATTU !"
            streaks_info.append({'player': p, 'type': 'Série > 30pts', 'val': s['active_30'], 'record': s['record_30'], 'msg': msg})

    # 9. TEAM PULSE
    team_avg_curr = week_df['Score'].mean()
    diff_team = team_avg_curr - team_avg_prev
    total_carrots = len(week_df[week_df['Score'] < 20])
    total_bp = week_df['IsBP'].sum()
    clean_sheet = week_df['Score'].min() >= 25

    return {
        "meta": {
            "week_num": int(target_deck),
            "has_sunday": True, # Avec les decks, on assume que la semaine est finie/en cours
            "start_date": start_date,
            "end_date": end_date
        },
        "podium": weekly_podium,
        "rotw_leaderboard": sorted_rotw,
        "sniper": snipers,
        "muraille": murailles,
        "remontada": remontada_winners,
        "sunday_clutch": sunday_winners,
        "streaks": streaks_info,
        "team_stats": {
            "avg": team_avg_curr, "diff": diff_team,
            "carrots": total_carrots, "bp": total_bp, "clean_sheet": clean_sheet
        }
    }
