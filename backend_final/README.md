### Frontend Integration Guide: DLSU Eatery Pathfinder  
**Backend Base URL:** `http://localhost:5000`  

---

### **1. Main Dashboard Screen**  
*Central hub for all functionalities*  

**UI Elements:**  
1. **Campus Map**  
   - Display nodes (buildings) and edges (paths) using coordinates from `/graph`   
2. **Action Panel:**  
   - "Find Path" button → Opens Pathfinder Screen  
   - "Compare Algorithms" button → Opens Comparison Screen  
   - "Top Eateries" button → Opens Ranking Screen  
   - "Manage Graph" button → Opens Graph Management  
   - "Manage Eateries" button → Opens Eatery Management  

**Backend Integration:**  
- **On Load:**  
  ```javascript
  // Fetch initial data
  GET /graph → Render map
  GET /eateries → Mark eateries on map
  ```

---

### **2. Pathfinder Screen**  
*Find routes to optimal eatery*  

**UI Elements:**  
1. **Start Location Selector**  
   - Dropdown populated with node IDs from `/graph`  
2. **Preference Value Field/Slider** (1-10 priority, 10 - highest):  
   - Rating, Price, Distance, Power Outlet, Halal Certified, WiFi, Aircon  
3. **Algorithm Selector:**  
   - "UCS" or "A*" buttons  
4. **Action Button:**  
   - "Find Optimal Path"  
5. **Results Display:**  
   - Path visualization on map  
   - Metrics panel:  
     ```json
     {
       "cost": "Total path cost",
       "execution_time_ms": "Algorithm runtime",
       "nodes_expanded": "Search efficiency"
     }
     ```
   - Eatery details card  

**Backend Integration:**  
```javascript
POST /find-path  
Request Body: {
  "start": "DLSU_Main_Gate",
  "algorithm": "astar",
  "preferences": {
    "rating": 8, 
    "price": 3,
    "halal_certified": 10
  }
}

Response: {
  "path": ["DLSU_Main_Gate", "Andrew_Building", "Henry_Sy_Bldg"],
  "eatery_info": { /* Detailed eatery data */ },
  "metrics": { /* Performance stats */ }
}
```

Sample Request Body:
```
{
  "start": "The value from the start-location-dropdown",
  "algorithm": "astar", // Default to A*, can be made selectable
  "preferences": { // Optional: include if the user saved preferences
    "rating": 1,
    "price": 2
    // ... other ranks
  }
}
```

Success Response:
```
{
  "start": "Andrew_Building",
  "goal": "KFC_DLSU",
  "goal_score": 0.85,
  "path": ["Andrew_Building", "Henry_Sy_Bldg", "KFC_DLSU"],
  "cost": 180.0,
  "algorithm": "astar",
  "eatery_info": {
    "name": "KFC DLSU", "rating": 4.0, "price": 2, ...
  },
  "weights_used": {"rating": 0.25, ...},
  "open_status": "Open",
  "distance": 150.5,
  "metrics": {
    "execution_time_ms": 2.5,
    "nodes_expanded": 5,
    "max_frontier_size": 4
  }
}
```

---

### **3. Algorithm Comparison Screen**  
*Side-by-side UCS vs A* analysis*  

**UI Elements:**  
1. **Configuration Panel**  
   - Start location selector  
   - Preference value field/sliders (same as Pathfinder)  
2. **Visualization Area:**  
   - Dual map view with color-coded paths.
3. **Comparison Table Sample:**  
   | Metric        | UCS  | A*   |  
   |---------------|------|------|  
   | Path Cost     | 210m | 175m |  
   | Compute Time  | 38ms | 24ms |  
   | Nodes Visited | 56   | 42   |  

**Backend Integration:**  
```javascript
POST /compare-algorithms  
Request Body: {
  "start": "Andrew_Building",
  "preferences": { /* Optional */ }
}

Response: {
  "ucs": { "path": [...], "metrics": {...} },
  "astar": { "path": [...], "metrics": {...} }
}
```

---

### **4. Top Eateries Screen**  
*Rank eateries by weighted preferences*  

**UI Elements:**  
1. **Preference Configuration:**  
   - Same sliders as Pathfinder  
   - "Number of Results" selector (1-10) - ex. if 3 then show top 3 max num of eateries
2. **Results Grid:**  
   | Rank | Eatery     | Score | Distance | Status |  
   |------|------------|-------|----------|--------|  
   | 1    | Study Cafe | 0.92  | 85m      | Open   |  
3. **Detail Panel:**  
   - Shows full attributes when row is selected  

**Backend Integration:**  
```javascript
POST /top-eateries  
Request Body: {
  "start": "Henry_Sy_Bldg",
  "top_n": 5,
  "preferences": { /* Optional */ }
}

Response: [
  {
    "id": "Study_Cafe",
    "rank": 1,
    "score": 0.92,
    "distance_meters": 85.3,
    "open_status": "Open",
    /* Full eatery attributes */
  }
]
```

---

### **5. Graph Management Screen**  
*Admin interface for modifying campus graph*  

**UI Elements:**  
1. **Node Operations:**  
   - Add Regular Node: ID + Latitude/Longitude inputs  
   - Add Eatery Node: Opens Eatery Creation Form  
   - Remove Node: Dropdown selector  
2. **Edge Operations:**  
   - Add Edge: Two node dropdowns (including eateries) + cost input  
   - Remove Edge: Two node dropdowns  
3. **Show Graph**  

**Backend Integration:**  
- **Add Regular Node:**  
  ```javascript
  POST /graph/nodes
  { "id": "Library", "lat": 14.566, "lng": 120.996 }
  ```  
- **Add Eatery Node:**  
  ```javascript
  POST /graph/eatery-nodes
  {
    "id": "New_Cafe",
    "lat": 14.5655,
    "lng": 120.9955,
    "attributes": { /* 8 required attributes */ }
  }
  ```  
- **Add Edge:**  
  ```javascript
  POST /graph/edges
  { "node_a": "Library", "node_b": "Andrew_Building", "cost": 30.0 }
  ```  
- **Remove Node:**  
  ```javascript
  DELETE /graph/nodes/Library
  ```
- **Remove Edge:**  
  ```javascript
DELETE /graph/edges
{
  "node_a": "Andrew_Building",
  "node_b": "Library"
}
  ```

---

### **6. Eatery Management Screen**  
*Update eatery attributes/hours*  

**UI Elements:**  
1. **Eatery Selector**  
   - Dropdown with existing eatery IDs/name  
2. **Attribute Editor:**  
   - Form fields matching required attributes:  
     - Text: Name, Hours, Address  
     - Number: Rating (0-5), Price (1-3)  
     - Toggles: Power Outlet, Halal, WiFi, Aircon  
3. **Eatery Operations**  
   - Add New Eatery, Remove Eatery

**Backend Integration:**  
- **Update Attributes:**  
  ```javascript
  PUT /eateries/Starbucks_DLSU
  { "attributes": { "wifi": 0, "hours": "7:00-22:00" } }
  ```  
- **Delete Eatery:**  
  ```javascript
  DELETE /eateries/Bacsilog_King
  ```  
- **Add New Eatery:**  
  *(Use Graph Management Screen)*  

---

### **7. Eatery Creation Form**  
*Specialized form for new eateries (use Graph Management Screen)*  

**Required Fields:**  
1. Node Basics:  
   - ID (text), Latitude (number), Longitude (number)  
2. Core Attributes:  
   - Name (text)  
   - Rating (0.0-5.0 slider)  
   - Price Level (1-3 selector)  
   - Hours (text: "HH:MM-HH:MM" or "24/7")  
3. Amenities (toggles):  
   - Power Outlet, Halal Certified, WiFi, Aircon  

**Backend Integration:**  
```javascript
POST /graph/eatery-nodes
{
  "id": "New_Eatery",
  "lat": 14.5650,
  "lng": 120.9970,
  "attributes": {
    "name": "Test Eatery",
    "rating": 4.0,
    "price": 2,
    "hours": "9:00-18:00",
    "power_outlet": 1,
    "halal_certified": 0,
    "wifi": 1,
    "aircon": 1,
    "address": "Test Location"  // Optional
  }
}
```

---

### **Note:**  

**a. Data Formats:**  
- Coordinates: `[latitude, longitude]`  
- Hours: `"9:00-21:00"` or `"24/7"`  
- Booleans: `1`/`0` or `true`/`false`  


**b. Error Handling:**  
- Standard response: `{ "error": "Descriptive message" }`  
- Status codes:  
  - 200: Success  
  - 400: Invalid request  
  - 404: Resource not found  
  - 500: Server error  
  ```
