
document.getElementById("form").addEventListener("submit", function (e) {
  e.preventDefault();

  const clickedButtonId = e.submitter.id;
  const start = document.getElementById("start_point").value;

  const preferences = {
    distance: Number(document.querySelector('[name="distance"]').value) || 0,
    rating: Number(document.querySelector('[name="rating"]').value) || 0,
    price: Number(document.querySelector('[name="price"]').value) || 0,
    wi_fi: document.querySelector('[name="wi_fi"]').checked ? 1 : 0,
    power_out: document.querySelector('[name="power_out"]').checked ? 1 : 0,
    halal_cert: document.querySelector('[name="halal_cert"]').checked ? 1 : 0,
    aircon: document.querySelector('[name="aircon"]').checked ? 1 : 0,
  };

  if (clickedButtonId === "find_path") {
    const algorithm = document.querySelector('input[name="algo_select"]:checked')?.value;

    const compareHeading = document.getElementById("compare_heading");
    if (algorithm === "ucs") {
      compareHeading.textContent = "Compared with A* Search Algorithm";
    } else if (algorithm === "astar") {
      compareHeading.textContent = "Compared with Uniform Cost Search Algorithm";
    } else {
      compareHeading.textContent = "Compared with ? Algorithm";
    }

    fetch("http://localhost:5000/find-path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ start, algorithm, preferences })
    })
      .then(res => res.json())
      .then(data => {
        console.log("End node:", data.goal);
        console.log("Path:", data.path);

        document.getElementById("performance_heading").textContent =
          `Performance Metrics From ${formatName(start)} to ${formatName(data.goal)}`;
        document.getElementById("distance").textContent = data.distance.toFixed(2);
        document.getElementById("cost").textContent = data.cost.toFixed(2);
        document.getElementById("timecomplex").textContent = data.time_complexity;
        document.getElementById("memcomplex").textContent = data.memory_complexity;

        const canvas = document.getElementById("pathCanvas");
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = "red";
        ctx.lineWidth = 4;

        const path = data.path;
        if (path.length > 1 && window.points && window.scaleX && window.scaleY) {
          ctx.beginPath();
          for (let i = 0; i < path.length; i++) {
            const nodeName = path[i];
            const coords = window.points[nodeName];
            if (!coords) continue;
            const [lat, lon] = coords;
            const x = window.scaleX(lon);
            const y = window.scaleY(lat);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }
          ctx.stroke();
        } else {
          console.error("Missing path data or scale functions.");
        }
      })
      .catch(err => console.error("Fetch error (find path):", err));
  }

  else if (clickedButtonId === "compare_algo") {    
       
    fetch("http://localhost:5000/compare-algorithms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ start, preferences })
    })
      .then(res => res.json())
      .then(data => {
        console.log("Comparison response:", data);

        const algoToShow = "ucs"; // or "astar"
        const result = data[algoToShow];

  
        document.getElementById("compare_eatery").textContent = formatName(result.eatery || "?");
        document.getElementById("compare_distance").textContent =
          result.metrics?.distance?.toFixed(2) || "N/A";
        document.getElementById("compare_cost").textContent = result.cost?.toFixed(2) || "N/A";
        document.getElementById("compare_timecomplex").textContent = result.metrics?.time_complexity || "N/A";
        document.getElementById("compare_memcomplex").textContent = result.metrics?.memory_complexity || "N/A";
      })
      .catch(err => console.error("Fetch error (compare):", err));
  }
});

function formatName(name) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
}

document.addEventListener("DOMContentLoaded", () => {
  // bootstrap modal instance
  const addNodeModal = new bootstrap.Modal(document.getElementById("addNodeModal"));

  document.getElementById("add_node").addEventListener("click", () => {
    addNodeModal.show();
  });

  // Handle form submission
  document.getElementById("submit_add_node").addEventListener("click", () => {
  const nodeId = document.getElementById("node_id").value.trim();
  const lat = parseFloat(document.getElementById("lat").value);
  const lng = parseFloat(document.getElementById("lng").value);
  const price = parseInt(document.getElementById("price").value);
  const rating = parseFloat(document.getElementById("rating").value);
  const name = document.getElementById("name").value.trim();
  const hours = document.getElementById("hours").value.trim();

  const wifi = document.getElementById("wifi").checked ? 1 : 0;
  const power_outlet = document.getElementById("power_out").checked ? 1 : 0;
  const halal_certified = document.getElementById("halal_cert").checked ? 1 : 0;
  const aircon = document.getElementById("aircon").checked ? 1 : 0;

  if (!nodeId || isNaN(lat) || isNaN(lng) || !name || !hours) {
    alert("Please fill out all required fields correctly.");
    return;
  }

  const payload = {
    id: nodeId,
    lat: lat,
    lng: lng,
    attributes: {
      name: name,
      rating: rating,
      price: price,
      hours: hours,
      power_outlet: power_outlet,
      halal_certified: halal_certified,
      wifi: wifi,
      aircon: aircon,
      address: "N/A" // optional field 
    }
  };

  fetch("http://localhost:5000/graph/eatery-nodes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("Error: " + data.error);
        return;
      }
      alert("Node added successfully!");
      window.addNodeToMap(nodeId, lat, lng);
      addNodeModal.hide();
      document.getElementById("addNodeForm").reset();
    })


     const edgeTo = document.getElementById("edge_to").value.trim();
  const edgeCost = parseFloat(document.getElementById("edge_weight").value) || 1;

  if (edgeTo) {
    fetch("http://localhost:5000/graph/edges", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        node_a: nodeId,
        node_b: edgeTo,
        cost: edgeCost
      })
    })
    .then(res => res.json())
    .then(edgeData => {
      if (edgeData.error) {
        console.warn("Edge error:", edgeData.error);
      } else {
        console.log("Edge added:", edgeData.message);
      }
    });
  }

  alert("Node and edge added!");
  window.addNodeToMap(nodeId, lat, lng);
  addNodeModal.hide();
  document.getElementById("addNodeForm").reset();
})
    .catch(err => {
      console.error("Failed to add node:", err);
      alert("Error adding node.");
    });
});



   

