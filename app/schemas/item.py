"""
DocuSense - Item Schemas
"""
from typing import Optional

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """Base schema for Item."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Name of the item")
    description: Optional[str] = Field(None, max_length=500, description="Description of the item")
    price: float = Field(..., gt=0, description="Price of the item (must be positive)")
    is_active: bool = Field(True, description="Whether the item is active")


class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an existing item."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the item")
    description: Optional[str] = Field(None, max_length=500, description="Description of the item")
    price: Optional[float] = Field(None, gt=0, description="Price of the item (must be positive)")
    is_active: Optional[bool] = Field(None, description="Whether the item is active")


class Item(ItemBase):
    """Schema for item response."""
    
    id: int = Field(..., description="Unique identifier of the item")

    model_config = {"from_attributes": True}
