"""
Configuration Module for RAGBot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_API_BASE_URL = os.getenv("QWEN_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# Process-only semantic index. Performance values and papers are not embedded.
PROCESS_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
PROCESS_VECTOR_TOP_K = int(os.getenv("PROCESS_VECTOR_TOP_K", "48"))

# LLM Model
LLM_MODEL = os.getenv("QWEN_MODEL", "qwen3.5-plus")

# RAG Configuration
DEFAULT_TOP_K = 5
RAG_DATABASE_PATH = os.getenv("RAG_DATABASE_PATH", "data/welding_rag.db")
