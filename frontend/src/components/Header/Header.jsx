import React, { useState, useEffect } from "react";
import { Bell, RotateCcw, Box } from "lucide-react";
import { articleService } from "../../services/api";
import "./Header.css";

// ── helpers ──
const timeAgo = (dateStr) => {
  if (!dateStr) return null;
  const diff = Math.floor((new Date() - new Date(dateStr)) / 60000);
  if (diff < 1) return "Vừa cập nhật";
  if (diff < 60) return `${diff} phút trước`;
  if (diff < 1440) return `${Math.floor(diff / 60)} giờ trước`;
  return `${Math.floor(diff / 1440)} ngày trước`;
};

// ── Main Header ──
const Header = () => {
  const [lastUpdated, setLastUpdated] = useState("Đang tải...");

  // fetch articles 1 lần để lấy last updated
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await articleService.getAllArticles();
        if (!data.length) { setLastUpdated("Chưa có dữ liệu"); return; }
        const latest = data.map((a) => a.processed_at).filter(Boolean).sort().reverse()[0];
        setLastUpdated(latest ? (timeAgo(latest) || "Vừa cập nhật") : "Vừa cập nhật");
      } catch {
        setLastUpdated("Không thể kết nối");
      }
    };
    fetchData();
  }, []);

  return (
    <header className="header">
      <h2 className="header-title">Phân tích Hệ thống (Sentinel)</h2>

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