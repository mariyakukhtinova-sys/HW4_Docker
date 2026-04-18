from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="HW4 API")

items_db = {}

class Item(BaseModel):
    name: str
    description: str | None = None

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    item = items_db.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "item": item}

@app.post("/items/{item_id}")
def create_item(item_id: int, item: Item):
    items_db[item_id] = item.model_dump()
    return {"message": "Item saved", "item_id": item_id, "item": items_db[item_id]}
