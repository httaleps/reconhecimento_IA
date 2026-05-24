from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    photos = relationship("Photo", back_populates="person", cascade="all, delete")
    logs = relationship("RecognitionLog", back_populates="person")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    filepath = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="photos")


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    person_name = Column(String, default="Desconhecido")
    confidence = Column(Float, default=0.0)
    recognized = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="logs")
