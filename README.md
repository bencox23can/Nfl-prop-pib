# NFL Prop Lab — local prototype (v0.1)

This is a local Streamlit application for comparing NFL player game logs with player prop lines. It is an **experimental, uncalibrated statistical model**, not verified positive-EV advice.

## Setup on Windows

1. Install Python 3.11 or 3.12 from python.org and enable **Add python.exe to PATH**.
2. Unzip the folder anywhere on your Windows PC.
3. Double-click `START_WINDOWS.bat`. On the first launch, Python downloads packages; your browser opens the app at `http://localhost:8501`.
4. For a guaranteed offline first run, select **Demo CSV** and click **Analyze props**; bundled fictional game logs are automatically used. You can also explicitly upload `data/demo_game_logs.csv`.
5. For actual player logs, leave the stats uploader empty and select **Analyze props** with internet available. The first request uses `nflreadpy` to download the target year plus the prior three seasons. Downloaded game logs are cached locally at `data/game_logs.csv`.
6. Upload an odds CSV with real player names, or enter your own The Odds API key to fetch live odds. Real odds require valid product coverage and may consume credits. Availability and permitted sportsbooks vary by region.

## Required odds CSV

`player,market,side,line,odds,bookmaker`

Optional: `game,commence_time,event_id,snapshot_time`

Market identifiers: `player_rush_yds`, `player_rush_attempts`, `player_reception_yds`, `player_receptions`. Side is `Over` or `Under`; odds use American format (e.g. -110 or +125).

## Required stats CSV

`season,week,player_name,rushing_yards,receiving_yards,receptions,carries`

Optional: `player_id,recent_team`. Every row should represent one **regular-season player-game**. For demonstration, see `data/demo_game_logs.csv`. The CSV import does not automatically filter pre/postseason or resolve duplicate player aliases.

## What is implemented

- Historical and current season mean blend, downweighted for small current-year samples.
- Player-specific empirical standard deviation with a floor; Normal approximation to evaluate over/under.
- Optional globally-applied scenario adjustments for defense, offensive personnel and game conditions.
- Real American-odds break-even, outcome probability, estimated ROI, results download.
- Optional The Odds API v4 upcoming event and per-event prop odds ingestion.
- Transparent offline fabricated samples and sanity tests.

## Limitations — important

- No learned defense rankings, automated injury effects or playcaller change detection yet. Scenario adjustments are **manual** and affect all players equally.
- No bet settlement, line comparison against a no-vig consensus, vig removal, performance calibration or statistical backtesting yet.
- No timestamped injury data, event-specific gameweek filtering, or walk-forward historical evaluation. **Do not use this version to evaluate historical pregame picks or claim genuine expected edge.** The stats importer can include games played after an odds snapshot for current-season comparisons.
- The demos are fictional. NFL data and API access depend on connectivity and providers; remote schemas may change.
- Player matching uses normalized display names; name variants, trades, duplicate names and initials can yield missed or wrong matches. Confirm identity for any actual analysis.
- Normal distributions are an imperfect fit for discrete catches/attempts and fat-tailed yardage. High apparent ROI may reflect model miscalibration.

## Next development milestones

1. Time-aware weekly game cutoffs using schedule IDs, roster IDs and odds timestamps.
2. Opponent-adjusted defensive features, offensive line/QB injuries, snaps and expected opportunities.
3. Historical prop snapshots and walk-forward performance testing with calibration.
4. Market consensus, no-vig reference lines, live odds snapshots and automated tracking.

## Run tests

`python -m pytest tests -q`

## Data providers

- nflreadpy: https://nflreadpy.nflverse.com/
- The Odds API v4: https://the-odds-api.com/liveapi/guides/v4/

## Mobile access

See [DEPLOY_MOBILE.md](DEPLOY_MOBILE.md) for same-Wi-Fi phone launch or optional Streamlit cloud hosting. The interface includes compact phone-friendly cards.
