"""
Mock Data Generator for Campaign Performance Analysis.

Generates realistic credit card campaign datasets using the Faker library
and saves them as CSV files in the ``data/`` directory. This module is
designed to be run once during project setup to bootstrap the SQLite
database with representative financial-services data.

Generated Files:
    - ``campaigns.csv``           — 5 campaign definitions
    - ``enrollments.csv``         — 500 customer enrollment records
    - ``redemptions.csv``         — 300 reward redemption transactions
    - ``campaign_performance.csv``— 30 monthly performance snapshots

Example Usage::

    # From the project root:
    python data/generate_mock_data.py

    # Or programmatically:
    from data.generate_mock_data import MockDataGenerator
    generator = MockDataGenerator()
    generator.generate_all()
"""

import os
import sys
import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

# Add project root to path so config can be imported when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings


class MockDataGenerator:
    """
    Generates realistic mock data for credit card campaign analysis.

    This generator creates four interrelated datasets that simulate a
    real-world campaign management system. Data relationships are
    maintained via foreign keys (campaign_id, enrollment_id) across
    the generated CSV files.

    Attributes:
        fake (Faker): Faker instance seeded for reproducible output.
        data_dir (str): Output directory for CSV files.
        campaign_types (list[str]): Available campaign categories.
        customer_segments (list[str]): Cardholder tier classifications.
        merchant_categories (list[str]): Merchant groupings for spend tracking.
        us_states (list[str]): US states used for geographic distribution.

    Example::

        generator = MockDataGenerator()
        campaigns_df = generator.generate_campaigns()
        enrollments_df = generator.generate_enrollments(campaigns_df)
    """

    # --- Domain Constants ---
    CAMPAIGN_TYPES = ["cashback", "travel", "dining", "retail"]
    CUSTOMER_SEGMENTS = ["premium", "standard", "student"]
    MERCHANT_CATEGORIES = ["restaurants", "airlines", "grocery", "electronics", "gas_stations"]
    ENROLLMENT_CHANNELS = ["web", "mobile", "branch"]
    US_STATES = [
        "California", "Texas", "New York", "Florida", "Illinois",
        "Pennsylvania", "Ohio", "Georgia", "Michigan", "Arizona",
    ]
    CAMPAIGN_PREFIXES = ["Summer", "Holiday", "Spring", "Year-End", "Launch"]
    CAMPAIGN_SUFFIXES = ["Bonanza", "Rewards", "Offer", "Special", "Deal"]
    MERCHANT_NAMES = [
        "Whole Foods", "Delta Airlines", "Olive Garden", "Best Buy",
        "Shell Gas", "Amazon", "Walmart", "Target", "Costco",
        "Starbucks", "Uber Eats", "Southwest Airlines", "Home Depot",
    ]

    def __init__(self, seed=None, data_dir=None):
        """
        Initialize the mock data generator with reproducible seeds.

        Args:
            seed (int, optional): Random seed for reproducibility.
                Defaults to ``Settings.MOCK_DATA_SEED`` (42).
            data_dir (str, optional): Output directory for CSV files.
                Defaults to ``Settings.DATA_DIR``.
        """
        seed = seed or Settings.MOCK_DATA_SEED
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        self.data_dir = data_dir or Settings.DATA_DIR

    def generate_campaigns(self, count=None):
        """
        Generate campaign definition records.

        Each campaign has a type, target segment, date range, budget,
        and a dynamically computed status based on the current date.

        Args:
            count (int, optional): Number of campaigns to generate.
                Defaults to ``Settings.NUM_CAMPAIGNS`` (5).

        Returns:
            pd.DataFrame: DataFrame with columns: campaign_id, campaign_name,
                campaign_type, start_date, end_date, target_segment,
                budget_allocated, merchant_category, status.
        """
        count = count or Settings.NUM_CAMPAIGNS
        today = datetime.now().date()
        campaigns = []

        for i in range(1, count + 1):
            start = self.fake.date_between(start_date="-6m", end_date="+1m")
            end = start + timedelta(days=random.randint(30, 180))

            # Derive status from date range relative to today
            if start <= today <= end:
                status = "active"
            elif end < today:
                status = "expired"
            else:
                status = "upcoming"

            campaigns.append({
                "campaign_id": f"CMP-{i:03d}",
                "campaign_name": (
                    f"{random.choice(self.CAMPAIGN_PREFIXES)} "
                    f"{random.choice(self.CAMPAIGN_TYPES).title()} "
                    f"{random.choice(self.CAMPAIGN_SUFFIXES)}"
                ),
                "campaign_type": random.choice(self.CAMPAIGN_TYPES),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "target_segment": random.choice(self.CUSTOMER_SEGMENTS),
                "budget_allocated": round(random.uniform(50000, 500000), 2),
                "merchant_category": random.choice(self.MERCHANT_CATEGORIES),
                "status": status,
            })

        df = pd.DataFrame(campaigns)
        df.to_csv(os.path.join(self.data_dir, "campaigns.csv"), index=False)
        print(f"  Generated {len(df)} campaigns -> campaigns.csv")
        return df

    def generate_enrollments(self, campaigns_df, count=None):
        """
        Generate customer enrollment records linked to campaigns.

        Each enrollment ties a customer to a campaign with a channel,
        segment, and geographic state. Enrollment dates fall within
        the parent campaign's active date range.

        Args:
            campaigns_df (pd.DataFrame): Campaign records (must include
                campaign_id, start_date, end_date columns).
            count (int, optional): Number of enrollments to generate.
                Defaults to ``Settings.NUM_ENROLLMENTS`` (500).

        Returns:
            pd.DataFrame: DataFrame with columns: enrollment_id, campaign_id,
                customer_id, customer_segment, enrollment_date, channel, state.
        """
        count = count or Settings.NUM_ENROLLMENTS
        enrollments = []

        for i in range(1, count + 1):
            campaign = campaigns_df.sample(1).iloc[0]
            start = datetime.fromisoformat(campaign["start_date"])
            end = datetime.fromisoformat(campaign["end_date"])
            enroll_date = self.fake.date_between(start_date=start, end_date=end)

            enrollments.append({
                "enrollment_id": f"ENR-{i:04d}",
                "campaign_id": campaign["campaign_id"],
                "customer_id": f"CUST-{random.randint(10000, 99999)}",
                "customer_segment": random.choice(self.CUSTOMER_SEGMENTS),
                "enrollment_date": enroll_date.isoformat(),
                "channel": random.choice(self.ENROLLMENT_CHANNELS),
                "state": random.choice(self.US_STATES),
            })

        df = pd.DataFrame(enrollments)
        df.to_csv(os.path.join(self.data_dir, "enrollments.csv"), index=False)
        print(f"  Generated {len(df)} enrollments -> enrollments.csv")
        return df

    def generate_redemptions(self, enrollments_df, campaigns_df, count=None):
        """
        Generate reward redemption transaction records.

        Each redemption is linked to an enrollment and campaign. Redemption
        dates fall between the enrollment date and campaign end date.
        Status is weighted: 80% completed, 15% pending, 5% reversed.

        Args:
            enrollments_df (pd.DataFrame): Enrollment records.
            campaigns_df (pd.DataFrame): Campaign records.
            count (int, optional): Number of redemptions to generate.
                Defaults to ``Settings.NUM_REDEMPTIONS`` (300).

        Returns:
            pd.DataFrame: DataFrame with columns: redemption_id, enrollment_id,
                campaign_id, redemption_date, redemption_amount, merchant_name,
                merchant_category, status.
        """
        count = count or Settings.NUM_REDEMPTIONS
        redemptions = []

        for i in range(1, count + 1):
            enrollment = enrollments_df.sample(1).iloc[0]
            campaign = campaigns_df[
                campaigns_df["campaign_id"] == enrollment["campaign_id"]
            ].iloc[0]

            enroll_date = datetime.fromisoformat(enrollment["enrollment_date"])
            end_date = datetime.fromisoformat(campaign["end_date"])
            redeem_date = self.fake.date_between(start_date=enroll_date, end_date=end_date)

            redemptions.append({
                "redemption_id": f"RED-{i:04d}",
                "enrollment_id": enrollment["enrollment_id"],
                "campaign_id": enrollment["campaign_id"],
                "redemption_date": redeem_date.isoformat(),
                "redemption_amount": round(random.uniform(5, 500), 2),
                "merchant_name": random.choice(self.MERCHANT_NAMES),
                "merchant_category": random.choice(self.MERCHANT_CATEGORIES),
                "status": random.choices(
                    ["completed", "pending", "reversed"],
                    weights=[0.80, 0.15, 0.05],
                )[0],
            })

        df = pd.DataFrame(redemptions)
        df.to_csv(os.path.join(self.data_dir, "redemptions.csv"), index=False)
        print(f"  Generated {len(df)} redemptions -> redemptions.csv")
        return df

    def generate_performance(self, campaigns_df, n_months=None):
        """
        Generate monthly campaign performance metric snapshots.

        Produces a time-series of KPIs for each campaign including
        impressions, clicks, enrollments, redemptions, revenue,
        cost-per-enrollment, and ROI percentage.

        Args:
            campaigns_df (pd.DataFrame): Campaign records.
            n_months (int, optional): Number of monthly records per campaign.
                Defaults to ``Settings.PERF_MONTHS`` (6).

        Returns:
            pd.DataFrame: DataFrame with columns: performance_id, campaign_id,
                month, impressions, clicks, enrollments_count, redemptions_count,
                revenue_generated, cost_per_enrollment, roi_percentage.
        """
        n_months = n_months or Settings.PERF_MONTHS
        records = []
        record_id = 1

        for _, campaign in campaigns_df.iterrows():
            start = datetime.fromisoformat(campaign["start_date"])

            for month_offset in range(n_months):
                month_date = start + timedelta(days=30 * month_offset)

                # Build a realistic metric funnel: impressions -> clicks -> enrollments -> redemptions
                impressions = random.randint(5000, 100000)
                clicks = int(impressions * random.uniform(0.02, 0.15))
                enrollments_count = int(clicks * random.uniform(0.05, 0.30))
                redemptions_count = int(enrollments_count * random.uniform(0.3, 0.8))

                revenue = round(redemptions_count * random.uniform(20, 200), 2)
                cost_per = round(random.uniform(5, 50), 2)
                total_cost = enrollments_count * cost_per
                roi = round(((revenue - total_cost) / max(total_cost, 1)) * 100, 2)

                records.append({
                    "performance_id": f"PERF-{record_id:03d}",
                    "campaign_id": campaign["campaign_id"],
                    "month": month_date.strftime("%Y-%m"),
                    "impressions": impressions,
                    "clicks": clicks,
                    "enrollments_count": enrollments_count,
                    "redemptions_count": redemptions_count,
                    "revenue_generated": revenue,
                    "cost_per_enrollment": cost_per,
                    "roi_percentage": roi,
                })
                record_id += 1

        df = pd.DataFrame(records)
        df.to_csv(os.path.join(self.data_dir, "campaign_performance.csv"), index=False)
        print(f"  Generated {len(df)} performance records -> campaign_performance.csv")
        return df

    def generate_all(self):
        """
        Generate all four datasets in dependency order.

        Calls each generator in sequence—campaigns first (no dependencies),
        then enrollments (depends on campaigns), then redemptions (depends
        on both), and finally performance metrics (depends on campaigns).

        Returns:
            dict: Dictionary with keys 'campaigns', 'enrollments',
                'redemptions', 'performance', each mapping to a DataFrame.
        """
        print("Generating mock campaign data...")
        campaigns = self.generate_campaigns()
        enrollments = self.generate_enrollments(campaigns)
        redemptions = self.generate_redemptions(enrollments, campaigns)
        performance = self.generate_performance(campaigns)
        print("Done! All CSV files saved to data/ folder.\n")

        return {
            "campaigns": campaigns,
            "enrollments": enrollments,
            "redemptions": redemptions,
            "performance": performance,
        }


# --- Script Entry Point ---
if __name__ == "__main__":
    generator = MockDataGenerator()
    generator.generate_all()
