import React from "react";
import { Search, Bell, RotateCcw, Box } from "lucide-react";
import "./Header.css";

const Header = () => {
  return (
    <header className="header">
      <h2 className="header-title">Phân tích Hệ thống (Sentinel)</h2>

      <div className="search-bar">
        <Search size={16} color="var(--text-muted)" />
        <input type="text" placeholder="Tìm kiếm mầm bệnh toàn cầu..." />
      </div>

      <div className="header-actions">
        <span className="last-updated">Cập nhật: 5p trước</span>
        <button className="icon-btn">
          <Bell size={18} />
        </button>
        <button className="icon-btn">
          <RotateCcw size={18} />
        </button>
        <button className="icon-btn">
          <Box size={18} />
        </button>
      </div>
    </header>
  );
};

export default Header;
