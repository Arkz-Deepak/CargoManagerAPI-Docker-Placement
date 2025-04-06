from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta

app = FastAPI()

# In-memory storage
zones = {
    "Crew_Quarters": [],
    "Storage_Bay": [],
    "Airlock": [],
    "Medical_Bay": [],
    "Engineering_Bay": [],
    "Lab": [],
    "Cockpit": [],
    "Command_Center": [],
    "Power_Bay": [],
    "External_Storage": [],
    "Life_Support": [],
    "Greenhouse": [],
    "Sanitation_Bay": [],
    "Engine_Bay": [],
    "Maintenance_Bay": []
}
logs = []

# Sample item placement zones
expanded_items_dict = {
    "Food Packet": ["Crew_Quarters", "Storage_Bay"],
    "Oxygen Cylinder": ["Airlock", "Crew_Quarters", "Medical_Bay"],
    "First Aid Kit": ["Medical_Bay", "Crew_Quarters"],
    "Water Bottle": ["Crew_Quarters", "Storage_Bay"]
}

class Item(BaseModel):
    name: str
    quantity: int
    priority: Optional[int] = 1
    expiry_days: Optional[int] = 30

@app.post("/api/placement")
def place_item(item: Item):
    if item.name not in expanded_items_dict:
        raise HTTPException(status_code=404, detail="Item not recognized")

    target_zone = expanded_items_dict[item.name][0]
    expiry_date = datetime.now() + timedelta(days=item.expiry_days)
    item_entry = {
        "name": item.name,
        "quantity": item.quantity,
        "priority": item.priority,
        "expiry": expiry_date.isoformat()
    }
    zones[target_zone].append(item_entry)
    logs.append(f"Placed {item.quantity}x {item.name} to {target_zone}")
    return {"message": f"Item placed in {target_zone}"}

@app.get("/api/retrieve")
def retrieve_items(name: Optional[str] = None):
    result = []
    for zone, items in zones.items():
        for item in items:
            if name is None or item["name"] == name:
                result.append({"zone": zone, **item})
    return result

@app.get("/api/search")
def search_items(name: str):
    return retrieve_items(name)

@app.post("/api/place")
def place_alias(item: Item):
    return place_item(item)

@app.post("/api/simulate/day")
def simulate_day(days: int):
    expired = []
    sim_time = datetime.now() + timedelta(days=days)
    for zone, items in zones.items():
        still_valid = []
        for item in items:
            if datetime.fromisoformat(item["expiry"]) < sim_time:
                expired.append({"zone": zone, "item": item})
            else:
                still_valid.append(item)
        zones[zone] = still_valid
    logs.append(f"Simulated time forward by {days} days")
    return {"expired": expired}

@app.post("/api/waste/identify")
def waste_identify():
    expired = []
    now = datetime.now()
    for zone, items in zones.items():
        for item in items:
            if datetime.fromisoformat(item["expiry"]) < now:
                expired.append({"zone": zone, "item": item})
    return {"expired": expired}

@app.post("/api/waste/return-plan")
def waste_return_plan():
    return {"message": "All expired items to be moved to Sanitation_Bay"}

@app.post("/api/waste/complete-undocking")
def complete_undocking():
    count = 0
    for zone, items in zones.items():
        zones[zone] = [item for item in items if datetime.fromisoformat(item["expiry"]) > datetime.now()]
        count += len(zones[zone])
    logs.append("Completed undocking of expired items")
    return {"message": f"{count} valid items retained"}

@app.post("/api/import/items")
def import_items(items: List[Item]):
    result = []
    for item in items:
        result.append(place_item(item))
    return result

@app.post("/api/import/containers")
def import_containers(data: Dict[str, List[Item]]):
    result = []
    for zone, items in data.items():
        for item in items:
            item_data = Item(**item.dict())
            zones[zone].append(item_data.dict())
            result.append(f"Placed {item.name} in {zone}")
    return {"message": result}

@app.get("/api/export/arrangement")
def export_arrangement():
    return zones

@app.get("/api/logs")
def get_logs():
    return {"logs": logs}

@app.get("/")
def root():
    return {"message": "Cargo Manager API Ready"}