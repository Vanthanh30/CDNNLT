import React from "react";
import MapWidget from "../../components/MapWidget/MapWidget";
import RightPanel from "../../components/RightPanel/RightPanel";
import StatCard from "../../components/StatCard/StatCard";
import { useArticles } from "../../hooks/useArticles";
import "./Dashboard.css";

const Dashboard = () => {
  // Lấy thêm uniqueOptions để đếm số lượng mầm bệnh (tags)
  const { totalArticlesCount, uniqueOptions, isLoading } = useArticles();

  return (
    <div className="content-grid">
      <div className="map-section panel">
        <MapWidget />
      </div>
      <div className="right-section panel">
        <RightPanel />
      </div>

      <div className="stats-section">
        <StatCard
          title="TỔNG SỐ TIN TỨC ĐÃ QUÉT"
          value={isLoading ? "..." : totalArticlesCount}
          subValue="Dữ liệu cào trực tiếp từ báo điện tử"
          color="cyan"
        />
        {/* ĐÃ CẬP NHẬT DỮ LIỆU THẬT Ở ĐÂY */}
        <StatCard
          title="ĐA DẠNG MẦM BỆNH"
          value={isLoading ? "..." : uniqueOptions?.tags?.length || 0}
          subValue="Từ khóa phân loại duy nhất"
          color="muted"
        />
        <StatCard
          title="TRẠNG THÁI HỆ THỐNG"
          value="99.9%"
          subValue="Tối ưu: Crawler & API Gateway hoạt động tốt"
          color="cyan"
        />
        <StatCard
          title="CẢNH BÁO RỦI RO"
          value="Nguy cơ"
          subValue="! Khẩn cấp: Cụm từ khóa bất thường gia tăng"
          color="red"
        />
      </div>
    </div>
  );
};

export default Dashboard;
