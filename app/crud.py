from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models


def get_customer_by_id(db: Session, customer_id: int):
    return db.query(models.Customer).filter_by(id=customer_id).first()


def get_customer_by_external_id(db: Session, external_id: int, source: str):
    return db.query(models.Customer).filter_by(external_id=external_id, source=source).first()


def get_customers(db: Session):
    return db.query(models.Customer).order_by(models.Customer.id).all()


def create_customer(db: Session, customer_data: dict):
    customer = models.Customer(**customer_data)
    db.add(customer)

    try:
        db.commit()
        db.refresh(customer)
        return customer, True
    except IntegrityError:
        db.rollback()
        existing = get_customer_by_external_id(
            db,
            external_id=customer_data["external_id"],
            source=customer_data["source"],
        )
        return existing, False


def get_activity_by_external_id(db: Session, external_id: int, source: str):
    return db.query(models.Activity).filter_by(external_id=external_id, source=source).first()


def get_activities(db: Session, source: str | None = None, activity_type: str | None = None):
    query = db.query(models.Activity)

    if source:
        query = query.filter_by(source=source)
    if activity_type:
        query = query.filter_by(type=activity_type)

    return query.order_by(models.Activity.id).all()


def get_activities_by_customer_id(db: Session, customer_id: int):
    return db.query(models.Activity).filter_by(customer_id=customer_id).order_by(models.Activity.id).all()


def create_activity(db: Session, activity_data: dict):
    activity = models.Activity(**activity_data)
    db.add(activity)

    try:
        db.commit()
        db.refresh(activity)
        return activity, True
    except IntegrityError:
        db.rollback()
        existing = get_activity_by_external_id(
            db,
            external_id=activity_data["external_id"],
            source=activity_data["source"],
        )
        return existing, False