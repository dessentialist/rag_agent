from datetime import datetime

from sqlalchemy import JSON

from database import db


class Document(db.Model):
    """Model to represent a document in the system"""

    __tablename__ = "documents"

    id = db.Column(db.String(100), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_metadata = db.Column(JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with chunks
    chunks = db.relationship(
        "DocumentChunk", backref="document", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def size(self):
        return len(self.content)

    def to_dict(self):
        """Convert the document to a dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "metadata": self.file_metadata,  # Return as 'metadata' for backward compatibility with frontend
            "created_at": self.created_at.isoformat(),
            "size": self.size,
        }


class DocumentChunk(db.Model):
    """Model to represent a chunk of a document used for RAG"""

    __tablename__ = "document_chunks"

    id = db.Column(db.String(100), primary_key=True)
    document_id = db.Column(db.String(100), db.ForeignKey("documents.id"), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    vector_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert the document chunk to a dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "vector_id": self.vector_id,
            "created_at": self.created_at.isoformat(),
        }


class Message(db.Model):
    """Model to represent a chat message"""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(100), db.ForeignKey("conversations.id"), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert the message to a dictionary"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


class Conversation(db.Model):
    """Model to represent a chat conversation"""

    __tablename__ = "conversations"

    id = db.Column(db.String(100), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with messages
    messages = db.relationship(
        "Message",
        backref="conversation",
        lazy=True,
        order_by="Message.timestamp",
        cascade="all, delete-orphan",
    )

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
        message = Message(conversation_id=self.id, role=role, content=content)
        db.session.add(message)
        self.updated_at = datetime.now()
        return message

    def to_dict(self):
        """Convert the conversation to a dictionary"""
        return {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Setting(db.Model):
    """Key-value settings storage

    Stores application configuration as JSON values under a unique string key.
    Examples:
      key: "general", value: {"brand_name": "RAG Agent", "logo_url": null}
      key: "theme", value: {"primary": "#7aa2f7", ...}
    """

    __tablename__ = "settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(JSON, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Agent(db.Model):
    """Multi-agent configuration stored in DB.

    Agents are selected at runtime via selection rules evaluated against
    retrieved documents and/or the user query.
    """

    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    role_system_prompt = db.Column(db.Text, nullable=False)
    llm_model = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    max_tokens = db.Column(db.Integer, nullable=False)
    response_format = db.Column(db.String(50), nullable=True)  # e.g., "json_object" or "text"
    selection_rules = db.Column(JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
