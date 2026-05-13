import React, { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap, CircleMarker } from "react-leaflet";
import L from "leaflet";
import type { Depot, Route } from "../types";
import { ROUTE_COLORS } from "../theme";

// Fix default Leaflet icons (Vite asset paths)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Props {
  depot: Depot;
  routes: Route[];
  baselineRoutes?: Route[];
  view: "single" | "side";
  onSelectRoute: (vehicleId: string) => void;
}

function depotIcon() {
  return L.divIcon({
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    html: `<div style="background:#231F20;color:#fff;border:2px solid #98012E;border-radius:6px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:10px;box-shadow:0 2px 6px rgba(0,0,0,.25)">HUB</div>`,
  });
}

function stopIcon(seq: number, color: string, isEv: boolean) {
  const leaf = isEv
    ? '<span style="position:absolute;top:-6px;right:-6px;background:#1B7F3A;color:#fff;border-radius:50%;width:12px;height:12px;display:flex;align-items:center;justify-content:center;font-size:8px">🌿</span>'
    : "";
  return L.divIcon({
    className: "",
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    html: `<div style="position:relative;background:${color};color:#fff;border:2px solid #fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:10px;box-shadow:0 1px 3px rgba(0,0,0,.4)">${seq}${leaf}</div>`,
  });
}

const FitBounds: React.FC<{ pts: [number, number][] }> = ({ pts }) => {
  const map = useMap();
  useEffect(() => {
    if (!pts.length) return;
    const bounds = L.latLngBounds(pts);
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [pts, map]);
  return null;
};

const SingleMap: React.FC<{
  depot: Depot;
  routes: Route[];
  onSelectRoute: (vid: string) => void;
  title: string;
}> = ({ depot, routes, onSelectRoute, title }) => {
  const allPts = useMemo<[number, number][]>(() => {
    const pts: [number, number][] = [[depot.lat, depot.lon]];
    for (const r of routes) for (const s of r.stops) pts.push([s.lat, s.lon]);
    return pts;
  }, [depot, routes]);

  return (
    <div className="relative h-[520px] rounded-md overflow-hidden border border-ceva-grayMid">
      <div className="absolute top-2 left-2 z-[400] bg-white/90 backdrop-blur px-2 py-1 rounded-md text-xs font-bold text-ceva-black shadow-card">
        {title}
      </div>
      <MapContainer center={[depot.lat, depot.lon]} zoom={11} className="h-full w-full">
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds pts={allPts} />
        <Marker position={[depot.lat, depot.lon]} icon={depotIcon()}>
          <Popup>
            <div className="font-bold">{depot.name}</div>
            <div className="text-xs">{depot.address}</div>
          </Popup>
        </Marker>
        {routes.map((r, i) => {
          const color = ROUTE_COLORS[i % ROUTE_COLORS.length];
          const isEv = r.fuel_type === "electric";
          if (r.polyline.length < 2) return null;
          return (
            <React.Fragment key={r.vehicle_id}>
              <Polyline
                positions={r.polyline as [number, number][]}
                pathOptions={{ color, weight: 4, opacity: 0.85 }}
                eventHandlers={{ click: () => onSelectRoute(r.vehicle_id) }}
              />
              {r.stops.map((s) => (
                <Marker
                  key={`${r.vehicle_id}-${s.seq}`}
                  position={[s.lat, s.lon]}
                  icon={stopIcon(s.seq, color, isEv)}
                  eventHandlers={{ click: () => onSelectRoute(r.vehicle_id) }}
                >
                  <Popup>
                    <div className="text-xs">
                      <div className="font-bold">#{s.seq} · {s.customer_name}</div>
                      <div>{s.address}</div>
                      <div>Order: {s.order_id} · {s.weight_kg} kg · {s.priority}</div>
                      <div>ETA: {Math.floor(s.eta_min / 60)}:{String(s.eta_min % 60).padStart(2, "0")} · {s.on_time ? "on time" : "LATE"}</div>
                      <div>Vehicle: {r.vehicle_id} ({r.vehicle_type}{isEv ? " · EV 🌿" : ""})</div>
                    </div>
                  </Popup>
                </Marker>
              ))}
              {/* small endpoint dot at depot for this route */}
              <CircleMarker
                center={[depot.lat, depot.lon]}
                radius={2}
                pathOptions={{ color, fillColor: color, fillOpacity: 1 }}
              />
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
};

const MapView: React.FC<Props> = ({ depot, routes, baselineRoutes, view, onSelectRoute }) => {
  if (view === "side" && baselineRoutes) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <SingleMap depot={depot} routes={baselineRoutes} onSelectRoute={onSelectRoute} title="Baseline" />
        <SingleMap depot={depot} routes={routes} onSelectRoute={onSelectRoute} title="Optimized" />
      </div>
    );
  }
  return <SingleMap depot={depot} routes={routes} onSelectRoute={onSelectRoute} title="Routes" />;
};

export default MapView;
