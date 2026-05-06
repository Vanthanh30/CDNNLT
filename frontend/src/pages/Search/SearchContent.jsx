import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Filter, ArrowUp, Zap, TrendingUp, ChevronLeft, ChevronRight, X, ExternalLink, AlertCircle, Clock, MapPin, Activity } from "lucide-react";
import { useArticles } from "../../hooks/useArticles";
import "./SearchContent.css";

const RISK_COLOR = { HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#10b981" };
const RISK_LABEL = { HIGH: "Cao", MEDIUM: "Trung bình", LOW: "Thấp" };

const RISK_META = {
  HIGH: { label: "Cao", cls: "risk-high" },
  MEDIUM: { label: "Trung bình", cls: "risk-medium" },
  LOW: { label: "Thấp", cls: "risk-low" },
};

const getFavicon = (url) => {
  try { return `https://www.google.com/s2/favicons?domain=${new URL(url).origin}&sz=32`; }
  catch { return null; }
};

const timeAgo = (dateStr) => {
  if (!dateStr) return null;
  const diff = Math.floor((new Date() - new Date(dateStr)) / 60000);
  if (diff < 1) return "Vừa cập nhật";
  if (diff < 60) return `${diff} phút trước`;
  if (diff < 1440) return `${Math.floor(diff / 60)} giờ trước`;
  return `${Math.floor(diff / 1440)} ngày trước`;
};

// ── Result Card từ Search Overlay ──
const ResultCard = ({ article }) => {
  const risk = RISK_META[article.risk_level] || RISK_META.LOW;
  const ago = timeAgo(article.processed_at);

  return (
    <div className="sr-card">
      <div className="sr-card-top">
        <div className="sr-card-info">
          {article.disease_name && (
            <span className="sr-disease">{article.disease_name}</span>
          )}
          <span className={`sr-risk ${risk.cls}`}>{risk.label}</span>
        </div>
        {ago && (
          <span className="sr-time">
            <Clock size={11} /> {ago}
          </span>
        )}
      </div>

      <h4 className="sr-title">{article.title || "Không có tiêu đề"}</h4>

      {(article.summary || article.content_clean) && (
        <p className="sr-summary">
          {(article.summary || article.content_clean || "").slice(0, 160)}
          {(article.summary || article.content_clean || "").length > 160 ? "…" : ""}
        </p>
      )}

      <div className="sr-card-footer">
        <div className="sr-meta">
          {article.location && (
            <span className="sr-location">
              <MapPin size={11} /> {article.location}
            </span>
          )}
          {(article.cases_infected > 0 || article.cases_dead > 0) && (
            <span className="sr-cases">
              <Activity size={11} />
              {article.cases_infected > 0 && `${article.cases_infected} ca nhiễm`}
              {article.cases_infected > 0 && article.cases_dead > 0 && " · "}
              {article.cases_dead > 0 && `${article.cases_dead} tử vong`}
            </span>
          )}
        </div>
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="sr-link"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink size={12} /> Xem bài báo
          </a>
        )}
      </div>
    </div>
  );
};

// ── Search Overlay ──
const SearchOverlay = ({ query, articles, onClose }) => {
  const [activeFilter, setActiveFilter] = useState("all");

  const q = query.toLowerCase().trim();

  const normalize = (s) =>
    (s || "")
      .toLowerCase()
      .replace(/[\-\/().]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const nq = normalize(q);

  const matchDisease = (a) => {
    const nd = normalize(a.disease_name);
    if (!nd) return false;
    if (nd === nq) return true;
    if (nd.includes(nq) || nq.includes(nd)) return true;
    return false;
  };

  const byDisease = articles.filter(matchDisease);
  const byLocation = byDisease.length === 0
    ? articles.filter((a) => normalize(a.location).includes(nq))
    : [];

  const allMatched = byDisease.length > 0 ? byDisease : byLocation;

  const riskOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  allMatched.sort((x, y) => {
    const rd = (riskOrder[x.risk_level] ?? 3) - (riskOrder[y.risk_level] ?? 3);
    if (rd !== 0) return rd;
    return new Date(y.processed_at || 0) - new Date(x.processed_at || 0);
  });

  const results = allMatched.filter((a) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "high") return a.risk_level === "HIGH";
    if (activeFilter === "medium") return a.risk_level === "MEDIUM";
    if (activeFilter === "low") return a.risk_level === "LOW";
    return true;
  });

  const searchMode = byDisease.length > 0 ? "disease" : byLocation.length > 0 ? "location" : "none";
  const filteredCount = results.length;

  return (
    <div className="sr-backdrop" onClick={onClose}>
      <div className="sr-overlay" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="sr-overlay-header">
          <div className="sr-overlay-query">
            <Search size={16} />
            <span>Kết quả tìm kiếm cho <strong>"{query}"</strong></span>
            <span className="sr-total">{filteredCount} kết quả</span>
          </div>
          <button className="sr-close" onClick={onClose}><X size={18} /></button>
        </div>

        {/* Filters */}
        <div className="sr-filters">
          {[
            { key: "all", label: "Tất cả" },
            { key: "high", label: "Rủi ro cao" },
            { key: "medium", label: "Trung bình" },
            { key: "low", label: "Thấp" },
          ].map((f) => (
            <button
              key={f.key}
              className={`sr-filter-btn ${activeFilter === f.key ? "active" : ""} ${f.key !== "all" ? f.key : ""}`}
              onClick={() => setActiveFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Results */}
        <div className="sr-results">
          {results.length === 0 ? (
            <div className="sr-empty">
              <AlertCircle size={32} />
              {searchMode === "none" ? (
                <>
                  <p>Không tìm thấy bệnh nào tên <strong>"{query}"</strong></p>
                  <span>Hệ thống chỉ tìm theo tên bệnh được NLP phân loại. Thử: "Sốt xuất huyết", "COVID-19", "Dịch tả lợn"...</span>
                </>
              ) : (
                <>
                  <p>Không có kết quả với bộ lọc <strong>"{activeFilter}"</strong></p>
                  <span>Thử chọn "Tất cả" hoặc bộ lọc mức rủi ro khác</span>
                </>
              )}
            </div>
          ) : (
            results.map((a, idx) => <ResultCard key={a.article_id || idx} article={a} />)
          )}
        </div>
      </div>
    </div>
  );
};

// ── Dropdown gợi ý ──
const SearchDropdown = ({ suggestions, query, onSelect }) => {
  if (!suggestions.length) return null;
  return (
    <div className="sr-dropdown">
      {suggestions.map((s, idx) => (
        <button key={idx} className="sr-suggestion" onClick={() => onSelect(s)}>
          <Search size={13} />
          <span dangerouslySetInnerHTML={{
            __html: s.replace(new RegExp(`(${query})`, "gi"), "<mark>$1</mark>"),
          }} />
        </button>
      ))}
    </div>
  );
};

// ── Article Row cho kết quả search thường ──
const ArticleRow = ({ article }) => {
  const [imgError, setImgError] = useState(false);
  const riskColor = RISK_COLOR[article.risk_level] || RISK_COLOR.LOW;
  const favicon = getFavicon(article.url);

  return (
    <div className="card article-card" style={{ display: "flex", gap: "16px", padding: "16px", marginBottom: "12px" }}>
      <div style={{ flexShrink: 0, width: "120px", height: "90px", borderRadius: "8px", overflow: "hidden", background: "#1e293b", display: "flex", alignItems: "center", justifyContent: "center" }}>
        {favicon && !imgError
          ? <img src={favicon} alt="" style={{ width: "40px", height: "40px", opacity: 0.7 }} onError={() => setImgError(true)} />
          : <span style={{ fontSize: "28px" }}>📰</span>}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap", marginBottom: "6px" }}>
          <span style={{ color: riskColor, borderColor: riskColor, fontSize: "11px", padding: "2px 8px", border: "1px solid", borderRadius: "4px", fontWeight: "700" }}>
            {(article.disease_name || "TIN TỨC CHUNG").toUpperCase()}
          </span>
          {article.location && <span style={{ fontSize: "11px", color: "#64748b" }}>📍 {article.location}</span>}
          <span style={{ fontSize: "11px", color: "#64748b", marginLeft: "auto" }}>
            {article.processed_at ? new Date(article.processed_at).toLocaleDateString("vi-VN") : "—"}
          </span>
        </div>
        <h3 style={{ margin: "0 0 6px", fontSize: "14px", lineHeight: "1.4" }}>
          <a href={article.url} target="_blank" rel="noreferrer" style={{ color: "inherit", textDecoration: "none" }}>
            {article.title || "Không có tiêu đề"}
          </a>
        </h3>
        {article.summary && (
          <p style={{ fontSize: "12px", color: "#94a3b8", margin: "0 0 8px", overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
            {article.summary}
          </p>
        )}
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontSize: "12px", color: riskColor, fontWeight: "bold", display: "flex", gap: "4px", alignItems: "center" }}>
            <Zap size={13} /> Rủi ro: {RISK_LABEL[article.risk_level] || "Thấp"}
          </span>
          {(article.cases_infected > 0 || article.cases_dead > 0) && (
            <span style={{ fontSize: "11px", color: "#64748b" }}>
              🤒 {article.cases_infected ?? 0} nhiễm | 💀 {article.cases_dead ?? 0} tử vong
            </span>
          )}
          <a href={article.url} target="_blank" rel="noreferrer"
            style={{ marginLeft: "auto", fontSize: "11px", color: "#3b82f6", display: "flex", gap: "4px", alignItems: "center" }}>
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
  const [focused, setFocused] = useState(false);
  const [showOverlay, setShowOverlay] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const inputRef = useRef(null);

  const { isLoading, searchQuery, setSearchQuery, handleSearch, filters, updateFilter, resetFilters, uniqueOptions, currentArticles, totalArticlesCount, pagination, articles } = useArticles();

  useEffect(() => {
    const loc = searchParams.get("location");
    if (loc) { updateFilter("location", loc); setShowAdvanced(true); }
  }, [searchParams]);

  // ✅ Tính toán stats từ articles thực tế
  const stats = useMemo(() => {
    if (!articles.length) return { highRisk: 0, topDisease: null, topCount: 0 };

    const highRisk = articles.filter(a => a.risk_level === "HIGH").length;

    const counts = {};
    articles.forEach(a => {
      if (a.disease_name) counts[a.disease_name] = (counts[a.disease_name] || 0) + 1;
    });

    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];

    return {
      highRisk,
      topDisease: top?.[0] || null,
      topCount: top?.[1] || 0
    };
  }, [articles]);

  // ── LOGIC TỪ HEADER: Gợi ý từ disease_name ──
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }
    const normalize = (s) => (s || "").toLowerCase().replace(/[-\/().]/g, " ").replace(/\s+/g, " ").trim();
    const nq = normalize(searchQuery);
    const seen = new Set();
    const sugg = [];
    articles.forEach((a) => {
      const name = a.disease_name;
      if (!name) return;
      const nd = normalize(name);
      if (nd.includes(nq) && !seen.has(name)) {
        seen.add(name);
        sugg.push(name);
      }
    });
    sugg.sort((a, b) => {
      const na = normalize(a), nb = normalize(b);
      return (na.startsWith(nq) ? 0 : 1) - (nb.startsWith(nq) ? 0 : 1);
    });
    setSuggestions(sugg.slice(0, 6));
  }, [searchQuery, articles]);

  // ── LOGIC TỪ HEADER: Xử lý search ──
  const handleSearchLocal = useCallback((q = searchQuery) => {
    if (!q.trim()) return;
    setShowOverlay(true);
    setFocused(false);
    inputRef.current?.blur();
  }, [searchQuery]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearchLocal();
    if (e.key === "Escape") { setFocused(false); setSearchQuery(""); }
  };

  const handleSelectSuggestion = (s) => {
    setSearchQuery(s);
    handleSearchLocal(s);
  };

  const closeOverlay = () => setShowOverlay(false);

  return (
    <div className="search-tab-container">
      <div className="search-header">
        <h2>Công cụ Tìm kiếm Thông minh</h2>
        <p>Tổng hợp thông tin y tế và dịch bệnh từ các nguồn báo chí điện tử</p>
        {filters.location && filters.location !== "Tất Cả" && (
          <div style={{ marginTop: "8px", padding: "6px 12px", background: "#1e293b", borderRadius: "6px", fontSize: "13px", color: "#0ea5e9", display: "inline-flex", gap: "8px", alignItems: "center" }}>
            📍 Đang lọc: <strong>{filters.location}</strong>
            <button onClick={() => updateFilter("location", "Tất Cả")} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", padding: "0" }}><X size={14} /></button>
          </div>
        )}
      </div>

      {/* ── SEARCH BAR TỪ HEADER ── */}
      <div className="search-controls">
        <div className={`search-bar ${focused ? "focused" : ""}`}>
          <Search size={15} color="var(--text-muted)" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Tìm kiếm mầm bệnh, địa điểm..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setTimeout(() => setFocused(false), 150)}
            onKeyDown={handleKeyDown}
          />
          {searchQuery && (
            <button className="search-clear" onClick={() => { setSearchQuery(""); setSuggestions([]); }}>
              <X size={13} />
            </button>
          )}
          {focused && searchQuery.length >= 2 && (
            <SearchDropdown
              suggestions={suggestions}
              query={searchQuery}
              onSelect={handleSelectSuggestion}
            />
          )}
        </div>

        <div className="date-filters">
          {["Tất Cả", "7 Ngày Qua", "30 Ngày Qua"].map(range => (
            <button key={range} className={`filter-btn ${filters.range === range ? "active" : ""}`} onClick={() => updateFilter("range", range)}>{range}</button>
          ))}
        </div>
        <button className={`advanced-btn ${showAdvanced ? "active-adv" : ""}`} onClick={() => setShowAdvanced(!showAdvanced)}>
          <Filter size={18} /> BỘ LỌC NÂNG CAO
        </button>
      </div>

      {showAdvanced && (
        <div className="advanced-filters-panel">
          <div className="filter-group">
            <label>Loại Bệnh</label>
            <select value={filters.disease || "Tất Cả"} onChange={e => updateFilter("disease", e.target.value)}>
              <option value="Tất Cả">Tất Cả Bệnh</option>
              {uniqueOptions.diseases?.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <label>Địa Điểm</label>
            <select value={filters.location || "Tất Cả"} onChange={e => updateFilter("location", e.target.value)}>
              <option value="Tất Cả">Toàn quốc</option>
              {uniqueOptions.locations?.map(loc => <option key={loc} value={loc}>{loc}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <label>Mức Rủi Ro</label>
            <select value={filters.risk_level || "Tất Cả"} onChange={e => updateFilter("risk_level", e.target.value)}>
              <option value="Tất Cả">Tất Cả</option>
              <option value="HIGH">Cao</option>
              <option value="MEDIUM">Trung bình</option>
              <option value="LOW">Thấp</option>
            </select>
          </div>
          <button className="clear-filter-btn" onClick={resetFilters}><X size={16} /> Xóa Lọc</button>
        </div>
      )}

      <div className="search-grid">
        <div className="main-column">
          {isLoading ? (
            <p style={{ textAlign: "center", padding: "40px", color: "#0ea5e9" }}>⏳ Đang tổng hợp dữ liệu...</p>
          ) : currentArticles.length === 0 ? (
            <p style={{ textAlign: "center", padding: "40px", color: "#94a3b8" }}>Không có dữ liệu phù hợp.</p>
          ) : (
            <>
              {currentArticles.map(art => <ArticleRow key={art.article_id} article={art} />)}
              {pagination.totalPages > 1 && (
                <div className="pagination">
                  <button className="page-btn" onClick={() => pagination.paginate(pagination.currentPage - 1)} disabled={pagination.currentPage === 1}><ChevronLeft size={18} /> Trước</button>
                  <span className="page-info">Trang <strong style={{ color: "#0ea5e9" }}>{pagination.currentPage}</strong> / {pagination.totalPages}</span>
                  <button className="page-btn" onClick={() => pagination.paginate(pagination.currentPage + 1)} disabled={pagination.currentPage === pagination.totalPages}>Sau <ChevronRight size={18} /></button>
                </div>
              )}
            </>
          )}
        </div>

        <div className="side-column">
          {/* Summary Stats Card */}
          <div className="card widget-card">
            <div className="widget-header"><h3>Tóm tắt Nhanh</h3></div>
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

          {/* Alert Card */}
          <div className="card alert-card">
            <div className="alert-header"><Zap size={18} fill="currentColor" /> CẢNH BÁO DỊCH BỆNH</div>
            <p>{stats?.highRisk > 0 ? `Phát hiện ${stats.highRisk} bài báo rủi ro cao.` : "Chưa phát hiện bài báo rủi ro cao."}</p>
            <button className="audit-btn">KÍCH HOẠT QUY TRÌNH KIỂM TRA</button>
          </div>

          {/* Risk Distribution Card */}
          <div className="card widget-card">
            <h3>Phân bố Mức độ Rủi ro</h3>
            <div className="risk-distribution">
              {[
                { label: "Cao (HIGH)", key: "HIGH", color: "#ef4444" },
                { label: "Trung bình (MEDIUM)", key: "MEDIUM", color: "#f59e0b" },
                { label: "Thấp / Chưa xác định", key: "LOW", color: "#10b981" },
              ].map(({ label, key, color }) => {
                const count = key === "LOW"
                  ? articles.filter(a => !a.risk_level || a.risk_level === "LOW").length
                  : articles.filter(a => a.risk_level === key).length;
                const pct = articles.length > 0 ? Math.round((count / articles.length) * 100) : 0;

                return (
                  <div key={key} className="risk-row">
                    <div className="risk-label-row">
                      <span className="risk-label" style={{ color }}>{label}</span>
                      <span className="risk-count">{count} bài ({pct}%)</span>
                    </div>
                    <div className="risk-bar-bg">
                      <div className="risk-bar-fill" style={{ width: `${pct}%`, backgroundColor: color }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="risk-total">
              Tổng cộng: <strong>{articles.length}</strong> bài đã phân tích
            </p>
          </div>
        </div>
      </div>

      {/* SEARCH OVERLAY */}
      {showOverlay && (
        <SearchOverlay
          query={searchQuery}
          articles={articles}
          onClose={closeOverlay}
        />
      )}
    </div>
  );
};

export default SearchContent;