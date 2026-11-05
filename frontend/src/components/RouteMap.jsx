import { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Coordinates for all supported ports
export const PORT_COORDINATES = {
  Australia: [-32.9283, 151.7817], // Port of Newcastle (NSW)
  'United States': [36.8468, -76.2951], // Hampton Roads / Norfolk, VA
  Mozambique: [-25.9692, 32.5732], // Port of Maputo
  Indonesia: [-1.2379, 116.8529], // Balikpapan Coal Terminal
  Russia: [43.1155, 131.8855], // Vladivostok Commercial Port

  // Indian Destination Ports
  Paradip: [20.2631, 86.6700],
  Visakhapatnam: [17.6868, 83.2185],
  Gangavaram: [17.6210, 83.2320],
  Gopalpur: [19.2613, 84.9075],
  Dhamra: [20.4700, 86.9000],
  'Sagar/Sandheads': [21.6543, 88.0815],
  Haldia: [22.0257, 88.1583],
};

export const PORT_DESCRIPTIONS = {
  Australia: 'Port of Newcastle (NSW) — Deepwater Coal Terminal',
  'United States': 'Hampton Roads (Norfolk, VA) — US East Coast Bulkers',
  Mozambique: 'Port of Maputo — Matola Coal Terminal',
  Indonesia: 'Balikpapan (East Kalimantan) — Thermal Coal Loading',
  Russia: 'Vladivostok / Vostochny — Russian Far East Coal Port',
  Paradip: 'Paradip Port (Odisha) — Major East Coast Bulk Hub',
  Visakhapatnam: 'Visakhapatnam Port (Andhra Pradesh) — Natural Deepwater Harbour',
  Gangavaram: 'Gangavaram Port (Andhra Pradesh) — Deepwater Bulk Terminal (21m Draft)',
  Gopalpur: 'Gopalpur Port (Odisha) — All-Weather Deepwater Port',
  Dhamra: 'Dhamra Port (Odisha) — Capesize Bulk Terminal',
  'Sagar/Sandheads': 'Sagar Island / Sandheads (West Bengal) — Lighterage Anchorage',
  Haldia: 'Haldia Dock Complex (West Bengal) — Riverine Bulk Terminal',
};

// Maritime corridor generator ensuring water-only navigation through open seas & straits
export function getMaritimeRoute(origin, destination) {
  const originCoord = PORT_COORDINATES[origin];
  const destCoord = PORT_COORDINATES[destination];

  if (!originCoord || !destCoord) return [];

  // Approach waypoint into the Bay of Bengal for the destination port
  const bayOfBengalApproach = [14.0, 85.0];

  let waypoints = [];

  switch (origin) {
    case 'Australia':
      // Maritime path south around Australia through Bass Strait & Cape Leeuwin into Indian Ocean
      waypoints = [
        originCoord,
        [-34.80, 151.50], // Off Sydney
        [-37.50, 150.20], // Off Cape Howe
        [-39.20, 147.00], // Bass Strait East
        [-39.50, 143.50], // South of Cape Otway
        [-37.00, 133.00], // Great Australian Bight
        [-35.50, 116.00], // South of Cape Leeuwin
        [-32.00, 110.00], // Indian Ocean turn NW
        [-20.00, 95.00],  // Central Indian Ocean
        [-5.00, 88.00],   // Equatorial Indian Ocean
        [6.00, 86.00],    // Entrance to Bay of Bengal
        bayOfBengalApproach,
        destCoord,
      ];
      break;

    case 'Mozambique':
      // Mozambique Channel -> north of Madagascar -> south of Sri Lanka -> Bay of Bengal
      waypoints = [
        originCoord,
        [-24.00, 36.00],  // Mozambique Channel South
        [-17.00, 42.00],  // Mozambique Channel Central
        [-11.50, 48.50],  // North of Madagascar
        [-3.00, 60.00],   // Equatorial Western Indian Ocean
        [4.50, 75.00],    // Southwest of Sri Lanka
        [5.80, 81.00],    // Dondra Head / South Sri Lanka
        bayOfBengalApproach,
        destCoord,
      ];
      break;

    case 'Indonesia':
      // Makassar Strait -> Java Sea -> Sunda Strait -> Indian Ocean -> Bay of Bengal
      waypoints = [
        originCoord,
        [-3.80, 117.50],  // Makassar Strait South
        [-6.50, 115.00],  // Java Sea East
        [-6.00, 108.00],  // Java Sea Central
        [-5.80, 106.00],  // Sunda Strait Approach
        [-6.10, 104.50],  // Sunda Strait Exit into Indian Ocean
        [-2.00, 96.00],   // Off Southwest Sumatra
        [5.50, 93.00],    // Great Channel / North Sumatra
        [10.00, 90.00],   // Andaman Sea
        bayOfBengalApproach,
        destCoord,
      ];
      break;

    case 'United States':
      // US East Coast -> North Atlantic -> South Atlantic -> Cape of Good Hope -> Indian Ocean -> Sri Lanka -> Bay of Bengal
      waypoints = [
        originCoord,
        [34.00, -74.00],  // Western Atlantic
        [20.00, -50.00],  // Mid-North Atlantic
        [0.00, -30.00],   // Equatorial Atlantic
        [-20.00, -10.00], // South Atlantic
        [-35.00, 15.00],  // South of Cape of Good Hope
        [-35.50, 25.00],  // Off Agulhas
        [-30.00, 45.00],  // Southwest Indian Ocean
        [-15.00, 65.00],  // Mid-South Indian Ocean
        [2.00, 78.00],    // Equatorial Indian Ocean
        [5.80, 81.00],    // South of Sri Lanka
        bayOfBengalApproach,
        destCoord,
      ];
      break;

    case 'Russia':
      // Sea of Japan -> Tsushima Strait -> East China Sea -> Taiwan Strait -> South China Sea -> Singapore Strait -> Malacca -> Bay of Bengal
      waypoints = [
        originCoord,
        [37.00, 131.00],  // Sea of Japan
        [34.00, 129.50],  // Tsushima Strait
        [30.00, 125.00],  // East China Sea
        [22.00, 120.50],  // Taiwan Strait
        [14.00, 113.00],  // South China Sea
        [4.00, 106.00],   // South China Sea South
        [1.30, 104.30],   // Singapore Strait East
        [1.20, 103.60],   // Singapore Strait
        [3.00, 101.00],   // Malacca Strait
        [5.50, 96.50],    // Malacca Exit
        [8.00, 93.00],    // Nicobar Passage into Bay of Bengal
        bayOfBengalApproach,
        destCoord,
      ];
      break;

    default:
      waypoints = [originCoord, destCoord];
      break;
  }

  return waypoints;
}

function AutoFitBounds({ routePoints }) {
  const map = useMap();
  useEffect(() => {
    if (!routePoints || routePoints.length === 0) return;
    try {
      map.fitBounds(routePoints, { padding: [50, 50], maxZoom: 5 });
    } catch {
      // Map may be unmounting
    }
  }, [map, routePoints]);
  return null;
}

export default function RouteMap({
  origin,
  destination,
  isTrainedModel,
  onSelectPort,
}) {
  const originCoord = PORT_COORDINATES[origin];
  const destCoord = PORT_COORDINATES[destination];

  const maritimeRoute = useMemo(
    () => getMaritimeRoute(origin, destination),
    [origin, destination]
  );

  return (
    <div className="route-map-wrapper">
      <div className="route-map-header">
        <div className="route-map-title-row">
          <span className="route-indicator-dot" style={{ background: isTrainedModel ? '#0284c7' : '#d97706' }} />
          <strong>Maritime Corridor: {origin} &rarr; {destination}</strong>
          <span className={`route-model-pill ${isTrainedModel ? 'pill-ml' : 'pill-stat'}`}>
            {isTrainedModel ? 'Trained ML Model' : 'Holt Statistical Baseline'}
          </span>
        </div>
        <p className="route-map-desc">
          Navigable deepwater shipping corridor via verified maritime choke points. Click any port pin on the East Coast of India to switch destinations.
        </p>
      </div>

      <div className="map-view-container">
        <MapContainer
          center={[10, 85]}
          zoom={3}
          minZoom={2}
          maxZoom={12}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%', borderRadius: '8px' }}
        >
          {/* OpenStreetMap Standard Tile Layer — Zero API Key Required */}
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            maxZoom={19}
          />

          {/* Maritime Navigation Path */}
          {maritimeRoute.length > 0 && (
            <Polyline
              positions={maritimeRoute}
              pathOptions={{
                color: isTrainedModel ? '#0284c7' : '#d97706',
                weight: 3.5,
                opacity: 0.85,
                dashArray: isTrainedModel ? undefined : '7, 5',
                lineJoin: 'round',
              }}
            />
          )}

          {/* Origin Marker with Outer Pulsing Ring */}
          {originCoord && (
            <>
              <CircleMarker
                center={originCoord}
                radius={14}
                pathOptions={{
                  color: '#0284c7',
                  fillColor: '#38bdf8',
                  fillOpacity: 0.25,
                  weight: 1.5,
                }}
              />
              <CircleMarker
                center={originCoord}
                radius={7}
                pathOptions={{
                  color: '#0369a1',
                  fillColor: '#0284c7',
                  fillOpacity: 1,
                  weight: 2,
                }}
              >
                <Tooltip permanent={false} direction="top">
                  <div className="map-marker-tooltip">
                    <strong>ORIGIN: {origin}</strong>
                    <span>{PORT_DESCRIPTIONS[origin] || origin}</span>
                  </div>
                </Tooltip>
              </CircleMarker>
            </>
          )}

          {/* Destination Marker with Distinct Amber Highlight Ring */}
          {destCoord && (
            <>
              <CircleMarker
                center={destCoord}
                radius={16}
                pathOptions={{
                  color: '#d97706',
                  fillColor: '#fbbf24',
                  fillOpacity: 0.28,
                  weight: 2,
                }}
              />
              <CircleMarker
                center={destCoord}
                radius={8}
                pathOptions={{
                  color: '#92400e',
                  fillColor: '#d97706',
                  fillOpacity: 1,
                  weight: 2,
                }}
              >
                <Tooltip permanent={true} direction="right" offset={[12, 0]}>
                  <div className="map-marker-tooltip">
                    <strong>DESTINATION: {destination}</strong>
                    <span>{PORT_DESCRIPTIONS[destination] || destination}</span>
                  </div>
                </Tooltip>
              </CircleMarker>
            </>
          )}

          {/* Other Indian Ports Markers for Quick Click */}
          {Object.entries(PORT_COORDINATES).map(([portName, coords]) => {
            const isIndianPort = [
              'Paradip',
              'Visakhapatnam',
              'Gangavaram',
              'Gopalpur',
              'Dhamra',
              'Sagar/Sandheads',
              'Haldia',
            ].includes(portName);

            if (!isIndianPort || portName === destination) return null;

            return (
              <CircleMarker
                key={portName}
                center={coords}
                radius={5}
                pathOptions={{
                  color: '#475569',
                  fillColor: '#94a3b8',
                  fillOpacity: 0.85,
                  weight: 1.5,
                }}
                eventHandlers={{
                  click: () => onSelectPort && onSelectPort(portName),
                }}
              >
                <Tooltip permanent={false} direction="top">
                  <div className="map-marker-tooltip">
                    <strong>Port of {portName}</strong>
                    <span style={{ color: '#0284c7', fontSize: '11px', fontWeight: 600 }}>Click to select port</span>
                  </div>
                </Tooltip>
              </CircleMarker>
            );
          })}

          <AutoFitBounds routePoints={maritimeRoute} />
        </MapContainer>
      </div>

      <div className="map-legend-bar">
        <div className="legend-chip">
          <span className="legend-dot" style={{ background: '#0284c7' }} />
          <span>Origin ({origin})</span>
        </div>
        <div className="legend-chip">
          <span className="legend-dot" style={{ background: '#d97706' }} />
          <span>Active Port ({destination})</span>
        </div>
        <div className="legend-chip">
          <span className="legend-dot" style={{ background: '#94a3b8' }} />
          <span>Other Indian Ports (Clickable)</span>
        </div>
        <div className="legend-chip">
          <span className="legend-line-sample" style={{ borderColor: isTrainedModel ? '#0284c7' : '#d97706', borderStyle: isTrainedModel ? 'solid' : 'dashed' }} />
          <span>{isTrainedModel ? 'Trained ML Voyage' : 'Statistical Baseline Voyage'}</span>
        </div>
      </div>
    </div>
  );
}
