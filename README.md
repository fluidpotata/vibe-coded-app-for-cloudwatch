# NexusCore V2.4 - Real-Time Data & Analytics Dashboard

NexusCore is a high-performance Flask application designed to serve and visualize massive datasets in real-time. It features a stateful backend with SQLite, background price calculation, and a premium frontend with live charting and multi-column filtering.

## 🚀 Key Features
- **Real-time Background Sync**: Refreshes data and market price every 5 seconds without page reloads.
- **Stateful Persistence**: Uses SQLite to maintain price history and global state across restarts.
- **Advanced Visualization**: Integrated Chart.js for price trend analysis and dynamic progress bars for sync timing.
- **High-Performance Filtering**: Multi-column selectors (Category, Priority, Status) and global search for navigating large JSON payloads.
- **Premium Aesthetics**: Dark-themed UI with glassmorphism, 3D CSS animations, and responsive layouts.

## 📂 Project Structure
```
project/
├── app.py              # Main Flask server & Background tasks
├── generate_data.py    # Utility script to generate huge data JSON
├── data.json           # The "Huge" dataset (generated)
├── state.db            # SQLite database (auto-created)
├── templates/
│   └── index.html      # Dashboard frontend template
└── static/
    ├── css/
    │   └── style.css   # Premium styling & animations
    └── js/
        └── main.js     # Real-time logic & Chart.js integration
```

## 🛠️ Step-by-Step Setup

### 1. Environment Setup
Ensure you have Python installed. Install the only required dependency:
```bash
pip install flask
```

### 2. Generate the Dataset
Create the `generate_data.py` file and run it to create `data.json` with 1000 records.
```bash
python generate_data.py
```

### 3. Application Files
- **app.py**: Handles the API endpoints and the background thread that updates the market price in SQLite.
- **index.html**: Uses semantic HTML5 and includes Chart.js from CDN.
- **style.css**: Implements the dark theme and 3D cube animation.
- **main.js**: Manages the `fetch()` calls, countdown timer, and UI rendering.

### 4. Running the App
Execute the following command in your terminal:
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

## 📈 Technical Details
- **Backend Threading**: A Python `threading.Thread` runs a loop in the background, updating the `base_price` in the database every 5-10 seconds.
- **Data Augmentation**: The API reads `data.json` but calculates the "Market Price" column on-the-fly using the persistent `base_price` from the DB.
- **Frontend Performance**: The JavaScript `renderData()` function uses aggressive filtering and slices the display to the first 100 matches to ensure smooth scrolling even with thousands of potential matches.

---
*NexusCore V2.4 - Engineered for speed and visual excellence.*
