import os
import json
import logging
import uuid
import shutil
from datetime import datetime
from models import Document, DocumentChunk
from utils.embeddings import chunk_text
from services.pinecone_service import upsert_to_pinecone, delete_from_pinecone, list_all_vectors
from database import db
from config import KNOWLEDGE_BASE_DIR

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py
logger.debug("File service logger configured with console output")

# Log knowledge base directory
logger.info(f"Knowledge base directory set to: {KNOWLEDGE_BASE_DIR}")

def save_file(file_id, filename, file_type, content):
    """
    Save a file to the database
    
    Args:
        file_id: Unique identifier for the file
        filename: Name of the file
        file_type: File type/extension
        content: File content
    
    Returns:
        The document object
    """
    try:
        # Determine document type based on filename and content
        doc_type = "other"
        
        # Check filename for type indicators
        if "course" in filename.lower() or "lesson" in filename.lower() or "university" in filename.lower():
            doc_type = "course"
        elif "documentation" in filename.lower() or "docs" in filename.lower() or "manual" in filename.lower():
            doc_type = "documentation"
            
        # Create a document object
        document = Document(
            id=file_id,
            filename=filename,
            file_type=file_type,
            content=content,
            file_metadata={
                "source": "user_upload",
                "file_type": file_type,
                "doc_type": doc_type
            }
        )
        
        # Save to database
        db.session.add(document)
        db.session.commit()
        
        logger.debug(f"File saved to database: {filename} (ID: {file_id})")
        return document
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving file: {str(e)}", exc_info=True)
        raise

def get_all_files():
    """
    Get all files metadata (without content)
    
    Returns:
        List of file metadata dictionaries
    """
    try:
        documents = Document.query.all()
        return [doc.to_dict() for doc in documents]
    except Exception as e:
        logger.error(f"Error getting all files: {str(e)}", exc_info=True)
        return []

def get_file_by_id(file_id):
    """
    Get a file by ID
    
    Args:
        file_id: ID of the file to retrieve
    
    Returns:
        Tuple of (file_metadata, file_content) or (None, None) if not found
    """
    try:
        document = Document.query.get(file_id)
        if not document:
            return None, None
        
        return document.to_dict(), document.content
    except Exception as e:
        logger.error(f"Error getting file by ID: {str(e)}", exc_info=True)
        return None, None

def delete_file_by_id(file_id):
    """
    Delete a file by ID
    
    Args:
        file_id: ID of the file to delete
    
    Returns:
        Boolean indicating success
    """
    try:
        document = Document.query.get(file_id)
        if not document:
            return False
        
        # Get the chunks associated with this file
        chunk_ids = [chunk.vector_id for chunk in document.chunks]
        
        # Delete the chunks from Pinecone
        for chunk_id in chunk_ids:
            delete_from_pinecone(chunk_id)
        
        # Delete the document from the database
        db.session.delete(document)
        db.session.commit()
        
        logger.debug(f"File deleted from database: {file_id}")
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        return False

def scan_knowledge_base():
    """
    Retrieve a list of all document chunks from Pinecone for display purposes.
    This function is read-only and doesn't modify the database.
    
    Returns:
        Dictionary with pinecone_stats and pinecone_documents
    """
    logger.info("Retrieving document information from Pinecone")
    
    # Get all documents from Pinecone
    pinecone_data = list_all_vectors()
    
    # Return statistics and document list
    return {
        "pinecone_stats": pinecone_data["stats"],
        "pinecone_documents": pinecone_data["documents"]
    }

def process_file_for_rag(file_id, filename, content, file_type):
    """
    Process a file for RAG by chunking it and upserting to Pinecone
    
    Args:
        file_id: ID of the file
        filename: Name of the file
        content: Content of the file
        file_type: Type of the file
    
    Returns:
        List of chunk IDs
    """
    try:
        # Parse content based on file type
        parsed_content = content
        category = None
        
        # Handle JSON files
        if file_type == 'json':
            try:
                json_data = json.loads(content)
                # Look for "Category" key in the JSON data
                if isinstance(json_data, dict) and "Category" in json_data:
                    category = json_data["Category"]
                    logger.info(f"Extracted Category '{category}' from JSON file: {filename}")
                # Convert JSON to a string representation
                parsed_content = json.dumps(json_data, indent=2)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON content in file: {filename}")
        
        # Handle JSONL (JSON Lines) files
        elif file_type == 'jsonl':
            try:
                # Process each line as a separate JSON object
                lines = content.strip().split('\n')
                processed_lines = []
                
                # Look for Category in first line
                if lines and len(lines) > 0:
                    try:
                        first_obj = json.loads(lines[0])
                        if isinstance(first_obj, dict) and "Category" in first_obj:
                            category = first_obj["Category"]
                            logger.info(f"Extracted Category '{category}' from JSONL file: {filename}")
                    except:
                        pass
                
                for i, line in enumerate(lines):
                    try:
                        json_obj = json.loads(line)
                        processed_lines.append(f"Record {i+1}: {json.dumps(json_obj, indent=2)}")
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in line {i+1} of JSONL file: {filename}")
                        processed_lines.append(f"Line {i+1}: {line} (Invalid JSON format)")
                
                parsed_content = "\n\n".join(processed_lines)
            except Exception as e:
                logger.warning(f"Error processing JSONL file {filename}: {str(e)}")
        
        # Handle CSV files
        elif file_type == 'csv':
            try:
                import csv
                from io import StringIO
                
                # Parse CSV
                csv_reader = csv.reader(StringIO(content))
                
                # Extract header and rows
                rows = list(csv_reader)
                if len(rows) > 0:
                    header = rows[0]
                    data_rows = rows[1:]
                    
                    # Check if one of the headers is 'Category'
                    category_index = -1
                    for i, header_name in enumerate(header):
                        if header_name.strip() == 'Category':
                            category_index = i
                            break
                    
                    # If we have a Category column and at least one data row, extract the value
                    if category_index >= 0 and len(data_rows) > 0:
                        first_data_row = data_rows[0]
                        if category_index < len(first_data_row):
                            category = first_data_row[category_index].strip()
                            logger.info(f"Extracted Category '{category}' from CSV file: {filename}")
                    
                    # Format as a more readable text
                    formatted_rows = []
                    
                    # Add header
                    formatted_rows.append("CSV Headers: " + ", ".join(header))
                    
                    # Add data rows
                    for i, row in enumerate(data_rows):
                        row_dict = {header[j]: value for j, value in enumerate(row) if j < len(header)}
                        formatted_rows.append(f"Row {i+1}: " + json.dumps(row_dict, indent=2))
                    
                    parsed_content = "\n\n".join(formatted_rows)
            except Exception as e:
                logger.warning(f"Error processing CSV file {filename}: {str(e)}")
        
        # Chunk the content
        chunks = chunk_text(parsed_content)
        
        # Track chunk IDs
        chunk_ids = []
        
        # Find the document
        document = Document.query.get(file_id)
        if not document:
            logger.error(f"Document not found for chunking: {file_id}")
            return []
        
        # Upsert each chunk to Pinecone
        for i, chunk_content in enumerate(chunks):
            chunk_id = f"{file_id}_chunk_{i}"
            
            # Find the document to get its metadata
            document = Document.query.get(file_id)
            if not document:
                logger.error(f"Document not found for metadata: {file_id}")
                continue
                
            # Initialize doc_type with a default value
            doc_type = "other"
            
            # Try to load document content as a JSON object
            try:
                document_content_json = json.loads(document.content)
                # Set doc_type to the value of "Type" if it exists
                doc_type = document_content_json.get("Type", "other")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON content for document {file_id}: {str(e)}", exc_info=True)
                # Keep using the default doc_type

            # If category was extracted from the file content, use it to determine the document type
            if category:
                if category.lower() == "course":
                    doc_type = "course"
                elif category.lower() == "documentation":
                    doc_type = "documentation"
                else:
                    # Default to documentation if not course
                    doc_type = "documentation"
                    
                # Update the document's metadata in the database with the extracted category
                document.file_metadata["doc_type"] = doc_type
                db.session.add(document)
                
                logger.info(f"Updated document type to '{doc_type}")
            
            # Metadata for the chunk
            metadata = {
                "content": chunk_content,
                "source_file_id": file_id,
                "source_filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "title": filename,
                "url": f"/api/files/{file_id}",
                "type": doc_type
            }
            
            # Upsert to Pinecone
            success = upsert_to_pinecone(chunk_id, chunk_content, metadata)
            
            if success:
                # Create a document chunk record
                document_chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=file_id,
                    chunk_index=i,
                    content=chunk_content,
                    vector_id=chunk_id
                )
                db.session.add(document_chunk)
                chunk_ids.append(chunk_id)
        
        # Commit the chunks to the database
        db.session.commit()
        
        logger.debug(f"File processed for RAG: {filename} (ID: {file_id}, Chunks: {len(chunks)})")
        return chunk_ids
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing file for RAG: {str(e)}", exc_info=True)
        return []
