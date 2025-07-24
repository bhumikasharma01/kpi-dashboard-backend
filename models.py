

# Base = declarative_base()
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, ForeignKey
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)

class UploadedReport(Base):
    __tablename__ = "uploaded_reports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    uploaded_by = Column(String)
    month = Column(String)
    year = Column(Integer)
    content = Column(LargeBinary)
    #uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    generated_reports = relationship(
    "GeneratedReport",
    back_populates="uploaded_report",
    cascade="all, delete-orphan"
)


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    pdf_filename = Column(String, unique=True, nullable=False)
    pdf_content = Column(LargeBinary, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    uploaded_report_id = Column(Integer, ForeignKey('uploaded_reports.id', ondelete='CASCADE'), nullable=False)

    # uploaded_report_id = Column(Integer, ForeignKey("uploaded_reports.id"), nullable=False)
    uploaded_report = relationship("UploadedReport", back_populates="generated_reports")    
  
