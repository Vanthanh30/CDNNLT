import React, { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search,
  Filter,
  ArrowUp,
  Zap,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  X,
  ExternalLink,
} from "lucide-react";
import FloatingChat from "../../components/FloatingChat/FloatingChat";
import { useArticles } from "../../hooks/useArticles";
import "./SearchContent.css";

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

  return (
    <div
      className="card article-card"
      style={{
        display: "flex",
        gap: "16px",
        padding: "16px",
        marginBottom: "12px",
      }}
    >
      <div
        style={{
          flexShrink: 0,
          width: "120px",
          height: "90px",
          borderRadius: "8px",
          overflow: "hidden",
          background: "#1e293b",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {favicon && !imgError ? (
          <img
            src={favicon}
            alt=""
            style={{ width: "40px", height: "40px", opacity: 0.7 }}
            onError={() => setImgError(true)}
          />
        ) : (
          <span style={{ fontSize: "28px" }}>📰</span>
        )}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: "flex",
            gap: "8px",
            alignItems: "center",
            flexWrap: "wrap",
            marginBottom: "6px",
          }}
        >
          <span
            style={{
              color: riskColor,
              borderColor: riskColor,
              fontSize: "11px",
              padding: "2px 8px",
              border: "1px solid",
              borderRadius: "4px",
              fontWeight: "700",
            }}
          >
            {(article.disease_name || "TIN TỨC CHUNG").toUpperCase()}
          </span>
          {article.location && (
            <span style={{ fontSize: "11px", color: "#64748b" }}>
              📍 {article.location}
            </span>
          )}
          <span
            style={{ fontSize: "11px", color: "#64748b", marginLeft: "auto" }}
          >
            {article.processed_at
              ? new Date(article.processed_at).toLocaleDateString("vi-VN")
              : "—"}
          </span>
        </div>
        <h3 style={{ margin: "0 0 6px", fontSize: "14px", lineHeight: "1.4" }}>
          <a
            href={article.url}
            target="_blank"
            rel="noreferrer"
            style={{ color: "inherit", textDecoration: "none" }}
          >
            {article.title || "Không có tiêu đề"}
          </a>
        </h3>
        {article.summary && (
          <p
            style={{
              fontSize: "12px",
              color: "#94a3b8",
              margin: "0 0 8px",
              overflow: "hidden",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
            }}
          >
            {article.summary}
          </p>
        )}
        <div
          style={{
            display: "flex",
            gap: "12px",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <span
            style={{
              fontSize: "12px",
              color: riskColor,
              fontWeight: "bold",
              display: "flex",
              gap: "4px",
              alignItems: "center",
            }}
          >
            <Zap size={13} /> Rủi ro: {RISK_LABEL[article.risk_level] || "Thấp"}
          </span>
          {(article.cases_infected > 0 || article.cases_dead > 0) && (
            <span style={{ fontSize: "11px", color: "#64748b" }}>
              🤒 {article.cases_infected ?? 0} nhiễm | 💀{" "}
              {article.cases_dead ?? 0} tử vong
            </span>
          )}
          <a
            href={article.url}
            target="_blank"
            rel="noreferrer"
            style={{
              marginLeft: "auto",
              fontSize: "11px",
              color: "#3b82f6",
              display: "flex",
              gap: "4px",
              alignItems: "center",
            }}
          >
            Đọc bài gốc <ExternalLink size={12} />
          </a>
        </div>
      </div>
    </div>
  );
};

const SearchContent = () => {
  const [searchParams] = useSearchParams();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const {
    isLoading,
    searchQuery,
    setSearchQuery,
    handleSearch,
    filters,
    updateFilter,
    resetFilters,
    uniqueOptions,
    currentArticles,
    totalArticlesCount,
    pagination,
    filteredArticles,
  } = useArticles();

  useEffect(() => {
    const loc = searchParams.get("location");
    if (loc) {
      updateFilter("location", loc);
      setShowAdvanced(true);
    }
  }, [searchParams]);

  const stats = useMemo(() => {
    if (!filteredArticles.length)
      return { highRisk: 0, topDisease: null, topCount: 0 };

    const highRisk = filteredArticles.filter(
      (a) => a.risk_level === "HIGH",
    ).length;

    const counts = {};
    filteredArticles.forEach((a) => {
      if (a.disease_name)
        counts[a.disease_name] = (counts[a.disease_name] || 0) + 1;
    });

    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];

    return {
      highRisk,
      topDisease: top?.[0] || null,
      topCount: top?.[1] || 0,
      total_articles: filteredArticles.length,
      top_keyword: top?.[0] || null,
      top_keyword_count: top?.[1] || 0,
    };
  }, [filteredArticles]);

  return (
    <div className="search-tab-container">
      <div className="search-header">
        <h2>Công cụ Tìm kiếm Thông minh</h2>
        <p>Tổng hợp thông tin y tế và dịch bệnh từ các nguồn báo chí điện tử</p>
        {filters.location && filters.location !== "Tất Cả" && (
          <div
            style={{
              marginTop: "8px",
              padding: "6px 12px",
              background: "#1e293b",
              borderRadius: "6px",
              fontSize: "13px",
              color: "#0ea5e9",
              display: "inline-flex",
              gap: "8px",
              alignItems: "center",
            }}
          >
            📍 Đang lọc: <strong>{filters.location}</strong>
            <button
              onClick={() => updateFilter("location", "Tất Cả")}
              style={{
                background: "none",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer",
                padding: "0",
              }}
            >
              <X size={14} />
            </button>
          </div>
        )}
      </div>

      <div className="search-controls">
        <div className="search-input-box">
          <Search className="icon-search" size={20} />
          <input
            type="text"
            placeholder="Nhập từ khóa mầm bệnh (vd: covid) và ấn Enter..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
          />
        </div>
        <div className="date-filters">
          {["Tất Cả", "7 Ngày Qua", "30 Ngày Qua"].map((range) => (
            <button
              key={range}
              className={`filter-btn ${filters.range === range ? "active" : ""}`}
              onClick={() => updateFilter("range", range)}
            >
              {range}
            </button>
          ))}
        </div>
        <button
          className={`advanced-btn ${showAdvanced ? "active-adv" : ""}`}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          <Filter size={18} /> BỘ LỌC NÂNG CAO
        </button>
      </div>

      {showAdvanced && (
        <div className="advanced-filters-panel">
          <div className="filter-group">
            <label>Loại Bệnh</label>
            <select
              value={filters.disease || "Tất Cả"}
              onChange={(e) => updateFilter("disease", e.target.value)}
            >
              <option value="Tất Cả">Tất Cả Bệnh</option>
              {uniqueOptions.diseases?.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Địa Điểm</label>
            <select
              value={filters.location || "Tất Cả"}
              onChange={(e) => updateFilter("location", e.target.value)}
            >
              <option value="Tất Cả">Toàn quốc</option>
              {uniqueOptions.locations?.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Mức Rủi Ro</label>
            <select
              value={filters.risk_level || "Tất Cả"}
              onChange={(e) => updateFilter("risk_level", e.target.value)}
            >
              <option value="Tất Cả">Tất Cả</option>
              <option value="HIGH">Cao</option>
              <option value="MEDIUM">Trung bình</option>
              <option value="LOW">Thấp</option>
            </select>
          </div>
          <button className="clear-filter-btn" onClick={resetFilters}>
            <X size={16} /> Xóa Lọc
          </button>
        </div>
      )}

      <div className="search-grid">
        <div className="main-column">
          {isLoading ? (
            <p
              style={{ textAlign: "center", padding: "40px", color: "#0ea5e9" }}
            >
              ⏳ Đang tổng hợp dữ liệu...
            </p>
          ) : currentArticles.length === 0 ? (
            <p
              style={{ textAlign: "center", padding: "40px", color: "#94a3b8" }}
            >
              Không có dữ liệu phù hợp.
            </p>
          ) : (
            <>
              {currentArticles.map((art) => (
                <ArticleRow key={art.article_id} article={art} />
              ))}
              {pagination.totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="page-btn"
                    onClick={() =>
                      pagination.paginate(pagination.currentPage - 1)
                    }
                    disabled={pagination.currentPage === 1}
                  >
                    <ChevronLeft size={18} /> Trước
                  </button>
                  <span className="page-info">
                    Trang{" "}
                    <strong style={{ color: "#0ea5e9" }}>
                      {pagination.currentPage}
                    </strong>{" "}
                    / {pagination.totalPages}
                  </span>
                  <button
                    className="page-btn"
                    onClick={() =>
                      pagination.paginate(pagination.currentPage + 1)
                    }
                    disabled={pagination.currentPage === pagination.totalPages}
                  >
                    Sau <ChevronRight size={18} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        <div className="side-column">
          {/* ✅ FIX: Summary Stats Card */}
          <div className="card widget-card">
            <div className="widget-header">
              <h3>Tóm tắt Nhanh</h3>
            </div>
            <div className="summary-list">
              <div className="summary-item">
                <div className="stat-value up">{totalArticlesCount}</div>
                <div className="stat-text">
                  <strong>TỔNG SỐ BÀI BÁO</strong>
                  <p>Hiển thị {totalArticlesCount} tin tức</p>
                </div>
              </div>
              {stats?.topDisease && (
                <div className="summary-item">
                  <div className="stat-value danger">{stats.topCount}</div>
                  <div className="stat-text">
                    <strong>{stats.topDisease.toUpperCase()}</strong>
                    <p>Bệnh xuất hiện nhiều nhất</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Risk Distribution Card */}
          <div className="card widget-card">
            <h3>Phân bố Mức độ Rủi ro</h3>
            <div className="risk-distribution">
              {[
                { label: "Cao (HIGH)", key: "HIGH", color: "#ef4444" },
                {
                  label: "Trung bình (MEDIUM)",
                  key: "MEDIUM",
                  color: "#f59e0b",
                },
                { label: "Thấp / Chưa xác định", key: "LOW", color: "#10b981" },
              ].map(({ label, key, color }) => {
                const count =
                  key === "LOW"
                    ? filteredArticles.filter(
                        (a) => !a.risk_level || a.risk_level === "LOW",
                      ).length
                    : filteredArticles.filter((a) => a.risk_level === key)
                        .length;

                const pct =
                  filteredArticles.length > 0
                    ? Math.round((count / filteredArticles.length) * 100)
                    : 0;

                return (
                  <div key={key} className="risk-row">
                    <div className="risk-label-row">
                      <span className="risk-label" style={{ color }}>
                        {label}
                      </span>
                      <span className="risk-count">
                        {count} bài ({pct}%)
                      </span>
                    </div>
                    <div className="risk-bar-bg">
                      <div
                        className="risk-bar-fill"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="risk-total">
              Tổng cộng: <strong>{totalArticlesCount}</strong> bài đã phân tích
            </p>
          </div>
        </div>
      </div>
      <FloatingChat
        stats={stats}
        analytics={{
          top_keywords: stats?.top_keyword
            ? [{ keyword: stats.top_keyword, count: stats.top_keyword_count }]
            : [],
        }}
      />
    </div>
  );
};

export default SearchContent;
