"""
RAG (Retrieval-Augmented Generation) Package for Campaign Performance Analysis.

Handles knowledge retrieval for company-specific data: campaign descriptions
are chunked, embedded, and stored in ChromaDB for semantic search.

Only data the LLM cannot know belongs here (campaign names, target segments,
reward structures, partner merchants, budgets). Generic business knowledge
(ROI definitions, metric formulas, benchmarks) is left to the LLM.

Sub-modules:
    documents    — Campaign description documents (Step 1)
    chunking     — Text splitting / chunking logic (Step 2)
    vector_store — ChromaDB embedding storage and semantic search (Steps 3-4, 6-8)
"""

from rag.vector_store import build_knowledge_base, search_similar, CampaignKnowledgeStore
