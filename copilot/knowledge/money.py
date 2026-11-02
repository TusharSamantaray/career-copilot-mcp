"""Educational money content: investing, layoff readiness, the economy.

General education, not personalised financial, tax or legal advice.
"""

DISCLAIMER = ("Educational information, not financial, tax or legal advice. "
              "Rules vary by country and situation; confirm with a licensed "
              "professional before acting.")

INVEST_GUIDES = {
    "order_of_operations": {
        "title": "Where the next dollar goes",
        "points": [
            "1. Keep 1 month of expenses in checking as a buffer.",
            "2. Capture any employer retirement match (an instant return).",
            "3. Pay off high-interest debt (credit cards).",
            "4. Build an emergency fund: 3-6 months of core spend, longer "
            "if income is volatile or a visa ties status to employment.",
            "5. Fill tax-advantaged accounts (e.g. US: HSA, IRA, 401(k)).",
            "6. Invest the rest in a taxable brokerage account.",
        ]},
    "what_works": {
        "title": "What the evidence says works",
        "points": [
            "Low-cost, broad index funds beat most active funds after fees "
            "over long periods.",
            "Time in the market beats timing the market: missing a few of "
            "the best days cuts long-run returns sharply.",
            "Asset allocation (stocks vs bonds vs cash) drives most of a "
            "portfolio's risk and return.",
            "Fees and taxes compound: a 1% fee can cost a large share of "
            "final wealth over decades.",
            "Lump-sum investing beats dollar-cost averaging about two "
            "thirds of the time historically; DCA reduces regret.",
            "Rebalance on a schedule or at bands (e.g. 5% drift), not on "
            "headlines.",
        ]},
    "allocation": {
        "title": "Choosing an allocation",
        "points": [
            "Money needed within ~3 years belongs in cash or short bonds, "
            "not stocks.",
            "Long-horizon money can hold mostly diversified equities if you "
            "can sit through 30-50% drops without selling.",
            "Diversify globally, not just your home market.",
            "A simple core: total-market index + international index + "
            "bonds sized to your horizon and nerve.",
        ]},
    "concentration": {
        "title": "Single-stock and employer-stock risk",
        "points": [
            "One stock above ~10% of your investments is concentration risk.",
            "Employer stock doubles the risk: a bad year can cost the job and "
            "the savings at once.",
            "Sell vested employer stock on a plan; tax timing matters, but "
            "should not override need or risk.",
        ]},
    "tax_timing": {
        "title": "Tax timing ideas worth asking a professional about",
        "points": [
            "Gains held over a year are often taxed at lower long-term rates.",
            "A low-income year (e.g. between jobs) can be a cheap year to "
            "realise gains.",
            "Never cash out retirement accounts early to fund a gap: income "
            "tax plus penalties make it the most expensive money you have.",
            "Use tax-loss harvesting to offset gains, minding wash-sale rules.",
        ]},
    "rebalancing": {
        "title": "Rebalancing",
        "points": [
            "Pick bands (e.g. rebalance when an asset drifts 5 points).",
            "Rebalance with new contributions first to avoid selling.",
            "In taxable accounts, prefer rebalancing inside tax-advantaged "
            "accounts.",
        ]},
}

LAYOFF_PLAYBOOK = [
    {"when": "Now, while employed",
     "do": ["Build the emergency fund toward 6+ months of core spend.",
            "Know your core spend: rent, food, insurance, transport, "
            "minimum debt payments.",
            "List which money is accessible (cash, brokerage) vs locked "
            "(retirement, HSA) vs illiquid (property, car).",
            "Reduce single-stock and employer-stock concentration.",
            "Keep your resume, story bank and network warm."]},
    {"when": "Week of the layoff",
     "do": ["Get the official separation date, severance terms and "
            "benefits end date in writing.",
            "If your status depends on employment (e.g. a work visa), "
            "talk to an immigration attorney this week.",
            "Cancel non-essential subscriptions; they are the fastest "
            "runway win.",
            "Start applying immediately: pipelines take weeks to move. "
            "Prep in parallel.",
            "Tell your network; referrals skip the queue."]},
    {"when": "Within 30-60 days",
     "do": ["Choose health coverage (e.g. US: COBRA vs marketplace; job "
            "loss opens a special enrollment window).",
            "Ask about unemployment benefits before assuming either way.",
            "Cut core spend to a target; recompute runway monthly.",
            "Do not cash out retirement accounts."]},
    {"when": "Longer gap",
     "do": ["Consider realising gains in the low-income year (ask a tax "
            "professional).",
            "Keep a dated scenario plan: offer by X, fallback by Y."]},
]

ECONOMY_GUIDES = {
    "supply_demand": {
        "title": "Supply, demand and price",
        "points": [
            "Price is where buyers' willingness meets sellers' cost. Shift "
            "either curve and the price moves.",
            "Short-run supply is rigid for commodities (mines, farms, "
            "refineries take years), so demand shocks move prices hard.",
            "Inventories are the buffer: low inventories mean price spikes.",
        ]},
    "money_rates_inflation": {
        "title": "Money, interest rates and inflation",
        "points": [
            "Central banks raise rates to cool inflation and cut them to "
            "support growth.",
            "Higher rates lower the present value of future profits, so "
            "growth stocks and long bonds fall most.",
            "Real rate = nominal rate minus inflation; it is what savers "
            "and borrowers actually feel.",
        ]},
    "business_cycle": {
        "title": "The business cycle",
        "points": [
            "Expansion, peak, contraction, trough. Hiring lags the cycle; "
            "layoffs often come after markets have already fallen.",
            "Leading signals: yield curve, PMIs, jobless claims, credit "
            "spreads. Lagging: unemployment rate.",
            "Defensive sectors (staples, utilities, healthcare) hold up "
            "better in contractions; cyclicals lead recoveries.",
        ]},
    "commodities": {
        "title": "Commodities and the real economy",
        "points": [
            "Energy feeds into almost every price: transport, plastics, "
            "fertiliser, food.",
            "Industrial metals (copper) track global construction and "
            "manufacturing.",
            "A strong dollar usually pressures dollar-priced commodities "
            "and emerging markets.",
        ]},
    "markets_link": {
        "title": "How the economy reaches stock prices",
        "points": [
            "Stock price = expected future profits discounted at a rate.",
            "Growth surprises raise profits; rate surprises change the "
            "discount. Markets move on surprises, not news.",
            "Sector exposure matters more than headlines: know which "
            "industries your holdings and your employer depend on.",
        ]},
    "how_to_use": {
        "title": "Using this as an individual",
        "points": [
            "Don't trade the macro: diversify and keep your allocation.",
            "Use it for career timing: strong sectors hire; weak ones cut.",
            "Use it for runway planning: in a slowdown, plan for a longer "
            "search and a bigger cash buffer.",
        ]},
}

WORLD_BANK_INDICATORS = {
    "gdp_growth": ("NY.GDP.MKTP.KD.ZG", "GDP growth, annual %"),
    "inflation": ("FP.CPI.TOTL.ZG", "Inflation, consumer prices, annual %"),
    "unemployment": ("SL.UEM.TOTL.ZS", "Unemployment, % of labour force"),
    "real_interest_rate": ("FR.INR.RINR", "Real interest rate, %"),
    "current_account": ("BN.CAB.XOKA.GD.ZS",
                        "Current account balance, % of GDP"),
    "gov_debt": ("GC.DOD.TOTL.GD.ZS", "Central government debt, % of GDP"),
}
