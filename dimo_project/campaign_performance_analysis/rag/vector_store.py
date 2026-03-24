"""
Vector Store Module for Campaign Performance Analysis.

Manages a ChromaDB-backed vector store that serves as the knowledge base
for the RAG (Retrieval-Augmented Generation) pipeline. Three categories
of documents are ingested:

1. **Campaign Descriptions** — Objective and targeting details per campaign.
2. **Performance Summaries** — Narrative analysis of each campaign's KPIs.
3. **Business Glossary** — Definitions of financial-services metrics and terms.

At query time, the ``search_similar`` function performs a semantic similarity
search against all ingested documents and returns the top-N matches along
with their metadata and distance scores.

Persistence:
    ChromaDB data is persisted to ``./chroma_db/`` so that embeddings survive
    across application restarts without re-computation.

Example Usage::

    from rag.vector_store import CampaignKnowledgeStore
    store = CampaignKnowledgeStore()
    store.build_knowledge_base()
    results = store.search_similar("What is ROI?", n_results=3)
"""

import os
import sys

import chromadb
from chromadb.utils import embedding_functions

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings


class CampaignKnowledgeStore:
    """
    ChromaDB-backed vector store for campaign domain knowledge.

    Handles embedding generation via HuggingFace sentence-transformers,
    document ingestion into a named ChromaDB collection, and semantic
    similarity retrieval.

    Attributes:
        chroma_dir (str): Filesystem path for ChromaDB persistent storage.
        collection_name (str): Name of the ChromaDB collection.
        embedding_model (str): HuggingFace model identifier for embeddings.
        _collection (chromadb.Collection | None): Lazily initialized collection handle.

    Example::

        store = CampaignKnowledgeStore()
        store.build_knowledge_base()
        hits = store.search_similar("enrollment rate benchmark")
    """

    def __init__(self, chroma_dir=None, collection_name=None, embedding_model=None):
        """
        Initialize the knowledge store with configurable paths and models.

        Args:
            chroma_dir (str, optional): Directory for ChromaDB persistence.
                Defaults to ``Settings.CHROMA_DIR``.
            collection_name (str, optional): Collection name in ChromaDB.
                Defaults to ``Settings.CHROMA_COLLECTION``.
            embedding_model (str, optional): Sentence-transformer model name.
                Defaults to ``Settings.EMBEDDING_MODEL``.
        """
        self.chroma_dir = chroma_dir or Settings.CHROMA_DIR
        self.collection_name = collection_name or Settings.CHROMA_COLLECTION
        self.embedding_model = embedding_model or Settings.EMBEDDING_MODEL
        self._collection = None

    def _get_embedding_function(self):
        """
        Create a HuggingFace sentence-transformer embedding function.

        Returns:
            SentenceTransformerEmbeddingFunction: Callable that converts
                text strings into dense vector embeddings.
        """
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

    def get_collection(self):
        """
        Get or create the ChromaDB collection (lazy singleton).

        On first call, initializes a ``PersistentClient`` and retrieves
        (or creates) the named collection. Subsequent calls return the
        cached collection handle.

        Returns:
            chromadb.Collection: The campaign knowledge collection.
        """
        if self._collection is None:
            client = chromadb.PersistentClient(path=self.chroma_dir)
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._get_embedding_function(),
            )
        return self._collection

    def _get_campaign_descriptions(self):
        """
        Return pre-authored campaign description documents.

        Each tuple contains (campaign_id, description_text). These serve
        as the qualitative context layer — explaining what each campaign
        is about, who it targets, and what rewards it offers.

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

    def _get_performance_summaries(self):
        """
        Return pre-authored performance summary narratives.

        Each tuple contains (campaign_id, summary_text). These provide
        the RAG system with pre-analyzed insights so it can answer
        performance questions without always hitting the database.

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

    def _get_business_glossary(self):
        """
        Return business glossary definitions for financial-services terms.

        These definitions help the LLM understand domain-specific concepts
        and provide accurate, contextual answers to business users.

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

    def build_knowledge_base(self):
        """
        Ingest all knowledge documents into the ChromaDB collection.

        Combines campaign descriptions, performance summaries, and business
        glossary entries into a single batch ingestion. Skips ingestion if
        the collection is already populated (idempotent on non-empty stores).

        Document IDs follow the convention:
            - ``desc_CMP-XXX`` for campaign descriptions
            - ``perf_CMP-XXX`` for performance summaries
            - ``glossary_N`` for glossary entries

        Returns:
            chromadb.Collection: The populated collection handle.
        """
        collection = self.get_collection()

        if collection.count() > 0:
            print(f"  Collection already has {collection.count()} documents. Skipping ingestion.")
            return collection

        documents, metadatas, ids = [], [], []

        # Ingest campaign descriptions
        for cid, desc in self._get_campaign_descriptions():
            documents.append(desc)
            metadatas.append({"type": "campaign_description", "campaign_id": cid})
            ids.append(f"desc_{cid}")

        # Ingest performance summaries
        for cid, summary in self._get_performance_summaries():
            documents.append(summary)
            metadatas.append({"type": "performance_summary", "campaign_id": cid})
            ids.append(f"perf_{cid}")

        # Ingest business glossary
        for i, definition in enumerate(self._get_business_glossary()):
            documents.append(definition)
            metadatas.append({"type": "business_glossary"})
            ids.append(f"glossary_{i}")

        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"  Ingested {len(documents)} documents into '{self.collection_name}' collection")
        return collection

    def search_similar(self, query, n_results=None):
        """
        Perform semantic similarity search against the knowledge base.

        Embeds the query string using the same sentence-transformer model
        used during ingestion, then retrieves the closest documents by
        cosine distance from ChromaDB.

        Args:
            query (str): Natural language search query.
            n_results (int, optional): Maximum number of results to return.
                Defaults to ``Settings.RAG_DEFAULT_RESULTS`` (3).

        Returns:
            list[dict]: List of result dictionaries, each containing:
                - ``content`` (str): The matched document text.
                - ``metadata`` (dict): Document metadata (type, campaign_id).
                - ``distance`` (float | None): Cosine distance score.
                Lower distance = higher relevance.

        Example::

            results = store.search_similar("best performing campaign")
            for r in results:
                print(r["metadata"]["type"], r["distance"])
        """
        n_results = n_results or Settings.RAG_DEFAULT_RESULTS
        collection = self.get_collection()

        if collection.count() == 0:
            return []

        results = collection.query(query_texts=[query], n_results=n_results)

        formatted = []
        for i in range(len(results["documents"][0])):
            formatted.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return formatted


# --- Module-Level Convenience Functions ---

_default_store = CampaignKnowledgeStore()


def build_knowledge_base():
    """Build the knowledge base using default settings. See ``CampaignKnowledgeStore.build_knowledge_base``."""
    return _default_store.build_knowledge_base()


def search_similar(query, n_results=None):
    """Search for similar documents. See ``CampaignKnowledgeStore.search_similar``."""
    return _default_store.search_similar(query, n_results)


# --- Script Entry Point ---
if __name__ == "__main__":
    print("Building knowledge base...")
    store = CampaignKnowledgeStore()
    store.build_knowledge_base()
    print("\nTesting semantic search: 'Which campaign has the best ROI?'")
    results = store.search_similar("Which campaign has the best ROI?")
    for r in results:
        print(f"\n  [{r['metadata']['type']}] (distance: {r['distance']:.3f})")
        print(f"  {r['content'][:120]}...")
