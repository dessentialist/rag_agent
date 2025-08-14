import os
import logging
import json
from typing import List, Dict, Any
import traceback
from openai import OpenAI
from config import (
    OPENAI_API_KEY, 
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_RESPONSE_FORMAT,
    COURSE_AGENT_NAME,
    COURSE_AGENT_DESCRIPTION,
    COURSE_AGENT_INSTRUCTIONS,
    DOC_AGENT_NAME,
    DOC_AGENT_DESCRIPTION,
    DOC_AGENT_INSTRUCTIONS,
    AGENT_PERSONA,
    AGENT_GOAL,
    AGENT_TOOLS,
    RAG_SYSTEM_MESSAGE_TEMPLATE,
    NO_DOCUMENTS_MESSAGE,
    CRITICAL_REMINDER_MESSAGE,
    LOG_LEVEL,
    LOG_FORMAT
)
from services.pinecone_service import semantic_search

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py
logger.debug("Agno service logger configured with console output")

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class AgnoAgent:
    """
    Implementation of the Agno agent integration using OpenAI
    """
    def __init__(self, name: str, description: str, instructions: str, persona: str, goal: str):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.persona = persona
        self.goal = goal
        self.tools = []
        logger.info(f"Initialized Agno agent: {name}")
    
    def add_tool(self, tool: Dict[str, Any]):
        """
        Add a tool to the agent
        
        Args:
            tool: Dictionary defining the tool
        """
        self.tools.append(tool)
        logger.debug(f"Added tool to agent {self.name}: {tool.get('name')}")
    
    async def run(self, query: str, context: Dict[str, Any] = None):
        """
        Run the agent with a query
        
        Args:
            query: User query
            context: Additional context (can include pre-retrieved docs)
        
        Returns:
            Agent response
        """
        logger.info(f"Running Agno agent with query: {query}")
        
        try:
            # Initialize context if None
            if context is None:
                context = {}
                
            # Get relevant documents - either from the provided context or by performing a new search
            relevant_docs = []
            if 'relevant_docs' in context:
                # Use pre-retrieved documents if available in context
                relevant_docs = context['relevant_docs']
                logger.info(f"[RAG] Using {len(relevant_docs)} pre-retrieved relevant documents")
            else:
                # Otherwise perform a new search
                logger.info(f"[RAG] Searching for relevant documents for query: {query}")
                relevant_docs = semantic_search(query, limit=5)
            
            # Log detailed information about the retrieved documents
            if relevant_docs:
                logger.info(f"[RAG] Retrieved {len(relevant_docs)} relevant documents from vector database")
                for i, doc in enumerate(relevant_docs):
                    doc_id = doc.get('id', 'unknown')
                    doc_score = doc.get('score', 0)
                    doc_source = doc.get('metadata', {}).get('source_filename', 'unknown')
                    doc_type = doc.get('metadata', {}).get('type', 'unknown')
                    doc_content_preview = doc.get('content', '')[:100] + "..." if len(doc.get('content', '')) > 100 else doc.get('content', '')
                    logger.info(f"[RAG] Document {i+1}: ID={doc_id}, Score={doc_score:.4f}, Source={doc_source}, Type={doc_type}")
                    logger.info(f"[RAG] Document {i+1} Preview: {doc_content_preview}")
            else:
                logger.warning(f"[RAG] No relevant documents found for query: {query}")
            
            # Format the context from relevant documents with explicit source information
            docs_context = ""
            if relevant_docs:
                for i, doc in enumerate(relevant_docs):
                    # Include metadata information if available
                    source_info = ""
                    metadata = doc.get('metadata', {})
                    if metadata:
                        if 'source_filename' in metadata:
                            source_info += f"Source filename: {metadata['source_filename']}\n"
                        if 'source' in metadata:
                            source_info += f"Source URL: {metadata['source']}\n"
                        if 'type' in metadata:
                            source_info += f"Document Type: {metadata['type']}\n"
                    
                    docs_context += f"Document {i+1} [ID: {doc.get('id', 'unknown')}]:\n{source_info}\nContent:\n{doc['content']}\n\n"
            
            # Create strict RAG-only system message using template from config
            rag_system_message = RAG_SYSTEM_MESSAGE_TEMPLATE.format(
                instructions=self.instructions,
                persona=self.persona,
                goal=self.goal
            )
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": rag_system_message}
            ]
            
            # Add context from relevant documents if available
            if docs_context:
                messages.append({
                    "role": "system", 
                    "content": f"## RETRIEVED DOCUMENTS (ONLY USE INFORMATION FROM THESE DOCUMENTS)\n\n{docs_context}"
                })
            else:
                # If no documents were found, add an explicit instruction
                messages.append({
                    "role": "system", 
                    "content": NO_DOCUMENTS_MESSAGE
                })
            
            # Add an additional reminder message
            messages.append({
                "role": "system", 
                "content": CRITICAL_REMINDER_MESSAGE
            })
            
            # Add the user query
            messages.append({"role": "user", "content": query})
            
            # Log API call information
            logger.info(f"[API] Making OpenAI API call with model: {LLM_MODEL}")
            logger.info(f"[API] Number of messages: {len(messages)}")
            # Redact the actual content to avoid logging sensitive data
            message_summary = [{"role": msg["role"], "content_length": len(msg["content"])} for msg in messages]
            logger.info(f"[API] Message structure: {json.dumps(message_summary)}")
            
            # Call OpenAI API using config parameters
            response = client.chat.completions.create(
                model=LLM_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                response_format=LLM_RESPONSE_FORMAT
            )
            
            logger.info(f"[API] Received response from OpenAI API, tokens used: {response.usage.total_tokens}")
            
            # Parse and return the response
            response_text = response.choices[0].message.content
            
            try:
                parsed_response = json.loads(response_text)
                
                # Log what documents were cited in the response
                if 'main' in parsed_response:
                    main_content = parsed_response['main']
                    logger.info(f"[RAG] Response generated with {len(main_content)} characters")
                    # Check if response contains citations
                    contains_document_citation = any(f"Document {i+1}" in main_content for i in range(len(relevant_docs)))
                    if contains_document_citation:
                        logger.info("[RAG] Response contains document citations")
                    else:
                        logger.warning("[RAG] Response does not contain document citations")
                
                return parsed_response
            except json.JSONDecodeError:
                # If JSON parsing fails, return a structured response anyway
                logger.warning(f"JSON parsing failed for response: {response_text}")
                return {
                    "main": response_text,
                    "related_concepts": [],
                    "resources": []
                }
            
        except Exception as e:
            error_message = f"Error running Agno agent: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            return {
                "main": "I'm sorry, I encountered an error while processing your request. Please try again.",
                "related_concepts": [],
                "resources": []
            }

# Generic function to create an agent
def create_agent(name, description, instructions):
    """
    Create an Agno agent with the specified parameters
    
    Args:
        name: The agent name
        description: The agent description
        instructions: The agent instructions
        
    Returns:
        AgnoAgent object
    """
    try:
        # Create the agent using the provided parameters and shared configurations
        agent = AgnoAgent(
            name=name,
            description=description,
            instructions=instructions,
            persona=AGENT_PERSONA,  # Shared persona
            goal=AGENT_GOAL         # Shared goal
        )
        
        # Add tools from configuration (same for all agents)
        for tool in AGENT_TOOLS:
            agent.add_tool(tool)
        
        logger.info(f"Created {name} agent")
        return agent
    
    except Exception as e:
        logger.error(f"Error creating {name} agent: {str(e)}", exc_info=True)
        return None

# Create the course agent instance
course_agent = create_agent(
    name=COURSE_AGENT_NAME,
    description=COURSE_AGENT_DESCRIPTION,
    instructions=COURSE_AGENT_INSTRUCTIONS
)

# Create the documentation agent instance
doc_agent = create_agent(
    name=DOC_AGENT_NAME,
    description=DOC_AGENT_DESCRIPTION,
    instructions=DOC_AGENT_INSTRUCTIONS
)

# Function to select the appropriate agent based on document type
def select_agent_by_doc_type(relevant_docs):
    """
    Select the appropriate agent based on document types in the retrieved documents
    
    Args:
        relevant_docs: List of relevant documents from semantic search
        
    Returns:
        The appropriate AgnoAgent instance
    """
    # Simply check for documents with "type" value of "documentation"
    for doc in relevant_docs:
        # Get the type directly from metadata
        metadata = doc.get('metadata', {}) or {}
        doc_type = metadata.get('type', '')
        
        # Log for debugging
        if doc_type:
            doc_id = doc.get('id', 'unknown')
            logger.info(f"Document type: {doc_type} (id={doc_id})")
        
        # Check if this is a documentation type (case-insensitive)
        if isinstance(doc_type, str) and doc_type.lower() == 'documentation':
            logger.info(f"Using doc_agent because document has type='documentation'")
            return doc_agent
    
    # Default to course agent if no documentation type found
    logger.info("Using course_agent (no documentation type documents found)")
    return course_agent


