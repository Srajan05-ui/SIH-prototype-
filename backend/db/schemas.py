from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AirfareCreate(BaseModel):
    source: str = Field(..., description="Source of truth (e.g. GoogleFlights, DGCA)")
    route: str = Field(..., description="Airport code route e.g. BOM-DEL")
    base_fare: float = Field(..., gt=0, description="Base ticket price must be > 0")
    taxes: float = Field(..., ge=0)
    baggage_fee: float = Field(default=0.0, ge=0)
    total_price: float = Field(..., gt=0)
    collection_method: str = Field(..., description="Scraping tool used")

class AirfareResponse(AirfareCreate):
    id: int
    timestamp: datetime
    
    class Config:
        orm_mode = True
