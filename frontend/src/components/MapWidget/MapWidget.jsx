import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from "react-leaflet";
import L from "leaflet";
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

// Hoàng Sa — nhóm An Vĩnh (đông) + nhóm Lưỡi Liềm (tây)
const HOANG_SA_DOTS = [
  { lat: 16.843, lng: 112.338, r: 2.2 }, // Phú Lâm (lớn nhất)
  { lat: 16.870, lng: 112.308, r: 1.4 },
  { lat: 16.856, lng: 112.362, r: 1.2 },
  { lat: 16.980, lng: 112.240, r: 1.5 }, // Linh Côn
  { lat: 16.960, lng: 112.185, r: 1.2 },
  { lat: 17.083, lng: 111.617, r: 1.2 }, // Đảo Bắc
  { lat: 17.062, lng: 111.542, r: 1.2 },
  { lat: 16.538, lng: 111.607, r: 1.8 }, // Đảo Hoàng Sa
  { lat: 16.487, lng: 111.570, r: 1.2 },
  { lat: 16.450, lng: 111.830, r: 1.2 },
  { lat: 16.358, lng: 111.748, r: 1.4 }, // Duy Mộng
  { lat: 16.392, lng: 111.680, r: 1.2 },
];

// Trường Sa — rải dọc 7°N–12°N
const TRUONG_SA_DOTS = [
  { lat: 11.921, lng: 114.360, r: 2.2 }, // Ba Bình
  { lat: 11.450, lng: 114.575, r: 1.5 }, // Song Tử Tây
  { lat: 11.460, lng: 114.715, r: 1.2 },
  { lat: 10.726, lng: 115.823, r: 1.5 }, // Thị Tứ
  { lat: 10.384, lng: 114.194, r: 1.2 },
  { lat: 10.178, lng: 114.268, r: 1.8 }, // Trường Sa Lớn
  { lat: 9.880, lng: 114.498, r: 1.2 },
  { lat: 9.648, lng: 113.947, r: 1.2 }, // An Bang
  { lat: 9.248, lng: 113.382, r: 1.2 },
  { lat: 8.648, lng: 111.923, r: 1.2 }, // Nam Yết
  { lat: 8.383, lng: 111.547, r: 1.2 },
  { lat: 7.983, lng: 111.768, r: 1.2 },
  { lat: 8.117, lng: 113.097, r: 1.2 },
  { lat: 8.848, lng: 114.482, r: 1.2 },
  { lat: 9.418, lng: 115.383, r: 1.2 },
  { lat: 10.183, lng: 115.250, r: 1.2 },
  { lat: 10.950, lng: 114.752, r: 1.2 },
];

// Style chấm đảo — be vàng nhạt giống màu đất Hainan trên Voyager
const ISLAND_DOT_STYLE = {
  color: "#e8e0c8",
  fillColor: "#f5f0e0",
  fillOpacity: 1.0,
  weight: 0.5,
};

// Label tên — khớp với font style chữ địa danh của tile Voyager
const makeArchipelagoLabel = (name) =>
  L.divIcon({
    className: "",
    html: `<div style="
      color: #4a6078;
      font-size: 10px;
      font-weight: 500;
      font-style: normal;
      white-space: nowrap;
      text-shadow: 0 1px 2px rgba(255,255,255,0.95), 0 0 4px rgba(255,255,255,0.8);
      pointer-events: none;
      user-select: none;
      letter-spacing: 0.2px;
      font-family: 'Helvetica Neue', Arial, sans-serif;
    ">${name}</div>`,
    iconAnchor: [0, 0],
  });

const MapWidget = ({ onLocationSelect }) => {
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
          if (!locMap[loc]) locMap[loc] = { count: 0, articles: [], allArticles: [], diseases: new Set() };
          locMap[loc].count += 1;
          locMap[loc].allArticles.push(a);
          if (locMap[loc].articles.length < 3) locMap[loc].articles.push(a.title || "");
          if (a.disease_name) locMap[loc].diseases.add(a.disease_name);
        });

        const result = Object.entries(locMap)
          .map(([name, data]) => ({
            name,
            lat: PROVINCE_COORDS[name][0],
            lng: PROVINCE_COORDS[name][1],
            count: data.count,
            articles: data.articles,
            allArticles: data.allArticles,
            diseases: [...data.diseases],
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

  const handleMarkerClick = (loc) => {
    if (onLocationSelect) {
      onLocationSelect({
        name: loc.name,
        count: loc.count,
        diseases: loc.diseases,
        allArticles: loc.allArticles,
      });
    }
  };

  return (
    <div className="map-wrapper">
      <div className="map-header">
        <div>
          <h2 className="map-title" style={{ color: "var(--accent-cyan)" }}>
            Bản đồ Giám sát Dịch bệnh
          </h2>
          <p className="map-subtitle">
            {loading
              ? "Đang tải dữ liệu..."
              : locations.length > 0
                ? `Phát hiện ${locations.length} khu vực trong ${locations.reduce((s, l) => s + l.count, 0)} bài viết`
                : "Chưa có dữ liệu địa điểm"}
          </p>
        </div>
        <div className="status-badge">ĐANG GIÁM SÁT</div>
      </div>

      <MapContainer
        center={[16.0, 106.5]}
        zoom={7}
        minZoom={6}
        maxZoom={11}
        maxBounds={[
          [6.5, 101.5],
          [23.5, 117.5],
        ]}
        maxBoundsViscosity={1.0}
        className="leaflet-map"
        zoomControl={false}
        scrollWheelZoom={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CartoDB</a>'
        />
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png"
          opacity={1}
        />

        {/* ── Quần đảo Hoàng Sa ── */}
        {HOANG_SA_DOTS.map((dot, i) => (
          <CircleMarker
            key={`hs-${i}`}
            center={[dot.lat, dot.lng]}
            pathOptions={ISLAND_DOT_STYLE}
            radius={dot.r}
            interactive={false}
          />
        ))}
        <Marker
          position={[16.15, 111.15]}
          icon={makeArchipelagoLabel("Q.đ. Hoàng Sa")}
          interactive={false}
        />

        {/* ── Quần đảo Trường Sa ── */}
        {TRUONG_SA_DOTS.map((dot, i) => (
          <CircleMarker
            key={`ts-${i}`}
            center={[dot.lat, dot.lng]}
            pathOptions={ISLAND_DOT_STYLE}
            radius={dot.r}
            interactive={false}
          />
        ))}
        <Marker
          position={[8.40, 113.50]}
          icon={makeArchipelagoLabel("Q.đ. Trường Sa")}
          interactive={false}
        />

        {/* ── Marker tỉnh/thành ── */}
        {locations.map((loc, idx) => {
          const color = getMarkerColor(idx, locations.length);
          return (
            <CircleMarker
              key={idx}
              center={[loc.lat, loc.lng]}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.5, weight: 2 }}
              radius={getRadius(loc.count)}
              eventHandlers={{ click: () => handleMarkerClick(loc) }}
            >
              <Popup className="custom-popup" minWidth={180}>
                <div style={{ minWidth: "180px" }}>
                  <strong style={{ color, fontSize: "14px" }}>{loc.name}</strong>
                  <br />
                  <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                    {loc.count} bài viết
                  </span>
                  {loc.diseases.length > 0 && (
                    <p style={{ fontSize: "11px", color: "#f59e0b", margin: "6px 0 0" }}>
                      {loc.diseases.slice(0, 2).join(", ")}
                    </p>
                  )}
                  <p style={{ fontSize: "11px", color: "#64748b", margin: "6px 0 0" }}>
                    Click để xem bài viết
                  </p>
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