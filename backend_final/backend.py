"""
DLSU Eatery Pathfinder - Core Backend Logic

Implements:
- UCS and A* pathfinding algorithms
- Multi-criteria eatery scoring
- Dynamic graph management
- Performance metrics collection
"""

import json
import heapq
import math
import time
import os
import datetime
from collections import defaultdict, deque

# =====================
# CONSTANTS AND CONFIGURATION
# =====================
GRAPH_FILE = 'graph.json'
EATERIES_FILE = 'eateries.json'
COST_FACTORS = {'price', 'distance'}  # Factors where lower values are better
MAX_TOP_EATERIES = 10

# Default preference weights (normalized to sum to 1.0)
DEFAULT_WEIGHTS = {
    'rating': 0.20,
    'price': 0.20,
    'distance': 0.20,
    'power_outlet': 0.15,
    'halal_certified': 0.15,
    'wifi': 0.10,
    'aircon': 0.10
}

# =====================
# UTILITY FUNCTIONS
# =====================
def safe_filename(filename):
    """Prevent path traversal attacks by using basename only"""
    return os.path.basename(filename)

# =====================
# FILE OPERATIONS
# =====================
def load_data(file_path):
    """Safely load JSON data from file with error handling"""
    file_path = safe_filename(file_path)
    try:
        if not os.path.exists(file_path):
            return {"error": f"File {file_path} not found"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in {file_path}: {str(e)}"}
    except Exception as e:
        return {"error": f"Error loading {file_path}: {str(e)}"}

def save_data(data, file_path):
    """Atomically save data to JSON file with validation"""
    file_path = safe_filename(file_path)
    temp_file = f"{file_path}.tmp"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Validate write
        with open(temp_file, 'r', encoding='utf-8') as f:
            written_data = json.load(f)
        if written_data != data:
            os.remove(temp_file)
            return {"error": "Data validation failed after write"}
            
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        return {"error": f"Error saving {file_path}: {str(e)}"}

# =====================
# GRAPH OPERATIONS
# =====================
def validate_graph(graph):
    """Validate graph structure integrity"""
    if not isinstance(graph, dict):
        return False, "Graph must be a dictionary"
    
    required_keys = {"nodes", "edges"}
    if not required_keys.issubset(graph.keys()):
        return False, "Graph missing required keys"
    
    # Validate nodes
    for node_id, coords in graph["nodes"].items():
        if not (isinstance(coords, list) and len(coords) == 2):
            return False, f"Invalid coordinates for node {node_id}"
        try:
            lat, lng = float(coords[0]), float(coords[1])
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                return False, f"Coordinates out of range for node {node_id}"
        except (ValueError, TypeError):
            return False, f"Non-numeric coordinates for node {node_id}"
    
    # Validate edges
    for node, edges in graph["edges"].items():
        if node not in graph["nodes"]:
            return False, f"Edge references missing node: {node}"
        for neighbor, weight in edges.items():
            if neighbor not in graph["nodes"]:
                return False, f"Edge references missing neighbor: {neighbor}"
            if neighbor == node:
                return False, f"Self-edge detected for node {node}"
            try:
                if float(weight) <= 0:
                    return False, f"Non-positive weight between {node} and {neighbor}"
            except (ValueError, TypeError):
                return False, f"Non-numeric weight between {node} and {neighbor}"
    
    return True, ""

def load_graph():
    """Load and validate graph data"""
    data = load_data(GRAPH_FILE)
    if "error" in data:
        return data
    
    valid, msg = validate_graph(data)
    if not valid:
        return {"error": f"Graph validation failed: {msg}"}
    
    return data

def save_graph(graph):
    """Save graph data after validation"""
    valid, msg = validate_graph(graph)
    if not valid:
        return {"error": f"Cannot save invalid graph: {msg}"}
    return save_data(graph, GRAPH_FILE)

def add_node(graph, node_id, lat, lng):
    """Add a new node to the graph"""
    if not isinstance(node_id, str) or not node_id.strip():
        return graph, "Node ID must be a non-empty string"
    
    try:
        lat, lng = float(lat), float(lng)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return graph, "Invalid coordinates range"
    except (ValueError, TypeError):
        return graph, "Latitude and longitude must be numbers"
    
    if node_id in graph["nodes"]:
        return graph, f"Node {node_id} already exists"
    
    graph["nodes"][node_id] = [lat, lng]
    graph["edges"][node_id] = {}
    return graph, f"Node {node_id} added successfully"

def add_edge(graph, node_a, node_b, cost):
    """Add bidirectional edge between nodes"""
    if node_a not in graph["nodes"] or node_b not in graph["nodes"]:
        return graph, "One or both nodes don't exist"
    if node_a == node_b:
        return graph, "Cannot create self-edge"
    
    try:
        cost = float(cost)
        if cost <= 0:
            return graph, "Cost must be a positive number"
    except (ValueError, TypeError):
        return graph, "Cost must be a number"
    
    graph["edges"][node_a][node_b] = cost
    graph["edges"][node_b][node_a] = cost
    return graph, f"Edge between {node_a} and {node_b} added successfully"

def remove_node(graph, node_id):
    """Remove a node and all its edges"""
    if node_id not in graph["nodes"]:
        return graph, f"Node {node_id} does not exist"
    
    del graph["nodes"][node_id]
    
    # Remove node's edges and references
    if node_id in graph["edges"]:
        del graph["edges"][node_id]
    
    for node, edges in graph["edges"].items():
        if node_id in edges:
            del edges[node_id]
    
    return graph, f"Node {node_id} removed successfully"

def remove_edge(graph, node_a, node_b):
    """Remove bidirectional edge between nodes"""
    if node_a not in graph["nodes"] or node_b not in graph["nodes"]:
        return graph, "One or both nodes don't exist"
    
    edge_exists = False
    for a, b in [(node_a, node_b), (node_b, node_a)]:
        if a in graph["edges"] and b in graph["edges"][a]:
            del graph["edges"][a][b]
            edge_exists = True
    
    if not edge_exists:
        return graph, f"No edge between {node_a} and {node_b}"
    
    return graph, f"Edge between {node_a} and {node_b} removed successfully"

# =====================
# EATERY ATTRIBUTES
# =====================
def validate_attributes(attributes):
    """Validate eatery attributes structure"""
    if not isinstance(attributes, dict):
        return False, "Attributes must be a dictionary"
    
    for eatery_id, attrs in attributes.items():
        if not isinstance(attrs, dict):
            return False, f"Attributes for {eatery_id} must be a dictionary"
        
        # Validate rating
        if 'rating' in attrs:
            try:
                rating = float(attrs['rating'])
                if not (0 <= rating <= 5):
                    return False, f"Rating for {eatery_id} must be between 0-5"
            except (ValueError, TypeError):
                return False, f"Invalid rating for {eatery_id}"
        
        # Validate price
        if 'price' in attrs:
            try:
                price = int(attrs['price'])
                if price < 0:
                    return False, f"Price level for {eatery_id} must be non-negative"
            except (ValueError, TypeError):
                return False, f"Invalid price level for {eatery_id}"
    
    return True, ""

def load_attributes():
    """Load and validate eatery attributes"""
    data = load_data(EATERIES_FILE)
    if "error" in data:
        return data
    
    valid, msg = validate_attributes(data)
    if not valid:
        return {"error": f"Attributes validation failed: {msg}"}
    
    return data

def save_attributes(attributes):
    """Save attributes after validation"""
    valid, msg = validate_attributes(attributes)
    if not valid:
        return {"error": f"Cannot save invalid attributes: {msg}"}
    return save_data(attributes, EATERIES_FILE)

def update_eatery(attributes, eatery_id, new_attrs):
    """Update eatery attributes or create new entry"""
    if not isinstance(new_attrs, dict):
        return attributes, "Attributes must be a dictionary"
    
    attributes.setdefault(eatery_id, {})
    
    # Convert boolean features to 1/0
    bool_features = {'power_outlet', 'halal_certified', 'wifi', 'aircon'}
    for key, value in new_attrs.items():
        if key in bool_features:
            if isinstance(value, bool):
                value = 1 if value else 0
            elif isinstance(value, str):
                value = 1 if value.lower() in ['true', 'yes', '1', 'y', 't'] else 0
            elif isinstance(value, (int, float)):
                value = 1 if value != 0 else 0
        
        attributes[eatery_id][key] = value
    
    return attributes, f"Eatery {eatery_id} updated successfully"

def remove_eatery(attributes, eatery_id):
    """Remove an eatery from attributes"""
    if eatery_id not in attributes:
        return attributes, f"Eatery {eatery_id} does not exist"
    
    del attributes[eatery_id]
    return attributes, f"Eatery {eatery_id} removed successfully"

# =====================
# GEOGRAPHIC CALCULATIONS
# =====================
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points (meters)
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        float: Distance in meters
    """
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi/2)**2 + 
         math.cos(phi1) * math.cos(phi2) * 
         math.sin(delta_lambda/2)**2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def is_open(hours_str):
    """Check if eatery is open based on current time"""
    if not hours_str or not isinstance(hours_str, str):
        return True  # Default to open if hours not provided
        
    if hours_str.strip().lower() == "24/7":
        return True
        
    try:
        now = datetime.datetime.now().time()
        parts = hours_str.split('-')
        
        if len(parts) != 2:
            return True  # Default to open for invalid format
            
        open_time = datetime.datetime.strptime(parts[0].strip(), "%H:%M").time()
        close_time = datetime.datetime.strptime(parts[1].strip(), "%H:%M").time()
        
        # Handle overnight schedules
        if close_time < open_time:
            return now >= open_time or now <= close_time
        return open_time <= now <= close_time
        
    except ValueError:
        return True  # Default to open if parsing fails

# =====================
# PREFERENCE HANDLING
# =====================
def convert_ranks_to_weights(rank_dict):
    """
    Convert user preference rankings to normalized weights
    
    Args:
        rank_dict (dict): User preference rankings (lower rank = higher priority)
        
    Returns:
        dict: Normalized weights summing to 1.0
    """
    if not rank_dict:
        return DEFAULT_WEIGHTS.copy()
    
    # Filter and validate ranks
    valid_ranks = {}
    for factor, rank in rank_dict.items():
        if factor in DEFAULT_WEIGHTS:
            try:
                rank = int(rank)
                if rank > 0:
                    valid_ranks[factor] = rank
            except (ValueError, TypeError):
                continue
    
    if not valid_ranks:
        return DEFAULT_WEIGHTS.copy()
    
    # Convert ranks to weights (invert ranks)
    max_rank = max(valid_ranks.values())
    inverse_ranks = {k: max_rank - v + 1 for k, v in valid_ranks.items()}
    total = sum(inverse_ranks.values())
    return {k: v/total for k, v in inverse_ranks.items()}

def normalize_value(value, min_val, max_val, invert=False):
    """
    Normalize value to 0-1 range with optional inversion
    
    Args:
        value: Value to normalize
        min_val: Minimum value in dataset
        max_val: Maximum value in dataset
        invert: If True, higher values get lower scores
        
    Returns:
        float: Normalized value between 0 and 1
    """
    if max_val <= min_val:
        return 0.5  # Handle uniform values
    
    clamped = max(min_val, min(value, max_val))
    normalized = (clamped - min_val) / (max_val - min_val)
    return 1 - normalized if invert else normalized

def compute_scores(attributes, graph, start_node, custom_weights=None):
    """
    Compute preference-based scores for all valid eateries
    
    Args:
        attributes (dict): Eatery attributes
        graph (dict): Graph structure
        start_node (str): Starting location
        custom_weights (dict): User preference weights
        
    Returns:
        dict: {eatery_id: score} for all valid eateries
    """
    weights = custom_weights or DEFAULT_WEIGHTS
    
    # Filter open eateries that exist in graph
    eatery_nodes = [
        node for node in attributes 
        if node in graph["nodes"] and is_open(attributes[node].get('hours', ''))
    ]
    
    if not eatery_nodes:
        return {}
    
    start_coords = graph["nodes"][start_node]
    start_lat, start_lng = start_coords
    
    # Precompute distances
    distances = {}
    for eatery in eatery_nodes:
        eatery_coords = graph["nodes"][eatery]
        distances[eatery] = haversine(start_lat, start_lng, *eatery_coords)
    
    # Collect values for normalization
    metrics = defaultdict(list)
    for eatery in eatery_nodes:
        data = attributes[eatery]
        for factor in weights:
            if factor == 'distance':
                metrics['distance'].append(distances[eatery])
            elif factor in data:
                metrics[factor].append(data[factor])
    
    # Calculate min/max for each factor
    min_max = {}
    for factor, values in metrics.items():
        if values:
            min_val = min(values)
            max_val = max(values)
            invert = factor in COST_FACTORS
            min_max[factor] = (min_val, max_val, invert)
    
    # Calculate final scores
    scores = {}
    for eatery in eatery_nodes:
        data = attributes[eatery]
        total_score = 0.0
        
        for factor, weight in weights.items():
            value = None
            
            if factor == 'distance':
                value = distances[eatery]
            elif factor in data:
                value = data[factor]
            
            if value is not None and factor in min_max:
                min_val, max_val, invert = min_max[factor]
                normalized = normalize_value(value, min_val, max_val, invert)
                total_score += weight * normalized
        
        scores[eatery] = total_score
    
    return scores

# =====================
# PATHFINDING ALGORITHMS
# =====================
def path_search(graph, start, goal, heuristic_func=None):
    """
    Generic pathfinding algorithm (UCS or A*)
    
    Args:
        graph: Graph structure
        start: Start node ID
        goal: Goal node ID
        heuristic_func: Heuristic function (None for UCS)
        
    Returns:
        tuple: (cost, path, metrics)
        metrics: {nodes_expanded, max_frontier_size, exec_time}
    """
    if start not in graph["nodes"]:
        return float('inf'), [], {"error": f"Start node '{start}' not found"}
    if goal not in graph["nodes"]:
        return float('inf'), [], {"error": f"Goal node '{goal}' not found"}
    if start == goal:
        return 0.0, [start], {"nodes_expanded": 1, "max_frontier_size": 1, "exec_time": 0}
    
    # Initialize tracking
    g_scores = {start: 0.0}  # Cost from start
    parents = {start: None}
    frontier = []
    explored = set()
    nodes_expanded = 0
    max_frontier_size = 0
    
    # UCS uses cost, A* uses f_score
    if heuristic_func:
        f_score = g_scores[start] + heuristic_func(start)
        heapq.heappush(frontier, (f_score, start))
    else:
        heapq.heappush(frontier, (g_scores[start], start))
    
    start_time = time.perf_counter()
    
    while frontier:
        max_frontier_size = max(max_frontier_size, len(frontier))
        
        # Get next node to explore
        current_cost, current = heapq.heappop(frontier)
        
        # Skip outdated entries
        if current in explored:
            continue
            
        explored.add(current)
        nodes_expanded += 1
        
        # Goal check
        if current == goal:
            path = []
            while current:
                path.append(current)
                current = parents[current]
            exec_time = time.perf_counter() - start_time
            return g_scores[goal], path[::-1], {
                "nodes_expanded": nodes_expanded,
                "max_frontier_size": max_frontier_size,
                "exec_time": exec_time
            }
        
        # Explore neighbors
        for neighbor, edge_cost in graph["edges"].get(current, {}).items():
            if neighbor in explored:
                continue
                
            tentative_g = g_scores[current] + edge_cost
            
            # New node or better path found
            if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                g_scores[neighbor] = tentative_g
                parents[neighbor] = current
                
                # UCS: priority = cost
                # A*: priority = cost + heuristic
                priority = tentative_g
                if heuristic_func:
                    priority += heuristic_func(neighbor)
                
                heapq.heappush(frontier, (priority, neighbor))
    
    # No path found
    exec_time = time.perf_counter() - start_time
    return float('inf'), [], {
        "nodes_expanded": nodes_expanded,
        "max_frontier_size": max_frontier_size,
        "exec_time": exec_time,
        "error": "No path exists"
    }

def ucs_search(graph, start, goal):
    """Uniform Cost Search implementation"""
    return path_search(graph, start, goal)

def a_star_search(graph, start, goal):
    """A* Search implementation with Haversine heuristic"""
    # Create heuristic function
    goal_coords = graph["nodes"][goal]
    goal_lat, goal_lng = goal_coords
    
    def heuristic(node):
        node_coords = graph["nodes"][node]
        return haversine(node_coords[0], node_coords[1], goal_lat, goal_lng)
    
    return path_search(graph, start, goal, heuristic)

# =====================
# CORE API FUNCTIONS
# =====================
def find_optimal_path(start_node, algorithm='astar', custom_ranks=None):
    """
    Find optimal path to best eatery based on user preferences
    
    Args:
        start_node (str): Starting location
        algorithm (str): 'ucs' or 'astar'
        custom_ranks (dict): User preference rankings
        
    Returns:
        dict: Pathfinding result with metrics
    """
    try:
        # Load and validate data
        graph = load_graph()
        if "error" in graph:
            return {"error": graph["error"]}
            
        attributes = load_attributes()
        if "error" in attributes:
            return {"error": attributes["error"]}
            
        if start_node not in graph["nodes"]:
            return {"error": f"Start node '{start_node}' not found"}
        
        # Convert preferences to weights
        weights = convert_ranks_to_weights(custom_ranks) if custom_ranks else DEFAULT_WEIGHTS
        
        # Compute scores for all eateries
        scores = compute_scores(attributes, graph, start_node, weights)
        if not scores:
            return {"error": "No valid eateries found"}
        
        # Sort eateries by score (best first)
        sorted_eateries = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Find path to best reachable eatery
        for eatery_id, score in sorted_eateries:
            if algorithm == 'ucs':
                cost, path, metrics = ucs_search(graph, start_node, eatery_id)
            elif algorithm == 'astar':
                cost, path, metrics = a_star_search(graph, start_node, eatery_id)
            else:
                return {"error": "Invalid algorithm. Choose 'ucs' or 'astar'"}
            
            if "error" in metrics:
                continue  # Try next eatery
                
            eatery_data = attributes.get(eatery_id, {}).copy()
            return {
                "start": start_node,
                "goal": eatery_id,
                "goal_score": score,
                "path": path,
                "cost": cost,
                "algorithm": algorithm,
                "eatery_info": eatery_data,
                "weights_used": weights,
                "open_status": "Open" if is_open(eatery_data.get('hours', '')) else "Closed",
                "distance": haversine(*graph["nodes"][start_node], *graph["nodes"][eatery_id]),
                "metrics": {
                    "execution_time_ms": round(metrics["exec_time"] * 1000, 2),
                    "nodes_expanded": metrics["nodes_expanded"],
                    "max_frontier_size": metrics["max_frontier_size"]
                }
            }
        
        return {"error": "No reachable eateries found"}
        
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def get_top_eateries(start_node, top_n=3, custom_ranks=None):
    """
    Get top-ranked eateries based on user preferences
    
    Args:
        start_node (str): Starting location
        top_n (int): Number of results
        custom_ranks (dict): User preference rankings
        
    Returns:
        list: Top eateries with details
    """
    try:
        # Validate parameters
        top_n = min(max(int(top_n), 1), MAX_TOP_EATERIES)
        
        # Load data
        graph = load_graph()
        if "error" in graph:
            return graph
            
        attributes = load_attributes()
        if "error" in attributes:
            return attributes
            
        if start_node not in graph["nodes"]:
            return {"error": f"Start node '{start_node}' not found"}
        
        # Compute scores
        weights = convert_ranks_to_weights(custom_ranks) if custom_ranks else DEFAULT_WEIGHTS
        scores = compute_scores(attributes, graph, start_node, weights)
        
        if not scores:
            return {"error": "No valid eateries found"}
        
        # Get top N eateries
        sorted_eateries = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        results = []
        for rank, (eatery_id, score) in enumerate(sorted_eateries, 1):
            eatery_data = attributes.get(eatery_id, {}).copy()
            eatery_data["id"] = eatery_id
            eatery_data["rank"] = rank
            eatery_data["score"] = round(score, 4)
            eatery_data["open_status"] = "Open" if is_open(eatery_data.get('hours', '')) else "Closed"
            
            # Calculate direct distance
            start_coords = graph["nodes"][start_node]
            eatery_coords = graph["nodes"][eatery_id]
            eatery_data["distance_meters"] = round(
                haversine(*start_coords, *eatery_coords), 1
            )
            
            results.append(eatery_data)
        
        return results
    
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def compare_algorithms(start_node, preferences=None):
    """
    Compare UCS vs A* algorithms
    
    Args:
        start_node (str): Starting location
        preferences (dict): User preferences
        
    Returns:
        dict: Comparison results for both algorithms
    """
    try:
        results = {}
        for algo in ['ucs', 'astar']:
            start_time = time.perf_counter()
            path_result = find_optimal_path(start_node, algo, preferences)
            total_time = time.perf_counter() - start_time
            
            if "error" in path_result:
                results[algo] = {"error": path_result["error"]}
            else:
                results[algo] = {
                    "path": path_result["path"],
                    "cost": path_result["cost"],
                    "eatery": path_result["goal"],
                    "metrics": path_result["metrics"]
                }
                results[algo]["metrics"]["total_execution_time_ms"] = round(total_time * 1000, 2)
        
        return results
    except Exception as e:
        return {"error": f"Comparison failed: {str(e)}"}

# =====================
# DATA RETRIEVAL
# =====================
def get_graph_data():
    """Get current graph structure"""
    return load_graph()

def get_eatery_list():
    """Get all eateries with attributes"""
    return load_attributes()