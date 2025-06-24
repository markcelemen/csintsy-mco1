| Attribute | Type | Requirements |
|-----------|------|-------------|
| `name`    | String | Display name |
| `rating` | Float | 0.0-5.0 scale |
| `price` | Integer | 1-3 (price level) |
| `hours` | String | "HH:MM-HH:MM" or "24/7" |
| `power_outlet` | Boolean | Availability |
| `halal_certified` | Boolean | Certification status |
| `wifi` | Boolean | Availability |
| `aircon` | Boolean | Availability |

to test via cmd (backend only):

a. open cmd under backend directory:
 
py -m venv venv

venv\Scripts\activate

pip install Flask flask-cors

python app.py

b. open another cmd under backend directory:

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
