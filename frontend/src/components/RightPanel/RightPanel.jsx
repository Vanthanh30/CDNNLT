import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { articleService } from "../../services/api";
import "./RightPanel.css";

const RISK_COLOR = {
  HIGH: { dot: "dot-red", text: "var(--accent-red)" },
  MEDIUM: { dot: "dot-orange", text: "#f97316" },
  LOW: { dot: "dot-blue", text: "var(--accent-cyan)" },
};

const RightPanel = () => {
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await articleService.getAllArticles();
        setTotalCount(data.length);
        setArticles(data.slice(0, 5));
      } catch (err) {
        console.error("Lỗi fetch:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
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
            articles.map((art) => {
              const risk = RISK_COLOR[art.risk_level] || RISK_COLOR.LOW;
              return (
                <div className="update-item" key={art.article_id}>
                  <div className={`dot ${risk.dot}`}></div>
                  <div className="update-content">
                    <h4 style={{ color: risk.text }}>
                      {art.disease_name
                        ? `${art.disease_name}${art.location ? ` — ${art.location}` : ""}`
                        : "Cập nhật chung"}
                    </h4>
                    <p>{art.title}</p>
                    <span className="timestamp">
                      {art.processed_at
                        ? new Date(art.processed_at).toLocaleString("vi-VN")
                        : "—"}
                    </span>
                    <a
                      href={art.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: "block",
                        fontSize: "0.7rem",
                        color: "#3b82f6",
                        marginTop: "4px",
                      }}
                    >
                      Đọc nguồn tin ↗
                    </a>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <button
          className="view-log-btn"
          onClick={() => navigate("/search")}
        >
          XEM TẤT CẢ ({totalCount}) TIN TỨC
        </button>
      </div>
    </div>
  );
};

export default RightPanel;