from flask import Flask, request, jsonify
from flask_cors import CORS
from algorithms import uniform_cost_search, a_star_search

app = Flask(__name__)
CORS(app)

@app.route("/api/path", methods=["POST"])
def solve_path():
    data = request.get_json()

    graph = data["graph"]
    positions = data["positions"]
    metadata = data["metadata"]
    start = data["start"]
    goals = data["goals"]
    user_type = data.get("user_type", "budget_conscious")  # default to budget conscious

    if start not in graph:
        return jsonify({"error": "Start node not found"}), 400
    if not goals:
        return jsonify({"error": "No goal nodes provided"}), 400

    # Define heuristic weights based on user type
    weights = {
        "foodie": {"alpha": 2.0, "beta": 10.0, "gamma": -7.0, "delta": -0.7},            # 70% rating, 10% price, 20% proximity
        "budget_conscious": {"alpha": 2.0, "beta": 60.0, "gamma": -2.0, "delta": -0.2},     # 20% rating, 60% price, 20% proximity
        "in_a_hurry": {"alpha": 6.0, "beta": 20.0, "gamma": -2.0, "delta": -0.2},           # 60% proximity, 20% price, 20% rating
        "balanced": {"alpha": 3.4, "beta": 33.0, "gamma": -3.3, "delta": -0.33},            # 34% proximity, 33% price, 33% rating
        "luxury_seeker": {"alpha": 4.0, "beta": 10.0, "gamma": -5.0, "delta": -0.5}         # 40% proximity, 10% price, 50% rating
    }.get(user_type, {"alpha": 3.4, "beta": 33.0, "gamma": -3.3, "delta": -0.33})

    ucs_path, ucs_cost = uniform_cost_search(graph, start, goals)
    astar_path, astar_cost = a_star_search(graph, positions, start, goals, metadata, weights)

    return jsonify({
        "ucs": {"path": ucs_path, "cost": ucs_cost},
        "astar": {"path": astar_path, "cost": astar_cost}
    })

if __name__ == "__main__":
    app.run(debug=True)
