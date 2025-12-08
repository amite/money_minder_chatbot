import random
from datetime import datetime, timedelta

import pandas as pd

categories = ["food", "shopping", "entertainment", "transport", "utilities", "health"]
merchants = [
    "Starbucks",
    "Amazon",
    "Netflix",
    "Uber",
    "Walmart",
    "Target",
    "Whole Foods",
    "Spotify",
    "Apple",
    "Google",
    "CVS",
    "Shell",
    "Exxon",
]


def generate_transactions(n=100):
    transactions = []
    start_date = datetime(2024, 1, 1)

    for i in range(n):
        date = start_date + timedelta(days=random.randint(0, 90))
        category = random.choice(categories)
        merchant = random.choice(merchants)

        # Generate amount based on category
        if category == "food":
            amount = round(random.uniform(5, 50), 2)
            description = f"{merchant} Purchase"
        elif category == "shopping":
            amount = round(random.uniform(20, 200), 2)
            description = f"{merchant} Shopping"
        elif category == "entertainment":
            amount = round(random.uniform(10, 30), 2)
            description = f"{merchant} Subscription"
        elif category == "transport":
            amount = round(random.uniform(15, 80), 2)
            description = f"{merchant} Fuel/Ride"
        else:
            amount = round(random.uniform(20, 150), 2)
            description = f"{merchant} Payment"

        transactions.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "description": description,
                "category": category,
                "amount": amount,
                "merchant": merchant,
                "id": i + 1000,
            }
        )

    return pd.DataFrame(transactions)


if __name__ == "__main__":
    df = generate_transactions(150)
    df.to_csv("data/transactions.csv", index=False)
    print(f"Generated {len(df)} transactions")
    print(df.head())
