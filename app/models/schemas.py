from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class BlockSearchRequest(BaseModel):
    block_id: Optional[str] = None
    block_name: Optional[str] = None
    
    @validator('block_id')
    def validate_block_id(cls, v):
        if v and not v.isdigit():
            raise ValueError('Block ID must contain only digits')
        return v
    
    @validator('block_name')
    def validate_block_name(cls, v):
        if v and len(v) > 100:
            raise ValueError('Block name too long')
        return v

class BoreholeData(BaseModel):
    name: str
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    length: Optional[float] = None
    diameter: Optional[float] = None
    angle: Optional[float] = None
    azimuth: Optional[float] = None

class BlockInfoResponse(BaseModel):
    block_id: str
    block_name: str
    crush_energy: Optional[float] = None
    holes_space: Optional[float] = None
    rows_distance: Optional[float] = None
    rock_name: Optional[str] = None
    rock_rigidity: Optional[str] = None
    rock_density: Optional[float] = None