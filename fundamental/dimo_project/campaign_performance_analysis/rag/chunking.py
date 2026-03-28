"""
Text Chunking Module for the RAG Pipeline.

Splits documents into smaller, overlapping chunks before embedding.
Uses LangChain's RecursiveCharacterTextSplitter which tries natural
boundaries (paragraphs, sentences, commas) before falling back to
character-level splits.

Chunk size and overlap are configurable via ``Settings.CHUNK_SIZE``
and ``Settings.CHUNK_OVERLAP``.
"""

import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Settings

logger = logging.getLogger("rag_pipeline")


def create_text_splitter():
    """
    Create a RecursiveCharacterTextSplitter with project-wide settings.

    Returns:
        RecursiveCharacterTextSplitter: Configured text splitter.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=Settings.CHUNK_SIZE,
        chunk_overlap=Settings.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def chunk_document(text, doc_id, metadata, text_splitter=None):
    """
    Split a document into chunks ready for ChromaDB ingestion.

    Args:
        text (str): The full document text.
        doc_id (str): Base document ID (e.g., 'desc_CMP-001').
        metadata (dict): Metadata to attach to each chunk.
        text_splitter (RecursiveCharacterTextSplitter, optional):
            Splitter instance. Creates default if None.

    Returns:
        tuple: (chunk_texts, chunk_metadatas, chunk_ids)
    """
    if text_splitter is None:
        text_splitter = create_text_splitter()

    chunks = text_splitter.split_text(text)
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
