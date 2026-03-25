"""
Vector Store Module for Campaign Performance Analysis.

Manages a ChromaDB-backed vector store that serves as the knowledge base
for the RAG (Retrieval-Augmented Generation) pipeline. Three categories
of documents are ingested:

1. **Campaign Descriptions** — Objective and targeting details per campaign.
2. **Performance Summaries** — Narrative analysis of each campaign's KPIs.
3. **Business Glossary** — Definitions of financial-services metrics and terms.

Documents are chunked using LangChain's RecursiveCharacterTextSplitter
before embedding, ensuring optimal retrieval granularity.

At query time, the ``search_similar`` function performs a semantic similarity
search against all ingested chunks and returns the top-N matches along
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
import logging

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings

logger = logging.getLogger("rag_pipeline")


class CampaignKnowledgeStore:
    """
    ChromaDB-backed vector store for campaign domain knowledge.

    Handles text chunking, embedding generation via HuggingFace
    sentence-transformers, document ingestion into a named ChromaDB
    collection, and semantic similarity retrieval.

    Attributes:
        chroma_dir (str): Filesystem path for ChromaDB persistent storage.
        collection_name (str): Name of the ChromaDB collection.
        embedding_model (str): HuggingFace model identifier for embeddings.
        _collection (chromadb.Collection | None): Lazily initialized collection handle.
    """

    def __init__(self, chroma_dir=None, collection_name=None, embedding_model=None):
        self.chroma_dir = chroma_dir or Settings.CHROMA_DIR
        self.collection_name = collection_name or Settings.CHROMA_COLLECTION
        self.embedding_model = embedding_model or Settings.EMBEDDING_MODEL
        self._collection = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Settings.CHUNK_SIZE,
            chunk_overlap=Settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
        )

    def _get_embedding_function(self):
        """Create a HuggingFace sentence-transformer embedding function."""
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

    def get_collection(self):
        """Get or create the ChromaDB collection (lazy singleton)."""
        if self._collection is None:
            client = chromadb.PersistentClient(path=self.chroma_dir)
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._get_embedding_function(),
            )
        return self._collection

    def _chunk_document(self, text, doc_id, metadata):
        """
        Split a document into chunks and return lists ready for ChromaDB ingestion.

        Args:
            text (str): The full document text.
            doc_id (str): Base document ID (e.g., 'desc_CMP-001').
            metadata (dict): Metadata to attach to each chunk.

        Returns:
            tuple: (chunks_texts, chunks_metadatas, chunks_ids)
        """
        chunks = self._text_splitter.split_text(text)
        logger.info(
            "  [STEP 2] CHUNKING: doc_id='%s' | original_length=%d chars | chunks_produced=%d | chunk_size=%d | overlap=%d",
            doc_id, len(text), len(chunks), Settings.CHUNK_SIZE, Settings.CHUNK_OVERLAP,
        )
        for i, chunk in enumerate(chunks):
            logger.debug("    Chunk %d/%d (%d chars): %.80s...", i + 1, len(chunks), len(chunk), chunk)

        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {**metadata, "chunk_index": i, "total_chunks": len(chunks), "source_doc_id": doc_id}
            chunk_texts.append(chunk)
            chunk_metadatas.append(chunk_meta)
            chunk_ids.append(f"{doc_id}_chunk{i}")

        return chunk_texts, chunk_metadatas, chunk_ids

    def _get_campaign_descriptions(self):
        """Return pre-authored campaign description documents."""
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
        """Return pre-authored performance summary narratives."""
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
        """Return business glossary definitions for financial-services terms."""
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
        Ingest all knowledge documents into ChromaDB with chunking.

        Documents are first split into chunks using RecursiveCharacterTextSplitter,
        then each chunk is embedded and stored in ChromaDB.

        Returns:
            chromadb.Collection: The populated collection handle.
        """
        collection = self.get_collection()

        if collection.count() > 0:
            logger.info("[STEP 1-4] Knowledge base already populated with %d chunks. Skipping ingestion.", collection.count())
            return collection

        all_texts, all_metadatas, all_ids = [], [], []
        total_original_docs = 0

        # --- STEP 1: Loading Documents ---
        logger.info("=" * 80)
        logger.info("[STEP 1] LOADING DOCUMENTS: Gathering campaign descriptions, performance summaries, and business glossary...")

        # Ingest campaign descriptions with chunking
        descriptions = self._get_campaign_descriptions()
        logger.info("[STEP 1] Loaded %d campaign descriptions", len(descriptions))
        for cid, desc in descriptions:
            total_original_docs += 1
            texts, metas, ids = self._chunk_document(
                desc, f"desc_{cid}", {"type": "campaign_description", "campaign_id": cid}
            )
            all_texts.extend(texts)
            all_metadatas.extend(metas)
            all_ids.extend(ids)

        # Ingest performance summaries with chunking
        summaries = self._get_performance_summaries()
        logger.info("[STEP 1] Loaded %d performance summaries", len(summaries))
        for cid, summary in summaries:
            total_original_docs += 1
            texts, metas, ids = self._chunk_document(
                summary, f"perf_{cid}", {"type": "performance_summary", "campaign_id": cid}
            )
            all_texts.extend(texts)
            all_metadatas.extend(metas)
            all_ids.extend(ids)

        # Ingest business glossary with chunking
        glossary = self._get_business_glossary()
        logger.info("[STEP 1] Loaded %d business glossary entries", len(glossary))
        for i, definition in enumerate(glossary):
            total_original_docs += 1
            texts, metas, ids = self._chunk_document(
                definition, f"glossary_{i}", {"type": "business_glossary"}
            )
            all_texts.extend(texts)
            all_metadatas.extend(metas)
            all_ids.extend(ids)

        logger.info("[STEP 2] CHUNKING COMPLETE: %d original documents → %d chunks (chunk_size=%d, overlap=%d)",
                     total_original_docs, len(all_texts), Settings.CHUNK_SIZE, Settings.CHUNK_OVERLAP)

        # --- STEP 3: Embedding Chunks ---
        logger.info("[STEP 3] EMBEDDING CHUNKS: Encoding %d chunks using model '%s'...", len(all_texts), self.embedding_model)

        # --- STEP 4: Storing in Vector Database ---
        collection.add(documents=all_texts, metadatas=all_metadatas, ids=all_ids)
        logger.info("[STEP 4] STORED IN VECTOR DATABASE: %d chunks ingested into ChromaDB collection '%s' at '%s'",
                     len(all_texts), self.collection_name, self.chroma_dir)
        logger.info("=" * 80)

        return collection

    def search_similar(self, query, n_results=None):
        """
        Perform semantic similarity search against the knowledge base.

        Args:
            query (str): Natural language search query.
            n_results (int, optional): Maximum number of results to return.

        Returns:
            list[dict]: List of result dictionaries with content, metadata, distance.
        """
        n_results = n_results or Settings.RAG_DEFAULT_RESULTS
        collection = self.get_collection()

        if collection.count() == 0:
            logger.warning("[STEP 7] Semantic search skipped — collection is empty.")
            return []

        # --- STEP 6: Embedding Query ---
        logger.info("-" * 80)
        logger.info("[STEP 6] EMBEDDING QUERY: Encoding user query using '%s'", self.embedding_model)
        logger.info("[STEP 6] Query text: \"%s\"", query)

        # --- STEP 7: Semantic Search ---
        logger.info("[STEP 7] SEMANTIC SEARCH: Finding top-%d closest vectors (cosine similarity) in collection '%s' (%d chunks)...",
                     n_results, self.collection_name, collection.count())

        results = collection.query(query_texts=[query], n_results=n_results)

        # --- STEP 8: Retrieving Semantically Closest Chunks ---
        formatted = []
        for i in range(len(results["documents"][0])):
            distance = results["distances"][0][i] if results.get("distances") else None
            metadata = results["metadatas"][0][i]
            content = results["documents"][0][i]
            formatted.append({
                "content": content,
                "metadata": metadata,
                "distance": distance,
            })
            logger.info(
                "[STEP 8] RETRIEVED CHUNK %d: type=%s | campaign=%s | distance=%.4f | chunk=%d/%d | preview=\"%.100s...\"",
                i + 1,
                metadata.get("type", "unknown"),
                metadata.get("campaign_id", "N/A"),
                distance if distance is not None else -1,
                metadata.get("chunk_index", 0) + 1,
                metadata.get("total_chunks", 1),
                content,
            )

        logger.info("-" * 80)
        return formatted


# --- Module-Level Convenience Functions ---

_default_store = CampaignKnowledgeStore()


def build_knowledge_base():
    """Build the knowledge base using default settings."""
    return _default_store.build_knowledge_base()


def search_similar(query, n_results=None):
    """Search for similar documents."""
    return _default_store.search_similar(query, n_results)


# --- Script Entry Point ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    print("Building knowledge base...")
    store = CampaignKnowledgeStore()
    store.build_knowledge_base()
    print("\nTesting semantic search: 'Which campaign has the best ROI?'")
    results = store.search_similar("Which campaign has the best ROI?")
    for r in results:
        print(f"\n  [{r['metadata']['type']}] (distance: {r['distance']:.3f})")
        print(f"  {r['content'][:120]}...")
