"""
Document Sources for the RAG Knowledge Base.

Provides the raw domain knowledge that gets chunked, embedded, and stored
in the vector database. Three categories of documents:

1. **Campaign Descriptions** — What each campaign offers, who it targets, budget.
2. **Performance Summaries** — Pre-analyzed KPI narratives per campaign.
3. **Business Glossary** — Definitions of financial-services metrics and terms.
"""


def get_campaign_descriptions():
    """
    Return pre-authored campaign description documents.

    Each tuple contains (campaign_id, description_text).

    Returns:
        list[tuple[str, str]]: List of (campaign_id, description) pairs.
    """
    return [
        ("CMP-001",
         "Summer Cashback Bonanza: A cashback rewards campaign targeting premium cardholders. "
         "Offers 5% cashback on grocery and gas station purchases. Runs during peak summer "
         "spending season to increase card usage among high-value customers. Budget: $250,000."),
        ("CMP-002",
         "Holiday Travel Rewards: A travel rewards campaign for standard segment customers. "
         "Offers double miles on airline and hotel bookings during the holiday travel season. "
         "Partners with Delta Airlines and Marriott. Budget: $350,000."),
        ("CMP-003",
         "Spring Dining Deal: A dining rewards campaign targeting student cardholders. "
         "Offers 10% cashback at partner restaurants including Olive Garden and Starbucks. "
         "Designed to increase engagement among younger customers. Budget: $100,000."),
        ("CMP-004",
         "Year-End Retail Special: A retail rewards campaign for premium customers. "
         "Offers bonus points on electronics and department store purchases. "
         "Timed for Black Friday and holiday shopping season. Budget: $400,000."),
        ("CMP-005",
         "Launch Cashback Offer: A new customer acquisition campaign offering flat 3% cashback "
         "on all purchases for the first 90 days. Targets all segments to grow the cardholder "
         "base. Budget: $200,000."),
    ]


def get_performance_summaries():
    """
    Return pre-authored performance summary narratives.

    Each tuple contains (campaign_id, summary_text).

    Returns:
        list[tuple[str, str]]: List of (campaign_id, summary) pairs.
    """
    return [
        ("CMP-001",
         "CMP-001 Performance Summary: The Summer Cashback Bonanza achieved a 12% enrollment "
         "rate with 142 enrollments from premium customers. Redemption rate was 68%, driven "
         "primarily by grocery purchases at Whole Foods and Costco. ROI came in at 185%, "
         "exceeding the 150% target. California and Texas led in enrollments."),
        ("CMP-002",
         "CMP-002 Performance Summary: Holiday Travel Rewards saw strong engagement with 95 "
         "enrollments and a 15% click-through rate. Redemption rate was 55% with average "
         "redemption value of $180. Delta Airlines bookings accounted for 40% of redemptions. "
         "ROI was 120%, slightly below target due to high cost-per-enrollment of $35."),
        ("CMP-003",
         "CMP-003 Performance Summary: Spring Dining Deal was highly effective with students, "
         "achieving 180 enrollments through mobile channel (72% of total). Redemption rate was "
         "74% — highest across all campaigns. Starbucks drove 45% of redemptions. ROI was 210% "
         "on a modest budget."),
        ("CMP-004",
         "CMP-004 Performance Summary: Year-End Retail Special generated the highest revenue at "
         "$85,000 from 120 enrollments. Best Buy and Amazon were top merchants. However, high "
         "acquisition costs resulted in ROI of only 95%. Premium segment responded well through "
         "web channel."),
        ("CMP-005",
         "CMP-005 Performance Summary: Launch Cashback Offer onboarded 163 new customers across "
         "all segments. The 3% flat cashback proved attractive with 62% redemption rate. "
         "Cost-per-enrollment was the lowest at $12. ROI reached 155%. Mobile was the dominant "
         "enrollment channel at 65%."),
    ]


def get_business_glossary():
    """
    Return business glossary definitions for financial-services terms.

    Returns:
        list[str]: List of glossary definition strings.
    """
    return [
        "Enrollment Rate: The percentage of users who enroll in a campaign after seeing it. "
        "Calculated as (enrollments / impressions) * 100. A good enrollment rate for credit "
        "card campaigns is typically 5-15%. Higher rates indicate strong campaign messaging.",
        "Redemption Rate: The percentage of enrolled customers who actually redeem their reward. "
        "Calculated as (redemptions / enrollments) * 100. Industry benchmark is 40-70%. "
        "High redemption rates indicate the reward is valuable and easy to use.",
        "ROI (Return on Investment): Measures campaign profitability. "
        "Calculated as ((revenue - cost) / cost) * 100. For credit card campaigns, "
        "ROI above 100% is considered successful. Top campaigns achieve 150-250% ROI.",
        "Campaign Types: Cashback campaigns offer percentage back on purchases. "
        "Travel campaigns reward airline/hotel spending with miles or points. "
        "Dining campaigns partner with restaurants for food-related rewards. "
        "Retail campaigns focus on shopping at partner stores and e-commerce.",
        "Merchant Categories: Restaurants (dining/fast food), Airlines (flights/travel), "
        "Grocery (supermarkets/wholesale), Electronics (tech/gadgets), Gas Stations "
        "(fuel/convenience). Each category has different average transaction values.",
        "Customer Segments: Premium — high-income, high-spend cardholders with annual fees. "
        "Standard — mid-tier customers with moderate spending. "
        "Student — younger demographic, lower spend but high engagement and long-term value.",
        "Cost Per Enrollment (CPE): The average cost to acquire one enrolled customer. "
        "Calculated as total campaign cost / number of enrollments. "
        "Lower CPE indicates more efficient customer acquisition. Benchmark: $10-$40.",
    ]
