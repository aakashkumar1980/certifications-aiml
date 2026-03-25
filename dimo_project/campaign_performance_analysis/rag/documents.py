"""
Document Sources for the RAG Knowledge Base.

Provides the raw domain knowledge that gets chunked, embedded, and stored
in the vector database. Only company-specific data that the LLM cannot
know belongs here:

1. **Campaign Descriptions** — What each campaign offers, who it targets, budget.

Generic knowledge like business glossary definitions (ROI, enrollment rate,
redemption rate) and performance analysis are NOT stored here — the LLM
already knows these from its training data and can reason about them
intelligently when given raw numbers.
"""


def get_campaign_descriptions():
    """
    Return pre-authored campaign description documents.

    These are company-specific facts that the LLM has no way to know:
    campaign names, target segments, reward structures, partner merchants,
    budgets, and timing. This is what makes RAG valuable — grounding
    the LLM in YOUR specific business data.

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
