import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="Free Kenya Surebet Tool + Auto Scan", layout="wide")
st.title("🎯 Free Arbitrage Surebet Tool (Kenya Edition + Auto Scan)")
st.markdown("**100% free • Manual + Auto with The Odds API** • Works offline/manual anytime, auto needs internet & free API key.")

# === MANUAL MODE ===
st.header("1. Manual Surebet Scanner (Local Kenyan Bookies)")
outcomes = st.number_input("Number of outcomes (2 for OU, 3 for 1X2)", min_value=2, max_value=5, value=3)

odds = []
bookies = []
outcome_names = []

for i in range(outcomes):
    col1, col2, col3 = st.columns(3)
    with col1:
        outcome_name = st.text_input(f"Outcome {i+1} name (e.g. Home, Draw, Away)", key=f"n{i}")
    with col2:
        bookie = st.text_input(f"Bookie {i+1} (e.g. SportPesa)", key=f"b{i}")
    with col3:
        odd = st.number_input(f"Odds {i+1}", min_value=1.01, value=2.0, key=f"o{i}")
    outcome_names.append(outcome_name or f"Outcome {i+1}")
    bookies.append(bookie)
    odds.append(odd)

if st.button("🔍 Check Manual Surebet"):
    total_implied = sum(1 / o for o in odds if o > 0)
    if total_implied < 1:
        profit_pct = round((1 - total_implied) * 100, 2)
        st.success(f"✅ SUREBET! Guaranteed profit: **{profit_pct}%**")
        
        total_stake = st.number_input("Total stake (KSh)", min_value=100, value=1000, key="man_stake")
        stakes = [round(total_stake * (1/o) / total_implied, 0) for o in odds]
        return_amount = round(total_stake / total_implied, 0)
        
        df = pd.DataFrame({
            "Outcome": outcome_names,
            "Bookie": bookies,
            "Odds": odds,
            "Stake (KSh)": stakes,
            "Payout if wins": [round(s * o, 0) for s, o in zip(stakes, odds)]
        })
        st.table(df)
        st.info(f"**Total stake: KSh {total_stake:,}** → **Guaranteed return: KSh {return_amount:,}** (profit ~KSh {int(return_amount - total_stake):,})")
        st.caption("Kenya: Factor 7.5% excise + 20% tax — aim for >2% profit to cover.")
    else:
        st.error("No surebet. Sum of implied probs >=100%.")

# === AUTO SCAN MODE ===
st.divider()
st.header("2. Auto Scan with The Odds API (Free 500 credits/mo)")

st.info("""
Sign up free: https://the-odds-api.com (30 sec, no card) → Get API key → paste below.
Focus: soccer (football). Regions: 'eu' for 1xBet etc. (good for Kenya access).
""")

api_key = st.text_input("Your The Odds API Key", type="password", key="api_key")
sport_key = st.selectbox("Sport/League", [
    "soccer_epl", "soccer_uefa_champs_league", "soccer_spain_la_liga", 
    "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_france_ligue_one"
], index=0)
region = st.selectbox("Region (bookmakers)", ["eu", "uk", "us", "au"], index=0)  # eu best for 1xBet
markets = st.multiselect("Markets", ["h2h", "totals", "spreads"], default=["h2h"])

if api_key and st.button("🚀 Scan for Potential Surebets"):
    if not api_key:
        st.error("Paste your API key first!")
    else:
        with st.spinner("Fetching odds... (uses 1 credit if h2h + 1 region)"):
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
            params = {
                "apiKey": api_key,
                "regions": region,
                "markets": ",".join(markets),
                "oddsFormat": "decimal",
                "dateFormat": "iso"
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    st.warning("No upcoming matches found for this league right now.")
                else:
                    st.success(f"Found {len(data)} upcoming/live matches!")
                    
                    # Simple arb detector: look for 3-way (h2h) mismatches across bookies
                    for event in data[:5]:  # Limit to first 5 to avoid overload
                        home = event.get("home_team", "Home")
                        away = event.get("away_team", "Away")
                        commence = event.get("commence_time", "TBD")
                        
                        st.subheader(f"{home} vs {away} ({commence})")
                        
                        bookie_odds = {}
                        for book in event.get("bookmakers", []):
                            bkey = book["key"]
                            for m in book["markets"]:
                                if m["key"] == "h2h":
                                    for out in m["outcomes"]:
                                        name = out["name"]
                                        price = out["price"]
                                        if name not in bookie_odds:
                                            bookie_odds[name] = {}
                                        bookie_odds[name][bkey] = price
                        
                        # Find best odds per outcome
                        if "Home" in bookie_odds and "Draw" in bookie_odds and "Away" in bookie_odds:
                            best_home = max(bookie_odds["Home"].values()) if bookie_odds["Home"] else 0
                            best_draw = max(bookie_odds["Draw"].values()) if "Draw" in bookie_odds else 0
                            best_away = max(bookie_odds["Away"].values()) if bookie_odds["Away"] else 0
                            
                            best_odds = [best_home, best_draw, best_away]
                            best_bookies = [
                                max(bookie_odds["Home"], key=bookie_odds["Home"].get) if best_home else "N/A",
                                max(bookie_odds.get("Draw", {}), key=bookie_odds["Draw"].get) if best_draw else "N/A",
                                max(bookie_odds["Away"], key=bookie_odds["Away"].get) if best_away else "N/A"
                            ]
                            
                            total_imp = sum(1/o for o in best_odds if o > 0)
                            if total_imp < 1:
                                profit = round((1 - total_imp) * 100, 2)
                                st.success(f"**SUREBET DETECTED! {profit}% profit**")
                            else:
                                st.info(f"No arb here (implied prob: {round(total_imp*100,1)}%)")
                            
                            df_auto = pd.DataFrame({
                                "Outcome": ["Home", "Draw", "Away"],
                                "Best Odds": best_odds,
                                "Best Bookie": best_bookies
                            })
                            st.table(df_auto)
                            
                            # Suggest manual cross-check
                            st.caption("Cross-check these with SportPesa/Betway for bigger arb if odds differ!")
            except Exception as e:
                st.error(f"Error: {str(e)} — Check key, internet, or quota (view usage at the-odds-api.com/account).")

st.caption("Pro: Use auto to spot global arbs (e.g. 1xBet misprices) → plug best odds into manual mode with local bookies. Refresh sparingly to save credits!")

st.markdown("---")
st.markdown("**Banu in Nairobi** • Your personal tool is live! Want tweaks: more leagues, auto-alerts (e.g. email), CSV export of scans, or filter by min profit %? Just say — I'll update code instantly. Test with today's matches!")
