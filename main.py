from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
import os

app = FastAPI()

# MongoDB connection details
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "testdb")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "items")

client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]
collection = database[COLLECTION_NAME]


class Item(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    price: float = Field(..., gt=0)


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    item_dict = item.dict()
    await collection.insert_one(item_dict)
    return item


@app.get("/items/", response_model=List[Item])
async def read_items():
    items = await collection.find().to_list(1000)
    return items


@app.get("/items/{name}", response_model=Item)
async def read_item(name: str):
    item = await collection.find_one({"name": name})
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{name}", response_model=Item)
async def update_item(name: str, item: Item):
    await collection.update_one({"name": name}, {"$set": item.dict()})
    updated_item = await collection.find_one({"name": name})
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@app.delete("/items/{name}", response_model=dict)
async def delete_item(name: str):
    delete_result = await collection.delete_one({"name": name})
    if delete_result.deleted_count == 1:
        return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
