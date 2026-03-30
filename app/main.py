from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from . import crud, models, schemas, services
from .database import engine, get_db

# Create tables on startup if they do not exist.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Unified Customer Activity Service", version="1.0.0")


@app.get("/")
# `-> dict[str, str]` shows this function returns a dictionary of strings.
def root() -> dict[str, str]:
    return {"message": "Unified Customer Activity Service is running"}


@app.post("/sync", response_model=schemas.SyncSummary)
def sync_data(db: Session = Depends(get_db)):
    return services.sync_data(db)


@app.get("/customers", response_model=list[schemas.CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return crud.get_customers(db)


@app.get("/customers/{customer_id}/activities", response_model=list[schemas.ActivityOut])
def list_customer_activities(customer_id: int, db: Session = Depends(get_db)):
    customer = crud.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return crud.get_activities_by_customer_id(db, customer_id)


@app.get("/activities", response_model=list[schemas.ActivityOut])
def list_activities(
    source: str | None = Query(default=None),
    activity_type: str | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
):
    return crud.get_activities(db, source=source, activity_type=activity_type)