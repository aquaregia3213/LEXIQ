import os
import pytest

# Ensure deterministic providers and test environment are used for the standard test suite
os.environ["AI_PROVIDER"] = "deterministic"
os.environ["LLM_PROVIDER"] = "deterministic"
os.environ["EMBEDDING_PROVIDER"] = "deterministic"
os.environ["ENVIRONMENT"] = "test"
