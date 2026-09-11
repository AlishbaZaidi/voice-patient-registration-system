import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Patient
from schemas import PatientCreate, PatientUpdate, PatientOut

# Logging setup — satisfies the "log agent conversations / final
# data payload to stdout" observability requirement
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("patient-api")

# Creates the table on startup if it doesn't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Patient Registration API")


def envelope(data=None, error=None):
    """Wraps every response in the required { data, error } shape."""
    return {"data": data, "error": error}


@app.get("/patients")
def list_patients(
    last_name: Optional[str] = Query(None),
    date_of_birth: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Patient).filter(Patient.deleted_at.is_(None))  # exclude soft-deleted

    if last_name:
        query = query.filter(Patient.last_name.ilike(last_name))
    if date_of_birth:
        query = query.filter(Patient.date_of_birth == date_of_birth)
    if phone_number:
        query = query.filter(Patient.phone_number == phone_number)

    patients = query.all()
    return envelope(data=[PatientOut.model_validate(p).model_dump(mode="json") for p in patients])


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id, Patient.deleted_at.is_(None)
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=envelope(error="Patient not found"))

    return envelope(data=PatientOut.model_validate(patient).model_dump(mode="json"))


@app.post("/patients", status_code=201)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    try:
        patient = Patient(patient_id=str(uuid4()), **patient_in.model_dump())
        db.add(patient)
        db.commit()
        db.refresh(patient)

        logger.info(f"New patient registered: {patient.first_name} {patient.last_name} "
                    f"(id={patient.patient_id}, phone={patient.phone_number})")

        return envelope(data=PatientOut.model_validate(patient).model_dump(mode="json"))

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create patient: {e}")
        raise HTTPException(status_code=500, detail=envelope(error=f"Could not save patient: {e}"))


@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, patient_in: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id, Patient.deleted_at.is_(None)
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=envelope(error="Patient not found"))

    update_data = patient_in.model_dump(exclude_unset=True)  # only fields actually sent
    for field, value in update_data.items():
        setattr(patient, field, value)

    try:
        db.commit()
        db.refresh(patient)
        logger.info(f"Patient updated: {patient.patient_id}")
        return envelope(data=PatientOut.model_validate(patient).model_dump(mode="json"))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=envelope(error=f"Update failed: {e}"))


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id, Patient.deleted_at.is_(None)
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=envelope(error="Patient not found"))

    patient.deleted_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Patient soft-deleted: {patient_id}")
    return envelope(data={"patient_id": patient_id, "deleted": True})


@app.get("/")
def root():
    return envelope(data={"message": "Patient Registration API is running. See /docs."})