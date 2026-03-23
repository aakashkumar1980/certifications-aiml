"""
Mock Data Generator for Campaign AI Assistant
Generates realistic credit card campaign data using Faker library.
Produces 4 CSV files: campaigns, enrollments, redemptions, campaign_performance.
"""

import os
import random
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

# Output directory (same folder as this script)
DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_campaigns(n=5):
    """Generate campaign records with realistic credit card campaign attributes."""
    campaign_types = ["cashback", "travel", "dining", "retail"]
    segments = ["premium", "standard", "student"]
    merchant_categories = ["restaurants", "airlines", "grocery", "electronics", "gas_stations"]
    statuses = ["active", "expired", "upcoming"]

    campaigns = []
    for i in range(1, n + 1):
        start = fake.date_between(start_date="-6m", end_date="+1m")
        end = start + timedelta(days=random.randint(30, 180))
        status = "active" if start <= datetime.now().date() <= end else (
            "expired" if end < datetime.now().date() else "upcoming"
        )

        campaigns.append({
            "campaign_id": f"CMP-{i:03d}",
            "campaign_name": f"{random.choice(['Summer', 'Holiday', 'Spring', 'Year-End', 'Launch'])} "
                             f"{random.choice(campaign_types).title()} {random.choice(['Bonanza', 'Rewards', 'Offer', 'Special', 'Deal'])}",
            "campaign_type": random.choice(campaign_types),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "target_segment": random.choice(segments),
            "budget_allocated": round(random.uniform(50000, 500000), 2),
            "merchant_category": random.choice(merchant_categories),
            "status": status,
        })

    df = pd.DataFrame(campaigns)
    df.to_csv(os.path.join(DATA_DIR, "campaigns.csv"), index=False)
    print(f"Generated {len(df)} campaigns")
    return df


def generate_enrollments(campaigns_df, n=500):
    """Generate enrollment records linking customers to campaigns."""
    channels = ["web", "mobile", "branch"]
    segments = ["premium", "standard", "student"]
    states = [
        "California", "Texas", "New York", "Florida", "Illinois",
        "Pennsylvania", "Ohio", "Georgia", "Michigan", "Arizona",
    ]

    enrollments = []
    for i in range(1, n + 1):
        campaign = campaigns_df.sample(1).iloc[0]
        start = datetime.fromisoformat(campaign["start_date"])
        end = datetime.fromisoformat(campaign["end_date"])
        enroll_date = fake.date_between(start_date=start, end_date=end)

        enrollments.append({
            "enrollment_id": f"ENR-{i:04d}",
            "campaign_id": campaign["campaign_id"],
            "customer_id": f"CUST-{random.randint(10000, 99999)}",
            "customer_segment": random.choice(segments),
            "enrollment_date": enroll_date.isoformat(),
            "channel": random.choice(channels),
            "state": random.choice(states),
        })

    df = pd.DataFrame(enrollments)
    df.to_csv(os.path.join(DATA_DIR, "enrollments.csv"), index=False)
    print(f"Generated {len(df)} enrollments")
    return df


def generate_redemptions(enrollments_df, campaigns_df, n=300):
    """Generate redemption records for enrolled customers."""
    merchant_names = [
        "Whole Foods", "Delta Airlines", "Olive Garden", "Best Buy",
        "Shell Gas", "Amazon", "Walmart", "Target", "Costco",
        "Starbucks", "Uber Eats", "Southwest Airlines", "Home Depot",
    ]
    merchant_categories = ["restaurants", "airlines", "grocery", "electronics", "gas_stations"]
    statuses = ["completed", "pending", "reversed"]

    redemptions = []
    for i in range(1, n + 1):
        enrollment = enrollments_df.sample(1).iloc[0]
        campaign = campaigns_df[campaigns_df["campaign_id"] == enrollment["campaign_id"]].iloc[0]
        enroll_date = datetime.fromisoformat(enrollment["enrollment_date"])
        end_date = datetime.fromisoformat(campaign["end_date"])
        redeem_date = fake.date_between(start_date=enroll_date, end_date=end_date)

        redemptions.append({
            "redemption_id": f"RED-{i:04d}",
            "enrollment_id": enrollment["enrollment_id"],
            "campaign_id": enrollment["campaign_id"],
            "redemption_date": redeem_date.isoformat(),
            "redemption_amount": round(random.uniform(5, 500), 2),
            "merchant_name": random.choice(merchant_names),
            "merchant_category": random.choice(merchant_categories),
            "status": random.choices(statuses, weights=[0.8, 0.15, 0.05])[0],
        })

    df = pd.DataFrame(redemptions)
    df.to_csv(os.path.join(DATA_DIR, "redemptions.csv"), index=False)
    print(f"Generated {len(df)} redemptions")
    return df


def generate_performance(campaigns_df, n_months=6):
    """Generate monthly performance metrics for each campaign."""
    records = []
    record_id = 1
    for _, campaign in campaigns_df.iterrows():
        for month_offset in range(n_months):
            start = datetime.fromisoformat(campaign["start_date"])
            month_date = start + timedelta(days=30 * month_offset)

            impressions = random.randint(5000, 100000)
            clicks = int(impressions * random.uniform(0.02, 0.15))
            enrollments_count = int(clicks * random.uniform(0.05, 0.30))
            redemptions_count = int(enrollments_count * random.uniform(0.3, 0.8))
            revenue = round(redemptions_count * random.uniform(20, 200), 2)
            cost_per = round(random.uniform(5, 50), 2)
            roi = round(((revenue - (enrollments_count * cost_per)) / max(enrollments_count * cost_per, 1)) * 100, 2)

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
    df.to_csv(os.path.join(DATA_DIR, "campaign_performance.csv"), index=False)
    print(f"Generated {len(df)} performance records")
    return df


if __name__ == "__main__":
    print("Generating mock campaign data...")
    campaigns = generate_campaigns(5)
    enrollments = generate_enrollments(campaigns, 500)
    generate_redemptions(enrollments, campaigns, 300)
    generate_performance(campaigns, 6)
    print("Done! CSV files saved to data/ folder.")
