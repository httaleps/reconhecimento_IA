from sqlalchemy.orm import Session
from app import models
from datetime import datetime


def get_or_create_person(db: Session, name: str) -> models.Person:
    person = db.query(models.Person).filter(
        models.Person.name == name
    ).first()
    if not person:
        person = models.Person(name=name)
        db.add(person)
        db.commit()
        db.refresh(person)
    return person


def get_person(db: Session, person_id: int) -> models.Person:
    return db.query(models.Person).filter(models.Person.id == person_id).first()


def get_all_persons(db: Session):
    return db.query(models.Person).all()


def delete_person(db: Session, person_id: int):
    person = get_person(db, person_id)
    if person:
        db.delete(person)
        db.commit()


def create_photo(db: Session, person_id: int, filepath: str, filename: str) -> models.Photo:
    photo = models.Photo(
        person_id=person_id,
        filepath=filepath,
        filename=filename
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def create_recognition_log(
    db: Session,
    person_name: str,
    confidence: float,
    recognized: bool,
    person_id: int = None
) -> models.RecognitionLog:
    log = models.RecognitionLog(
        person_id=person_id,
        person_name=person_name,
        confidence=confidence,
        recognized=recognized,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_recognition_logs(db: Session, limit: int = 100):
    return db.query(models.RecognitionLog)\
        .order_by(models.RecognitionLog.timestamp.desc())\
        .limit(limit)\
        .all()
