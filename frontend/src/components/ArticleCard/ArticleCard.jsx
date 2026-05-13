import React from "react";
import { Zap } from "lucide-react";
import "./ArticleCard.css";

const RISK_COLOR = {
  HIGH: "#ef4444",
  MEDIUM: "#f59e0b",
  LOW: "#10b981",
};

const ArticleCard = ({ article }) => {
  const tag = article.disease_name || "TIN TỨC CHUNG";
  const date = article.processed_at
    ? new Date(article.processed_at).toLocaleDateString("vi-VN")
    : "—";
  const color = RISK_COLOR[article.risk_level] || RISK_COLOR.LOW;
  const hasStats = article.cases_infected > 0 || article.cases_dead > 0;

  return (
    <div className="article-card">
      <div className="article-image-placeholder">
        <div className="mock-lines" />
      </div>

      <div className="article-info">
        <div className="article-meta">
          <span className="tag" style={{ color, borderColor: color }}>
            {tag.toUpperCase()}
          </span>
          <span className="time">{date}</span>
        </div>

        <h3>
          <a href={article.url} target="_blank" rel="noreferrer">
            {article.title || "Không có tiêu đề"}
          </a>
        </h3>

        <div className="smart-summary">
          <Zap className="icon-zap" size={16} />
          <div>
            <strong>AI PHÂN TÍCH</strong>
            <p className="disease-info" style={{ color }}>
              {article.disease_name
                ? `${article.disease_name}${article.location ? ` — ${article.location}` : ""}`
                : "Đang chờ NLP phân tích..."}
            </p>
            {hasStats && (
              <p className="stats">
                🤒 Nhiễm: {article.cases_infected ?? 0} | 💀 Tử vong: {article.cases_dead ?? 0}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticleCard;