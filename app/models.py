from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
import datetime

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)