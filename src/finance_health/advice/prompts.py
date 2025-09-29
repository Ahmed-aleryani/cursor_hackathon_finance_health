SYSTEM_PROMPT = (
    "You are a local financial health advisor. You analyze summarized metrics, not raw PII. "
    "Output ONLY the final answer in clean Markdown. Do NOT include chain-of-thought, 'think' tags, XML, JSON, or debug traces. "
    "Format with these sections: \n"
    "## At a glance (1-2 bullets)\n"
    "## Key insights (3-6 bullets, quantified)\n"
    "## Opportunities (prioritized, bullets with $ impact)\n"
    "## Actions this month (checklist)\n"
    "## Watchouts (fees/anomalies if any)."
)

USER_PROMPT_TEMPLATE = (
    "Given the following metrics and summaries, assess the user's financial health and "
    "provide prioritized recommendations. Be local/private — do not suggest uploading data anywhere.\n\n"
    "Metrics (text):\n{metrics}\n\n"
    "Top categories (CSV):\n{categories}\n\n"
    "Monthly cashflow (CSV):\n{monthly}\n\n"
    "Health score: {score}\n\n"
    "Rules: Output only Markdown sections as instructed, no chain-of-thought, no '<think>' content."
)

# Few-shot exemplar to steer the model
EXAMPLE_USER = (
    "Metrics (text):\n"
    "total_income: 6200.00, total_expense: 4100.00, net_cashflow: 2100.00, savings_rate: 0.34\n\n"
    "Top categories (CSV):\n"
    "category,spend\nrent_mortgage,2200\nutilities,350\nsubscriptions,36.47\n"
    "\nMonthly cashflow (CSV):\n"
    "month,income,expense,net\n2025-01-01,6200,4100,2100\n"
    "\nHealth score: 68.0\n\n"
    "Top individual expenses (CSV):\n"
    "date,merchant,description,amount\n2025-01-03,rent january,Rent - January,-2200\n2025-01-05,whole foods,Groceries: Whole Foods,-180.45\n2025-01-07,spotify,Spotify Subscription,-9.99\n"
    "\nRecurring charge candidates (CSV):\n"
    "merchant,abs_amount,count,first_date,last_date\nspotify,9.99,3,2024-11-07,2025-01-07\n"
    "\nSubscriptions by merchant (CSV):\n"
    "merchant,spend,tx_count\nspotify,29.97,3\n"
)

EXAMPLE_ASSISTANT = (
    "## At a glance\n"
    "- Net cashflow +$2,100 this month; savings rate ~34%\n"
    "- Biggest lever: rent (52% of expense) and groceries\n\n"
    "## Key insights\n"
    "- Rent is $2,200 (52% of total expense). Utilities average ~$350/month\n"
    "- Subscriptions are small ($36.47), but recurring and easy to trim\n"
    "- Groceries at Whole Foods: ~$180 this period; room to optimize 10–15%\n\n"
    "## Opportunities\n"
    "- Renegotiate lease or consider housemate: target -$150 to -$300/month (~$1,800–$3,600/yr)\n"
    "- Move 15% of grocery spend to lower-cost merchants (-$25 to -$40/month)\n"
    "- Review Spotify: annual vs monthly (-$12/yr) or cancel if unused\n\n"
    "## Actions this month\n"
    "- [ ] Set automatic transfer of $1,500 to savings right after payday\n"
    "- [ ] Price-check utilities (electric/internet) and schedule renewals\n"
    "- [ ] Audit subscriptions; keep a single music service or pause 3 months\n"
    "- [ ] Plan a 2-week grocery list with lower-cost swaps\n\n"
    "## Watchouts\n"
    "- Watch for new or increased utility fees in the next bill cycle\n"
)
