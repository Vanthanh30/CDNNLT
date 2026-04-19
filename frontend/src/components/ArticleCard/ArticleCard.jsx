import React from "react";
import { Zap } from "lucide-react";
import "./ArticleCard.css";

const ArticleCard = ({ article }) => {
  const tag = article.keywords
    ? article.keywords.split(",")[0].toUpperCase()
    : "TIN TỨC";
  const date = new Date(article.created_at).toLocaleDateString("vi-VN");

  return (
    <div className="card article-card">
      <div className="article-image-placeholder">
        <div className="mock-lines"></div>
      </div>
      <div className="article-info">
        <div className="article-meta">
          <span className="tag">{tag}</span>
          <span className="time">{date}</span>
        </div>
        <h3>
          <a
            href={article.link}
            target="_blank"
            rel="noreferrer"
            style={{ color: "inherit", textDecoration: "none" }}
          >
            {article.title}
          </a>
        </h3>
        <div className="smart-summary">
          <Zap className="icon-zap" size={16} />
          <div>
            <strong>AI PHÂN TÍCH TỪ KHÓA</strong>
            <p style={{ color: "#f43f5e", fontWeight: "bold" }}>
              {article.keywords || "Đang chờ NLP phân tích..."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticleCard;
