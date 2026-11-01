import pandas as pd
from model import implied_probability, estimate, evaluate

def test_implied():
    assert abs(implied_probability(-110)-.5238095)<1e-5
    assert abs(implied_probability(150)-.4)<1e-8

def test_projection():
    g=pd.DataFrame({'season':[2024]*5+[2026]*5,'week':list(range(1,6))*2,
                    'rushing_yards':[80]*5+[50]*5})
    r=estimate(g,'player_rush_yds',2026)
    assert 50 < r['projection'] < 80
    e=evaluate(r,50.5,'Over',-110)
    assert 0 <= e['model_prob'] <= 1
    assert e['expected_roi_pct'] > -100
