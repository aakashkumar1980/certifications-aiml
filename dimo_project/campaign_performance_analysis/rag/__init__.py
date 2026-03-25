"""
RAG (Retrieval-Augmented Generation) Package for Campaign Performance Analysis.

Handles all knowledge retrieval: document loading, text chunking,
embedding generation, vector storage, and semantic search.

Sub-modules:
    documents    — Hard-coded campaign knowledge documents (Step 1)
    chunking     — Text splitting / chunking logic (Step 2)
    vector_store — ChromaDB embedding storage and semantic search (Steps 3-4, 6-8)
"""

from rag.vector_store import build_knowledge_base, search_similar, CampaignKnowledgeStore
