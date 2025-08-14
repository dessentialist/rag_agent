import logging

import pytest

# Skip this module during chunks 4–6 because it requires configured external services
pytest.skip(
    "Skipping agent selection test during chunks 4–6; requires configured OpenAI/Pinecone.",
    allow_module_level=True,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_agent_selection")
