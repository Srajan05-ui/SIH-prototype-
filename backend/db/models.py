from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from backend.db.database import Base

class AirfareRecord(Base):
    __tablename__ = "airfare_records"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True) # e.g. "GoogleFlights", "DGCA"
    route = Column(String, index=True)  # e.g. "BOM-DEL"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Financials
    base_fare = Column(Float, nullable=False)
    taxes = Column(Float, nullable=False)
    baggage_fee = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    
    # Audit Trail / Provenance
    ip_address = Column(String, nullable=True)
    collection_method = Column(String) # e.g. "curl_cffi", "scrapy"
