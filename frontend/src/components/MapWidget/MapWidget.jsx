import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./MapWidget.css";

const API_BASE_URL = "http://localhost:8000";

const PROVINCE_COORDS = {
  "Hà Nội": [21.0285, 105.8542], "Hải Phòng": [20.8449, 106.6881],
  "Quảng Ninh": [21.0064, 107.2925], "Hải Dương": [20.9399, 106.3309],
  "Hưng Yên": [20.6463, 106.0511], "Thái Bình": [20.4501, 106.3406],
  "Nam Định": [20.4200, 106.1683], "Ninh Bình": [20.2539, 105.9745],
  "Hà Nam": [20.5835, 105.9230], "Vĩnh Phúc": [21.3609, 105.5474],
  "Bắc Ninh": [21.1861, 106.0763], "Bắc Giang": [21.2731, 106.1946],
  "Lạng Sơn": [21.8537, 106.7615], "Cao Bằng": [22.6667, 106.2500],
  "Bắc Kạn": [22.1473, 105.8348], "Thái Nguyên": [21.5942, 105.8480],
  "Tuyên Quang": [21.8233, 105.2180], "Hà Giang": [22.8026, 104.9784],
  "Lào Cai": [22.4809, 103.9755], "Yên Bái": [21.7051, 104.9054],
  "Phú Thọ": [21.4217, 105.2281], "Sơn La": [21.3256, 103.9188],
  "Điện Biên": [21.3856, 103.0230], "Lai Châu": [22.3964, 103.4581],
  "Hòa Bình": [20.8449, 105.3381], "Thanh Hóa": [19.8079, 105.7764],
  "Nghệ An": [19.2342, 104.9200], "Hà Tĩnh": [18.3559, 105.8877],
  "Quảng Bình": [17.6102, 106.3487], "Quảng Trị": [16.7943, 107.0418],
  "Thừa Thiên Huế": [16.4637, 107.5909], "Đà Nẵng": [16.0544, 108.2022],
  "Quảng Nam": [15.5394, 108.0191], "Quảng Ngãi": [15.1213, 108.8044],
  "Bình Định": [13.7765, 109.2233], "Phú Yên": [13.0882, 109.0928],
  "Khánh Hòa": [12.2388, 109.1967], "Ninh Thuận": [11.5645, 108.9885],
  "Bình Thuận": [10.9804, 108.2580], "Kon Tum": [14.3497, 108.0005],
  "Gia Lai": [13.9810, 108.0000], "Đắk Lắk": [12.7100, 108.2378],
  "Đắk Nông": [12.0046, 107.6873], "Lâm Đồng": [11.5753, 108.1429],
  "TP. Hồ Chí Minh": [10.8231, 106.6297], "Bình Dương": [11.1651, 106.6512],
  "Đồng Nai": [11.0686, 107.1676], "Bà Rịa - Vũng Tàu": [10.5417, 107.2429],
  "Bình Phước": [11.7512, 106.7235], "Tây Ninh": [11.3351, 106.1099],
  "Long An": [10.6956, 106.2431], "Tiền Giang": [10.4493, 106.3421],
  "Bến Tre": [10.2433, 106.3759], "Trà Vinh": [9.9513, 106.3426],
  "Vĩnh Long": [10.2538, 105.9722], "Đồng Tháp": [10.4938, 105.6882],
  "An Giang": [10.5216, 105.1259], "Kiên Giang": [10.0125, 105.0809],
  "Cần Thơ": [10.0452, 105.7469], "Hậu Giang": [9.7579, 105.6413],
  "Sóc Trăng": [9.6003, 105.9800], "Bạc Liêu": [9.2940, 105.7216],
  "Cà Mau": [9.1769, 105.1524],
};

const MapWidget = () => {
  const navigate = useNavigate();
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAndCalc = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/articles`);
        const articles = await res.json();
        const locMap = {};
        articles.forEach((a) => {
          const loc = a.location;
          if (!loc || !PROVINCE_COORDS[loc]) return;
          if (!locMap[loc]) locMap[loc] = { count: 0, articles: [], diseases: new Set() };
          locMap[loc].count += 1;
          if (locMap[loc].articles.length < 3) locMap[loc].articles.push(a.title || "");
          if (a.disease_name) locMap[loc].diseases.add(a.disease_name);
        });
        const result = Object.entries(locMap)
          .map(([name, data]) => ({
            name, lat: PROVINCE_COORDS[name][0], lng: PROVINCE_COORDS[name][1],
            count: data.count, articles: data.articles, diseases: [...data.diseases],
          }))
          .sort((a, b) => b.count - a.count);
        setLocations(result);
      } catch (err) {
        console.error("MapWidget fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAndCalc();
  }, []);

  const maxCount = locations.length > 0 ? locations[0].count : 1;
  const getMarkerColor = (rank, total) => {
    const ratio = rank / total;
    if (ratio < 0.33) return "#ef4444";
    if (ratio < 0.66) return "#f97316";
    return "#0ea5e9";
  };
  const getRadius = (count) => Math.max(7, Math.round((count / maxCount) * 20));

  return (
    <div className="map-wrapper">
      <div className="map-header">
        <div>
          <h2 className="map-title" style={{ color: "var(--accent-cyan)" }}>
            Bản đồ Giám sát Dịch bệnh
          </h2>
          <p className="map-subtitle">
            {loading ? "Đang tải dữ liệu..."
              : locations.length > 0
                ? `Phát hiện ${locations.length} khu vực trong ${locations.reduce((s, l) => s + l.count, 0)} bài viết`
                : "Chưa có dữ liệu địa điểm"}
          </p>
        </div>
        <div className="status-badge">ĐANG GIÁM SÁT</div>
      </div>

      <MapContainer
        center={[16.4637, 107.5909]} zoom={6.5} minZoom={6}
        maxBounds={[[8.0, 102.0], [23.5, 110.0]]}
        maxBoundsViscosity={1.0} className="leaflet-map"
        zoomControl={false} scrollWheelZoom={true}
      >
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png" attribution="&copy; OpenStreetMap" />
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png" />

        {locations.map((loc, idx) => {
          const color = getMarkerColor(idx, locations.length);
          return (
            <CircleMarker key={idx} center={[loc.lat, loc.lng]}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.5, weight: 2 }}
              radius={getRadius(loc.count)}
            >
              <Popup className="custom-popup" minWidth={210}>
                <div style={{ minWidth: "210px" }}>
                  <strong style={{ color, fontSize: "14px" }}>{loc.name}</strong><br />
                  <span style={{ fontSize: "12px" }}>{loc.count} bài viết</span>

                  {loc.diseases.length > 0 && (
                    <p style={{ fontSize: "11px", color: "#f59e0b", margin: "6px 0 0" }}>
                      🦠 {loc.diseases.slice(0, 2).join(", ")}
                    </p>
                  )}

                  {loc.articles.slice(0, 2).map((title, i) => (
                    <p key={i} style={{
                      fontSize: "11px", color: "#94a3b8", margin: "4px 0 0",
                      overflow: "hidden", textOverflow: "ellipsis",
                      whiteSpace: "nowrap", maxWidth: "200px",
                    }}>• {title}</p>
                  ))}

                  {/* Nút xem tất cả bài báo tại vùng này */}
                  <button
                    onClick={() => navigate(`/search?location=${encodeURIComponent(loc.name)}`)}
                    style={{
                      marginTop: "10px", width: "100%", padding: "7px 0",
                      background: color, color: "#fff", border: "none",
                      borderRadius: "6px", fontSize: "12px", fontWeight: "600",
                      cursor: "pointer",
                    }}
                  >
                    Xem {loc.count} bài tại {loc.name}
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {!loading && locations.length > 0 && (
        <div className="map-legend">
          <span style={{ color: "#ef4444" }}>● Nhiều nhất</span>
          <span style={{ color: "#f97316" }}>● Trung bình</span>
          <span style={{ color: "#0ea5e9" }}>● Ít nhất</span>
        </div>
      )}
    </div>
  );
};

export default MapWidget;