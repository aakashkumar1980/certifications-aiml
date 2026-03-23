"""
Vector Store Module for Campaign AI Assistant
Uses ChromaDB with HuggingFace sentence-transformers for RAG-based retrieval.
Ingests campaign descriptions, performance summaries, and business glossary.
"""

import os
import chromadb
from chromadb.utils import embedding_functions

# Persist ChromaDB to disk alongside the project
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
COLLECTION_NAME = "campaign_knowledge"


def get_embedding_function():
    """Return HuggingFace sentence-transformer embedding function."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


def get_collection():
    """Get or create the ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = get_embedding_function()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )
    return collection


def build_knowledge_base():
    """
    Ingest campaign knowledge documents into ChromaDB.
    Three document types: campaign descriptions, performance summaries, business glossary.
    """
    collection = get_collection()

    # Skip if already populated
    if collection.count() > 0:
        print(f"Collection already has {collection.count()} documents. Skipping ingestion.")
        return collection

    documents = []
    metadatas = []
    ids = []

    # --- Campaign Descriptions ---
    campaign_docs = [
        ("CMP-001", "Summer Cashback Bonanza: A cashback rewards campaign targeting premium cardholders. "
                     "Offers 5% cashback on grocery and gas station purchases. Runs during peak summer spending season "
                     "to increase card usage among high-value customers. Budget: $250,000."),
        ("CMP-002", "Holiday Travel Rewards: A travel rewards campaign for standard segment customers. "
                     "Offers double miles on airline and hotel bookings during the holiday travel season. "
                     "Partners with Delta Airlines and Marriott. Budget: $350,000."),
        ("CMP-003", "Spring Dining Deal: A dining rewards campaign targeting student cardholders. "
                     "Offers 10% cashback at partner restaurants including Olive Garden and Starbucks. "
                     "Designed to increase engagement among younger customers. Budget: $100,000."),
        ("CMP-004", "Year-End Retail Special: A retail rewards campaign for premium customers. "
                     "Offers bonus points on electronics and department store purchases. "
                     "Timed for Black Friday and holiday shopping season. Budget: $400,000."),
        ("CMP-005", "Launch Cashback Offer: A new customer acquisition campaign offering flat 3% cashback "
                     "on all purchases for the first 90 days. Targets all segments to grow the cardholder base. "
                     "Budget: $200,000."),
    ]
    for cid, desc in campaign_docs:
        documents.append(desc)
        metadatas.append({"type": "campaign_description", "campaign_id": cid})
        ids.append(f"desc_{cid}")

    # --- Performance Summaries ---
    perf_docs = [
        ("CMP-001", "CMP-001 Performance Summary: The Summer Cashback Bonanza achieved a 12% enrollment rate "
                     "with 142 enrollments from premium customers. Redemption rate was 68%, driven primarily by "
                     "grocery purchases at Whole Foods and Costco. ROI came in at 185%, exceeding the 150% target. "
                     "California and Texas led in enrollments."),
        ("CMP-002", "CMP-002 Performance Summary: Holiday Travel Rewards saw strong engagement with 95 enrollments "
                     "and a 15% click-through rate. Redemption rate was 55% with average redemption value of $180. "
                     "Delta Airlines bookings accounted for 40% of redemptions. ROI was 120%, slightly below target "
                     "due to high cost-per-enrollment of $35."),
        ("CMP-003", "CMP-003 Performance Summary: Spring Dining Deal was highly effective with students, achieving "
                     "180 enrollments through mobile channel (72% of total). Redemption rate was 74% — highest across "
                     "all campaigns. Starbucks drove 45% of redemptions. ROI was 210% on a modest budget."),
        ("CMP-004", "CMP-004 Performance Summary: Year-End Retail Special generated the highest revenue at $85,000 "
                     "from 120 enrollments. Best Buy and Amazon were top merchants. However, high acquisition costs "
                     "resulted in ROI of only 95%. Premium segment responded well through web channel."),
        ("CMP-005", "CMP-005 Performance Summary: Launch Cashback Offer onboarded 163 new customers across all "
                     "segments. The 3% flat cashback proved attractive with 62% redemption rate. Cost-per-enrollment "
                     "was the lowest at $12. ROI reached 155%. Mobile was the dominant enrollment channel at 65%."),
    ]
    for cid, summary in perf_docs:
        documents.append(summary)
        metadatas.append({"type": "performance_summary", "campaign_id": cid})
        ids.append(f"perf_{cid}")

    # --- Business Glossary ---
    glossary_docs = [
        ("Enrollment Rate: The percentage of users who enroll in a campaign after seeing it. "
         "Calculated as (enrollments / impressions) * 100. A good enrollment rate for credit card "
         "campaigns is typically 5-15%. Higher rates indicate strong campaign messaging and targeting."),
        ("Redemption Rate: The percentage of enrolled customers who actually redeem their reward. "
         "Calculated as (redemptions / enrollments) * 100. Industry benchmark is 40-70%. "
         "High redemption rates indicate the reward is valuable and easy to use."),
        ("ROI (Return on Investment): Measures campaign profitability. "
         "Calculated as ((revenue - cost) / cost) * 100. For credit card campaigns, "
         "ROI above 100% is considered successful. Top campaigns achieve 150-250% ROI."),
        ("Campaign Types: Cashback campaigns offer percentage back on purchases. "
         "Travel campaigns reward airline/hotel spending with miles or points. "
         "Dining campaigns partner with restaurants for food-related rewards. "
         "Retail campaigns focus on shopping at partner stores and e-commerce."),
        ("Merchant Categories: Restaurants (dining/fast food), Airlines (flights/travel), "
         "Grocery (supermarkets/wholesale), Electronics (tech/gadgets), Gas Stations (fuel/convenience). "
         "Each category has different average transaction values and redemption patterns."),
        ("Customer Segments: Premium — high-income, high-spend cardholders with annual fees. "
         "Standard — mid-tier customers with moderate spending. "
         "Student — younger demographic, lower spend but high engagement and long-term value."),
        ("Cost Per Enrollment (CPE): The average cost to acquire one enrolled customer. "
         "Calculated as total campaign cost / number of enrollments. "
         "Lower CPE indicates more efficient customer acquisition. Benchmark: $10-$40."),
    ]
    for i, doc in enumerate(glossary_docs):
        documents.append(doc)
        metadatas.append({"type": "business_glossary"})
        ids.append(f"glossary_{i}")

    # Ingest all documents
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Ingested {len(documents)} documents into ChromaDB collection '{COLLECTION_NAME}'")
    return collection


def search_similar(query, n_results=3):
    """Search the vector store for documents similar to the query."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=n_results)

    # Format results for easy consumption
    formatted = []
    for i in range(len(results["documents"][0])):
        formatted.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return formatted


if __name__ == "__main__":
    print("Building knowledge base...")
    build_knowledge_base()
    print("\nTesting search:")
    results = search_similar("Which campaign has the best ROI?")
    for r in results:
        print(f"\n[{r['metadata']['type']}] (distance: {r['distance']:.3f})")
        print(f"  {r['content'][:120]}...")
