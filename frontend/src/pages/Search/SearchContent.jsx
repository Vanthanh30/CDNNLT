import React, { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Filter, ChevronLeft, ChevronRight, X } from "lucide-react";
import FloatingChat from "../../components/FloatingChat/FloatingChat";
import ArticleRow from "../../components/ArticleRow/ArticleRow";
import { useArticles } from "../../hooks/useArticles";
import "./SearchContent.css";

// ── Constants ──────────────────────────────────────────────
const DATE_RANGES = ["Tất Cả", "7 Ngày Qua", "30 Ngày Qua"];

const RISK_LEVELS = [
  { label: "Cao (HIGH)", key: "HIGH", color: "#ef4444" },
  { label: "Trung bình (MEDIUM)", key: "MEDIUM", color: "#f59e0b" },
  { label: "Thấp / Chưa xác định", key: "LOW", color: "#10b981" },
];

// ── Helpers ───────────────────────────────────────────────
const countRisk = (articles, key) =>
  key === "LOW"
    ? articles.filter((a) => !a.risk_level || a.risk_level === "LOW").length
    : articles.filter((a) => a.risk_level === key).length;

const pct = (count, total) =>
  total > 0 ? Math.round((count / total) * 100) : 0;

// ── Sub-components ────────────────────────────────────────
const LocationBadge = ({ location, onClear }) => (
  <div
    style={{
      marginTop: 8,
      padding: "6px 12px",
      background: "#1e293b",
      borderRadius: 6,
      fontSize: 13,
      color: "#0ea5e9",
      display: "inline-flex",
      gap: 8,
      alignItems: "center",
    }}
  >
    📍 Đang lọc: <strong>{location}</strong>
    <button
      onClick={onClear}
      style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", padding: 0 }}
    >
      <X size={14} />
    </button>
  </div>
);

// ✅ Fix: nhận riskKey thay vì key (key là reserved prop của React)
const RiskRow = ({ label, riskKey, color, articles }) => {
  const count = countRisk(articles, riskKey);
  const percentage = pct(count, articles.length);
  return (
    <div className="risk-row">
      <div className="risk-label-row">
        <span className="risk-label" style={{ color }}>{label}</span>
        <span className="risk-count">{count} bài ({percentage}%)</span>
      </div>
      <div className="risk-bar-bg">
        <div className="risk-bar-fill" style={{ width: `${percentage}%`, backgroundColor: color }} />
      </div>
    </div>
  );
};

const Pagination = ({ pagination }) => {
  const { currentPage, totalPages, paginate } = pagination;
  if (totalPages <= 1) return null;
  return (
    <div className="pagination">
      <button className="page-btn" onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1}>
        <ChevronLeft size={18} /> Trước
      </button>
      <span className="page-info">
        Trang <strong style={{ color: "#0ea5e9" }}>{currentPage}</strong> / {totalPages}
      </span>
      <button className="page-btn" onClick={() => paginate(currentPage + 1)} disabled={currentPage === totalPages}>
        Sau <ChevronRight size={18} />
      </button>
    </div>
  );
};

// ── Main component ────────────────────────────────────────
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

  // Auto-open advanced panel when navigating from map with ?location=
  useEffect(() => {
    const loc = searchParams.get("location");
    if (loc) {
      updateFilter("location", loc);
      setShowAdvanced(true);
    }
  }, [searchParams, updateFilter]);

  // Sidebar stats derived from filtered articles
  const stats = useMemo(() => {
    if (!filteredArticles.length) return { highRisk: 0, topDisease: null, topCount: 0 };

    const counts = filteredArticles.reduce((acc, a) => {
      if (a.disease_name) acc[a.disease_name] = (acc[a.disease_name] || 0) + 1;
      return acc;
    }, {});

    const [topDisease, topCount] = Object.entries(counts).sort((a, b) => b[1] - a[1])[0] ?? [null, 0];

    return {
      highRisk: filteredArticles.filter((a) => a.risk_level === "HIGH").length,
      topDisease,
      topCount,
      total_articles: filteredArticles.length,
      top_keyword: topDisease,
      top_keyword_count: topCount,
    };
  }, [filteredArticles]);

  const hasLocationFilter = filters.location && filters.location !== "Tất Cả";

  return (
    <div className="search-tab-container">
      {/* Header */}
      <div className="search-header">
        <h2>Công cụ Tìm kiếm Thông minh</h2>
        <p>Tổng hợp thông tin y tế và dịch bệnh từ các nguồn báo chí điện tử</p>
        {hasLocationFilter && (
          <LocationBadge location={filters.location} onClear={() => updateFilter("location", "Tất Cả")} />
        )}
      </div>

      {/* Search controls */}
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
          {DATE_RANGES.map((range) => (
            <button
              key={range}
              className={`filter-btn${filters.range === range ? " active" : ""}`}
              onClick={() => updateFilter("range", range)}
            >
              {range}
            </button>
          ))}
        </div>
        <button
          className={`advanced-btn${showAdvanced ? " active-adv" : ""}`}
          onClick={() => setShowAdvanced((v) => !v)}
        >
          <Filter size={18} /> BỘ LỌC NÂNG CAO
        </button>
      </div>

      {/* Advanced filters */}
      {showAdvanced && (
        <div className="advanced-filters-panel">
          <div className="filter-group">
            <label>Loại Bệnh</label>
            <select value={filters.disease || "Tất Cả"} onChange={(e) => updateFilter("disease", e.target.value)}>
              <option value="Tất Cả">Tất Cả Bệnh</option>
              {uniqueOptions.diseases?.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <label>Địa Điểm</label>
            <select value={filters.location || "Tất Cả"} onChange={(e) => updateFilter("location", e.target.value)}>
              <option value="Tất Cả">Toàn quốc</option>
              {uniqueOptions.locations?.map((loc) => <option key={loc} value={loc}>{loc}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <label>Mức Rủi Ro</label>
            <select value={filters.risk_level || "Tất Cả"} onChange={(e) => updateFilter("risk_level", e.target.value)}>
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

      {/* Main grid */}
      <div className="search-grid">
        {/* Articles list */}
        <div className="main-column">
          {isLoading ? (
            <p style={{ textAlign: "center", padding: 40, color: "#0ea5e9" }}>⏳ Đang tổng hợp dữ liệu...</p>
          ) : currentArticles.length === 0 ? (
            <p style={{ textAlign: "center", padding: 40, color: "#94a3b8" }}>Không có dữ liệu phù hợp.</p>
          ) : (
            <>
              {currentArticles.map((art) => <ArticleRow key={art.article_id} article={art} />)}
              <Pagination pagination={pagination} />
            </>
          )}
        </div>

        {/* Sidebar */}
        <div className="side-column">
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
              {stats.topDisease && (
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

          <div className="card widget-card">
            <h3 style={{ margin: "0 0 16px" }}>Phân bố Mức độ Rủi ro</h3>
            <div className="risk-distribution">
              {/* ✅ Fix: tách riskKey ra khỏi spread để tránh lỗi React key prop */}
              {RISK_LEVELS.map((level) => (
                <RiskRow
                  key={level.key}
                  label={level.label}
                  riskKey={level.key}
                  color={level.color}
                  articles={filteredArticles}
                />
              ))}
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
          top_keywords: stats.top_keyword
            ? [{ keyword: stats.top_keyword, count: stats.top_keyword_count }]
            : [],
        }}
      />
    </div>
  );
};

export default SearchContent;