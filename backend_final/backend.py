
"""
DLSU Eatery Pathfinder - Core Backend Logic

This module implements:
- UCS (Uniform Cost Search) and A* pathfinding algorithms
- Multi-criteria eatery scoring system
- Dynamic graph management
"""

import json
import heapq
import math
import time
import os
import datetime
import tracemalloc
from collections import defaultdict, deque

# =====================
# CONSTANTS AND CONFIGURATION
# =====================
GRAPH_FILE = 'graph.json'
EATERIES_FILE = 'eateries.json'
COST_FACTORS = {'price', 'distance'}  # Factors where lower values are better

# Default preference weights (normalized to sum to 1.0)
_DEFAULT_WEIGHTS_UNNORMALIZED = {
    'rating': 0.20,
    'price': 0.20,
    'distance': 0.20,
    'power_outlet': 0.15,
    'halal_certified': 0.15,
    'wifi': 0.10,
    'aircon': 0.10
}
_TOTAL_WEIGHTS = sum(_DEFAULT_WEIGHTS_UNNORMALIZED.values())
DEFAULT_WEIGHTS = {k: v/_TOTAL_WEIGHTS for k, v in _DEFAULT_WEIGHTS_UNNORMALIZED.items()}

KNOWN_FACTORS = set(DEFAULT_WEIGHTS.keys())  # For validation
EARTH_RADIUS = 6371000  # Earth's radius in meters
MAX_TOP_EATERIES = 10   # Safety limit for top eateries request
DEBUG_MODE = True       # Enable debug logging

# =====================
# UTILITY FUNCTIONS
# =====================
def debug_log(message):
    """Print debug messages if debug mode is enabled"""
    if DEBUG_MODE:
        print(f"DEBUG: {message}")

def safe_filename(filename):
    """Prevent path traversal attacks by using basename only"""
    return os.path.basename(filename)

# =====================
# FILE OPERATIONS
# =====================
def load_data(file_path):
    """
    Safely load JSON data from file with comprehensive error handling
    
    Args:
        file_path (str): Path to JSON file
        
    Returns:
        dict: Loaded data or error dictionary
    """
    file_path = safe_filename(file_path)
    try:
        if not os.path.exists(file_path):
            return {"error": f"File {file_path} not found"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in {file_path}: {str(e)}"}
    except PermissionError:
        return {"error": f"Permission denied accessing {file_path}"}
    except Exception as e:
        return {"error": f"Error loading {file_path}: {str(e)}"}

def save_data(data, file_path):
    """
    Atomically save data to JSON file with write validation
    
    Args:
        data (dict): Data to save
        file_path (str): Target file path
        
    Returns:
        bool or dict: True on success, error dict on failure
    """
    file_path = safe_filename(file_path)
    temp_file = f"{file_path}.tmp"
    try:
        # Write to temporary file first
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Validate write was successful
        with open(temp_file, 'r', encoding='utf-8') as f:
            written_data = json.load(f)
        if written_data != data:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return {"error": "Data validation failed after write"}
            
        # Atomically replace original file
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return {"error": f"Error saving {file_path}: {str(e)}"}

# =====================
# GRAPH OPERATIONS AND VALIDATION
# =====================
def validate_graph(graph):
    """
    Validate graph structure for integrity and connectivity
    
    Args:
        graph (dict): Graph data structure
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not isinstance(graph, dict):
        return False, "Graph must be a dictionary"
    
    if "nodes" not in graph or not isinstance(graph["nodes"], dict):
        return False, "Missing or invalid 'nodes' dictionary"
    
    if "edges" not in graph or not isinstance(graph["edges"], dict):
        return False, "Missing or invalid 'edges' dictionary"
    
    # Validate node coordinates
    for node_id, coords in graph["nodes"].items():
        if not isinstance(coords, list) or len(coords) != 2:
            return False, f"Invalid coordinates for node {node_id}"
        try:
            lat, lng = float(coords[0]), float(coords[1])
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                return False, f"Invalid coordinates range for node {node_id}"
        except (ValueError, TypeError):
            return False, f"Non-numeric coordinates for node {node_id}"
    
    # Validate edge references
    for node in graph["edges"]:
        if node not in graph["nodes"]:
            return False, f"Edge references missing node: {node}"
        for neighbor in graph["edges"][node]:
            if neighbor not in graph["nodes"]:
                return False, f"Edge references missing neighbor: {neighbor}"
    
    # Validate edge weights
    for node, edges in graph["edges"].items():
        for neighbor, weight in edges.items():
            if neighbor == node:
                return False, f"Self-edge detected for node {node}"
            try:
                weight = float(weight)
                if weight <= 0:
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
    """Add a new node to the graph with validation"""
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
    """Add bidirectional edge between nodes with validation"""
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
    
    # Add edge in both directions for undirected graph
    graph["edges"][node_a][node_b] = cost
    graph["edges"][node_b][node_a] = cost
    return graph, f"Edge between {node_a} and {node_b} added successfully"

def remove_node(graph, node_id):
    """Remove a node from the graph and clean all references"""
    if node_id not in graph["nodes"]:
        return graph, f"Node {node_id} does not exist"
    
    # Remove node from nodes dictionary
    del graph["nodes"][node_id]
    
    # Remove node's edge list
    if node_id in graph["edges"]:
        del graph["edges"][node_id]
    
    # Remove all references to this node from other nodes
    for node, edges in graph["edges"].items():
        if node_id in edges:
            del edges[node_id]
    
    return graph, f"Node {node_id} removed successfully"

def remove_edge(graph, node_a, node_b):
    """Remove bidirectional edge between nodes"""
    if node_a not in graph["nodes"] or node_b not in graph["nodes"]:
        return graph, "One or both nodes don't exist"
    
    edge_exists = False
    
    # Remove edge in both directions
    if node_a in graph["edges"] and node_b in graph["edges"][node_a]:
        del graph["edges"][node_a][node_b]
        edge_exists = True
    
    if node_b in graph["edges"] and node_a in graph["edges"][node_b]:
        del graph["edges"][node_b][node_a]
        edge_exists = True
    
    if not edge_exists:
        return graph, f"No edge between {node_a} and {node_b}"
    
    return graph, f"Edge between {node_a} and {node_b} removed successfully"

# =====================
# EATERY ATTRIBUTES MANAGEMENT
# =====================
def validate_attributes(attributes):
    """Validate eatery attributes structure with range checks"""
    if not isinstance(attributes, dict):
        return False, "Attributes must be a dictionary"
    
    for eatery_id, attrs in attributes.items():
        if not isinstance(attrs, dict):
            return False, f"Attributes for {eatery_id} must be a dictionary"
        
        # Validate rating range
        if 'rating' in attrs:
            try:
                rating = float(attrs['rating'])
                if not (0 <= rating <= 5):
                    return False, f"Rating for {eatery_id} must be between 0-5"
            except (ValueError, TypeError):
                return False, f"Invalid rating for {eatery_id}"
        
        # Validate price level
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
    """Update eatery attributes or create new entry with validation"""
    if not isinstance(new_attrs, dict):
        return attributes, "Attributes must be a dictionary"
    
    if eatery_id not in attributes:
        attributes[eatery_id] = {}
    
    for key, value in new_attrs.items():
        if key == 'rating':
            try:
                value = float(value)
                if not (0 <= value <= 5):
                    return attributes, "Rating must be between 0-5"
            except (ValueError, TypeError):
                return attributes, "Invalid rating value"
        elif key == 'price':
            try:
                value = int(value)
                if value < 0:
                    return attributes, "Price level must be non-negative"
            except (ValueError, TypeError):
                return attributes, "Invalid price level"
        elif key in {'power_outlet', 'halal_certified', 'wifi', 'aircon'}:
            # Convert various truthy representations to 1/0
            if isinstance(value, bool):
                value = 1 if value else 0
            elif isinstance(value, int):
                value = 1 if value != 0 else 0
            elif isinstance(value, str):
                value = 1 if value.lower() in ['true', 'yes', '1', 'y', 't'] else 0
            else:
                value = 0
        
        attributes[eatery_id][key] = value
    
    return attributes, f"Eatery {eatery_id} updated successfully"

def remove_eatery(attributes, eatery_id):
    """Remove an eatery from attributes"""
    if eatery_id not in attributes:
        return attributes, f"Eatery {eatery_id} does not exist"
    
    del attributes[eatery_id]
    return attributes, f"Eatery {eatery_id} removed successfully"

# =====================
# GEOGRAPHIC AND TIME CALCULATIONS
# =====================
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points using Haversine formula
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        float: Distance in meters
    """
    # Convert degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_phi/2)**2 + 
         math.cos(phi1) * math.cos(phi2) * 
         math.sin(delta_lambda/2)**2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS * c

def is_open(hours_str):
    """
    Check if eatery is open based on current time
    
    Supported formats:
    - "24/7": Always open
    - "HH:MM-HH:MM": Standard hours
    - "HH:MM-HH:MM": Overnight hours (close time < open time)
    
    Returns True for invalid/missing hours (fail-safe approach)
    """
    if not hours_str or not isinstance(hours_str, str):
        return True  # Default to open if hours not provided
        
    if hours_str.strip().lower() == "24/7":
        return True
        
    try:
        now = datetime.datetime.now().time()
        parts = hours_str.split('-')
        
        if len(parts) != 2:
            return True  # Default to open for invalid format
            
        open_time_str = parts[0].strip()
        close_time_str = parts[1].strip()
        
        open_time = datetime.datetime.strptime(open_time_str, "%H:%M").time()
        close_time = datetime.datetime.strptime(close_time_str, "%H:%M").time()
        
        # Handle overnight schedules (e.g., 17:00-3:00)
        if close_time < open_time:
            return now >= open_time or now <= close_time
        return open_time <= now <= close_time
        
    except ValueError:
        return True  # Default to open if parsing fails

# =====================
# PREFERENCE HANDLING AND SCORING
# =====================
def convert_ranks_to_weights(rank_dict):
    """
    Convert user preference rankings to normalized weights
    
    Lower rank numbers indicate higher priority.
    Example: {'distance': 1, 'rating': 2} -> {'distance': 0.667, 'rating': 0.333}
    
    Args:
        rank_dict (dict): User preference rankings
        
    Returns:
        dict: Normalized weights summing to 1.0
    """
    if not rank_dict:
        return DEFAULT_WEIGHTS.copy()
        
    valid_ranks = {}
    for factor, rank in rank_dict.items():
        if factor in KNOWN_FACTORS:
            try:
                rank = int(rank)
                if rank > 0:
                    valid_ranks[factor] = rank
            except (ValueError, TypeError):
                continue
    
    if not valid_ranks:
        return DEFAULT_WEIGHTS.copy()
    
    # Convert ranks to weights (invert so lower rank = higher weight)
    max_rank = max(valid_ranks.values())
    inverse_ranks = {k: max_rank - v + 1 for k, v in valid_ranks.items()}
    
    total = sum(inverse_ranks.values())
    return {k: round(v/total, 4) for k, v in inverse_ranks.items()}

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
        return 0.5  # Handle case where all values are equal
    
    # Clamp value to valid range
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
    
    # Filter eateries that are currently open and exist in graph
    eatery_nodes = [
        node for node in attributes 
        if node in graph["nodes"] and is_open(attributes[node].get('hours', ''))
    ]
    
    debug_log(f"Found {len(eatery_nodes)} open eateries: {eatery_nodes}")
    
    if not eatery_nodes:
        return {}
    
    start_coords = graph["nodes"][start_node]
    start_lat, start_lng = start_coords
    
    # Precompute distances for all eateries
    distances = {}
    for eatery in eatery_nodes:
        eatery_coords = graph["nodes"][eatery]
        distances[eatery] = haversine(start_lat, start_lng, *eatery_coords)
    
    # Collect all values for normalization
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
        
        scores[eatery] = round(total_score, 4)
    
    debug_log(f"Computed scores: {scores}")
    return scores

# =====================
# CONNECTIVITY CHECKING
# =====================
def check_connectivity(graph, start, goal):
    """
    Check if there's a path from start to goal using BFS
    
    Args:
        graph (dict): Graph structure
        start (str): Starting node
        goal (str): Target node
        
    Returns:
        bool: True if path exists, False otherwise
    """
    if start == goal:
        return True
        
    if start not in graph["nodes"] or goal not in graph["nodes"]:
        return False
    
    visited = set()
    queue = deque([start])
    
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
            
        visited.add(current)
        
        if current == goal:
            return True
            
        # Add unvisited neighbors to queue
        for neighbor in graph["edges"].get(current, {}):
            if neighbor not in visited:
                queue.append(neighbor)
    
    return False

# =====================
# PATHFINDING ALGORITHMS
# =====================
def ucs_search(graph, start, goal):
    """
    Uniform Cost Search implementation with comprehensive metrics
    
    Returns:
        tuple: (cost, path, nodes_expanded, max_frontier_size, error_msg, peak_memory)
    """
    debug_log(f"UCS: Searching from {start} to {goal}")
    
    if start not in graph["nodes"]:
        return float('inf'), [], 0, 0, f"Start node '{start}' not found", 0
    if goal not in graph["nodes"]:
        return float('inf'), [], 0, 0, f"Goal node '{goal}' not found", 0
    
    if start == goal:
        return 0.0, [start], 1, 1, "", 0
    
    # Quick connectivity check
    if not check_connectivity(graph, start, goal):
        debug_log(f"UCS: No connectivity between {start} and {goal}")
        return float('inf'), [], 0, 0, f"No path exists from {start} to {goal}", 0
    
    tracemalloc.start()
    try:
        # Priority queue: (cost, path)
        frontier = [(0.0, [start])]
        visited = set()
        nodes_expanded = 0
        max_frontier_size = 0

        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            
            cost, path = heapq.heappop(frontier)
            current = path[-1]
            
            # Skip if already visited with better cost
            if current in visited:
                continue
            
            visited.add(current)
            nodes_expanded += 1
            
            debug_log(f"UCS: Expanding {current} with cost {cost}")
            
            if current == goal:
                if not validate_path(graph, path):
                    return float('inf'), [], nodes_expanded, max_frontier_size, "Invalid path generated", 0
                _, peak_memory = tracemalloc.get_traced_memory()
                debug_log(f"UCS: Found path {path} with cost {cost}")
                return cost, path, nodes_expanded, max_frontier_size, "", peak_memory
            
            # Explore neighbors
            for neighbor, edge_cost in graph["edges"].get(current, {}).items():
                if neighbor not in visited:
                    new_cost = cost + edge_cost
                    new_path = path + [neighbor]
                    heapq.heappush(frontier, (new_cost, new_path))
        
        return float('inf'), [], nodes_expanded, max_frontier_size, "No path exists", 0
    finally:
        tracemalloc.stop()

def a_star_search(graph, start, goal):
    """
    A* Search implementation with Haversine heuristic
    
    Returns:
        tuple: (cost, path, nodes_expanded, max_frontier_size, error_msg, peak_memory)
    """
    debug_log(f"A*: Searching from {start} to {goal}")
    
    if start not in graph["nodes"]:
        return float('inf'), [], 0, 0, f"Start node '{start}' not found", 0
    if goal not in graph["nodes"]:
        return float('inf'), [], 0, 0, f"Goal node '{goal}' not found", 0
    
    if start == goal:
        return 0.0, [start], 1, 1, "", 0
    
    # Quick connectivity check
    if not check_connectivity(graph, start, goal):
        debug_log(f"A*: No connectivity between {start} and {goal}")
        return float('inf'), [], 0, 0, f"No path exists from {start} to {goal}", 0
    
    goal_coords = graph["nodes"][goal]
    goal_lat, goal_lng = goal_coords
    
    # Heuristic function using Haversine distance
    def heuristic(node):
        node_coords = graph["nodes"][node]
        return haversine(node_coords[0], node_coords[1], goal_lat, goal_lng)
    
    tracemalloc.start()
    try:
        # Priority queue: (f_score, g_cost, path)
        start_h = heuristic(start)
        frontier = [(start_h, 0.0, [start])]
        visited = set()
        nodes_expanded = 0
        max_frontier_size = 0

        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            
            f_score, g_cost, path = heapq.heappop(frontier)
            current = path[-1]
            
            # Skip if already visited
            if current in visited:
                continue
            
            visited.add(current)
            nodes_expanded += 1
            
            debug_log(f"A*: Expanding {current} with g={g_cost}, f={f_score}")
            
            if current == goal:
                if not validate_path(graph, path):
                    return float('inf'), [], nodes_expanded, max_frontier_size, "Invalid path generated", 0
                _, peak_memory = tracemalloc.get_traced_memory()
                debug_log(f"A*: Found path {path} with cost {g_cost}")
                return g_cost, path, nodes_expanded, max_frontier_size, "", peak_memory
            
            # Explore neighbors
            for neighbor, edge_cost in graph["edges"].get(current, {}).items():
                if neighbor not in visited:
                    new_g = g_cost + edge_cost
                    new_h = heuristic(neighbor)
                    new_f = new_g + new_h
                    new_path = path + [neighbor]
                    heapq.heappush(frontier, (new_f, new_g, new_path))
        
        return float('inf'), [], nodes_expanded, max_frontier_size, "No path exists", 0
    finally:
        tracemalloc.stop()

def validate_path(graph, path):
    """
    Verify that a path is valid in the graph
    
    Args:
        graph (dict): Graph structure
        path (list): Sequence of nodes
        
    Returns:
        bool: True if path is valid
    """
    if len(path) < 2:
        return True
        
    for i in range(1, len(path)):
        prev = path[i-1]
        curr = path[i]
        if curr not in graph["edges"].get(prev, {}):
            debug_log(f"Invalid path: no edge from {prev} to {curr}")
            return False
    return True

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
        dict: Complete pathfinding result with metrics
    """
    debug_log(f"Finding optimal path from {start_node} using {algorithm}")
    
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
        
        # Convert user preferences to weights
        weights = convert_ranks_to_weights(custom_ranks) if custom_ranks else DEFAULT_WEIGHTS
        debug_log(f"Using weights: {weights}")
        
        # Compute scores for all eateries
        scores = compute_scores(attributes, graph, start_node, weights)
        if not scores:
            return {"error": "No valid eateries found"}
        
        # Sort eateries by score (best first)
        sorted_eateries = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        debug_log(f"Top eateries by score: {[(e, round(s, 3)) for e, s in sorted_eateries[:5]]}")
        
        # Try to find path to best reachable eatery
        for eatery_id, score in sorted_eateries:
            debug_log(f"Trying to find path to {eatery_id} (score: {score})")
            
            start_time = time.perf_counter()
            
            if algorithm == 'ucs':
                cost, path, nodes_expanded, max_frontier, error, peak_memory = ucs_search(
                    graph, start_node, eatery_id
                )
            elif algorithm == 'astar':
                cost, path, nodes_expanded, max_frontier, error, peak_memory = a_star_search(
                    graph, start_node, eatery_id
                )
            else:
                return {"error": "Invalid algorithm. Choose 'ucs' or 'astar'"}
            
            exec_time = time.perf_counter() - start_time
            
            if not error and path:
                debug_log(f"Successfully found path to {eatery_id}: {path}")
                return {
                    "start": start_node,
                    "goal": eatery_id,
                    "goal_score": score,
                    "path": path,
                    "cost": cost,
                    "algorithm": algorithm,
                    "eatery_info": attributes.get(eatery_id, {}).copy(),
                    "weights_used": weights,
                    "open_status": "Open" if is_open(attributes.get(eatery_id, {}).get('hours', '')) else "Closed",
                    "distance": haversine(*graph["nodes"][start_node], *graph["nodes"][eatery_id]),
                    "metrics": {
                        "execution_time": round(exec_time * 1000, 2),
                        "nodes_expanded": nodes_expanded,
                        "max_frontier_size": max_frontier,
                        "peak_memory_kb": round(peak_memory / 1024, 2) if peak_memory else 0
                    }
                }
            else:
                debug_log(f"Failed to find path to {eatery_id}: {error}")
        
        return {"error": "No reachable eateries found among top candidates"}
        
    except Exception as e:
        debug_log(f"Unexpected error in find_optimal_path: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()

def get_top_eateries(start_node, top_n=3, custom_ranks=None):
    """
    Get top-ranked eateries based on user preferences
    
    Args:
        start_node (str): Starting location
        top_n (int): Number of results to return
        custom_ranks (dict): User preference rankings
        
    Returns:
        list: Top eateries with detailed information
    """
    try:
        # Validate parameters
        try:
            top_n = int(top_n)
            if top_n < 1:
                return {"error": "top_n must be at least 1"}
            if top_n > MAX_TOP_EATERIES:
                top_n = MAX_TOP_EATERIES
        except (ValueError, TypeError):
            return {"error": "Invalid top_n value"}
        
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
            eatery_data["score"] = score
            eatery_data["open_status"] = "Open" if is_open(eatery_data.get('hours', '')) else "Closed"
            
            # Calculate direct distance
            try:
                start_coords = graph["nodes"][start_node]
                eatery_coords = graph["nodes"][eatery_id]
                eatery_data["distance_meters"] = round(haversine(*start_coords, *eatery_coords), 1)
            except KeyError:
                eatery_data["distance_meters"] = 0
            
            results.append(eatery_data)
        
        return results
    
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def compare_algorithms(start_node, preferences=None):
    """
    Compare performance of UCS vs A* algorithms
    
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
            exec_time = time.perf_counter() - start_time
            
            if "error" in path_result:
                results[algo] = {"error": path_result["error"]}
            else:
                results[algo] = {
                    "path": path_result["path"],
                    "cost": path_result["cost"],
                    "eatery": path_result["goal"],
                    "metrics": path_result["metrics"]
                }
            results[algo]["total_execution_time"] = round(exec_time * 1000, 2)
        
        return results
    except Exception as e:
        return {"error": f"Comparison failed: {str(e)}"}

# =====================
# DATA RETRIEVAL FUNCTIONS
# =====================
def get_graph_data():
    """Get current graph structure"""
    return load_graph()

def get_eatery_list():
    """Get all eateries with their attributes"""
    return load_attributes()
