import React, { useState, useEffect } from "react";
import { articleService } from "../../services/api";
import "./RightPanel.css";

const RightPanel = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecentArticles = async () => {
      try {
        const data = await articleService.getAllArticles();
        setArticles(data.slice(0, 5));
      } catch (err) {
        console.error("Lỗi fetch:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentArticles();
  }, []);

  return (
    <div className="right-panel-wrapper">
      <div className="updates-section">
        <div className="section-header">
          <h3>Cập nhật Mới nhất</h3>
        </div>

        <div className="update-list">
          {loading ? (
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Đang tải dữ liệu API...
            </p>
          ) : articles.length === 0 ? (
            <p>Chưa có dữ liệu</p>
          ) : (
            articles.map((art) => (
              <div className="update-item" key={art.id}>
                <div className="dot dot-red"></div>
                <div className="update-content">
                  <h4 style={{ color: "var(--accent-cyan)" }}>
                    {art.keywords || "Cập nhật chung"}
                  </h4>
                  <p>{art.title}</p>
                  <span className="timestamp">
                    {new Date(art.created_at).toLocaleTimeString("vi-VN")}
                  </span>
                  <a
                    href={art.link}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: "block",
                      fontSize: "0.7rem",
                      color: "#3b82f6",
                      marginTop: "4px",
                    }}
                  >
                    Đọc nguồn tin
                  </a>
                </div>
              </div>
            ))
          )}
        </div>
        <button className="view-log-btn">
          XEM TẤT CẢ ({articles.length}) TIN TỨC
        </button>
      </div>
    </div>
  );
};

export default RightPanel;
