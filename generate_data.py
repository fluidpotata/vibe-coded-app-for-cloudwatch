import json
import random
import uuid

def generate_huge_data(count=1000):
    data = []
    for i in range(count):
        data.append({
            "id": str(uuid.uuid4()),
            "index": i,
            "name": f"Item {i}",
            "value": random.randint(100, 9999),
            "status": random.choice(["Active", "Pending", "Completed", "Failed"]),
            "timestamp": "2026-02-24T12:50:24Z",
            "metadata": {
                "category": random.choice(["Finance", "Health", "Tech", "Logistics"]),
                "priority": random.choice(["Low", "Medium", "High"]),
                "tags": ["live", "data", "stream"]
            },
            "description": "This is a sample description for a huge data entry to simulate real-world payloads."
        })
    return data

if __name__ == "__main__":
    huge_data = generate_huge_data()
    with open("data.json", "w") as f:
        json.dump(huge_data, f, indent=4)
    print("huge_data.json created with 1000 items.")
