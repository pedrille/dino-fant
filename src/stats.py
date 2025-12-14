import pandas as pd
import numpy as np
import streamlit as st

# OPTIMISATION : CACHING STATS CALCULATION
@st.cache_data(ttl=300, show_spinner=False) 
def compute_stats(df, bp_map, daily_max_map):
    stats = []
    if df.empty: return pd.DataFrame()
    
    # --- PRÉ-CALCULS GLOBAUX (CONTEXTE) ---
    
    # 1. Moyennes et Rangs par jour pour Dominator, Medalist, Shield
    daily_groups = df.groupby('Pick')['Score']
    daily_means = daily_groups.mean()
    
    # Rang Descendant (1er = Meilleur score) pour Medalist
    df['RankDesc'] = daily_groups.rank(ascending=False, method='min')
    
    # Rang Ascendant (1er = Pire score) pour Shield
    df['RankAsc'] = daily_groups.rank(ascending=True, method='min')
    
    # 2. Identification du "Pire soir" pour The Savior
    daily_sums = daily_groups.sum()
    worst_night_pick = daily_sums.idxmin() if not daily_sums.empty else -1
    
    # 3. Soloist : Soirs où un SEUL joueur a dépassé 40
    over_40 = df[df['Score'] > 40].groupby('Pick')['Player'].count()
    soloist_picks = over_40[over_40 == 1].index.tolist()

    # --- CALCULS PAR JOUEUR ---
    
    # Prép. Trend Data
    trend_data = {}
    for p, d in df.sort_values('Pick').groupby('Player'): 
        trend_data[p] = d['Score'].tail(20).tolist()
    
    season_avgs = df.groupby('Player')['Score'].mean()
    season_avgs_raw = df.groupby('Player')['ScoreVal'].mean()
    latest_pick = df['Pick'].max()
    
    # Moyennes glissantes globales
    df_15 = df[df['Pick'] > (latest_pick - 15)]
    avg_15 = df_15.groupby('Player')['Score'].mean()
    df_10 = df[df['Pick'] > (latest_pick - 10)]
    avg_10 = df_10.groupby('Player')['Score'].mean()

    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        
        # Vecteurs de données
        scores = d['Score'].values
        scores_raw = d['ScoreVal'].values
        picks = d['Pick'].values
        bonuses = d['IsBonus'].values
        z_scores = d['ZScore'].values
        is_bp_list = d['IsBP'].values
        ranks_desc = d['RankDesc'].values
        ranks_asc = d['RankAsc'].values
        
        # --- 1. METRIQUES CLASSIQUES ---
        bonus_data = d[d['IsBonus'] == True]
        scores_with_bonus = bonus_data['Score'].values
        scores_without_bonus = d[d['IsBonus'] == False]['Score'].values
        
        avg_with_bonus = scores_with_bonus.mean() if len(scores_with_bonus) > 0 else 0
        avg_without_bonus = scores_without_bonus.mean() if len(scores_without_bonus) > 0 else 0
        best_with_bonus = scores_with_bonus.max() if len(scores_with_bonus) > 0 else 0
        best_without_bonus = scores_without_bonus.max() if len(scores_without_bonus) > 0 else 0 
        
        # --- 2. SÉRIES HISTORIQUES (Fonction Helper) ---
        def get_max_streak(val_list, threshold):
            max_s = 0
            curr_s = 0
            for v in val_list:
                if v >= threshold:
                    curr_s += 1
                    max_s = max(max_s, curr_s)
                else:
                    curr_s = 0
            return max_s

        # Séries en cours (Trends)
        current_no_carrot_streak = 0
        for s in reversed(scores):
            if s >= 20: current_no_carrot_streak += 1
            else: break
            
        streak_30_curr = 0
        for s in reversed(scores):
            if s >= 30: streak_30_curr += 1
            else: break

        # Séries HoF
        max_no_carrot = get_max_streak(scores, 20)
        max_unstoppable = get_max_streak(scores, 40)
        max_alien_streak = get_max_streak(scores, 60)
        
        # --- 3. LOGIQUES SPÉCIFIQUES HOF ---
        try: prime_time = d.groupby('Month')['Score'].mean().max()
        except: prime_time = 0
        
        iron_lungs = scores_raw.sum()
        sixth_man_count = len(scores[(scores >= 30) & (scores < 40)])
        medalist_count = np.sum(ranks_desc <= 3)
        last_place_count = np.sum(ranks_asc == 1)
        
        dominator_count = 0
        for pick_idx, sc in zip(picks, scores):
            if pick_idx in daily_means and sc > daily_means[pick_idx]:
                dominator_count += 1
                
        savior_val = 0
        savior_match = d[d['Pick'] == worst_night_pick]
        if not savior_match.empty:
            savior_val = savior_match['Score'].iloc[0]
            
        soloist_count = len(d[d['Pick'].isin(soloist_picks) & (d['Score'] > 40)])
        
        ghost_count = 0
        for sc, rk in zip(scores, ranks_desc):
            if sc > 35 and rk > 1:
                ghost_count += 1
                
        # CORRECTION BAD LUCK : Score BRUT max sans BP
        non_bp_raw_scores = scores_raw[~is_bp_list]
        bad_luck_score = non_bp_raw_scores.max() if len(non_bp_raw_scores) > 0 else 0
        
        bp_scores_only = scores[is_bp_list]
        braqueur_score = bp_scores_only.min() if len(bp_scores_only) > 0 else 999 
        
        deck_score = 0
        if len(scores) >= 7:
            deck_score = pd.Series(scores).rolling(window=7).sum().max()
            
        phoenix_score = 0
        for i in range(1, len(scores)):
            if scores[i-1] < 20 and scores[i] > phoenix_score: 
                phoenix_score = scores[i]

        try:
            vals, counts = np.unique(scores, return_counts=True)
            max_count_idx = np.argmax(counts)
            mode_score = vals[max_count_idx]
            mode_count = counts[max_count_idx]
        except: mode_score = 0; mode_count = 0

        spread = scores.max() - scores.min()

        # --- 4. EXPORT ---
        scores_last_7 = d['Score'].tail(7)
        avg_last_7 = scores_last_7.mean() if len(scores_last_7) > 0 else 0
        diff_7 = avg_last_7 - scores.mean() 
        trend_icon = "↗️" if diff_7 >= 1 else ("↘️" if diff_7 <= -1 else "➡️")
        
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        
        bp_count = d['IsBP'].sum()
        
        alpha_count = 0; bonus_points_gained = 0; bonus_scores_list = []
        for i, (pick_num, score) in enumerate(zip(picks, scores)):
            if pick_num in daily_max_map and score >= daily_max_map[pick_num] and score > 0: alpha_count += 1
            if bonuses[i]: 
                gain = score - scores_raw[i]
                bonus_points_gained += gain
                bonus_scores_list.append(score)
        
        best_bonus = max(bonus_scores_list) if bonus_scores_list else 0
        worst_bonus = min(bonus_scores_list) if bonus_scores_list else 0
        avg_bonus_score = np.mean(bonus_scores_list) if bonus_scores_list else 0
        
        s_avg = season_avgs.get(p, 0)
        s_avg_raw = season_avgs_raw.get(p, 0)
        l15_avg = avg_15.get(p, s_avg)
        l10_avg = avg_10.get(p, s_avg)
        progression_pct = ((l15_avg - s_avg) / s_avg) * 100 if s_avg > 0 else 0
        reliability_pct = ((len(scores) - len(scores[scores < 20])) / len(scores)) * 100
        avg_z = np.mean(z_scores) if len(z_scores) > 0 else 0
        
        count_20_30 = len(scores[(scores >= 20) & (scores <= 30)])

        stats.append({
            'Player': p, 'Games': len(scores),
            'Total': scores.sum(), 'Moyenne': scores.mean(), 'Moyenne_Raw': s_avg_raw,
            'StdDev': scores.std(), 'Best': scores.max(), 'Best_Raw': scores_raw.max(),
            'Worst': scores.min(), 'Worst_Raw': scores_raw.min(), 
            'Last': scores[-1], 'LastIsBonus': bonuses[-1] if len(bonuses) > 0 else False, 
            'Last5': last5_avg, 'Last10': l10_avg, 'Last15': l15_avg,
            
            # Counts
            'Count30': len(scores[scores >= 30]), 'Count40': len(scores[scores >= 40]),
            'Count35': len(scores[scores > 35]), 'Count2030': count_20_30,
            'Carottes': len(scores[scores < 20]), 'Nukes': len(scores[scores >= 50]),
            'BP_Count': bp_count, 'Alpha_Count': alpha_count,
            
            # HOF New Metrics
            'MaxUnstoppable': max_unstoppable,
            'PrimeTime': prime_time,
            'IronLungs': iron_lungs,
            'SixthMan': sixth_man_count,
            'Medalist': medalist_count,
            'ShieldCount': last_place_count,
            'Dominator': dominator_count,
            'SaviorScore': savior_val,
            'Soloist': soloist_count,
            'Ghost': ghost_count,
            'Braqueur': braqueur_score,
            'BadLuck': bad_luck_score,
            'MaxDeck': deck_score,
            'MaxPhoenix': phoenix_score,
            'CurrentNoCarrot': current_no_carrot_streak, 
            'MaxNoCarrot': max_no_carrot, 
            'MaxAlien': max_alien_streak,
            
            # Context
            'Bonus_Gained': bonus_points_gained, 'Best_Bonus': best_bonus, 'Worst_Bonus': worst_bonus,
            'Avg_Bonus': avg_bonus_score, 'Momentum': momentum, 'ProgressionPct': progression_pct, 
            'ReliabilityPct': reliability_pct, 'AvgZ': avg_z, 'Trend': trend_data.get(p, []), 
            'AvgWithBonus': avg_with_bonus, 'AvgWithoutBonus': avg_without_bonus, 'BonusPlayed': len(scores_with_bonus),
            'ModeScore': mode_score, 'ModeCount': mode_count, 'Spread': spread, 'Trend7Icon': trend_icon
        })
    return pd.DataFrame(stats)

def get_comparative_stats(df, current_pick, lookback=15):
    start_pick = max(1, current_pick - lookback)
    current_stats = df.groupby('Player')['Score'].agg(['sum', 'mean'])
    current_stats['rank'] = current_stats['sum'].rank(ascending=False)
    df_past = df[df['Pick'] <= start_pick]
    if df_past.empty: return pd.DataFrame() 
    past_stats = df_past.groupby('Player')['Score'].agg(['sum', 'mean'])
    past_stats['rank'] = past_stats['sum'].rank(ascending=False)
    stats_delta = pd.DataFrame(index=current_stats.index)
    stats_delta['mean_diff'] = current_stats['mean'] - past_stats['mean']
    stats_delta['rank_diff'] = past_stats['rank'] - current_stats['rank'] 
    return stats_delta

# --- NOUVELLE FONCTION POUR LE DUEL ---
def get_head_to_head_stats(df, p1, p2):
    # On filtre uniquement les données des deux joueurs
    df_filtered = df[df['Player'].isin([p1, p2])]
    
    # On pivote pour avoir : Index=Pick, Colonnes=Joueurs, Valeur=Score
    # dropna() permet de ne garder que les picks où LES DEUX ont joué
    pivot = df_filtered.pivot_table(index='Pick', columns='Player', values='Score').dropna()
    
    if pivot.empty or p1 not in pivot.columns or p2 not in pivot.columns:
        return 0, 0
    
    # Calcul des victoires
    wins_p1 = (pivot[p1] > pivot[p2]).sum()
    wins_p2 = (pivot[p2] > pivot[p1]).sum()
    
    return wins_p1, wins_p2
