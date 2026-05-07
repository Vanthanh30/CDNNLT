import React, { useState, useEffect } from "react";
import MapWidget from "../../components/MapWidget/MapWidget";
import RightPanel from "../../components/RightPanel/RightPanel";
import StatCard from "../../components/StatCard/StatCard";
import { articleService } from "../../services/api";
import FloatingChat from "../../components/FloatingChat/FloatingChat";
import "./Dashboard.css";

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await articleService.getAllArticles();

        // Tính stats từ data thật
        const total = data.length;
        const withEvent = data.filter((a) => a.disease_name).length;
        const highRisk = data.filter((a) => a.risk_level === "HIGH").length;
        const uniqueDiseases = new Set(
          data.map((a) => a.disease_name).filter(Boolean),
        ).size;
        const uniqueLocations = new Set(
          data.map((a) => a.location).filter(Boolean),
        ).size;

        // Top disease
        const diseaseCounts = {};
        data.forEach((a) => {
          if (a.disease_name) {
            diseaseCounts[a.disease_name] =
              (diseaseCounts[a.disease_name] || 0) + 1;
          }
        });
        const topDisease = Object.entries(diseaseCounts).sort(
          (a, b) => b[1] - a[1],
        )[0];

        setStats({
          total,
          total_articles: total,
          withEvent,
          highRisk,
          uniqueDiseases,
          uniqueLocations,
          top_keyword: topDisease?.[0] || null,
          top_keyword_count: topDisease?.[1] || 0,
          processRate: total > 0 ? Math.round((withEvent / total) * 100) : 0,
        });
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  const getRiskInfo = () => {
    if (!stats) return { value: "...", sub: "Đang phân tích..." };
    if (stats.highRisk === 0)
      return { value: "Bình thường", sub: "Chưa phát hiện bất thường" };
    return {
      value: stats.highRisk > 10 ? "Nguy cơ cao" : "Theo dõi",
      sub: `${stats.highRisk} bài được đánh giá rủi ro cao`,
    };
  };

  const riskInfo = getRiskInfo();

  const dummyAnalytics = {
    top_keywords: stats?.top_keyword
      ? [{ keyword: stats.top_keyword, count: stats.top_keyword_count }]
      : [],
  };

  return (
    <div className="content-grid" style={{ position: "relative" }}>
      <div className="map-section panel">
        <MapWidget />
      </div>
      <div className="right-section panel">
        <RightPanel />
      </div>

      <div className="stats-section">
        <StatCard
          title="TỔNG SỐ TIN TỨC ĐÃ QUÉT"
          value={isLoading ? "..." : (stats?.total ?? 0)}
          subValue={`${stats?.uniqueLocations ?? 0} tỉnh/thành được đề cập`}
          color="cyan"
        />
        <StatCard
          title="ĐA DẠNG MẦM BỆNH"
          value={isLoading ? "..." : (stats?.uniqueDiseases ?? 0)}
          subValue={`${stats?.withEvent ?? 0} bài đã phân tích NLP thành công`}
          color="muted"
        />
        <StatCard
          title="TRẠNG THÁI HỆ THỐNG"
          value={isLoading ? "..." : `${stats?.processRate ?? 0}%`}
          subValue={
            (stats?.processRate ?? 0) >= 50
              ? "Tối ưu: Crawler & Processor hoạt động tốt"
              : "Đang khởi động hệ thống..."
          }
          color="cyan"
        />
        <StatCard
          title="CẢNH BÁO RỦI RO"
          value={isLoading ? "..." : riskInfo.value}
          subValue={riskInfo.sub}
          color={stats?.highRisk > 10 ? "red" : "muted"}
        />
      </div>
      {!isLoading && <FloatingChat stats={stats} analytics={dummyAnalytics} />}
    </div>
  );
};

export default Dashboard;
