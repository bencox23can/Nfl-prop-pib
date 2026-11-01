"""Transparent baseline model; research prototype, NOT a validated betting system."""
import math
import re
import numpy as np
import pandas as pd
from scipy.stats import norm

MARKETS = {
    'player_rush_yds': 'rushing_yards',
    'player_reception_yds': 'receiving_yards',
    'player_receptions': 'receptions',
    'player_rush_attempts': 'carries',
}

def norm_name(name):
    name = str(name).lower().replace('.', '').replace("'", '')
    name = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name)

def american_profit(odds):
    odds = float(odds)
    if odds == 0 or abs(odds) < 100:
        raise ValueError('American odds should be <= -100 or >= +100')
    return odds / 100 if odds > 0 else 100 / abs(odds)

def implied_probability(odds):
    return 1 / (1 + american_profit(odds))

def estimate(games, market, season, recency_games=5, current_weight=.65,
             matchup_pct=0, offensive_pct=0, game_pct=0):
    """Returns descriptive projection, not causally learned effects.

    All games strictly before the target event must be provided by the caller.
    current and prior game observations get separate season-aware weights.
    """
    stat = MARKETS[market]
    g = games.copy()
    g = g[pd.to_numeric(g[stat], errors='coerce').notna()].copy()
    g[stat] = pd.to_numeric(g[stat], errors='coerce')
    g['season'] = pd.to_numeric(g['season'], errors='coerce')
    g['week'] = pd.to_numeric(g['week'], errors='coerce')
    g = g.sort_values(['season','week'])
    current = g[g.season == season]
    history = g[(g.season < season) & (g.season >= season - 3)]
    if len(g) < 3: return None
    recent = current.tail(recency_games)
    prior = history.tail(48)
    if len(recent) and len(prior):
        # Shrink current-year influence when sample small
        effective_weight = current_weight * len(recent)/(len(recent) + 4) + .15
        effective_weight = min(.9,max(.15,effective_weight))
        base = effective_weight*recent[stat].mean() + (1-effective_weight)*prior[stat].mean()
    elif len(recent): base = recent[stat].mean()
    elif len(prior): base = prior[stat].mean()
    else: return None
    # Adjustments intentionally human-entered, and capped to avoid unrealistic extrapolation.
    adj = np.clip((matchup_pct + offensive_pct + game_pct)/100, -.35, .35)
    mean = max(0, float(base * (1+adj)))
    # Conservative floor on dispersion; cannot assume certainty from small sample
    sample = g.tail(40)[stat]
    sd = max(float(sample.std(ddof=1)) if len(sample)>1 else 0, max(2, mean*.27))
    return {'projection':mean,'std_dev':sd,'games':len(g), 'current_games':len(current),
            'recent_avg':float(recent[stat].mean()) if len(recent) else None,
            'prior_avg':float(prior[stat].mean()) if len(prior) else None,
            'base':float(base), 'adjustment_pct':float(adj*100)}

def evaluate(estimate_result, line, side, odds):
    mu, sd = estimate_result['projection'], estimate_result['std_dev']
    if side.lower() == 'over':
        p = float(norm.sf(line, loc=mu, scale=sd))
    elif side.lower() == 'under':
        p = float(norm.cdf(line, loc=mu, scale=sd))
    else: raise ValueError('Side must be Over or Under')
    profit=american_profit(odds)
    return {'model_prob':p, 'break_even_prob':1/(1+profit),
            'prob_edge_pp':100*(p-1/(1+profit)), 'expected_roi_pct':100*(p*profit-(1-p))}
