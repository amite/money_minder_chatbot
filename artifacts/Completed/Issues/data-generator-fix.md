Script is working. Summary of fixes:

## Issues Fixed:

1. **Missing "monthly" frequency weight**: The `frequency_weights` dictionary didn't include "monthly", causing a `KeyError` when processing monthly non-subscription merchants (gym memberships, utilities).

2. **Missing monthly date generation**: Added a `_generate_monthly_date()` method to handle monthly transaction dates.

3. **Date generation logic**: Updated the date generation to handle the "monthly" frequency case.

The script now generates 200 transactions with realistic patterns:
- Subscriptions (Netflix, Spotify, etc.)
- Regular spending (coffee shops, groceries, etc.)
- Monthly recurring items (utilities, gym memberships)
- Various categories (food, transport, health, shopping, entertainment, utilities)

The output CSV file has been created at `data/transactions.csv` with all transactions sorted by date.