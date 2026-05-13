import React, { useState, useEffect } from "react";
import { Bell, RotateCcw, Box } from "lucide-react";
import { articleService } from "../../services/api";
import "./Header.css";

const formatTimeAgo = (dateStr) => {
  if (!dateStr) return null;
  const diff = Math.floor((new Date() - new Date(dateStr)) / 60000);
  if (diff < 1) return "Vừa cập nhật";
  if (diff < 60) return `${diff} phút trước`;
  if (diff < 1440) return `${Math.floor(diff / 60)} giờ trước`;
  return `${Math.floor(diff / 1440)} ngày trước`;
};

const Header = () => {
  const [lastUpdated, setLastUpdated] = useState("Đang tải...");

  const fetchData = async () => {
    try {
      const data = await articleService.getAllArticles();
      if (!data?.length) return setLastUpdated("Chưa có dữ liệu");

      const latest = data
        .map(a => a.processed_at)
        .filter(Boolean)
        .sort()
        .reverse()[0];

      setLastUpdated(formatTimeAgo(latest) || "Vừa cập nhật");
    } catch {
      setLastUpdated("Lỗi kết nối");
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <header className="header">
      <h2 className="header-title">Phân tích Hệ thống <span>(Sentinel)</span></h2>

      <div className="header-actions">
        <span className="last-updated">{lastUpdated}</span>
        <div className="btn-group">
          <button className="icon-btn"><Bell size={18} /></button>
          <button className="icon-btn" onClick={fetchData}><RotateCcw size={18} /></button>
          <button className="icon-btn"><Box size={18} /></button>
        </div>
      </div>
    </header>
  );
};

export default Header;