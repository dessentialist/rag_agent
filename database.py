import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)