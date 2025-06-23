to test via cmd (backend only):

a. open cmd under backend directory:
 
py -m venv venv

venv\Scripts\activate

pip install Flask flask-cors

python app.py

b. open another cmd under backend directory:

1. Basic Pathfinding Tests

curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{\"start\":\"DLSU_Main_Gate\", \"algorithm\":\"ucs\"}"

curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{\"start\":\"Henry_Sy_Bldg\", \"algorithm\":\"astar\"}"

curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{\"start\":\"St_Joseph_Bldg\", \"preferences\":{\"distance\":1,\"rating\":2}}"

2. Top Eateries Ranking

curl -X POST http://localhost:5000/top-eateries -H "Content-Type: application/json" -d "{\"start\":\"DLSU_Main_Gate\"}"

curl -X POST http://localhost:5000/top-eateries -H "Content-Type: application/json" -d "{\"start\":\"Andrew_Building\", \"top_n\":5, \"preferences\":{\"halal_certified\":1}}"

3. Algorithm Comparison

curl -X POST http://localhost:5000/compare-algorithms -H "Content-Type: application/json" -d "{\"start\":\"DLSU_Main_Gate\"}"

curl -X POST http://localhost:5000/compare-algorithms -H "Content-Type: application/json" -d "{\"start\":\"Greenwich_DLSU\", \"preferences\":{\"price\":1}}"

4. Graph Modification Tests

curl -X POST http://localhost:5000/graph/nodes -H "Content-Type: application/json" -d "{\"id\":\"Cafeteria\", \"lat\":14.5658, \"lng\":120.9965}"

curl -X POST http://localhost:5000/graph/edges -H "Content-Type: application/json" -d "{\"node_a\":\"Andrew_Building\", \"node_b\":\"Cafeteria\", \"cost\":25.0}"

curl http://localhost:5000/graph

curl -X DELETE http://localhost:5000/graph/edges -H "Content-Type: application/json" -d "{\"node_a\":\"Andrew_Building\", \"node_b\":\"Cafeteria\"}"

curl -X DELETE http://localhost:5000/graph/nodes/Cafeteria

5. Eatery Management Tests

curl -X PUT http://localhost:5000/eateries/McDonalds_DLSU -H "Content-Type: application/json" -d "{\"attributes\":{\"wifi\":0}}"

curl http://localhost:5000/eateries

curl -X DELETE http://localhost:5000/eateries/Bacsilog_King

curl http://localhost:5000/eateries

6. Error Handling Tests

curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{\"start\":\"Unknown_Location\"}"

curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{\"start\":\"DLSU_Main_Gate\", \"algorithm\":\"dfs\"}"

curl -X POST http://localhost:5000/find-path -H "Content-Type: application/json" -d "{}"
