# DLSU Eatery Pathfinder 🏫🍽️

A campus-based pathfinding and recommendation system designed to help Lasallian students quickly locate the best routes and nearby eateries around 
De La Salle University. This project combines advanced search algorithms with a user-friendly web interface to deliver optimized paths, eatery recommendations, 
and interactive visualizations.

## 🚀 Features 
🔍 **Pathfinding Algorithms**: Supports Uniform Cost Search (UCS) and A* to find the most efficient routes.  
🍴 **Eatery Recommendations**: Ranks and suggests top eateries based on customizable criteria.  
⚖️ **Algorithm Comparison**: Side-by-side performance metrics for UCS vs. A* (cost, runtime, path length).  
🗺️ **Interactive Visualization**: Graph-based map with dynamic route rendering on the frontend.  
⚒️ **CRUD Functionality**: Add, update, or remove nodes, edges, and eateries dynamically.  
🔄 **Dynamic Graph Management**: Handles real-time updates to the campus graph and eateries data.  
🎨 **User-Friendly Frontend**: Intuitive interface for selecting start/end points and visualizing results.  

## 🛠️ Tech Stack 

⚙️ **Backend**: Python (Flask)  
🌐 **Frontend**: Bootstrap, JavaScript  
📂 **Data Management**: JSON (graph + eateries)  
🧪 **Deployment/Testing**: Runs locally via Python 3.x and browser-based frontend  

## 📥 Installation

1. Clone the repository
   ```bash
   git clone https://github.com/markcelemen/dlsu-eatery-pathfinder.git
   cd dlsu-eatery-pathfinder
   ```
3. Set up the backend
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```
   
   Backend will run on: `http://127.0.0.1:5000/`
   
5. Set up the frontend
   ```bash
   cd ../frontend
   python -m http.server 8000
   ```

   Frontend will run on: `http://localhost:8000/`

## 💻 Usage

- **Access the app**: Open `http://localhost:8000` in your browser.  
- **Find a path**: Select a starting point and destination; choose either UCS or A* for route calculation.  
- **View recommendations**: Explore top eatery suggestions based on your criteria.  
- **Compare algorithms**: Run UCS and A* side by side to see differences in cost, runtime, and path.  
- **Manage data**: Use API endpoints to add, edit, or delete nodes, edges, and eateries.  
- **Visualize results**: See paths highlighted dynamically on the interactive campus map.  

## 👥 Team

🧑‍💻 **Mark Armas**   
🧑‍💻 **Arron Baranquil**  
🧑‍💻 **Mark Celemen**  
🧑‍💻 **Michael Sumilang**  
