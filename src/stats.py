import pandas as pd
import numpy as np
import streamlit as st

# OPTIMISATION : CACHING STATS CALCULATION
@st.cache_data(ttl=300, show_spinner=False) 
def compute_stats(df, bp_map, daily_max_map):
    stats = []
    if df.empty: return pd.DataFrame()
    
    # Pré-calculs globaux pour le Medalist (Top 3 journalier)
    # On rank les scores par Pick pour savoir qui a fini 1er, 2e, 3e
    df['DailyRank'] = df.groupby('Pick')['Score'].rank(ascending=False, method='min')
    
    latest_pick = df['Pick'].max()
    season_avgs = df.groupby('Player')['Score'].mean()
    season_avgs_raw = df.groupby('Player')['ScoreVal'].mean()
    
    # Dataframes filtrés pour tendances
    df_15 = df[df['Pick'] > (latest_pick - 15)]
    avg_15 = df_15.groupby('Player')['Score'].mean()
    df_10 = df[df['Pick'] > (latest_pick - 10)]
    avg_10 = df_10.groupby('Player')['Score'].mean()
    
    trend_data = {}
    for p, d in df.sort_values('Pick').groupby('Player'): 
        trend_data[p] = d['Score'].tail(20).tolist()

    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        
        # Vecteurs de données
        scores = d['Score'].values
        scores_raw = d['ScoreVal'].values
        picks = d['Pick'].values
        bonuses = d['IsBonus'].values
        z_scores = d['ZScore'].values
        is_bp_list = d['IsBP'].values
        daily_ranks = d['DailyRank'].values
        months = d['Month'].values
        
        # --- 1. CALCULS BASIQUES ---
        bonus_data = d[d['IsBonus'] == True]
        scores_with_bonus = bonus_data['Score'].values
        scores_without_bonus = d[d['IsBonus'] == False]['Score'].values
        
        avg_with_bonus = scores_with_bonus.mean() if len(scores_with_bonus) > 0 else 0
        avg_without_bonus = scores_without_bonus.mean() if len(scores_without_bonus) > 0 else 0
        best_with_bonus = scores_with_bonus.max() if len(scores_with_bonus) > 0 else 0
        best_without_bonus = scores_without_bonus.max() if len(scores_without_bonus) > 0 else 0 # Pure Scorer
        
        # --- 2. CALCULS DE SÉRIES (HISTORIQUES) ---
        
        # Fonction helper pour max streak
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

        # Séries Actuelles (pour Trends)
        current_no_carrot_streak = 0
        for s in reversed(scores):
            if s >= 20: current_no_carrot_streak += 1
            else: break
            
        streak_30_curr = 0
        for s in reversed(scores):
            if s >= 30: streak_30_curr += 1
            else: break

        # Séries Historiques (pour Hall of Fame)
        max_no_carrot = get_max_streak(scores, 20) # Iron Man
        max_unstoppable = get_max_streak(scores, 40) # Unstoppable (>40)
        max_alien_streak = get_max_streak(scores, 60) # The Alien
        max_intouch_streak = get_max_streak(scores, 30) # Unstoppable (Legacy >30) / Intouchable

        # --- 3. CALCULS SPECIFIQUES (HOF) ---
        
        # Prime Time (Meilleur mois)
        try:
            prime_time = d.groupby('Month')['Score'].mean().max()
        except: prime_time = 0
        
        # Iron Lungs (Total Brut)
        iron_lungs = scores_raw.sum()
        
        # The 6th Man (30 <= Score < 40)
        sixth_man_count = len(scores[(scores >= 30) & (scores < 40)])
        
        # Medalist (Top 3 Daily)
        medalist_count = np.sum(daily_ranks <= 3)
        
        # Bad Luck (Max score sans BP)
        # On filtre les scores où IsBP est False, puis on prend le max
        non_bp_scores = scores[~is_bp_list] # ~ inverse le booléen
        bad_luck_score = non_bp_scores.max() if len(non_bp_scores) > 0 else 0
        
        # King of Decks (Max Rolling Sum 7j)
        deck_score = 0
        if len(scores) >= 7:
            deck_score = pd.Series(scores).rolling(window=7).sum().max()
            
        # The Phoenix (Rebond post-carotte)
        phoenix_score = 0
        for i in range(1, len(scores)):
            if scores[i-1] < 20: 
                if scores[i] > phoenix_score: phoenix_score = scores[i]

        # Mode (The Maniac)
        try:
            vals, counts = np.unique(scores, return_counts=True)
            max_count_idx = np.argmax(counts)
            mode_score = vals[max_count_idx]
            mode_count = counts[max_count_idx]
        except:
            mode_score = 0; mode_count = 0

        spread = scores.max() - scores.min()

        # --- 4. TENDANCES & FORME ---
        scores_last_7 = d['Score'].tail(7)
        avg_last_7 = scores_last_7.mean() if len(scores_last_7) > 0 else 0
        diff_7 = avg_last_7 - scores.mean() 
        
        if diff_7 >= 1: trend_icon = "↗️"
        elif diff_7 <= -1: trend_icon = "↘️"
        else: trend_icon = "➡️"
        
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()
        
        # OPTIMISATION : BP Count
        bp_count = d['IsBP'].sum()
        
        # Alpha Dog (Top scoreur team) & Bonus Logic
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
        
        # Moyennes & Pourcentages
        s_avg = season_avgs.get(p, 0)
        s_avg_raw = season_avgs_raw.get(p, 0)
        l15_avg = avg_15.get(p, s_avg)
        l10_avg = avg_10.get(p, s_avg)
        progression_pct = ((l15_avg - s_avg) / s_avg) * 100 if s_avg > 0 else 0
        reliability_pct = ((len(scores) - len(scores[scores < 20])) / len(scores)) * 100
        avg_z = np.mean(z_scores) if len(z_scores) > 0 else 0
        
        count_20_30 = len(scores[(scores >= 20) & (scores <= 30)])

        stats.append({
            'Player': p, 
            'Games': len(scores),
            'Total': scores.sum(), 
            'Moyenne': scores.mean(), 
            'Moyenne_Raw': s_avg_raw,
            'StdDev': scores.std(), 
            'Best': scores.max(), 
            'Best_Raw': scores_raw.max(), # Pure Scorer
            'Worst': scores.min(), 
            'Worst_Raw': scores_raw.min(), 
            'Last': scores[-1], 
            'LastIsBonus': bonuses[-1] if len(bonuses) > 0 else False, 
            'Last5': last5_avg, 'Last10': l10_avg, 'Last15': l15_avg,
            
            # Counts & Thresholds
            'Count30': len(scores[scores >= 30]), 
            'Count40': len(scores[scores >= 40]),
            'Count35': len(scores[scores > 35]), 
            'Count2030': count_20_30,
            'Carottes': len(scores[scores < 20]), 
            'Nukes': len(scores[scores >= 50]),
            
            # Streaks & HOF Metrics
            'Streak30_Curr': streak_30_curr,
            'MaxUnstoppable': max_unstoppable, # New > 40
            'MaxStreak30': max_intouch_streak,
            'CurrentNoCarrot': current_no_carrot_streak, 
            'MaxNoCarrot': max_no_carrot, # Iron Man
            'MaxAlien': max_alien_streak,
            'PrimeTime': prime_time,
            'IronLungs': iron_lungs,
            'SixthMan': sixth_man_count,
            'Medalist': medalist_count,
            'BadLuck': bad_luck_score,
            'MaxDeck': deck_score,
            'MaxPhoenix': phoenix_score,
            
            # Contextual
            'BP_Count': bp_count, 
            'Alpha_Count': alpha_count,
            'Bonus_Gained': bonus_points_gained, 
            'Best_Bonus': best_bonus, 
            'Worst_Bonus': worst_bonus,
            'Avg_Bonus': avg_bonus_score, 
            'Momentum': momentum, 
            'ProgressionPct': progression_pct, 
            'ReliabilityPct': reliability_pct, 
            'AvgZ': avg_z,
            'Trend': trend_data.get(p, []), 
            'AvgWithBonus': avg_with_bonus, 
            'AvgWithoutBonus': avg_without_bonus, 
            'BonusPlayed': len(scores_with_bonus),
            'ModeScore': mode_score, 
            'ModeCount': mode_count, 
            'Spread': spread,
            'Trend7Icon': trend_icon
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
