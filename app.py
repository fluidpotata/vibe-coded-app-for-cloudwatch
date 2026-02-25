import sqlite3
import random
import time
import threading
import os
import json
from flask import Flask, render_template, jsonify

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'state.db')

def init_db():
    """Build the state database if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value REAL
            )
        ''')
        conn.execute('''
            INSERT OR IGNORE INTO system_state (key, value)
            VALUES ('base_price', 94.0)
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print("Database initialized.")

def get_base_price():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT value FROM system_state WHERE key = ?', ('base_price',))
        row = cursor.fetchone()
        return row[0] if row else 94.0

def update_base_price(new_price):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('UPDATE system_state SET value = ? WHERE key = ?', (new_price, 'base_price'))
        conn.execute('INSERT INTO price_history (price) VALUES (?)', (new_price,))

def get_price_history(limit=50):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT price, timestamp FROM price_history ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        # Return in chronological order for the chart
        return [{"price": r[0], "time": r[1]} for r in reversed(rows)]

init_db()

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
