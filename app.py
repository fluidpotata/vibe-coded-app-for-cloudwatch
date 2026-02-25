import redis
import random
import time
import threading
import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Initialize base price if it doesn't exist
if not redis_client.exists('base_price'):
    redis_client.set('base_price', 94.0)

def get_base_price():
    value = redis_client.get('base_price')
    return float(value) if value is not None else 94.0

def update_base_price(new_price):
    redis_client.set('base_price', new_price)
    
    # Store price history as JSON
    entry = json.dumps({
        "price": new_price,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    redis_client.lpush('price_history', entry)
    # Keep only the last 10 entries
    redis_client.ltrim('price_history', 0, 9)

def get_price_history(limit=10):
    # Fetch from Redis
    items = redis_client.lrange('price_history', 0, limit - 1)
    
    # Parse JSON
    history = [json.loads(item) for item in items]
    
    # Return in chronological order
    return list(reversed(history))

# Global config for background updater
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')
NEXT_UPDATE_INTERVAL = random.randint(5, 10)
LAST_UPDATE_TIME = time.time()

def price_updater():
    """Background task to update price in DB every 5-10 seconds."""
    global NEXT_UPDATE_INTERVAL, LAST_UPDATE_TIME
    while True:
        time.sleep(1)
        if time.time() - LAST_UPDATE_TIME >= NEXT_UPDATE_INTERVAL:
            current_price = get_base_price()
            change = random.uniform(-3, 3)
            new_price = max(10, current_price + change)
            update_base_price(new_price)
            
            LAST_UPDATE_TIME = time.time()
            NEXT_UPDATE_INTERVAL = random.randint(5, 10)
            print(f"DEBUG: Persistent price updated to {new_price:.2f}")

# Start the background thread
threading.Thread(target=price_updater, daemon=True).start()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

@app.route('/')
def index():
    """Serve the main frontend page."""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """Serve data with stateful price."""
    data = load_data()
    base_price = get_base_price()
    
    # Calculate prices and format data
    for item in data:
        units = item.get('value', 0)
        item['price'] = round(units * base_price, 2)
    
    return jsonify({
        "data": data,
        "base_price": round(base_price, 2),
        "next_update_in": round(NEXT_UPDATE_INTERVAL - (time.time() - LAST_UPDATE_TIME), 1)
    })

@app.route('/api/history')
def get_history():
    """Serve price history for charts."""
    history = get_price_history()
    return jsonify(history)

if __name__ == '__main__':
    # Ensure templates and static directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, port=5000)
