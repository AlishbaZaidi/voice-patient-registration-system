# Pydantic models define what shape requests/responses must be and
# validate them automatically.
import re
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC"
}

class SexEnum(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"
    decline = "Decline to Answer"

NAME_PATTERN = re.compile(r"^[A-Za-z'\-]{1,50}$")
PHONE_PATTERN = re.compile(r"^\d{10}$")
ZIP_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    sex: SexEnum
    phone_number: str
    email: Optional[EmailStr] = None

    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str

    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v):
        if not NAME_PATTERN.match(v):
            raise ValueError("Name must be 1-50 alphabetic characters, hyphens, or apostrophes only")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)  # strip spaces/dashes/parens before checking
        if not PHONE_PATTERN.match(digits):
            raise ValueError("Phone number must be a valid 10-digit US number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        v = v.upper()
        if v not in US_STATES:
            raise ValueError("State must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if not ZIP_PATTERN.match(v):
            raise ValueError("ZIP code must be 5 digits or ZIP+4 format")
        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[SexEnum] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientOut(PatientBase):
    patient_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  