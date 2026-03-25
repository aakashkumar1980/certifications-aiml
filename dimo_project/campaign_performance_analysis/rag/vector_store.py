"""
Vector Store Module for the RAG Pipeline.

Manages the ChromaDB-backed vector store — handles embedding storage
and semantic similarity retrieval. Document loading and chunking are
delegated to ``rag.documents`` and ``rag.chunking`` respectively.

Persistence:
    ChromaDB data is persisted to ``./chroma_db/`` so that embeddings
    survive across application restarts without re-computation.
"""

import logging

import chromadb
from chromadb.utils import embedding_functions

from config.settings import Settings
from rag.documents import get_campaign_descriptions, get_performance_summaries, get_business_glossary
from rag.chunking import create_text_splitter, chunk_document

logger = logging.getLogger("rag_pipeline")


class CampaignKnowledgeStore:
    """
    ChromaDB-backed vector store for campaign domain knowledge.

    Orchestrates the full ingestion pipeline (load → chunk → embed → store)
    and provides semantic similarity search at query time.
    """

    def __init__(self, chroma_dir=None, collection_name=None, embedding_model=None):
        self.chroma_dir = chroma_dir or Settings.CHROMA_DIR
        self.collection_name = collection_name or Settings.CHROMA_COLLECTION
        self.embedding_model = embedding_model or Settings.EMBEDDING_MODEL
        self._collection = None

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

    def build_knowledge_base(self):
        """
        Ingest all knowledge documents into ChromaDB with chunking.

        Orchestrates: Load documents → Chunk → Embed → Store in ChromaDB.

        Returns:
            chromadb.Collection: The populated collection handle.
        """
        collection = self.get_collection()

        if collection.count() > 0:
            logger.info("[STEP 1-4] Knowledge base already populated with %d chunks. Skipping ingestion.", collection.count())
            return collection

        all_texts, all_metadatas, all_ids = [], [], []
        total_original_docs = 0
        splitter = create_text_splitter()

        # --- STEP 1: Loading Documents ---
        logger.info("=" * 80)
        logger.info("[STEP 1] LOADING DOCUMENTS: Gathering campaign descriptions, performance summaries, and business glossary...")

        descriptions = get_campaign_descriptions()
        logger.info("[STEP 1] Loaded %d campaign descriptions", len(descriptions))
        for cid, desc in descriptions:
            total_original_docs += 1
            texts, metas, ids = chunk_document(
                desc, f"desc_{cid}", {"type": "campaign_description", "campaign_id": cid}, splitter
            )
            all_texts.extend(texts)
            all_metadatas.extend(metas)
            all_ids.extend(ids)

        summaries = get_performance_summaries()
        logger.info("[STEP 1] Loaded %d performance summaries", len(summaries))
        for cid, summary in summaries:
            total_original_docs += 1
            texts, metas, ids = chunk_document(
                summary, f"perf_{cid}", {"type": "performance_summary", "campaign_id": cid}, splitter
            )
            all_texts.extend(texts)
            all_metadatas.extend(metas)
            all_ids.extend(ids)

        glossary = get_business_glossary()
        logger.info("[STEP 1] Loaded %d business glossary entries", len(glossary))
        for i, definition in enumerate(glossary):
            total_original_docs += 1
            texts, metas, ids = chunk_document(
                definition, f"glossary_{i}", {"type": "business_glossary"}, splitter
            )
            all_texts.extend(texts)
            all_metadatas.extend(metas)
            all_ids.extend(ids)

        logger.info("[STEP 2] CHUNKING COMPLETE: %d original documents -> %d chunks (chunk_size=%d, overlap=%d)",
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
            list[dict]: List of result dicts with content, metadata, distance.
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
