# csintsy-mco1

This API finds the optimal path to the best eatery using two algorithms:
- Uniform Cost Search (UCS)
- A* Search (with dynamic user preferences)

----------------------------
SETUP INSTRUCTIONS
----------------------------

1. Install dependencies:
   pip install flask flask-cors

2. Run the backend:
   cd backend
   python app.py

3. The server will start at:
   http://localhost:5000

----------------------------
API USAGE
----------------------------

POST /api/path

Description:
    Computes the optimal path to an eatery based on a graph, metadata, and user preferences.

Request JSON Body:
```json
{
  "graph": {
    "A": { "B": 2, "C": 3 },
    "B": { "A": 2, "D": 2 },
    "C": { "A": 3, "D": 4 },
    "D": { "B": 2, "C": 4 }
  },
  "positions": {
    "A": [0, 0],
    "B": [1, 1],
    "C": [1, -1],
    "D": [2, 0]
  },
  "metadata": {
    "B": { "price": 50, "quality": 4.5, "reviews": 80 },
    "C": { "price": 40, "quality": 4.0, "reviews": 60 },
    "D": { "price": 60, "quality": 4.2, "reviews": 75 }
  },
  "start": "A",
  "goals": ["B", "C", "D"],
  "user_type": "foodie"
}
```
User Types:
- foodie
- budget_conscious
- in_a_hurry
- balanced
- luxury_seeker

Response Format:
```json
{
  "ucs": {
    "path": ["A", "B"],
    "cost": 2
  },
  "astar": {
    "path": ["A", "C"],
    "cost": 3.25
  }
}
```