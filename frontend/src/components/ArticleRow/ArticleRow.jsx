import React, { useState } from "react";
import { Zap, ExternalLink } from "lucide-react";
import "./ArticleRow.css";

const RISK_COLOR = { HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#10b981" };
const RISK_LABEL = { HIGH: "Cao", MEDIUM: "Trung bình", LOW: "Thấp" };

const getFavicon = (url) => {
  try {
    return `https://www.google.com/s2/favicons?domain=${new URL(url).origin}&sz=32`;
  } catch {
    return null;
  }
};

const ArticleRow = ({ article }) => {
  const [imgError, setImgError] = useState(false);
  const riskColor = RISK_COLOR[article.risk_level] || RISK_COLOR.LOW;
  const favicon = getFavicon(article.url);
  const hasStats = article.cases_infected > 0 || article.cases_dead > 0;

  return (
    <div className="article-row-container">
      <div className="article-row-img-box">
        {favicon && !imgError ? (
          <img
            src={favicon}
            alt=""
            className="article-row-favicon"
            onError={() => setImgError(true)}
          />
        ) : (
          <span className="article-row-placeholder">📰</span>
        )}
      </div>

      <div className="article-row-content">
        <div className="article-row-meta">
          <span className="disease-badge" style={{ color: riskColor, borderColor: riskColor }}>
            {(article.disease_name || "TIN TỨC CHUNG").toUpperCase()}
          </span>

          {article.location && <span className="meta-location">📍 {article.location}</span>}

          <span className="meta-date">
            {article.processed_at
              ? new Date(article.processed_at).toLocaleDateString("vi-VN")
              : "—"}
          </span>
        </div>

        <h3 className="article-row-title">
          <a href={article.url} target="_blank" rel="noreferrer">
            {article.title || "Không có tiêu đề"}
          </a>
        </h3>

        {article.summary && <p className="article-row-summary">{article.summary}</p>}

        <div className="article-row-footer">
          <span className="risk-info" style={{ color: riskColor }}>
            <Zap size={13} /> Rủi ro: {RISK_LABEL[article.risk_level] || "Thấp"}
          </span>

          {hasStats && (
            <span className="stats-info">
              🤒 {article.cases_infected ?? 0} nhiễm | 💀 {article.cases_dead ?? 0} tử vong
            </span>
          )}

          <a href={article.url} target="_blank" rel="noreferrer" className="read-more-link">
            Đọc bài gốc <ExternalLink size={12} />
          </a>
        </div>
      </div>
    </div>
  );
};

export default ArticleRow;