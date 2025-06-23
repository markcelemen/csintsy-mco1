
"""
DLSU Eatery Pathfinder - Flask API Server

- Pathfinding using UCS and A* algorithms
- Dynamic graph management (add/remove nodes and edges)
- Eatery preference scoring and ranking
- Algorithm performance comparison
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from backend import (
    find_optimal_path,
    get_top_eateries,
    get_graph_data,
    get_eatery_list,
    add_node,
    add_edge,
    remove_node,
    remove_edge,
    update_eatery,
    remove_eatery,
    load_graph,
    save_graph,
    load_attributes,
    save_attributes,
    compare_algorithms,
    debug_log
)
import time
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# =====================
# MIDDLEWARE AND DECORATORS
# =====================
def log_request(f):
    """Decorator to log API requests and responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        debug_log(f"API: {request.method} {request.path} - {request.get_json(silent=True)}")
        
        result = f(*args, **kwargs)
        
        elapsed = round((time.time() - start_time) * 1000, 2)
        debug_log(f"API: {request.method} {request.path} completed in {elapsed}ms")
        
        return result
    return decorated_function

def validate_json_request(required_fields=None):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"error": "Invalid or missing JSON data"}), 400
                
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =====================
# CORE PATHFINDING ENDPOINTS
# =====================
@app.route('/find-path', methods=['POST'])
@log_request
@validate_json_request(['start'])
def api_find_path():
    """
    Find optimal path to best eatery based on user preferences
    
    Request Body:
    {
        "start": "NodeID",           # Starting location (required)
        "algorithm": "astar"|"ucs",  # Search algorithm (default: astar)
        "preferences": {             # User preference rankings (optional)
            "factor": rank,          # Lower rank = higher priority
            ...
        }
    }
    
    Response:
    {
        "start": str,               # Starting node
        "goal": str,                # Best eatery found
        "goal_score": float,        # Eatery's calculated score
        "path": [str],              # Optimal path nodes
        "cost": float,              # Total path cost
        "algorithm": str,           # Algorithm used
        "eatery_info": dict,        # Eatery details
        "weights_used": dict,       # Normalized preference weights
        "open_status": str,         # Current open/closed status
        "distance": float,          # Direct distance in meters
        "metrics": dict             # Performance metrics
    }
    """
    data = request.get_json()
    start = data.get('start')
    algorithm = data.get('algorithm', 'astar').lower()
    preferences = data.get('preferences')
    
    # Validate algorithm parameter
    if algorithm not in ['astar', 'ucs']:
        return jsonify({"error": "Invalid algorithm. Choose 'astar' or 'ucs'"}), 400
        
    # Execute pathfinding
    result = find_optimal_path(start, algorithm, preferences)
    
    # Return appropriate HTTP status code
    if "error" in result:
        return jsonify(result), 400
    else:
        return jsonify(result), 200

@app.route('/top-eateries', methods=['POST'])
@log_request
@validate_json_request(['start'])
def api_top_eateries():
    """
    Get top-ranked eateries based on user preferences
    
    Request Body:
    {
        "start": "NodeID",      # Starting location (required)
        "top_n": int,           # Number of results (default: 3)
        "preferences": {        # User preference rankings (optional)
            "factor": rank,
            ...
        }
    }
    
    Response: Array of eatery objects with ranking information
    """
    data = request.get_json()
    start = data.get('start')
    top_n = data.get('top_n', 3)
    preferences = data.get('preferences')
    
    results = get_top_eateries(start, top_n, preferences)
    
    if isinstance(results, list):
        return jsonify(results), 200
    else:
        return jsonify(results), 400

@app.route('/compare-algorithms', methods=['POST'])
@log_request
@validate_json_request(['start'])
def api_compare_algorithms():
    """
    Compare performance of UCS vs A* algorithms
    
    Request Body:
    {
        "start": "NodeID",      # Starting location (required)
        "preferences": {        # User preference rankings (optional)
            "factor": rank,
            ...
        }
    }
    
    Response:
    {
        "ucs": {               # UCS algorithm results
            "path": [str],
            "cost": float,
            "eatery": str,
            "metrics": dict,
            "total_execution_time": float
        },
        "astar": {             # A* algorithm results
            "path": [str],
            "cost": float,
            "eatery": str,
            "metrics": dict,
            "total_execution_time": float
        }
    }
    """
    data = request.get_json()
    start = data.get('start')
    preferences = data.get('preferences')
    
    results = compare_algorithms(start, preferences)
    
    if "error" in results:
        return jsonify(results), 400
    else:
        return jsonify(results), 200

# =====================
# DATA RETRIEVAL ENDPOINTS
# =====================
@app.route('/graph', methods=['GET'])
@log_request
def api_graph_data():
    """
    Get current graph structure with all nodes and edges
    
    Response:
    {
        "nodes": {
            "NodeID": [lat, lng],
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
    """
    graph_data = get_graph_data()
    
    if "error" in graph_data:
        return jsonify(graph_data), 500
    else:
        return jsonify(graph_data), 200

@app.route('/eateries', methods=['GET'])
@log_request
def api_eatery_list():
    """
    Get all eateries with their attributes
    
    Response:
    {
        "EateryID": {
            "name": str,
            "rating": float,
            "price": int,
            "power_outlet": 0|1,
            "halal_certified": 0|1,
            "wifi": 0|1,
            "aircon": 0|1,
            "hours": str,
            "address": str
        },
        ...
    }
    """
    eateries_data = get_eatery_list()
    
    if "error" in eateries_data:
        return jsonify(eateries_data), 500
    else:
        return jsonify(eateries_data), 200

# =====================
# DYNAMIC GRAPH MANAGEMENT ENDPOINTS
# =====================
@app.route('/graph/nodes', methods=['POST'])
@log_request
@validate_json_request(['id', 'lat', 'lng'])
def api_add_node():
    """
    Add a new node to the graph
    
    Request Body:
    {
        "id": "NodeID",    # Unique node identifier
        "lat": float,      # Latitude (-90 to 90)
        "lng": float       # Longitude (-180 to 180)
    }
    """
    data = request.get_json()
    node_id = data.get('id')
    lat = data.get('lat')
    lng = data.get('lng')
    
    # Load current graph
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    # Add node with validation
    graph, msg = add_node(graph, node_id, lat, lng)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    # Save updated graph
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 201

@app.route('/graph/edges', methods=['POST'])
@log_request
@validate_json_request(['node_a', 'node_b', 'cost'])
def api_add_edge():
    """
    Add a bidirectional edge between two nodes
    
    Request Body:
    {
        "node_a": "NodeID",  # First node
        "node_b": "NodeID",  # Second node
        "cost": float        # Edge weight (positive)
    }
    """
    data = request.get_json()
    node_a = data.get('node_a')
    node_b = data.get('node_b')
    cost = data.get('cost')
    
    # Load current graph
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    # Add edge with validation
    graph, msg = add_edge(graph, node_a, node_b, cost)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    # Save updated graph
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 201

@app.route('/graph/edges', methods=['DELETE'])
@log_request
@validate_json_request(['node_a', 'node_b'])
def api_remove_edge():
    """
    Remove a bidirectional edge between two nodes
    
    Request Body:
    {
        "node_a": "NodeID",  # First node
        "node_b": "NodeID"   # Second node
    }
    """
    data = request.get_json()
    node_a = data.get('node_a')
    node_b = data.get('node_b')
    
    # Load current graph
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    # Remove edge with validation
    graph, msg = remove_edge(graph, node_a, node_b)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    # Save updated graph
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

@app.route('/graph/nodes/<node_id>', methods=['DELETE'])
@log_request
def api_remove_node(node_id):
    """
    Remove a node and all its edges from the graph
    
    URL Parameter:
        node_id: ID of the node to remove
    """
    # Load current graph
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    # Remove node with validation
    graph, msg = remove_node(graph, node_id)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 404
    
    # Save updated graph
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

# =====================
# EATERY MANAGEMENT ENDPOINTS
# =====================
@app.route('/eateries/<eatery_id>', methods=['PUT'])
@log_request
@validate_json_request(['attributes'])
def api_update_eatery(eatery_id):
    """
    Update or create eatery attributes
    
    URL Parameter:
        eatery_id: ID of the eatery to update
        
    Request Body:
    {
        "attributes": {
            "name": str,
            "rating": float (0-5),
            "price": int (0+),
            "power_outlet": bool|int,
            "halal_certified": bool|int,
            "wifi": bool|int,
            "aircon": bool|int,
            "hours": str,
            "address": str
        }
    }
    """
    data = request.get_json()
    attrs = data.get('attributes')
    
    # Load current attributes
    attributes = load_attributes()
    if "error" in attributes:
        return jsonify(attributes), 500
    
    # Update eatery with validation
    attributes, msg = update_eatery(attributes, eatery_id, attrs)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    # Save updated attributes
    save_result = save_attributes(attributes)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

@app.route('/eateries/<eatery_id>', methods=['DELETE'])
@log_request
def api_remove_eatery(eatery_id):
    """
    Remove an eatery and all its attributes
    
    URL Parameter:
        eatery_id: ID of the eatery to remove
    """
    # Load current attributes
    attributes = load_attributes()
    if "error" in attributes:
        return jsonify(attributes), 500
    
    # Remove eatery with validation
    attributes, msg = remove_eatery(attributes, eatery_id)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 404
    
    # Save updated attributes
    save_result = save_attributes(attributes)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

# =====================
# ERROR HANDLERS
# =====================
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({"error": "Method not allowed for this endpoint"}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

# =====================
# SERVER CONFIGURATION AND STARTUP
# =====================
if __name__ == '__main__':
    print("=" * 60)
    print("DLSU Eatery Pathfinder Backend Server")
    print("MCO1: State-Based Pathfinding System")
    print("=" * 60)
    print("Server starting on http://0.0.0.0:5000")
    print("Debug mode: ON")
    print("\nAvailable API endpoints:")
    print("  POST /find-path           - Find optimal path to best eatery")
    print("  POST /top-eateries        - Get ranked list of eateries")
    print("  POST /compare-algorithms  - Compare UCS vs A* performance")
    print("  GET  /graph              - Get current graph structure")
    print("  GET  /eateries           - Get all eatery information")
    print("  POST /graph/nodes        - Add new node to graph")
    print("  POST /graph/edges        - Add new edge to graph")
    print("  DELETE /graph/edges      - Remove edge from graph")
    print("  DELETE /graph/nodes/<id> - Remove node from graph")
    print("  PUT  /eateries/<id>      - Update eatery attributes")
    print("  DELETE /eateries/<id>    - Remove eatery from system")
    print("=" * 60)
    print("Ready to receive requests...")
    
    # Test data loading on startup
    graph = get_graph_data()
    eateries = get_eatery_list()
    
    if "error" in graph:
        print(f"WARNING: Graph loading failed: {graph['error']}")
    else:
        print(f"✓ Graph loaded successfully: {len(graph['nodes'])} nodes, {sum(len(edges) for edges in graph['edges'].values())} edges")
    
    if "error" in eateries:
        print(f"WARNING: Eateries loading failed: {eateries['error']}")
    else:
        print(f"✓ Eateries loaded successfully: {len(eateries)} eateries")
    
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
