import React, { useState, useEffect } from "react";
import { Search, Bell, RotateCcw, Box } from "lucide-react";
import { articleService } from "../../services/api";
import "./Header.css";

const Header = () => {
  const [lastUpdated, setLastUpdated] = useState("Đang tải...");

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const data = await articleService.getAllArticles();
        if (!data.length) {
          setLastUpdated("Chưa có dữ liệu");
          return;
        }
        // Lấy processed_at mới nhất
        const latest = data
          .map((a) => a.processed_at)
          .filter(Boolean)
          .sort()
          .reverse()[0];

        if (!latest) {
          setLastUpdated("Vừa cập nhật");
          return;
        }

        const diff = Math.floor((new Date() - new Date(latest)) / 60000);
        if (diff < 1) setLastUpdated("Vừa cập nhật");
        else if (diff < 60) setLastUpdated(`${diff} phút trước`);
        else if (diff < 1440) setLastUpdated(`${Math.floor(diff / 60)} giờ trước`);
        else setLastUpdated(`${Math.floor(diff / 1440)} ngày trước`);
      } catch {
        setLastUpdated("Không thể kết nối");
      }
    };
    fetchLatest();
  }, []);

  return (
    <header className="header">
      <h2 className="header-title">Phân tích Hệ thống (Sentinel)</h2>

      <div className="search-bar">
        <Search size={16} color="var(--text-muted)" />
        <input type="text" placeholder="Tìm kiếm mầm bệnh toàn cầu..." />
      </div>

      <div className="header-actions">
        <span className="last-updated">Cập nhật: {lastUpdated}</span>
        <button className="icon-btn"><Bell size={18} /></button>
        <button className="icon-btn"><RotateCcw size={18} /></button>
        <button className="icon-btn"><Box size={18} /></button>
      </div>
    </header>
  );
};

export default Header;