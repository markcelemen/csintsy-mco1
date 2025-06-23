# DLSU Eatery Pathfinder - Backend Documentation
**MCO1: State-Based Pathfinding System**

## Project Overview
This hcuchcugss uses intelligent pathfinding algorithms to help users find optimal routes to eateries around De La Salle University (DLSU). The system uses graph-based search algorithms (UCS and A*) combined with multi-criteria scoring to recommend the best dining options based on user preferences.

## Features
- **Pathfinding Algorithms**: UCS (Uniform Cost Search) and A* with Haversine heuristic
- **Dynamic Graph Management**: Add/remove nodes and edges in real-time
- **Multi-Criteria Scoring**: Rating, price, distance, amenities (WiFi, AC, power outlets, Halal options)
- **Preference Weighting**: User-customizable preference rankings
- **Performance Monitoring**: Memory usage and execution time tracking
- **Flask-based API**: For frontend integration

## System Requirements
- Python 3.7+
- Flask 2.3.2
- Flask-CORS 3.0.10

## Installation & Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure data files exist:
   - `graph.json` - Graph structure with nodes and edges
   - `eateries.json` - Eatery attributes and information

3. Run the server:
   ```bash
   python app.py
   ```

4. Server will start on `http://0.0.0.0:5000`

## API Endpoints

### Core Pathfinding
- `POST /find-path` - Find optimal path to best eatery
- `POST /top-eateries` - Get ranked list of eateries
- `POST /compare-algorithms` - Compare UCS vs A* performance

### Data Retrieval
- `GET /graph` - Get current graph structure
- `GET /eateries` - Get all eatery information

### Dynamic Management
- `POST /graph/nodes` - Add new node
- `POST /graph/edges` - Add new edge
- `DELETE /graph/edges` - Remove edge
- `DELETE /graph/nodes/<id>` - Remove node
- `PUT /eateries/<id>` - Update eatery attributes
- `DELETE /eateries/<id>` - Remove eatery

## Algorithm Implementation

### UCS (Uniform Cost Search)
- **Guarantee**: Finds optimal solution
- **Strategy**: Always expands lowest-cost node first

### A* Search
- **Guarantee**: Optimal with admissible heuristic
- **Strategy**: Uses Haversine distance as heuristic function - pede den sana euclidean kaso mas applicable toh pag longi & lati

## Scoring System
Eateries are scored using weighted combination of factors:
- **Rating** (0-5): Restaurant quality score
- **Price** (0-4): Cost level (lower is better)
- **Distance**: Haversine distance from start point (lower is better) - since lati & longi gagamitin
- **Power Outlets** (0/1): Availability of charging points
- **Halal Certified** (0/1): Halal certified foods availability (idk if add pa nung mga vegan etc, dami kasi)
- **WiFi** (0/1): Internet connectivity
- **Air Conditioning** (0/1): if gusto malamig

## Data Structures

### Graph Format (graph.json)
```json
{
  "nodes": {
    "NodeID": [latitude, longitude],
    ...
  },
  "edges": {
    "NodeID": {
      "NeighborID": cost,
      ...
    },
    ...
  }
}
```

### Eatery Attributes (eateries.json)
```json
{
  "EateryID": {
    "name": "Display Name",
    "rating": 4.5,
    "price": 2,
    "power_outlet": 1,
    "halal_certified": 1,
    "wifi": 1,
    "aircon": 1,
    "hours": "9:00-21:00",
    "address": "Full Address"
  },
  ...
}
```

## Usage Examples

### Find Optimal Path
```bash
curl -X POST http://localhost:5000/find-path \
  -H "Content-Type: application/json" \
  -d '{
    "start": "DLSU_Main_Gate",
    "algorithm": "astar",
    "preferences": {
      "distance": 1,
      "rating": 2,
      "price": 3
    }
  }'
```

### Get Top Eateries
```bash
curl -X POST http://localhost:5000/top-eateries \
  -H "Content-Type: application/json" \
  -d '{
    "start": "DLSU_Main_Gate",
    "top_n": 5,
    "preferences": {
      "rating": 1,
      "wifi": 2
    }
  }'
```

## Performance Monitoring
Each pathfinding request includes metrics:
- **Execution Time**: Algorithm runtime in milliseconds
- **Nodes Expanded**: Number of nodes explored
- **Max Frontier Size**: Peak memory usage of search frontier
- **Peak Memory**: Maximum memory consumption in KB

## Project Structure
```
backend/
├── app.py              # Flask API server
├── backend.py          # Core algorithms and logic
├── graph.json          # Graph structure data
├── eateries.json       # Eatery attributes data
├── requirements.txt    # Python dependencies
└── README.md          # This documentation
```

SAMPLE RESULTS (TIG COPY KO LANG i2 sa terminalz)
C:\Users\Arron\Documents\backend>curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{ \"start\": \"DLSU_Main_Gate\", \"algorithm\": \"astar\", \"preferences\": { \"distance\": 1, \"rating\": 2, \"price\": 3 } }"
{
  "algorithm": "astar",
  "cost": 85.0,
  "distance": 116.06568854311674,
  "eatery_info": {
    "address": "Andrew Building, DLSU",
    "aircon": 1,
    "halal_certified": 1,
    "hours": "7:00-19:00",
    "name": "Andrew Cafe",
    "power_outlet": 1,
    "price": 2,
    "rating": 4.2,
    "wifi": 1
  },
  "goal": "Andrew_Building",
  "goal_score": 0.7262,
  "metrics": {
    "execution_time": 28.86,
    "max_frontier_size": 3,
    "nodes_expanded": 2,
    "peak_memory_kb": 1.05
  },
  "open_status": "Open",
  "path": [
    "DLSU_Main_Gate",
    "Andrew_Building"
  ],
  "start": "DLSU_Main_Gate",
  "weights_used": {
    "distance": 0.5,
    "price": 0.1667,
    "rating": 0.3333
  }
}

C:\Users\Arron\Documents\backend>curl -X POST http://localhost:5000/top-eateries -H "Content-Type: application/json" -d "{ \"start\": \"DLSU_Main_Gate\", \"top_n\": 5, \"preferences\": { \"rating\": 1, \"wifi\": 2 } }"
[
  {
    "address": "2450 Taft Ave, Malate, Manila",
    "aircon": 1,
    "distance_meters": 235.2,
    "halal_certified": 0,
    "hours": "8:00-22:00",
    "id": "Study_Cafe",
    "name": "The Study Cafe",
    "open_status": "Open",
    "power_outlet": 1,
    "price": 3,
    "rank": 1,
    "rating": 4.6,
    "score": 1.0,
    "wifi": 1
  },
  {
    "address": "2410 Taft Ave, Malate, Manila",
    "aircon": 1,
    "distance_meters": 562.4,
    "halal_certified": 0,
    "hours": "6:00-23:00",
    "id": "Starbucks_DLSU",
    "name": "Starbucks near DLSU",
    "open_status": "Open",
    "power_outlet": 1,
    "price": 3,
    "rank": 2,
    "rating": 4.5,
    "score": 0.9048,
    "wifi": 1
  },
  {
    "address": "Andrew Building, DLSU",
    "aircon": 1,
    "distance_meters": 116.1,
    "halal_certified": 1,
    "hours": "7:00-19:00",
    "id": "Andrew_Building",
    "name": "Andrew Cafe",
    "open_status": "Open",
    "power_outlet": 1,
    "price": 2,
    "rank": 3,
    "rating": 4.2,
    "score": 0.619,
    "wifi": 1
  },
  {
    "address": "2401 Taft Ave, Malate, Manila",
    "aircon": 1,
    "distance_meters": 464.0,
    "halal_certified": 1,
    "hours": "9:00-21:00",
    "id": "Chowking_DLSU",
    "name": "Chowking DLSU",
    "open_status": "Open",
    "power_outlet": 0,
    "price": 2,
    "rank": 4,
    "rating": 4.1,
    "score": 0.5238,
    "wifi": 1
  },
  {
    "address": "2420 Taft Ave, Malate, Manila",
    "aircon": 1,
    "distance_meters": 465.0,
    "halal_certified": 1,
    "hours": "24/7",
    "id": "McDonalds_DLSU",
    "name": "McDonald's DLSU",
    "open_status": "Open",
    "power_outlet": 0,
    "price": 1,
    "rank": 5,
    "rating": 4.0,
    "score": 0.4285,
    "wifi": 1
  }
]

C:\Users\Arron\Documents\backend>

C:\Users\Arron\Documents\backend>curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{ \"start\": \"DLSU_Main_Gate\", \"algorithm\": \"ucs\", \"preferences\": { \"distance\": 1, \"rating\": 2, \"price\": 3 } }"
{
  "algorithm": "ucs",
  "cost": 85.0,
  "distance": 116.06568854311674,
  "eatery_info": {
    "address": "Andrew Building, DLSU",
    "aircon": 1,
    "halal_certified": 1,
    "hours": "7:00-19:00",
    "name": "Andrew Cafe",
    "power_outlet": 1,
    "price": 2,
    "rating": 4.2,
    "wifi": 1
  },
  "goal": "Andrew_Building",
  "goal_score": 0.7262,
  "metrics": {
    "execution_time": 3.26,
    "max_frontier_size": 3,
    "nodes_expanded": 3,
    "peak_memory_kb": 0.94
  },
  "open_status": "Open",
  "path": [
    "DLSU_Main_Gate",
    "Andrew_Building"
  ],
  "start": "DLSU_Main_Gate",
  "weights_used": {
    "distance": 0.5,
    "price": 0.1667,
    "rating": 0.3333
  }
}

C:\Users\Arron\Documents\backend>
