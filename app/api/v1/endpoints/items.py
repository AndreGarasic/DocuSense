"""
DocuSense - Items CRUD Endpoints
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.item import Item, ItemCreate, ItemUpdate

router = APIRouter()

# In-memory storage for demo purposes
items_db: dict[int, Item] = {}
item_counter = 0


@router.get("/", response_model=list[Item], tags=["Items"])
async def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
):
    """
    List all items with pagination.
    
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Maximum number of items to return (default: 10, max: 100)
    """
    items = list(items_db.values())
    return items[skip : skip + limit]


@router.get("/{item_id}", response_model=Item, tags=["Items"])
async def get_item(item_id: int):
    """
    Get a specific item by ID.
    
    - **item_id**: The unique identifier of the item
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@router.post("/", response_model=Item, status_code=201, tags=["Items"])
async def create_item(item: ItemCreate):
    """
    Create a new item.
    
    - **name**: Name of the item (required)
    - **description**: Optional description of the item
    - **price**: Price of the item (must be positive)
    - **is_active**: Whether the item is active (default: True)
    """
    global item_counter
    item_counter += 1
    
    new_item = Item(
        id=item_counter,
        name=item.name,
        description=item.description,
        price=item.price,
        is_active=item.is_active,
    )
    items_db[item_counter] = new_item
    return new_item


@router.put("/{item_id}", response_model=Item, tags=["Items"])
async def update_item(item_id: int, item: ItemUpdate):
    """
    Update an existing item.
    
    - **item_id**: The unique identifier of the item to update
    - **name**: New name for the item (optional)
    - **description**: New description for the item (optional)
    - **price**: New price for the item (optional)
    - **is_active**: New active status for the item (optional)
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    existing_item = items_db[item_id]
    update_data = item.model_dump(exclude_unset=True)
    
    updated_item = existing_item.model_copy(update=update_data)
    items_db[item_id] = updated_item
    return updated_item


@router.delete("/{item_id}", status_code=204, tags=["Items"])
async def delete_item(item_id: int):
    """
    Delete an item.
    
    - **item_id**: The unique identifier of the item to delete
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del items_db[item_id]
    return None
