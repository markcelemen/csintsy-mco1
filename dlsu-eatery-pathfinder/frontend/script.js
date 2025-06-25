// Global variables
let campusGraph = null;
let campusEateries = null;
let mapNodes = {};
let activeScreen = 'dashboard';
let currentZoom = 1;

// DOM Elements
const screens = {
    dashboard: document.getElementById('dashboardScreen'),
    pathfinder: document.getElementById('pathfinderScreen'),
    top: document.getElementById('topScreen'),
    graph: document.getElementById('graphScreen'),
    eatery: document.getElementById('eateryScreen')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Setup navigation
    setupNavigation();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadInitialData();
    
    // Setup slider value displays
    setupSliders();
});

function setupNavigation() {
    // Navigation buttons
    document.getElementById('dashboardBtn').addEventListener('click', () => showScreen('dashboard'));
    document.getElementById('pathfinderBtn').addEventListener('click', () => showScreen('pathfinder'));
    document.getElementById('topBtn').addEventListener('click', () => showScreen('top'));
    document.getElementById('graphBtn').addEventListener('click', () => showScreen('graph'));
    document.getElementById('eateryBtn').addEventListener('click', () => showScreen('eatery'));
    
    // Quick action buttons
    document.getElementById('quickPathfinder').addEventListener('click', () => showScreen('pathfinder'));
    document.getElementById('quickTop').addEventListener('click', () => showScreen('top'));
}

function setupEventListeners() {
    // Pathfinder
    document.getElementById('findPathBtn').addEventListener('click', findOptimalPath);
    document.getElementById('resetPathBtn').addEventListener('click', resetPathfinder);
    
    // Top Eateries
    document.getElementById('findTopBtn').addEventListener('click', findTopEateries);
    
    // Dashboard
    document.getElementById('refreshMap').addEventListener('click', renderCampusMap);
    
    // Graph Management
    document.getElementById('addNodeBtn').addEventListener('click', addNewNode);
    document.getElementById('addEateryNodeBtn').addEventListener('click', openEateryCreation);
    document.getElementById('removeNodeBtn').addEventListener('click', removeSelectedNode);
    document.getElementById('addEdgeBtn').addEventListener('click', addNewEdge);
    document.getElementById('removeEdgeBtn').addEventListener('click', removeSelectedEdge);
    
    // Eatery Management
    document.getElementById('eaterySelect').addEventListener('change', loadEateryDetails);
    document.getElementById('saveEateryBtn').addEventListener('click', saveEateryChanges);
    document.getElementById('removeEateryBtn').addEventListener('click', removeSelectedEatery);
    document.getElementById('resetEateryBtn').addEventListener('click', resetEateryForm);
    document.getElementById('createEateryBtn').addEventListener('click', createNewEatery);
    
    // Eatery creation form
    document.getElementById('newEateryRating').addEventListener('input', () => {
        document.getElementById('newRatingValue').textContent = 
            document.getElementById('newEateryRating').value;
    });
    
    // Zoom controls
    document.getElementById('zoomInBtn').addEventListener('click', () => zoomMap(1.2));
    document.getElementById('zoomOutBtn').addEventListener('click', () => zoomMap(0.8));
    document.getElementById('resetZoomBtn').addEventListener('click', resetMapZoom);
}

function setupSliders() {
    // Pathfinder sliders
    setupSlider('distancePref', 'distanceValue');
    setupSlider('ratingPref', 'ratingValue');
    setupSlider('pricePref', 'priceValue');
    setupSlider('outletPref', 'outletValue');
    setupSlider('halalPref', 'halalValue');
    setupSlider('wifiPref', 'wifiValue');
    setupSlider('airconPref', 'airconValue');
    
    // Top Eateries sliders
    setupSlider('topDistance', null, true);
    setupSlider('topRating', null, true);
    setupSlider('topPrice', null, true);
    setupSlider('topOutlet', null, true);
    setupSlider('topHalal', null, true);
    setupSlider('topWifi', null, true);
    setupSlider('topAircon', null, true);
}

function setupSlider(sliderId, valueId, compact = false) {
    const slider = document.getElementById(sliderId);
    const valueDisplay = valueId ? document.getElementById(valueId) : slider.nextElementSibling;
    
    // Set initial value
    if (valueDisplay) {
        valueDisplay.textContent = slider.value;
    } else if (compact) {
        slider.nextElementSibling.textContent = slider.value;
    }
    
    // Update on change
    slider.addEventListener('input', () => {
        if (valueDisplay) {
            valueDisplay.textContent = slider.value;
        } else if (compact) {
            slider.nextElementSibling.textContent = slider.value;
        }
    });
}

function showScreen(screenName) {
    // Hide all screens
    Object.values(screens).forEach(screen => screen.classList.add('hidden'));
    
    // Show selected screen
    screens[screenName].classList.remove('hidden');
    activeScreen = screenName;
    
    // Update active nav button
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${screenName}Btn`).classList.add('active');
    
    // Screen-specific initialization
    if (screenName === 'dashboard') {
        renderCampusMap();
    } else if (screenName === 'pathfinder') {
        initPathfinder();
    } else if (screenName === 'top') {
        initTopEateries();
    } else if (screenName === 'graph') {
        initGraphManagement();
    } else if (screenName === 'eatery') {
        initEateryManagement();
    }
}

function loadInitialData() {
    // Fetch graph data
    fetch('http://localhost:5000/graph')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading graph:', data.error);
                return;
            }
            campusGraph = data;
            renderCampusMap();
            populateLocationDropdowns();
            updateStats();
        })
        .catch(error => console.error('Error loading graph:', error));
    
    // Fetch eatery data
    fetch('http://localhost:5000/eateries')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading eateries:', data.error);
                return;
            }
            campusEateries = data;
            updateStats();
        })
        .catch(error => console.error('Error loading eateries:', error));
}

function populateLocationDropdowns() {
    if (!campusGraph || !campusGraph.nodes) return;
    
    const locationSelectors = [
        document.getElementById('startLocation'),
        document.getElementById('topStart')
    ];
    
    locationSelectors.forEach(selector => {
        // Clear existing options except the first
        while (selector.options.length > 1) {
            selector.remove(1);
        }
        
        // Add new options
        Object.keys(campusGraph.nodes).forEach(nodeId => {
            const option = document.createElement('option');
            option.value = nodeId;
            option.textContent = formatNodeName(nodeId);
            selector.appendChild(option);
        });
    });
}

function updateStats() {
    if (campusGraph && campusGraph.nodes) {
        // Count actual eateries
        const eateryCount = Object.keys(campusEateries || {}).length;
        document.getElementById('eateryCount').textContent = eateryCount;
        
        // Count actual paths
        let pathCount = 0;
        if (campusGraph.edges) {
            for (const node in campusGraph.edges) {
                pathCount += Object.keys(campusGraph.edges[node]).length;
            }
            // Since edges are bidirectional, divide by 2
            pathCount = Math.floor(pathCount / 2);
        }
        document.getElementById('pathCount').textContent = pathCount;
    }
}

function renderCampusMap() {
    const map = document.getElementById('map');
    const canvas = document.getElementById('pathCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Clear previous nodes by class name
    document.querySelectorAll('.node').forEach(node => node.remove());
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (!campusGraph || !campusGraph.nodes) return;
    
    // Extract coordinates to calculate min/max
    const lats = Object.values(campusGraph.nodes).map(coord => coord[0]);
    const lons = Object.values(campusGraph.nodes).map(coord => coord[1]);
    
    const latMin = Math.min(...lats);
    const latMax = Math.max(...lats);
    const lonMin = Math.min(...lons);
    const lonMax = Math.max(...lons);
    
    // Set canvas dimensions to match container
    canvas.width = map.clientWidth;
    canvas.height = map.clientHeight;
    
    // Calculate scaling factors with 5% margin
    const mapWidth = canvas.width;
    const mapHeight = canvas.height;
    const margin = Math.min(mapWidth, mapHeight) * 0.05; // 5% margin
    
    const scaleX = lon => margin + ((lon - lonMin) / (lonMax - lonMin)) * (mapWidth - 2 * margin);
    const scaleY = lat => margin + ((latMax - lat) / (latMax - latMin)) * (mapHeight - 2 * margin);
    
    // Draw edges first
    ctx.strokeStyle = '#5a7d1c';
    ctx.lineWidth = 2;
    ctx.font = 'bold 12px Arial';
    ctx.fillStyle = '#000';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    if (campusGraph.edges) {
        Object.entries(campusGraph.edges).forEach(([fromNode, edges]) => {
            const fromCoords = campusGraph.nodes[fromNode];
            if (!fromCoords) return;
            
            Object.entries(edges).forEach(([toNode, cost]) => {
                const toCoords = campusGraph.nodes[toNode];
                if (!toCoords) return;
                
                const x1 = scaleX(fromCoords[1]);
                const y1 = scaleY(fromCoords[0]);
                const x2 = scaleX(toCoords[1]);
                const y2 = scaleY(toCoords[0]);
                
                // Draw path
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
                
                // Draw cost in the middle of the path
                const midX = (x1 + x2) / 2;
                const midY = (y1 + y2) / 2;
                
                // Draw background for better readability
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.fillRect(midX - 20, midY - 10, 40, 20);
                
                // Draw cost text
                ctx.fillStyle = '#000';
                ctx.fillText(`${cost.toFixed(1)}m`, midX, midY);
            });
        });
    }
    
    // Create and position nodes
    Object.entries(campusGraph.nodes).forEach(([nodeId, coords]) => {
        const x = scaleX(coords[1]);
        const y = scaleY(coords[0]);
        
        const node = document.createElement('div');
        node.className = 'node';
        node.style.left = `${x}px`;
        node.style.top = `${y}px`;
        
        node.textContent = campusEateries && campusEateries[nodeId]?.name
        ? campusEateries[nodeId].name
        : formatNodeName(nodeId);

        node.dataset.nodeId = nodeId;
        
        // Add eatery class if this node has eatery data
        if (campusEateries && campusEateries[nodeId]) {
            node.classList.add('eatery');
        }
        
        node.addEventListener('click', () => {
            // Highlight node on click
            document.querySelectorAll('.node').forEach(n => n.classList.remove('selected'));
            node.classList.add('selected');
        });
        
        map.appendChild(node);
    });
    
    // Reset zoom
    resetMapZoom();
}

function zoomMap(factor) {
    currentZoom *= factor;
    const map = document.getElementById('map');
    map.style.transform = `scale(${currentZoom})`;
    map.style.transformOrigin = 'center';
}

function resetMapZoom() {
    currentZoom = 1;
    document.getElementById('map').style.transform = 'scale(1)';
}

function initPathfinder() {
    // Set default start location if none selected
    const startSelect = document.getElementById('startLocation');
    if (!startSelect.value && startSelect.options.length > 1) {
        startSelect.value = startSelect.options[1].value;
    }
}

function findOptimalPath() {
    const startLocation = document.getElementById('startLocation').value;
    if (!startLocation) {
        alert('Please select a start location');
        return;
    }
    
    const algorithm = document.querySelector('input[name="algorithm"]:checked').value;
    
    // Collect preferences
    const preferences = {
        distance: parseInt(document.getElementById('distancePref').value),
        rating: parseInt(document.getElementById('ratingPref').value),
        price: parseInt(document.getElementById('pricePref').value),
        power_outlet: parseInt(document.getElementById('outletPref').value),
        halal_certified: parseInt(document.getElementById('halalPref').value),
        wifi: parseInt(document.getElementById('wifiPref').value),
        aircon: parseInt(document.getElementById('airconPref').value)
    };
    
    // Show loading state
    const eateryDetails = document.getElementById('eateryDetails');
    eateryDetails.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Finding optimal path...</div>';
    
    // Make API request
    fetch('http://localhost:5000/find-path', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start: startLocation,
            algorithm: algorithm,
            preferences: preferences
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display results
        displayPathfinderResults(data);
    })
    .catch(error => {
        console.error('Error:', error);
        eateryDetails.innerHTML = `<div class="error">${error.message || 'Failed to find path'}</div>`;
    });
}

function displayPathfinderResults(data) {
    // Update metrics
    document.getElementById('pathCost').textContent = data.cost.toFixed(2);
    document.getElementById('executionTime').textContent = `${data.metrics.execution_time_ms} ms`;
    document.getElementById('nodesExpanded').textContent = data.metrics.nodes_expanded;
    document.getElementById('frontierSize').textContent = data.metrics.max_frontier_size;
    
    // Display eatery details
    const eateryDetails = document.getElementById('eateryDetails');
    eateryDetails.innerHTML = `
        <div class="eatery-header">
            <h4>${data.eatery_info.name || formatNodeName(data.goal)}</h4>
            <span class="badge ${data.open_status === 'Open' ? 'status-open' : 'status-closed'}">
                ${data.open_status}
            </span>
        </div>
        <div class="eatery-detail">
            <h4>Rating</h4>
            <div class="rating-stars">
                ${renderStars(data.eatery_info.rating || 0)}
            </div>
            <p>${(data.eatery_info.rating || 0).toFixed(1)}/5.0</p>
        </div>
        <div class="eatery-detail">
            <h4>Price Level</h4>
            <p>${renderPriceLevel(data.eatery_info.price || 0)}</p>
        </div>
        <div class="eatery-detail">
            <h4>Distance</h4>
            <p>${data.distance.toFixed(1)} meters</p>
        </div>
        <div class="eatery-detail">
            <h4>Amenities</h4>
            <div class="amenities">
                <span class="amenity ${data.eatery_info.wifi ? 'available' : ''}">
                    <i class="fas fa-wifi"></i> WiFi
                </span>
                <span class="amenity ${data.eatery_info.power_outlet ? 'available' : ''}">
                    <i class="fas fa-plug"></i> Outlets
                </span>
                <span class="amenity ${data.eatery_info.aircon ? 'available' : ''}">
                    <i class="fas fa-wind"></i> Aircon
                </span>
                <span class="amenity ${data.eatery_info.halal_certified ? 'available' : ''}">
                    <i class="fas fa-certificate"></i> Halal
                </span>
            </div>
        </div>
        <div class="eatery-detail">
            <h4>Hours</h4>
            <p>${data.eatery_info.hours || 'Not specified'}</p>
        </div>
    `;
    
    // Visualize path
    visualizePath(data.path, 'pathMapCanvas', '#28a745');
}

function renderStars(rating) {
    let stars = '';
    const fullStars = Math.floor(rating);
    const halfStar = rating % 1 >= 0.5;
    
    for (let i = 0; i < fullStars; i++) {
        stars += '<i class="fas fa-star"></i>';
    }
    
    if (halfStar) {
        stars += '<i class="fas fa-star-half-alt"></i>';
    }
    
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
    for (let i = 0; i < emptyStars; i++) {
        stars += '<i class="far fa-star"></i>';
    }
    
    return stars;
}

function renderPriceLevel(price) {
    return '$'.repeat(price) + ' '.repeat(3 - price); // Using spaces for alignment
}

function visualizePath(path, canvasId, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (!campusGraph || !campusGraph.nodes || !path || path.length === 0) return;
    
    // Extract coordinates to calculate min/max
    const lats = Object.values(campusGraph.nodes).map(coord => coord[0]);
    const lons = Object.values(campusGraph.nodes).map(coord => coord[1]);
    
    const latMin = Math.min(...lats);
    const latMax = Math.max(...lats);
    const lonMin = Math.min(...lons);
    const lonMax = Math.max(...lons);
    
    // Calculate scaling factors
    const mapWidth = canvas.width;
    const mapHeight = canvas.height;
    const margin = 50;
    
    const scaleX = lon => margin + ((lon - lonMin) / (lonMax - lonMin)) * (mapWidth - 2 * margin);
    const scaleY = lat => margin + ((latMax - lat) / (latMax - latMin)) * (mapHeight - 2 * margin);
    
    // Draw edges
    ctx.strokeStyle = '#5a7d1c';
    ctx.lineWidth = 2;
    
    if (campusGraph.edges) {
        Object.entries(campusGraph.edges).forEach(([fromNode, edges]) => {
            const fromCoords = campusGraph.nodes[fromNode];
            if (!fromCoords) return;
            
            Object.keys(edges).forEach(toNode => {
                const toCoords = campusGraph.nodes[toNode];
                if (!toCoords) return;
                
                const x1 = scaleX(fromCoords[1]);
                const y1 = scaleY(fromCoords[0]);
                const x2 = scaleX(toCoords[1]);
                const y2 = scaleY(toCoords[0]);
                
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
            });
        });
    }
    
    // Draw the path
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.beginPath();
    
    for (let i = 0; i < path.length; i++) {
        const nodeId = path[i];
        const coords = campusGraph.nodes[nodeId];
        if (!coords) continue;
        
        const x = scaleX(coords[1]);
        const y = scaleY(coords[0]);
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    
    ctx.stroke();
    
    // Draw nodes
    path.forEach((nodeId, index) => {
        const coords = campusGraph.nodes[nodeId];
        if (!coords) return;
        
        const x = scaleX(coords[1]);
        const y = scaleY(coords[0]);
        
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        
        if (index === 0) {
            ctx.fillStyle = '#28a745'; // Start node (green)
        } else if (index === path.length - 1) {
            ctx.fillStyle = '#dc3545'; // Goal node (red)
        } else {
            ctx.fillStyle = '#007bff'; // Intermediate node (blue)
        }
        
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw node label
        ctx.fillStyle = '#000';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(formatNodeName(nodeId), x, y + 25);
    });
}

function resetPathfinder() {
    // Reset sliders to default values
    document.getElementById('distancePref').value = 5;
    document.getElementById('ratingPref').value = 8;
    document.getElementById('pricePref').value = 7;
    document.getElementById('outletPref').value = 6;
    document.getElementById('halalPref').value = 5;
    document.getElementById('wifiPref').value = 7;
    document.getElementById('airconPref').value = 9;
    
    // Update displayed values
    document.getElementById('distanceValue').textContent = '5';
    document.getElementById('ratingValue').textContent = '8';
    document.getElementById('priceValue').textContent = '7';
    document.getElementById('outletValue').textContent = '6';
    document.getElementById('halalValue').textContent = '5';
    document.getElementById('wifiValue').textContent = '7';
    document.getElementById('airconValue').textContent = '9';
    
    // Clear results
    document.getElementById('pathCost').textContent = '-';
    document.getElementById('executionTime').textContent = '-';
    document.getElementById('nodesExpanded').textContent = '-';
    document.getElementById('frontierSize').textContent = '-';
    
    const eateryDetails = document.getElementById('eateryDetails');
    eateryDetails.innerHTML = '<p class="placeholder">Pathfinder results will appear here</p>';
    
    // Clear path visualization
    const canvas = document.getElementById('pathMapCanvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
}

function initTopEateries() {
    // Set default start location if none selected
    const startSelect = document.getElementById('topStart');
    if (!startSelect.value && startSelect.options.length > 1) {
        startSelect.value = startSelect.options[1].value;
    }
}

function findTopEateries() {
    const startLocation = document.getElementById('topStart').value;
    if (!startLocation) {
        alert('Please select a start location');
        return;
    }
    
    const topN = parseInt(document.getElementById('resultCount').value);
    
    // Collect preferences
    const preferences = {
        distance: parseInt(document.getElementById('topDistance').value),
        rating: parseInt(document.getElementById('topRating').value),
        price: parseInt(document.getElementById('topPrice').value),
        power_outlet: parseInt(document.getElementById('topOutlet').value),
        halal_certified: parseInt(document.getElementById('topHalal').value),
        wifi: parseInt(document.getElementById('topWifi').value),
        aircon: parseInt(document.getElementById('topAircon').value)
    };
    
    // Show loading state
    const resultsContainer = document.getElementById('rankingResults');
    resultsContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Finding top eateries...</div>';
    
    // Make API request
    fetch('http://localhost:5000/top-eateries', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start: startLocation,
            top_n: topN,
            preferences: preferences
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display results
        displayTopEateries(data);
    })
    .catch(error => {
        console.error('Error:', error);
        resultsContainer.innerHTML = `<div class="error">${error.message || 'Failed to find top eateries'}</div>`;
    });
}

function displayTopEateries(eateries) {
    const resultsContainer = document.getElementById('rankingResults');
    
    if (!eateries || eateries.length === 0) {
        resultsContainer.innerHTML = '<div class="placeholder-row"><i class="fas fa-utensils"></i><p>No eateries found matching your criteria</p></div>';
        return;
    }
    
    let html = '';
    
    eateries.forEach(eatery => {
        html += `
            <div class="ranking-item">
                <div class="rank-col">${eatery.rank}</div>
                <div class="name-col">${eatery.name || formatNodeName(eatery.id)}</div>
                <div class="score-col">${eatery.score.toFixed(2)}</div>
                <div class="distance-col">${eatery.distance_meters.toFixed(1)} m</div>
                <div class="status-col ${eatery.open_status === 'Open' ? 'status-open' : 'status-closed'}">
                    ${eatery.open_status}
                </div>
                <div class="actions-col">
                    <button class="btn btn-sm btn-outline-primary view-details" data-id="${eatery.id}">
                        <i class="fas fa-info-circle"></i> Details
                    </button>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    
    // Add event listeners to details buttons
    document.querySelectorAll('.view-details').forEach(button => {
        button.addEventListener('click', () => {
            const eateryId = button.dataset.id;
            showEateryDetails(eateryId);
        });
    });
}

function showEateryDetails(eateryId) {
    // Find eatery in the list
    const eatery = campusEateries[eateryId];
    if (!eatery) return;
    
    const modalTitle = document.getElementById('eateryDetailTitle');
    const modalContent = document.getElementById('eateryDetailContent');
    
    modalTitle.textContent = eatery.name || formatNodeName(eateryId);
    
    modalContent.innerHTML = `
        <div class="eatery-detail-card">
            <div class="detail-row">
                <span class="detail-label">Rating:</span>
                <span class="detail-value">${eatery.rating} ${renderStars(eatery.rating)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Price Level:</span>
                <span class="detail-value">${renderPriceLevel(eatery.price)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Hours:</span>
                <span class="detail-value">${eatery.hours || 'Not specified'}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Address:</span>
                <span class="detail-value">${eatery.address || 'Not specified'}</span>
            </div>
            <div class="amenities-grid">
                <div class="amenity ${eatery.power_outlet ? 'available' : ''}">
                    <i class="fas fa-plug"></i> Power Outlets
                </div>
                <div class="amenity ${eatery.halal_certified ? 'available' : ''}">
                    <i class="fas fa-certificate"></i> Halal Certified
                </div>
                <div class="amenity ${eatery.wifi ? 'available' : ''}">
                    <i class="fas fa-wifi"></i> WiFi
                </div>
                <div class="amenity ${eatery.aircon ? 'available' : ''}">
                    <i class="fas fa-wind"></i> Air Conditioning
                </div>
            </div>
        </div>
    `;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('eateryDetailModal'));
    modal.show();
}

function initGraphManagement() {
    // Populate node dropdowns
    populateNodeDropdowns();
}

function populateNodeDropdowns() {
    if (!campusGraph || !campusGraph.nodes) return;
    
    const dropdowns = [
        document.getElementById('removeNodeSelect'),
        document.getElementById('edgeNodeA'),
        document.getElementById('edgeNodeB'),
        document.getElementById('removeEdgeNodeA'),
        document.getElementById('removeEdgeNodeB')
    ];
    
    dropdowns.forEach(dropdown => {
        // Clear existing options except the first
        while (dropdown.options.length > 1) {
            dropdown.remove(1);
        }
        
        // Add new options
        Object.keys(campusGraph.nodes).forEach(nodeId => {
            const option = document.createElement('option');
            option.value = nodeId;
            option.textContent = formatNodeName(nodeId);
            dropdown.appendChild(option);
        });
    });
}

function addNewNode() {
    const nodeId = document.getElementById('nodeId').value.trim();
    const lat = parseFloat(document.getElementById('nodeLat').value);
    const lng = parseFloat(document.getElementById('nodeLng').value);
    
    if (!nodeId || isNaN(lat) || isNaN(lng)) {
        alert('Please fill all fields with valid values');
        return;
    }
    
    // Add node to graph
    fetch('http://localhost:5000/graph/nodes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id: nodeId,
            lat: lat,
            lng: lng
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Reload graph data
        loadInitialData();
        alert('Node added successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Failed to add node: ${error.message}`);
    });
}

function openEateryCreation() {
    const modal = new bootstrap.Modal(document.getElementById('eateryCreationModal'));
    modal.show();
}

function createNewEatery() {
    const nodeId = document.getElementById('newEateryId').value.trim();
    const lat = parseFloat(document.getElementById('newEateryLat').value);
    const lng = parseFloat(document.getElementById('newEateryLng').value);
    const name = document.getElementById('newEateryName').value.trim();
    
    if (!nodeId || isNaN(lat) || isNaN(lng) || !name) {
        alert('Please fill all required fields');
        return;
    }
    
    const eateryData = {
        name: name,
        rating: parseFloat(document.getElementById('newEateryRating').value),
        price: parseInt(document.getElementById('newEateryPrice').value),
        hours: document.getElementById('newEateryHours').value.trim(),
        address: document.getElementById('newEateryAddress').value.trim(),
        power_outlet: document.getElementById('newEateryPower').checked ? 1 : 0,
        halal_certified: document.getElementById('newEateryHalal').checked ? 1 : 0,
        wifi: document.getElementById('newEateryWifi').checked ? 1 : 0,
        aircon: document.getElementById('newEateryAircon').checked ? 1 : 0
    };
    
    // First add the node
    fetch('http://localhost:5000/graph/nodes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id: nodeId,
            lat: lat,
            lng: lng
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Then add eatery attributes
        return fetch(`http://localhost:5000/eateries/${nodeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                attributes: eateryData
            })
        });
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Reload data and close modal
        loadInitialData();
        bootstrap.Modal.getInstance(document.getElementById('eateryCreationModal')).hide();
        alert('Eatery created successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Failed to create eatery: ${error.message}`);
    });
}

function removeSelectedNode() {
    const nodeId = document.getElementById('removeNodeSelect').value;
    if (!nodeId) {
        alert('Please select a node to remove');
        return;
    }
    
    if (confirm(`Are you sure you want to remove node ${nodeId}? This cannot be undone.`)) {
        fetch(`http://localhost:5000/graph/nodes/${nodeId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Reload graph data
            loadInitialData();
            alert('Node removed successfully!');
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Failed to remove node: ${error.message}`);
        });
    }
}

function addNewEdge() {
    const nodeA = document.getElementById('edgeNodeA').value;
    const nodeB = document.getElementById('edgeNodeB').value;
    const cost = parseFloat(document.getElementById('edgeCost').value);
    
    if (!nodeA || !nodeB || isNaN(cost) || cost <= 0) {
        alert('Please select two nodes and enter a valid cost');
        return;
    }
    
    if (nodeA === nodeB) {
        alert('Cannot create edge between the same node');
        return;
    }
    
    fetch('http://localhost:5000/graph/edges', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            node_a: nodeA,
            node_b: nodeB,
            cost: cost
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Reload graph data
        loadInitialData();
        alert('Edge added successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Failed to add edge: ${error.message}`);
    });
}

function removeSelectedEdge() {
    const nodeA = document.getElementById('removeEdgeNodeA').value;
    const nodeB = document.getElementById('removeEdgeNodeB').value;
    
    if (!nodeA || !nodeB) {
        alert('Please select two nodes');
        return;
    }
    
    if (confirm(`Are you sure you want to remove the edge between ${nodeA} and ${nodeB}?`)) {
        fetch('http://localhost:5000/graph/edges', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                node_a: nodeA,
                node_b: nodeB
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Reload graph data
            loadInitialData();
            alert('Edge removed successfully!');
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Failed to remove edge: ${error.message}`);
        });
    }
}

function initEateryManagement() {
    // Populate eatery dropdown
    const eaterySelect = document.getElementById('eaterySelect');
    while (eaterySelect.options.length > 1) {
        eaterySelect.remove(1);
    }
    
    if (campusEateries) {
        Object.keys(campusEateries).forEach(eateryId => {
            const option = document.createElement('option');
            option.value = eateryId;
            option.textContent = campusEateries[eateryId].name || formatNodeName(eateryId);
            eaterySelect.appendChild(option);
        });
    }
}

function loadEateryDetails() {
    const eateryId = document.getElementById('eaterySelect').value;
    if (!eateryId) {
        resetEateryForm();
        return;
    }
    
    const eatery = campusEateries[eateryId];
    if (!eatery) return;
    
    // Fill form fields
    document.getElementById('eateryName').value = eatery.name || '';
    document.getElementById('eateryRating').value = eatery.rating || 0;
    document.getElementById('eateryPrice').value = eatery.price || 2;
    document.getElementById('eateryHours').value = eatery.hours || '';
    document.getElementById('eateryAddress').value = eatery.address || '';
    
    // Set amenities checkboxes
    document.getElementById('eateryPowerOutlet').checked = eatery.power_outlet === 1;
    document.getElementById('eateryHalal').checked = eatery.halal_certified === 1;
    document.getElementById('eateryWifi').checked = eatery.wifi === 1;
    document.getElementById('eateryAircon').checked = eatery.aircon === 1;
    
    // Update preview
    updateEateryPreview(eateryId);
}

function updateEateryPreview(eateryId) {
    const eatery = campusEateries[eateryId];
    if (!eatery) return;
    
    document.getElementById('previewName').textContent = eatery.name || formatNodeName(eateryId);
    document.getElementById('previewRating').textContent = eatery.rating || 'N/A';
    document.getElementById('previewPrice').textContent = renderPriceLevel(eatery.price || 0);
    document.getElementById('previewHours').textContent = eatery.hours || 'Not specified';
    document.getElementById('previewAddress').textContent = eatery.address || 'Not specified';
    
    // Determine open status
    const now = new Date();
    const hours = now.getHours() * 100 + now.getMinutes();
    let isOpen = false;
    
    if (eatery.hours && eatery.hours.toLowerCase() !== '24/7') {
        const [openStr, closeStr] = eatery.hours.split('-');
        const openTime = parseInt(openStr.replace(':', ''));
        const closeTime = parseInt(closeStr.replace(':', ''));
        
        if (closeTime > openTime) {
            isOpen = hours >= openTime && hours <= closeTime;
        } else {
            isOpen = hours >= openTime || hours <= closeTime;
        }
    } else {
        isOpen = true;
    }
    
    document.getElementById('previewStatus').textContent = isOpen ? 'Open' : 'Closed';
    document.getElementById('previewStatus').className = isOpen ? 'badge bg-success' : 'badge bg-danger';
    
    // Build amenities string
    const amenities = [];
    if (eatery.power_outlet) amenities.push('Power Outlets');
    if (eatery.halal_certified) amenities.push('Halal Certified');
    if (eatery.wifi) amenities.push('WiFi');
    if (eatery.aircon) amenities.push('Air Conditioning');
    
    document.getElementById('previewAmenities').textContent = 
        amenities.length > 0 ? amenities.join(', ') : 'None';
}

function saveEateryChanges() {
    const eateryId = document.getElementById('eaterySelect').value;
    if (!eateryId) {
        alert('Please select an eatery to update');
        return;
    }
    
    const updatedData = {
        name: document.getElementById('eateryName').value,
        rating: parseFloat(document.getElementById('eateryRating').value),
        price: parseInt(document.getElementById('eateryPrice').value),
        hours: document.getElementById('eateryHours').value,
        address: document.getElementById('eateryAddress').value,
        power_outlet: document.getElementById('eateryPowerOutlet').checked ? 1 : 0,
        halal_certified: document.getElementById('eateryHalal').checked ? 1 : 0,
        wifi: document.getElementById('eateryWifi').checked ? 1 : 0,
        aircon: document.getElementById('eateryAircon').checked ? 1 : 0
    };
    
    fetch(`http://localhost:5000/eateries/${eateryId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            attributes: updatedData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Reload eatery data
        loadInitialData();
        alert('Eatery updated successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Failed to update eatery: ${error.message}`);
    });
}

function removeSelectedEatery() {
    const eateryId = document.getElementById('eaterySelect').value;
    if (!eateryId) {
        alert('Please select an eatery to remove');
        return;
    }
    
    if (confirm(`Are you sure you want to remove ${eateryId}? This cannot be undone.`)) {
        fetch(`http://localhost:5000/eateries/${eateryId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Reload eatery data
            loadInitialData();
            resetEateryForm();
            alert('Eatery removed successfully!');
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Failed to remove eatery: ${error.message}`);
        });
    }
}

function resetEateryForm() {
    document.getElementById('eateryName').value = '';
    document.getElementById('eateryRating').value = '';
    document.getElementById('eateryPrice').value = '2';
    document.getElementById('eateryHours').value = '';
    document.getElementById('eateryAddress').value = '';
    document.getElementById('eateryPowerOutlet').checked = false;
    document.getElementById('eateryHalal').checked = false;
    document.getElementById('eateryWifi').checked = false;
    document.getElementById('eateryAircon').checked = false;
    
    // Reset preview
    document.getElementById('previewName').textContent = 'Eatery Name';
    document.getElementById('previewRating').textContent = '4.0';
    document.getElementById('previewPrice').textContent = '$$';
    document.getElementById('previewHours').textContent = '9:00-21:00';
    document.getElementById('previewAddress').textContent = 'Location';
    document.getElementById('previewAmenities').textContent = 'WiFi, Aircon';
    document.getElementById('previewStatus').textContent = 'Open';
    document.getElementById('previewStatus').className = 'badge bg-success';
}

// Helper function to format node names
function formatNodeName(nodeId) {
    return nodeId
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase())
        .replace(/Dlsu/g, 'DLSU');
}