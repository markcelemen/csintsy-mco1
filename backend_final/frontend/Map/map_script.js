window.points = {
      "DLSU_Main_Gate": [14.5645, 120.9932],
      "Andrew_Building": [14.5652, 120.9940],
      "Henry_Sy_Bldg": [14.5660, 120.9955],
      "St_Joseph_Bldg": [14.5650, 120.9968],
      "Chowking_DLSU": [14.5648, 120.9975],
      "Starbucks_DLSU": [14.5665, 120.9980],
      "McDonalds_DLSU": [14.5672, 120.9965],
      "Greenwich_DLSU": [14.5670, 120.9950],
      "Halal_Street": [14.5655, 120.9985],
      "Study_Cafe": [14.5662, 120.9945],
      "KFC_DLSU": [14.5675, 120.9970],
      "Bacsilog_King": [14.5638, 120.9925]
    };

    const latMin = 14.5638, latMax = 14.5675;
    const lonMin = 120.9925, lonMax = 120.9985;

    const mapWidth = 1900, mapHeight = 600;
    const margin = 75; //padding sa edges

    window.scaleX = (lon) => margin + ((lon - lonMin) / (lonMax - lonMin)) * (mapWidth - 2 * margin) *0.55;
    window.scaleY = (lat) => margin + ((latMax - lat) / (latMax - latMin)) * (mapHeight - 2 * margin) * 0.6; 

    const map = document.getElementById("map");

    for (const name in points) {
      const [lat, lon] = points[name];
      const x = scaleX(lon);
      const y = scaleY(lat);

      const node = document.createElement("div");
      node.className = "node";
      node.style.left = `${x}px`;
      node.style.top = `${y}px`;
      node.textContent = name;
      map.appendChild(node);
    }

