"""
Realistic Transaction Data Generator
Generates transactions that match real-world spending patterns
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np


class RealisticTransactionGenerator:
    """Generate realistic transaction data with proper patterns"""

    def __init__(self, start_date: str = "2024-01-01", num_months: int = 3):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.num_months = num_months
        self.end_date = self.start_date + timedelta(days=30 * num_months)

        # Define realistic merchant profiles
        self.merchant_profiles = {
            # Grocery stores - weekly pattern
            "Whole Foods": {
                "categories": {"food": 0.8, "health": 0.2},
                "amount_range": (30, 150),
                "frequency": "weekly",
                "description_templates": [
                    "Grocery shopping",
                    "Weekly groceries",
                    "Food purchase",
                    "Organic produce",
                ],
            },
            "Walmart": {
                "categories": {"food": 0.4, "shopping": 0.4, "health": 0.2},
                "amount_range": (25, 180),
                "frequency": "weekly",
                "description_templates": [
                    "Shopping trip",
                    "Grocery shopping",
                    "General merchandise",
                    "Household items",
                ],
            },
            "Target": {
                "categories": {"shopping": 0.5, "food": 0.3, "health": 0.2},
                "amount_range": (20, 160),
                "frequency": "biweekly",
                "description_templates": [
                    "Shopping",
                    "Home goods",
                    "Clothing purchase",
                    "Essentials",
                ],
            },
            # Coffee shops - high frequency
            "Starbucks": {
                "categories": {"food": 1.0},
                "amount_range": (4.50, 12.00),
                "frequency": "frequent",  # 2-3x per week
                "description_templates": [
                    "Coffee",
                    "Latte and pastry",
                    "Morning coffee",
                    "Coffee break",
                ],
            },
            "Dunkin": {
                "categories": {"food": 1.0},
                "amount_range": (3.50, 10.00),
                "frequency": "frequent",
                "description_templates": [
                    "Coffee and donut",
                    "Breakfast",
                    "Coffee",
                    "Morning stop",
                ],
            },
            # Restaurants - variable frequency
            "Chipotle": {
                "categories": {"food": 1.0},
                "amount_range": (12, 18),
                "frequency": "occasional",
                "description_templates": ["Lunch", "Burrito bowl", "Dinner", "Takeout"],
            },
            "McDonald's": {
                "categories": {"food": 1.0},
                "amount_range": (6, 15),
                "frequency": "occasional",
                "description_templates": [
                    "Fast food",
                    "Lunch",
                    "Quick meal",
                    "Drive-thru",
                ],
            },
            # Online retailers - varied categories
            "Amazon": {
                "categories": {
                    "shopping": 0.5,
                    "entertainment": 0.2,
                    "health": 0.15,
                    "food": 0.15,
                },
                "amount_range": (15, 200),
                "frequency": "weekly",
                "description_templates": [
                    "Online purchase",
                    "Package delivery",
                    "Prime order",
                    "Online shopping",
                ],
            },
            "Apple": {
                "categories": {"shopping": 0.7, "entertainment": 0.3},
                "amount_range": (10, 300),
                "frequency": "occasional",
                "description_templates": [
                    "App Store purchase",
                    "iTunes",
                    "Apple product",
                    "Digital purchase",
                ],
            },
            # Subscriptions - monthly recurring
            "Netflix": {
                "categories": {"entertainment": 1.0},
                "amount_range": (15.49, 15.49),  # Fixed amount
                "frequency": "monthly",
                "description_templates": ["Subscription", "Monthly subscription"],
            },
            "Spotify": {
                "categories": {"entertainment": 1.0},
                "amount_range": (10.99, 10.99),
                "frequency": "monthly",
                "description_templates": ["Premium subscription", "Music subscription"],
            },
            "YouTube Premium": {
                "categories": {"entertainment": 1.0},
                "amount_range": (11.99, 11.99),
                "frequency": "monthly",
                "description_templates": ["Premium subscription"],
            },
            "Disney+": {
                "categories": {"entertainment": 1.0},
                "amount_range": (7.99, 7.99),
                "frequency": "monthly",
                "description_templates": ["Streaming subscription"],
            },
            # Transportation
            "Uber": {
                "categories": {"transport": 0.8, "food": 0.2},  # Uber Eats
                "amount_range": (12, 45),
                "frequency": "occasional",
                "description_templates": [
                    "Ride",
                    "Trip",
                    "Uber Eats delivery",
                    "Transportation",
                ],
            },
            "Lyft": {
                "categories": {"transport": 1.0},
                "amount_range": (10, 40),
                "frequency": "rare",
                "description_templates": ["Ride", "Trip", "Transportation"],
            },
            "Shell": {
                "categories": {"transport": 0.85, "food": 0.15},  # Gas + snacks
                "amount_range": (35, 65),
                "frequency": "weekly",
                "description_templates": ["Fuel", "Gas", "Fill-up", "Gas and snacks"],
            },
            "Exxon": {
                "categories": {"transport": 0.9, "food": 0.1},
                "amount_range": (30, 60),
                "frequency": "weekly",
                "description_templates": ["Fuel", "Gas", "Fill-up"],
            },
            # Utilities
            "Con Edison": {
                "categories": {"utilities": 1.0},
                "amount_range": (80, 150),
                "frequency": "monthly",
                "description_templates": ["Electric bill", "Utility payment"],
            },
            "Verizon": {
                "categories": {"utilities": 1.0},
                "amount_range": (65, 85),
                "frequency": "monthly",
                "description_templates": ["Phone bill", "Mobile service"],
            },
            "Comcast": {
                "categories": {"utilities": 1.0},
                "amount_range": (90, 120),
                "frequency": "monthly",
                "description_templates": ["Internet bill", "Cable/Internet"],
            },
            # Pharmacy/Health
            "CVS": {
                "categories": {"health": 0.6, "shopping": 0.3, "food": 0.1},
                "amount_range": (15, 85),
                "frequency": "occasional",
                "description_templates": [
                    "Pharmacy",
                    "Prescription",
                    "Health & beauty",
                    "Drugstore",
                ],
            },
            "Walgreens": {
                "categories": {"health": 0.6, "shopping": 0.3, "food": 0.1},
                "amount_range": (12, 75),
                "frequency": "occasional",
                "description_templates": [
                    "Pharmacy",
                    "Prescription pickup",
                    "Drugstore",
                    "Health items",
                ],
            },
            # Gym/Fitness
            "Planet Fitness": {
                "categories": {"health": 1.0},
                "amount_range": (10.00, 10.00),
                "frequency": "monthly",
                "description_templates": ["Gym membership", "Monthly membership"],
            },
            "Equinox": {
                "categories": {"health": 1.0},
                "amount_range": (200, 200),
                "frequency": "monthly",
                "description_templates": ["Gym membership", "Fitness membership"],
            },
        }

    def generate_transactions(self, num_transactions: int = 200) -> pd.DataFrame:
        """Generate realistic transaction dataset"""
        transactions = []
        current_id = 1000

        # Generate recurring subscriptions first
        transactions.extend(self._generate_subscriptions(current_id))
        current_id += len(transactions)

        # Generate regular spending with patterns
        transactions.extend(
            self._generate_regular_spending(
                num_transactions - len(transactions), current_id
            )
        )

        # Sort by date
        df = pd.DataFrame(transactions)
        df = df.sort_values("date").reset_index(drop=True)

        # Add some realistic noise
        df = self._add_realistic_variations(df)

        return df

    def _generate_subscriptions(self, start_id: int) -> List[Dict]:
        """Generate recurring monthly subscriptions"""
        transactions = []
        subscription_merchants = [
            m
            for m, p in self.merchant_profiles.items()
            if p["frequency"] == "monthly"
            and "subscription" in p["description_templates"][0].lower()
        ]

        # User has 2-4 subscriptions
        active_subscriptions = random.sample(
            subscription_merchants, k=random.randint(2, 4)
        )

        for merchant in active_subscriptions:
            profile = self.merchant_profiles[merchant]

            # Generate for each month
            current_date = self.start_date
            while current_date < self.end_date:
                # Subscriptions typically charge on same day each month
                charge_day = random.randint(1, 28)
                charge_date = current_date.replace(day=charge_day)

                if charge_date < self.end_date:
                    category = self._select_category(profile["categories"])
                    amount = profile["amount_range"][0]  # Fixed amount

                    transactions.append(
                        {
                            "date": charge_date.strftime("%Y-%m-%d"),
                            "description": random.choice(
                                profile["description_templates"]
                            ),
                            "category": category,
                            "amount": amount,
                            "merchant": merchant,
                            "id": start_id + len(transactions),
                        }
                    )

                # Move to next month
                current_date = self._add_months(current_date, 1)

        return transactions

    def _generate_regular_spending(
        self, num_transactions: int, start_id: int
    ) -> List[Dict]:
        """Generate regular spending with realistic patterns"""
        transactions = []

        # Non-subscription merchants
        regular_merchants = [
            m
            for m, p in self.merchant_profiles.items()
            if p["frequency"] != "monthly"
            or "subscription" not in p["description_templates"][0].lower()
        ]

        # Calculate frequency weights
        frequency_weights = {
            "frequent": 15,  # 2-3x per week
            "weekly": 4,
            "biweekly": 2,
            "occasional": 1,
            "rare": 0.5,
            "monthly": 1,  # Monthly non-subscription items (utilities, gym, etc.)
        }

        # Create weighted merchant list
        weighted_merchants = []
        for merchant in regular_merchants:
            profile = self.merchant_profiles[merchant]
            weight = frequency_weights[profile["frequency"]]
            weighted_merchants.extend([merchant] * int(weight * 10))

        # Generate transactions
        days_range = (self.end_date - self.start_date).days

        for _ in range(num_transactions):
            merchant = random.choice(weighted_merchants)
            profile = self.merchant_profiles[merchant]

            # Generate date based on frequency pattern
            if profile["frequency"] == "frequent":
                # Cluster around weekdays, mornings
                date = self._generate_frequent_date(days_range)
            elif profile["frequency"] == "weekly":
                # Weekly pattern, often weekends for groceries
                date = self._generate_weekly_date(days_range)
            elif profile["frequency"] == "monthly":
                # Monthly pattern - same day each month
                date = self._generate_monthly_date()
            else:
                # Random with slight weekend bias
                date = self._generate_occasional_date(days_range)

            category = self._select_category(profile["categories"])
            amount = self._generate_amount(profile["amount_range"], category)
            description = random.choice(profile["description_templates"])

            transactions.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "description": description,
                    "category": category,
                    "amount": round(amount, 2),
                    "merchant": merchant,
                    "id": start_id + len(transactions),
                }
            )

        return transactions

    def _generate_frequent_date(self, days_range: int) -> datetime:
        """Generate date for frequent purchases (weekday bias)"""
        date = self.start_date + timedelta(days=random.randint(0, days_range))
        # Retry if weekend (30% chance to accept weekend)
        while date.weekday() >= 5 and random.random() > 0.3:
            date = self.start_date + timedelta(days=random.randint(0, days_range))
        return date

    def _generate_weekly_date(self, days_range: int) -> datetime:
        """Generate date for weekly purchases (weekend bias for groceries)"""
        date = self.start_date + timedelta(days=random.randint(0, days_range))
        # Slight weekend bias (60% weekend)
        if random.random() < 0.6:
            # Move to nearest weekend
            days_until_weekend = (5 - date.weekday()) % 7
            date += timedelta(days=days_until_weekend)
        return date

    def _generate_occasional_date(self, days_range: int) -> datetime:
        """Generate random date"""
        return self.start_date + timedelta(days=random.randint(0, days_range))

    def _generate_monthly_date(self) -> datetime:
        """Generate date for monthly transactions (same day each month)"""
        # Pick a random day of month (1-28 to avoid overflow)
        day = random.randint(1, 28)
        # Pick a random month within the date range
        months_elapsed = random.randint(0, self.num_months - 1)
        date = self._add_months(self.start_date, months_elapsed)
        return date.replace(day=day)

    def _select_category(self, category_probs: Dict[str, float]) -> str:
        """Select category based on probability distribution"""
        categories = list(category_probs.keys())
        probabilities = list(category_probs.values())
        return random.choices(categories, weights=probabilities, k=1)[0]

    def _generate_amount(
        self, amount_range: Tuple[float, float], category: str
    ) -> float:
        """Generate realistic amount with slight randomness"""
        min_amt, max_amt = amount_range

        if min_amt == max_amt:
            # Fixed amount (subscriptions)
            return min_amt

        # Use normal distribution for more realistic amounts
        mean = (min_amt + max_amt) / 2
        std = (max_amt - min_amt) / 6  # 99.7% within range

        amount = np.random.normal(mean, std)

        # Clamp to range
        amount = max(min_amt, min(max_amt, amount))

        return amount

    def _add_realistic_variations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic variations like tips, taxes, etc."""

        # Add tips to restaurants and rideshares (15-20%)
        food_mask = (df["category"] == "food") & ~df["merchant"].isin(
            ["Starbucks", "Dunkin"]
        )
        rideshare_mask = df["merchant"].isin(["Uber", "Lyft"])

        for mask in [food_mask, rideshare_mask]:
            if mask.any():
                tip_multiplier = np.random.uniform(1.15, 1.20, mask.sum())
                df.loc[mask, "amount"] = df.loc[mask, "amount"] * tip_multiplier

        # Round all amounts to 2 decimals
        df["amount"] = df["amount"].round(2)

        return df

    def _add_months(self, date: datetime, months: int) -> datetime:
        """Add months to date"""
        month = date.month + months
        year = date.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(date.day, 28)  # Avoid date overflow
        return date.replace(year=year, month=month, day=day)

    def generate_and_save(
        self, filename: str = "data/transactions.csv", num_transactions: int = 200
    ):
        """Generate and save transaction data"""
        df = self.generate_transactions(num_transactions)

        # Ensure directory exists
        import os

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        df.to_csv(filename, index=False)

        # Print summary
        print(f"✓ Generated {len(df)} transactions")
        print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
        print(f"\nTransactions by category:")
        print(df["category"].value_counts().to_string())
        print(f"\nTop merchants:")
        print(df["merchant"].value_counts().head(10).to_string())
        print(f"\nTotal spending: ${df['amount'].sum():,.2f}")
        print(f"Average transaction: ${df['amount'].mean():.2f}")

        return df


if __name__ == "__main__":
    # Generate 200 transactions over 3 months
    generator = RealisticTransactionGenerator(start_date="2024-01-01", num_months=3)

    df = generator.generate_and_save(
        filename="data/transactions.csv", num_transactions=200
    )

    print("\n" + "=" * 50)
    print("Sample transactions:")
    print("=" * 50)
    print(df.head(15).to_string(index=False))
