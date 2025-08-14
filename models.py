from datetime import datetime
import json
from database import db
from sqlalchemy.dialects.postgresql import JSON

class Document(db.Model):
    """Model to represent a document in the system"""
    __tablename__ = 'documents'
    
    id = db.Column(db.String(100), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_metadata = db.Column(JSON, default={})
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with chunks
    chunks = db.relationship('DocumentChunk', backref='document', lazy=True, cascade='all, delete-orphan')
    
    @property
    def size(self):
        return len(self.content)
    
    def to_dict(self):
        """Convert the document to a dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "metadata": self.file_metadata, # Return as 'metadata' for backward compatibility with frontend
            "created_at": self.created_at.isoformat(),
            "size": self.size
        }


class DocumentChunk(db.Model):
    """Model to represent a chunk of a document used for RAG"""
    __tablename__ = 'document_chunks'
    
    id = db.Column(db.String(100), primary_key=True)
    document_id = db.Column(db.String(100), db.ForeignKey('documents.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    vector_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Convert the document chunk to a dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "vector_id": self.vector_id,
            "created_at": self.created_at.isoformat()
        }


class Message(db.Model):
    """Model to represent a chat message"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(100), db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Convert the message to a dictionary"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


class Conversation(db.Model):
    """Model to represent a chat conversation"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(100), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship with messages
    messages = db.relationship('Message', backref='conversation', lazy=True, order_by="Message.timestamp", cascade='all, delete-orphan')
    
    def add_message(self, role, content):
        """Add a message to the conversation
        
        Args:
            role: The role of the message sender ('user' or 'assistant')
            content: The content of the message
            
        Returns:
            The created Message object
            
        Note:
            This method adds the message to the session but does not commit.
            The caller is responsible for committing the session.
        """
        message = Message(
            conversation_id=self.id,
            role=role,
            content=content
        )
        db.session.add(message)
        self.updated_at = datetime.now()
        return message
    
    def to_dict(self):
        """Convert the conversation to a dictionary"""
        return {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
