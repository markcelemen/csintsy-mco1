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
      console.log ("fetch done");
    })
    .catch((err) => console.error("Error:", err));
});