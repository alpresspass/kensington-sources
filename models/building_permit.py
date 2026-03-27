"""
Building permit models for NYC DOB data.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class BuildingPermitItem(BaseModel):
    """
    A building permit issued in NYC.
    
    Based on NYC Open Data DOB Permit Issuance dataset:
    https://data.cityofnewyork.us/Housing-Development/DOB-Permit-Issuance/ipu4-2q9a
    """
    
    permit_number: str = Field(..., description="Unique permit identifier")
    job_type: str = Field(..., description="Type of work (AL=Alteration, NB=New Building, etc.)")
    building_class: Optional[str] = Field(None, description="Building class code")
    block: int = Field(..., description="Manhattan block number")
    lot: int = Field(..., description="Lot number within block")
    borough: str = Field(..., description="Borough (1=Manhattan, 2=Bronx, 3=Queens, 4=Brooklyn, 5=Staten Island)")
    house_number: Optional[str] = Field(None, description="Street number")
    street_name: Optional[str] = Field(None, description="Street name")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    work_type: Optional[str] = Field(None, description="Type of work being performed")
    permit_issued_date: date = Field(..., description="Date permit was issued")
    expiration_date: Optional[date] = Field(None, description="Permit expiration date")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost of work")
    
    class Config:
        json_schema_extra = {
            "example": {
                "permit_number": "123456789",
                "job_type": "AL1",  # Alteration Type 1
                "building_class": "R2",
                "block": 1234,
                "lot": 56,
                "borough": 4,  # Brooklyn
                "house_number": "123",
                "street_name": "KENSINGTON AVENUE",
                "zip_code": "11218",
                "work_type": "ALTERATION",
                "permit_issued_date": date(2026, 3, 27),
                "expiration_date": date(2026, 9, 27),
                "estimated_cost": 50000.00
            }
        }
