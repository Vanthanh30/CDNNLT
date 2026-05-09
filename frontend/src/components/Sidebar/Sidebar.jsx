import React, { useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, BarChart2, FileText, Search, AlertTriangle } from "lucide-react";
import { articleService } from "../../services/api";
import "./Sidebar.css";

const Sidebar = () => {
  const [alertMsg, setAlertMsg] = useState("Đang phân tích dữ liệu...");

  useEffect(() => {
    const fetchAlert = async () => {
      try {
        const data = await articleService.getAllArticles();
        if (!data.length) {
          setAlertMsg("Hệ thống đang thu thập dữ liệu.");
          return;
        }

        // Tìm bệnh xuất hiện nhiều nhất
        const counts = {};
        data.forEach((a) => {
          if (a.disease_name) counts[a.disease_name] = (counts[a.disease_name] || 0) + 1;
        });
        const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
        const highRisk = data.filter((a) => a.risk_level === "HIGH").length;

        if (top) {
          setAlertMsg(
            `Phát hiện ${top[1]} bài về "${top[0]}". ${highRisk > 0 ? `${highRisk} bài rủi ro cao.` : ""}`
          );
        } else {
          setAlertMsg(`Đã quét ${data.length} bài, chưa phân loại bệnh.`);
        }
      } catch {
        setAlertMsg("Không thể kết nối API.");
      }
    };
    fetchAlert();
  }, []);

  return (
    <aside className="sidebar">
      <div className="brand">
        <h1 className="brand-name">Clinical Sentinel</h1>
        <span className="brand-version">V2.4 GIÁM SÁT TRỰC TIẾP</span>
      </div>

      <nav className="nav-menu">
        <NavLink to="/" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
          <LayoutDashboard size={18} /> Tổng quan
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
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
        <p>{alertMsg}</p>
      </div>
    </aside>
  );
};

export default Sidebar;