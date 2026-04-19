import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  BarChart2,
  FileText,
  Search,
  AlertTriangle,
} from "lucide-react";
import "./Sidebar.css";

const Sidebar = () => {
  return (
    <aside className="sidebar">
      <div className="brand">
        <h1 className="brand-name">Clinical Sentinel</h1>
        <span className="brand-version">V2.4 GIÁM SÁT TRỰC TIẾP</span>
      </div>

      <nav className="nav-menu">
        <NavLink
          to="/"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <LayoutDashboard size={18} /> Tổng quan
        </NavLink>

        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <BarChart2 size={18} /> Phân tích
        </NavLink>

        <NavLink to="/reports" className="nav-item">
          <FileText size={18} /> Báo cáo
        </NavLink>

        <NavLink to="/search" className="nav-item">
          <Search size={18} /> Tìm kiếm
        </NavLink>
      </nav>

      <div className="risk-alert">
        <div className="alert-header">
          <AlertTriangle size={16} color="var(--accent-red)" />
          <span>Hệ thống Cảnh báo</span>
        </div>
        <p>Phát hiện 3 ổ dịch rủi ro cao tại khu vực miền Trung.</p>
      </div>
    </aside>
  );
};

export default Sidebar;
