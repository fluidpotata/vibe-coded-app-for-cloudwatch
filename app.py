import redis
import random
import time
import threading
import os
import json
import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger
from flask import Flask, render_template, jsonify

# --- LOGGING SETUP ---
log_dir = '/var/log/flaskapp'
os.makedirs(log_dir, exist_ok=True) # Ensure dir exists if running locally

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logHandler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

app = Flask(__name__)

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Graceful initialization
try:
    if not redis_client.exists('base_price'):
        redis_client.set('base_price', 94.0)
    logger.info("Successfully connected to Redis and initialized state.")
except redis.ConnectionError:
    logger.error("Failed to connect to Redis on startup. Ensure Redis is running.")

def get_base_price():
    try:
        value = redis_client.get('base_price')
        return float(value) if value is not None else 94.0
    except redis.ConnectionError:
        logger.error("Redis connection error during get_base_price.")
        return 94.0 # Fallback

def update_base_price(new_price):
    try:
        redis_client.set('base_price', new_price)
        
        # Store price history as JSON
        entry = json.dumps({
            "price": new_price,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        redis_client.lpush('price_history', entry)
        # Keep only the last 10 entries
        redis_client.ltrim('price_history', 0, 9)
    except redis.ConnectionError:
        logger.error("Redis connection error during update_base_price.")

def get_price_history(limit=10):
    try:
        items = redis_client.lrange('price_history', 0, limit - 1)
        history = [json.loads(item) for item in items]
        return list(reversed(history))
    except redis.ConnectionError:
        logger.error("Redis connection error during get_price_history.")
        return []

# Global config for background updater
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')
NEXT_UPDATE_INTERVAL = random.randint(5, 10)
LAST_UPDATE_TIME = time.time()

def price_updater():
    """Background task to update price in DB every 5-10 seconds."""
    global NEXT_UPDATE_INTERVAL, LAST_UPDATE_TIME
    
    # Small delay to ensure Redis is fully up before thread starts hitting it
    time.sleep(2) 
    
    while True:
        time.sleep(1)
        if time.time() - LAST_UPDATE_TIME >= NEXT_UPDATE_INTERVAL:
            current_price = get_base_price()
            change = random.uniform(-3, 3)
            new_price = max(10, current_price + change)
            
            update_base_price(new_price)
            
            LAST_UPDATE_TIME = time.time()
            NEXT_UPDATE_INTERVAL = random.randint(5, 10)
            
            # --- STRUCTURED LOGGING ---
            if new_price < 50:
                logger.warning("CRITICAL_PRICE_DROP", extra={"current_price": round(new_price, 2)})
            else:
                logger.info("Persistent price updated", extra={"current_price": round(new_price, 2)})

# Start the background thread
threading.Thread(target=price_updater, daemon=True).start()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    data = load_data()
    base_price = get_base_price()
    
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
    history = get_price_history()
    return jsonify(history)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    app.run(debug=True, port=5000)