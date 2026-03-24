"""
Centralized Configuration Settings for Campaign Performance Analysis.

This module serves as the single source of truth for all application-wide
constants, file paths, model parameters, and environment-driven settings.
All other modules import their configuration from here rather than
defining local constants, ensuring consistency and easy maintenance.

Environment Variables:
    ANTHROPIC_API_KEY (str): Required. API key for Claude LLM access.

Example Usage::

    from config.settings import Settings
    settings = Settings()
    print(settings.DB_PATH)
    print(settings.LLM_MODEL)
"""

import os
from dotenv import load_dotenv

# Load .env file from the project root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


class Settings:
    """
    Application-wide configuration container.

    Centralizes all paths, model names, and tunable parameters so that
    every module reads from one place. Values are resolved once at
    import time; path properties are computed relative to the project root.

    Attributes:
        PROJECT_ROOT (str): Absolute path to the project root directory.
        DATA_DIR (str): Directory where generated CSV files are stored.
        DB_PATH (str): Full path to the SQLite database file.
        CHROMA_DIR (str): Directory for ChromaDB persistent storage.
        CHROMA_COLLECTION (str): Name of the ChromaDB collection.
        EMBEDDING_MODEL (str): HuggingFace model used for text embeddings.
        LLM_MODEL (str): Claude model identifier for all LLM calls.
        LLM_TEMPERATURE (float): Sampling temperature for LLM responses.
        LLM_MAX_TOKENS (int): Maximum token count for LLM responses.
        ANTHROPIC_API_KEY (str | None): API key loaded from environment.
        MOCK_DATA_SEED (int): Random seed for reproducible data generation.
        NUM_CAMPAIGNS (int): Number of campaigns to generate.
        NUM_ENROLLMENTS (int): Number of enrollment records to generate.
        NUM_REDEMPTIONS (int): Number of redemption records to generate.
        PERF_MONTHS (int): Number of monthly performance records per campaign.
    """

    # --- Directory Paths ---
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(PROJECT_ROOT, "database", "data")
    DB_PATH = os.path.join(PROJECT_ROOT, "database", "campaign.db")
    CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

    # --- ChromaDB Settings ---
    CHROMA_COLLECTION = "campaign_knowledge"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # --- Claude LLM Settings ---
    LLM_MODEL = "claude-sonnet-4-20250514"
    LLM_TEMPERATURE = 0
    LLM_MAX_TOKENS = 2048
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # --- Mock Data Generation ---
    MOCK_DATA_SEED = 42
    NUM_CAMPAIGNS = 5
    NUM_ENROLLMENTS = 500
    NUM_REDEMPTIONS = 300
    PERF_MONTHS = 6

    # --- Agent Settings ---
    AGENT_MAX_ITERATIONS = 5
    RAG_DEFAULT_RESULTS = 3

    @classmethod
    def validate(cls):
        """
        Validate that all required configuration values are present.

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set in the environment.

        Returns:
            bool: True if all validations pass.
        """
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Please create a .env file from .env and add your API key."
            )
        return True
