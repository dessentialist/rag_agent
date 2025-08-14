import json
import logging
import requests
from services.pinecone_service import semantic_search
from services.agent_registry import select_agent_for_request

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_agent_selection")

def test_query(query, expected_agent_type=None):
    """
    Test a query for agent selection and report results
    
    Args:
        query: The query to test
        expected_agent_type: Optional expected agent type for validation
    """
    logger.info(f"\n{'='*80}\nTESTING QUERY: '{query}'\n{'='*80}")
    
    # 1. Test direct agent selection logic
    logger.info("STEP 1: Testing select_agent_for_request function directly")
    relevant_docs = semantic_search(query, limit=5)
    selected_agent, matched = select_agent_for_request(relevant_docs, query)
    agent_type = selected_agent.name if selected_agent else 'none'
    logger.info(f"RESULT: Selected agent is '{agent_type}' with rules: {matched}")
    
    # Track document types for analysis
    doc_types = []
    doc_type_counts = {}
    
    for idx, doc in enumerate(relevant_docs):
        metadata = doc.get('metadata', {})
        doc_type = metadata.get('type', 'unknown')
        doc_types.append(doc_type)
        
        # Count normalized types
        if isinstance(doc_type, str):
            norm_type = doc_type.lower()
            doc_type_counts[norm_type] = doc_type_counts.get(norm_type, 0) + 1
    
    logger.info(f"Document types found: {doc_types}")
    logger.info(f"Document type counts: {doc_type_counts}")
    
    # 2. Test the select-agent API endpoint
    try:
        logger.info("\nSTEP 2: Testing /api/health endpoint")
        response = requests.post(
            "http://localhost:5000/api/health",
            json={},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"API RESULT: health ok -> {response.json()}")
        else:
            logger.error(f"API Error: Status {response.status_code}")
            logger.error(f"Response: {response.text}")
    
    except Exception as e:
        logger.error(f"Error testing API: {str(e)}")
    
    logger.info(f"{'='*80}\nTEST COMPLETE\n{'='*80}\n")
    return agent_type

# Documentation query test
logger.info("\n\n### TESTING DOCUMENTATION QUERY ###\n")
doc_query = "what is a data source connector? how many types are there, and how do I use it?"
doc_agent_type = test_query(doc_query, "documentation")

# Course query test
logger.info("\n\n### TESTING COURSE QUERY ###\n")
course_query = "what are the steps for me to set up classifiers for data scanning?"
course_agent_type = test_query(course_query, "course")

# Report overall results
logger.info("\n\n### SUMMARY RESULTS ###\n")
logger.info(f"Documentation query => {doc_agent_type} agent")
logger.info(f"Course query => {course_agent_type} agent")
logger.info("\nTest completed!")