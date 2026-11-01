"""NFL game logs and optional live odds. No background calls or stored API keys."""
from pathlib import Path
import requests
import pandas as pd
from model import MARKETS

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'data'/'game_logs.csv'

def load_game_logs(seasons, refresh=False):
    if CACHE.exists() and not refresh:
        df=pd.read_csv(CACHE)
        if set(seasons).issubset(set(df.season.astype(int).unique())):
            return df[df.season.isin(seasons)].copy()
    import nflreadpy as nfl
    frame=nfl.load_player_stats(seasons)
    df=frame.to_pandas()
    # nflverse calls rushing attempts 'carries'; defensive stats not loaded in MVP.
    needed=['season','week','player_id','player_name','recent_team','rushing_yards','receiving_yards','receptions','carries']
    aliases={'player_name':['player_display_name','player_name','player_name_short'],
             'recent_team':['recent_team','team'],'carries':['carries','rushing_attempts'],
             'rushing_yards':['rushing_yards'], 'receiving_yards':['receiving_yards'],
             'receptions':['receptions'],'player_id':['player_id','gsis_id'],
             'season':['season'],'week':['week']}
    for dest, choices in aliases.items():
        if dest not in df.columns:
            src=next((a for a in choices if a in df.columns),None)
            if src is None: raise RuntimeError(f'Missing NFL data field: {dest}. Available: {list(df.columns)[:30]}')
            df[dest]=df[src]
    if 'season_type' in df.columns:
        df=df[df.season_type=='REG']
    df=df[needed].copy()
    # Prevent duplicated records from producing impossible weighted averages.
    df=df.drop_duplicates(['season','week','player_id'])
    CACHE.parent.mkdir(exist_ok=True)
    df.to_csv(CACHE,index=False)
    return df[df.season.isin(seasons)].copy()

def fetch_live_odds(key, region='us', max_events=16):
    """Queries The Odds API v4 one event at a time; each event consumes odds quota."""
    session=requests.Session()
    base='https://api.the-odds-api.com/v4/sports/americanfootball_nfl'
    r=session.get(base+'/events',params={'apiKey':key},timeout=25)
    r.raise_for_status()
    events=r.json()[:max_events]
    result=[]
    for event in events:
        response=session.get(f"{base}/events/{event['id']}/odds",params={
            'apiKey':key,'regions':region,'markets':','.join(MARKETS), 'oddsFormat':'american'
        }, timeout=35)
        response.raise_for_status()
        payload=response.json()
        for book in payload.get('bookmakers',[]):
            for market in book.get('markets',[]):
                if market['key'] not in MARKETS: continue
                for o in market.get('outcomes',[]):
                    if o.get('name') not in ('Over','Under') or 'point' not in o: continue
                    result.append({'player':o.get('description',''), 'market':market['key'],
                     'side':o['name'], 'line':o['point'], 'odds':o['price'],
                     'bookmaker':book.get('title',''), 'game':f"{event.get('away_team','')} @ {event.get('home_team','')}",
                     'commence_time':event.get('commence_time',''), 'event_id':event['id'],
                     'snapshot_time':book.get('last_update','')})
    return pd.DataFrame(result)

REQUIRED_ODDS=['player','market','side','line','odds','bookmaker']
def validate_odds(df):
    df=df.copy()
    missing=set(REQUIRED_ODDS)-set(df.columns)
    if missing: raise ValueError('Odds CSV missing columns: '+', '.join(sorted(missing)))
    df['line']=pd.to_numeric(df.line,errors='coerce')
    df['odds']=pd.to_numeric(df.odds,errors='coerce')
    df=df[df.market.isin(MARKETS) & df.side.isin(['Over','Under'])]
    df=df[df.line.notna() & df.odds.notna() & (df.odds.abs()>=100)]
    return df
