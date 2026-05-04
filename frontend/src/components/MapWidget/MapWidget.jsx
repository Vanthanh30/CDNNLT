import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./MapWidget.css";

const API_BASE_URL = "http://localhost:8000";

const MapWidget = () => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const vnCenter = [16.4637, 107.5909];
  const zoomLevel = 6.5;
  const vnBounds = [
    [8.0, 102.0],
    [23.5, 110.0],
  ];

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        setError(null);
        console.log("🔄 Fetching locations from:", `${API_BASE_URL}/locations`);

        const res = await fetch(`${API_BASE_URL}/locations`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });

        console.log("📡 Response status:", res.status);

        if (!res.ok) {
          throw new Error(`HTTP Error ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        console.log("✅ Locations data received:", data);

        if (Array.isArray(data) && data.length > 0) {
          setLocations(data);
          console.log(`✅ Successfully loaded ${data.length} locations`);
        } else {
          console.warn("⚠️ Data is empty or not an array");
          setLocations([]);
          setError("⚠️ Không có dữ liệu vùng dịch bệnh");
        }
      } catch (err) {
        console.error("❌ Error fetching locations:", err);
        setError(`❌ ${err.message}`);
        setLocations([]);
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, []);

  // Chia màu theo rank (vị trí trong danh sách đã sort)
  const getMarkerColor = (rank, total) => {
    if (total === 0) return "#0ea5e9";
    const ratio = rank / (total - 1);
    if (ratio < 0.33) return "#ef4444"; // đỏ - cao
    if (ratio < 0.66) return "#f97316"; // cam - trung bình
    return "#0ea5e9"; // xanh - thấp
  };

  const maxCount = locations.length > 0 ? locations[0].count : 1;

  const getRadius = (count) => {
    const ratio = maxCount > 0 ? count / maxCount : 0;
    return Math.max(7, Math.round(ratio * 20));
  };

  const totalArticles = locations.reduce((sum, loc) => sum + loc.count, 0);

  return (
    <div className="map-wrapper">
      <div className="map-header">
        <div>
          <h2 className="map-title" style={{ color: "var(--accent-cyan)" }}>
            Bản đồ Giám sát Dịch bệnh
          </h2>
          <p className="map-subtitle">
            {loading
              ? "⏳ Đang tải dữ liệu..."
              : error
                ? error
                : locations.length > 0
                  ? `✅ Phát hiện ${locations.length} khu vực được đề cập trong ${totalArticles} bài viết`
                  : "⚠️ Không có dữ liệu"}
          </p>
        </div>
        <div className="status-badge">ĐANG GIÁM SÁT</div>
      </div>

      <div className="leaflet-container">
        <MapContainer
          center={vnCenter}
          zoom={zoomLevel}
          minZoom={6}
          maxBounds={vnBounds}
          maxBoundsViscosity={1.0}
          className="leaflet-map"
          zoomControl={false}
          scrollWheelZoom={true}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
            attribution="&copy; OpenStreetMap contributors"
          />
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
          />

          {/* Render markers */}
          {locations.map((loc, idx) => {
            const color = getMarkerColor(idx, locations.length);
            const radius = getRadius(loc.count);

            return (
              <CircleMarker
                key={`${loc.name}-${idx}`}
                center={[loc.lat, loc.lng]}
                pathOptions={{
                  color: color,
                  fillColor: color,
                  fillOpacity: 0.6,
                  weight: 2,
                }}
                radius={radius}
              >
                <Popup className="custom-popup">
                  <div style={{ minWidth: "160px" }}>
                    <strong style={{ color: color, fontSize: "13px" }}>
                      {loc.name}
                    </strong>
                    <br />
                    <span style={{ fontSize: "12px", color: "#e2e8f0" }}>
                      📰 {loc.count} bài viết
                    </span>
                    {loc.articles && loc.articles.length > 0 && (
                      <>
                        <hr style={{ margin: "4px 0", opacity: 0.3 }} />
                        {loc.articles.slice(0, 3).map((title, i) => (
                          <p
                            key={i}
                            style={{
                              fontSize: "11px",
                              color: "#94a3b8",
                              margin: "3px 0",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              maxWidth: "220px",
                            }}
                            title={title}
                          >
                            • {title}
                          </p>
                        ))}
                      </>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      {/* Legend */}
      {!loading && locations.length > 0 && (
        <div className="map-legend">
          <span style={{ color: "#ef4444" }}>● Cao</span>
          <span style={{ color: "#f97316" }}>● Trung bình</span>
          <span style={{ color: "#0ea5e9" }}>● Theo dõi</span>
        </div>
      )}
    </div>
  );
};

export default MapWidget;