import React from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./MapWidget.css";

const MapWidget = () => {
  // 1. Tọa độ trung tâm bao quát cả 3 miền Việt Nam
  const vnCenter = [16.4637, 107.5909];

  // 2. Tăng zoomLevel lên 6.5 hoặc 7 để thấy rõ ranh giới tỉnh khi vừa load
  const zoomLevel = 6.5;

  // 3. Thiết lập ranh giới "khóa" bản đồ (Max Bounds)
  // Giới hạn trong khoảng tọa độ địa lý của Việt Nam
  const vnBounds = [
    [8.0, 102.0], // Góc Tây Nam
    [23.5, 110.0], // Góc Đông Bắc
  ];

  return (
    <div className="map-wrapper">
      <div className="map-header">
        <div>
          <h2 className="map-title" style={{ color: "var(--accent-cyan)" }}>
            Bản đồ Giám sát Dịch bệnh
          </h2>
          <p className="map-subtitle">
            Hệ thống theo dõi dịch bệnh thời gian thực tại Việt Nam
          </p>
        </div>
        <div className="status-badge">ĐANG GIÁM SÁT</div>
      </div>

      <MapContainer
        center={vnCenter}
        zoom={zoomLevel}
        minZoom={6} // Không cho phép thu nhỏ quá mức để lộ nước khác
        maxBounds={vnBounds} // Khóa khung hình trong phạm vi VN
        maxBoundsViscosity={1.0} // Độ cứng của ranh giới (ngăn kéo lùi ra ngoài)
        className="leaflet-map"
        zoomControl={false}
        scrollWheelZoom={true}
      >
        {/* Sử dụng bản đồ Dark Matter không nhãn để tạo nền xanh đen sạch sẽ */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
          attribution="&copy; OpenStreetMap contributors"
        />

        {/* Đè thêm lớp nhãn địa danh lên trên - giúp tập trung vào các tỉnh VN */}
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png" />

        {/* Điểm dữ liệu tại Đà Nẵng */}
        <CircleMarker
          center={[16.0544, 108.2022]}
          pathOptions={{
            color: "var(--accent-cyan)",
            fillColor: "var(--accent-cyan)",
            fillOpacity: 0.4,
            weight: 1,
          }}
          radius={12}
        >
          <Popup className="custom-popup">Đà Nẵng: Đang giám sát</Popup>
        </CircleMarker>

        {/* Điểm cảnh báo tại TP.HCM */}
        <CircleMarker
          center={[10.8231, 106.6297]}
          pathOptions={{
            color: "var(--accent-red)",
            fillColor: "var(--accent-red)",
            fillOpacity: 0.6,
            weight: 2,
          }}
          radius={15}
        >
          <Popup>TP.HCM: Cảnh báo bùng phát</Popup>
        </CircleMarker>
      </MapContainer>
    </div>
  );
};

export default MapWidget;
