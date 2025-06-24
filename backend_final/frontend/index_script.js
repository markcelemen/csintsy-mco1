document.getElementById("form").addEventListener("submit", function (e) {
  e.preventDefault(); 

  const start = document.getElementById("start_point").value;
  const algorithm = document.querySelector('input[name="algo_select"]:checked')?.value;

  const preferences = {
    distance: Number(document.querySelector('[name="distance"]').value) || 0,
    rating: Number(document.querySelector('[name="rating"]').value) || 0,
    price: Number(document.querySelector('[name="price"]').value) || 0,
    wi_fi: Number(document.querySelector('[name="wi_fi"]').value) || 0,
    power_out: Number(document.querySelector('[name="power_out"]').value) || 0,
    halal_cert: Number(document.querySelector('[name="halal_cert"]').value) || 0,
    aircon: Number(document.querySelector('[name="aircon"]').value) || 0,
  };

  fetch("http://localhost:5000/find-path", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ start, algorithm, preferences })
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("End node:", data.goal);
      console.log("path", data.path);
      console.log ("fetch done");

      document.getElementById("end node").textContent = data.goal;
      document.getElementById("distance").textContent = data.distance.toFixed(2);
      document.getElementById("cost").textContent = data.cost.toFixed(2);
        
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
        const coords = window.points[nodeName]; //gets yung long/lat sa map_script 

        if (!coords) {
          console.warn(` No coordinates found for node: "${nodeName}"`); // just in case mali yung input ng name sa map script
          continue;
        }

        const [lat, lon] = coords;
        const x = window.scaleX(lon);
        const y = window.scaleY(lat);

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.stroke();
    } else {
      console.error("Missing path data");
    }
    })
    .catch((err) => console.error("Error:", err));
});