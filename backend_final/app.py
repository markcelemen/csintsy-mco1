"""
DLSU Eatery Pathfinder - Flask API Server

Endpoints:
- Pathfinding using UCS and A*
- Dynamic graph management
- Eatery preference scoring
- Algorithm comparison
"""

from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from functools import wraps
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
    add_eatery_node,
    load_graph,
    save_graph,
    load_attributes,
    save_attributes,
    compare_algorithms,
    add_eatery_node  
)
import time
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        logging.info(f"Request: {request.method} {request.path}")
        
        result = f(*args, **kwargs)
        
        elapsed = round((time.time() - start_time) * 1000, 2)
        logging.info(f"Response: {result[1]} in {elapsed}ms")
        return result
    return decorated_function

def validate_json(required_fields=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"error": "Invalid JSON"}), 400
                
            if required_fields:
                missing = [f for f in required_fields if f not in data]
                if missing:
                    return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator

# =====================
# CORE ENDPOINTS
# =====================
@app.route('/find-path', methods=['POST'])
@log_request
@validate_json(['start'])
def api_find_path():
    data = request.get_json()
    result = find_optimal_path(
        data['start'],
        data.get('algorithm', 'astar'),
        data.get('preferences')
    )
    return jsonify(result), 400 if "error" in result else 200

@app.route('/top-eateries', methods=['POST'])
@log_request
@validate_json(['start'])
def api_top_eateries():
    data = request.get_json()
    result = get_top_eateries(
        data['start'],
        data.get('top_n', 3),
        data.get('preferences')
    )
    if isinstance(result, list):
        return jsonify(result), 200
    return jsonify(result), 400

@app.route('/compare-algorithms', methods=['POST'])
@log_request
@validate_json(['start'])
def api_compare_algorithms():
    data = request.get_json()
    result = compare_algorithms(data['start'], data.get('preferences'))
    return jsonify(result), 400 if "error" in result else 200

# =====================
# DATA ENDPOINTS
# =====================
@app.route('/graph', methods=['GET'])
@log_request
def api_graph_data():
    data = get_graph_data()
    return jsonify(data), 500 if "error" in data else 200

@app.route('/eateries', methods=['GET'])
@log_request
def api_eatery_list():
    data = get_eatery_list()
    return jsonify(data), 500 if "error" in data else 200

# =====================
# DYNAMIC UPDATES
# =====================
@app.route('/graph/nodes', methods=['POST'])
@log_request
@validate_json(['id', 'lat', 'lng'])
def api_add_node():
    data = request.get_json()
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    graph, msg = add_node(graph, data['id'], data['lat'], data['lng'])
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 201

@app.route('/graph/edges', methods=['POST'])
@log_request
@validate_json(['node_a', 'node_b', 'cost'])
def api_add_edge():
    data = request.get_json()
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    graph, msg = add_edge(graph, data['node_a'], data['node_b'], data['cost'])
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 201

@app.route('/graph/edges', methods=['DELETE'])
@log_request
@validate_json(['node_a', 'node_b'])
def api_remove_edge():
    data = request.get_json()
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    graph, msg = remove_edge(graph, data['node_a'], data['node_b'])
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

@app.route('/graph/nodes/<node_id>', methods=['DELETE'])
@log_request
def api_remove_node(node_id):
    graph = load_graph()
    if "error" in graph:
        return jsonify(graph), 500
    
    graph, msg = remove_node(graph, node_id)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 404
    
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

@app.route('/eateries/<eatery_id>', methods=['PUT'])
@log_request
@validate_json(['attributes'])
def api_update_eatery(eatery_id):
    data = request.get_json()
    attributes = load_attributes()
    if "error" in attributes:
        return jsonify(attributes), 500
    
    attributes, msg = update_eatery(attributes, eatery_id, data['attributes'])
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    save_result = save_attributes(attributes)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

@app.route('/eateries/<eatery_id>', methods=['DELETE'])
@log_request
def api_remove_eatery(eatery_id):
    attributes = load_attributes()
    if "error" in attributes:
        return jsonify(attributes), 500
    
    attributes, msg = remove_eatery(attributes, eatery_id)
    if "error" in msg.lower():
        return jsonify({"error": msg}), 404
    
    save_result = save_attributes(attributes)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 200

# =====================
# ATOMIC EATERY CREATION
# =====================
@app.route('/graph/eatery-nodes', methods=['POST'])
@log_request
@validate_json(['id', 'lat', 'lng', 'attributes'])
def api_add_eatery_node():
    data = request.get_json()
    
    # Load both datasets
    graph = load_graph()
    attributes = load_attributes()
    
    if "error" in graph:
        return jsonify({"error": graph["error"]}), 500
    if "error" in attributes:
        return jsonify({"error": attributes["error"]}), 500
    
    # Call atomic operation
    graph, attributes, msg = add_eatery_node(
        graph,
        attributes,
        data['id'],
        data['lat'],
        data['lng'],
        data['attributes']
    )
    
    if "error" in msg.lower():
        return jsonify({"error": msg}), 400
    
    # Save both datasets
    save_result = save_graph(graph)
    if save_result is not True:
        return jsonify(save_result), 500
    
    save_result = save_attributes(attributes)
    if save_result is not True:
        return jsonify(save_result), 500
    
    return jsonify({"message": msg}), 201
    
# =====================
# ERROR HANDLERS
# =====================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# =====================
# SERVER STARTUP
# =====================
if __name__ == '__main__':
    print("DLSU Eatery Pathfinder Backend")
    print("Server starting on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
