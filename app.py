import os
from pathlib import Path
import pandas as pd
import streamlit as st
from model import MARKETS, norm_name, estimate, evaluate
from sources import load_game_logs, fetch_live_odds, validate_odds

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='NFL Prop Lab',page_icon='🏈',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
@media (max-width: 640px) {
 .block-container {padding-top: 1rem; padding-left: .85rem; padding-right: .85rem; padding-bottom: 2rem;}
 h1 {font-size: 1.65rem !important;}
 div[data-testid="stMetricValue"] {font-size: 1.25rem;}
 div[data-testid="stButton"] button {min-height: 3rem;}
}
</style>''',unsafe_allow_html=True)
st.title('🏈 NFL Prop Lab')
st.caption('Local research prototype • No wagers placed • Baseline probabilities are uncalibrated')
with st.expander('⚙️ Data sources and model settings', expanded=True):
    st.header('1. Player statistics')
    current_season=st.number_input('Target NFL season',min_value=2023,max_value=2035,value=2026,step=1)
    stat_file=st.file_uploader('Optional game logs CSV',type='csv',key='stat')
    refresh=st.checkbox('Refresh nflverse download (requires internet)',value=False)
    st.header('2. Player props')
    source=st.radio('Odds source',['Demo CSV','Upload CSV','The Odds API (live)'])
    odds_file=st.file_uploader('Odds CSV',type='csv',key='odds') if source=='Upload CSV' else None
    api_key=st.text_input('The Odds API key',type='password',value=os.getenv('ODDS_API_KEY','')) if source=='The Odds API (live)' else None
    region=st.selectbox('Sportsbook region',['us','us2','eu','uk','au']) if source=='The Odds API (live)' else 'us'
    event_limit=st.slider('Max games to request (may cost API credits)',1,16,8) if source=='The Odds API (live)' else 8
    st.header('3. Model assumptions')
    recency=st.slider('Current-season recent games',3,10,5)
    weight=st.slider('Current-season weighting',.2,.9,.65,.05)
    st.caption('Manual adjustments are scenario assumptions, not measured injury or opponent effects.')
    matchup=st.slider('Matchup / opposing defense adjustment (%)',-25,25,0)
    offense=st.slider('O-line / QB / playcaller adjustment (%)',-25,25,0)
    game=st.slider('Game script / weather adjustment (%)',-20,20,0)
    min_edge=st.slider('Minimum modeled ROI (%)',-20,50,0)
    run=st.button('🏈 Analyze props',type='primary',use_container_width=True)

st.info('Start with Demo CSV and select **Analyze props** (works offline using bundled fictional data). Actual NFL stats download on first run when using an uploaded or live odds source without a game-logs CSV. Demo odds are fabricated and must not be treated as market quotes.')
with st.expander('Required CSV formats'):
    st.code('player,market,side,line,odds,bookmaker,game,commence_time\nExample Player,player_rush_yds,Over,50.5,-110,SampleBook,AWAY @ HOME,2026-11-01T18:00:00Z')
    st.code('season,week,player_id,player_name,recent_team,rushing_yards,receiving_yards,receptions,carries\n2026,1,123,Example Player,SEA,75,12,2,17')
    st.write('Supported markets:',', '.join(MARKETS))

if run:
    try:
        if stat_file is not None:
            logs=pd.read_csv(stat_file)
        elif source=='Demo CSV':
            logs=pd.read_csv(ROOT/'data'/'demo_game_logs.csv')
        else:
            with st.spinner('Loading NFL game logs (first download can take a moment)...'):
                logs=load_game_logs(list(range(int(current_season)-3,int(current_season)+1)),refresh=refresh)
        required={'season','week','player_name',*MARKETS.values()}
        missing=required-set(logs.columns)
        if missing: raise ValueError(f'Game logs missing: {sorted(missing)}')
        logs['season']=pd.to_numeric(logs.season,errors='coerce')
        logs['week']=pd.to_numeric(logs.week,errors='coerce')
        if source=='Demo CSV':
            props=pd.read_csv(ROOT/'data'/'demo_props.csv')
        elif source=='Upload CSV':
            if odds_file is None: raise ValueError('Upload an odds CSV first.')
            props=pd.read_csv(odds_file)
        else:
            if not api_key: raise ValueError('Enter The Odds API key first.')
            with st.spinner('Fetching live odds; API usage may be billed...'):
                props=fetch_live_odds(api_key,region,event_limit)
        props=validate_odds(props)
        if props.empty: raise ValueError('No compatible odds available from this source.')
        # Avoid treating duplicate normalized names as unique players.
        logs['name_key']=logs.player_name.map(norm_name)
        props['name_key']=props.player.map(norm_name)
        unique=logs.groupby('name_key').player_name.nunique()
        ambiguous=set(unique[unique>1].index)
        records=[]; unmatched=[]
        for _,prop in props.iterrows():
            if prop.name_key in ambiguous:
                unmatched.append(f"{prop.player} (ambiguous identity)")
                continue
            history=logs[logs.name_key==prop.name_key]
            if history.empty:
                unmatched.append(prop.player); continue
            # When a game timestamp is available, prevent using stats from future seasons,
            # but week/date alignment requires a real game schedule and is not implemented.
            # Therefore live odds for the target season are unsafe for strict backtesting.
            history=history[history.season <= current_season]
            calc=estimate(history,prop.market,current_season,recency,weight,matchup,offense,game)
            if calc is None: continue
            ev=evaluate(calc,float(prop.line),prop.side,float(prop.odds))
            records.append({**prop.to_dict(),**calc,**ev})
        result=pd.DataFrame(records)
        if result.empty:
            st.warning('No player names from these prop rows matched game logs with enough observations. For demo mode, supply matching game logs or use the bundled sample logs.')
        else:
            result=result.sort_values('expected_roi_pct',ascending=False)
            st.session_state['results']=result
            st.session_state['unmatched']=sorted(set(unmatched))
            st.session_state['demo']=source=='Demo CSV'
    except Exception as exc:
        st.error(f'Unable to analyze: {exc}')

if 'results' in st.session_state:
    result=st.session_state.results
    displayed=result[result.expected_roi_pct>=min_edge]
    c1,c2,c3=st.columns(3)
    c1.metric('Props analyzed',len(result))
    c2.metric('Above ROI filter',len(displayed))
    c3.metric('Highest modeled ROI',f"{result.expected_roi_pct.max():.1f}%")
    if st.session_state.demo: st.warning('DEMO MODE: Lines and odds are fictional. Do not use these outputs for betting.')
    st.subheader('Top opportunities')
    for _, pick in displayed.head(8).iterrows():
        with st.container(border=True):
            st.markdown(f"**{pick['player']}** · {pick['bookmaker']}")
            st.write(f"{pick['side']} {pick['line']:g} · {pick['market']} · {int(pick['odds']):+d}")
            a,b=st.columns(2)
            a.metric('Model probability',f"{pick['model_prob']:.1%}")
            b.metric('Modeled ROI',f"{pick['expected_roi_pct']:+.1f}%")
            st.caption(f"Projection: {pick['projection']:.1f} · Break-even: {pick['break_even_prob']:.1%} · Games: {int(pick['games'])}")
    with st.expander('Full detailed results table'):
        st.dataframe(displayed[['player','market','side','line','odds','bookmaker','projection','std_dev','model_prob','break_even_prob','prob_edge_pp','expected_roi_pct','games','recent_avg','prior_avg']].style.format({
            'projection':'{:.1f}','std_dev':'{:.1f}','model_prob':'{:.1%}','break_even_prob':'{:.1%}',
            'prob_edge_pp':'{:+.1f}','expected_roi_pct':'{:+.1f}%','recent_avg':'{:.1f}','prior_avg':'{:.1f}'},na_rep='—'),use_container_width=True,hide_index=True)
    st.download_button('Download full analysis CSV',result.to_csv(index=False).encode(),file_name='nfl_prop_analysis.csv',mime='text/csv')
    if st.session_state.unmatched:
        with st.expander(f"Unmatched or ambiguous players ({len(st.session_state.unmatched)})"):
            st.write(st.session_state.unmatched)
    st.subheader('Interpreting the estimates')
    st.write('Probabilities use a Normal distribution with volatility estimated from player game logs and a conservative floor. Real NFL props can be skewed, discrete, and sensitive to injuries. Model outputs are **not calibrated or backtested**, so even high estimated ROI values may be spurious.')
    st.warning('Live injury feeds, opponent-adjusted defense, QB changes, lineup confirmation, odds histories, game-date leakage prevention, and rigorous walk-forward backtesting are planned but NOT implemented in this initial build. Manual scenario sliders apply to every player and should not be treated as measured effects.')
