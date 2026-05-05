import React, { useState, useEffect, useRef, useCallback } from "react";
import { Search, Bell, RotateCcw, Box, X, ExternalLink, AlertCircle, Clock, MapPin, Activity } from "lucide-react";
import { articleService } from "../../services/api";
import "./Header.css";

// ── helpers ──
const timeAgo = (dateStr) => {
  if (!dateStr) return null;
  const diff = Math.floor((new Date() - new Date(dateStr)) / 60000);
  if (diff < 1) return "Vừa cập nhật";
  if (diff < 60) return `${diff} phút trước`;
  if (diff < 1440) return `${Math.floor(diff / 60)} giờ trước`;
  return `${Math.floor(diff / 1440)} ngày trước`;
};

const RISK_META = {
  HIGH: { label: "Cao", cls: "risk-high" },
  MEDIUM: { label: "Trung bình", cls: "risk-medium" },
  LOW: { label: "Thấp", cls: "risk-low" },
};

// ── Search Result Card ──
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

  // Chỉ lọc theo disease_name — bài phải được NLP gán đúng tên bệnh khớp query.
  // Không match title/summary để tránh false positive (bài nhắc tới bệnh nhưng không phải chủ đề chính).
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
    // exact
    if (nd === nq) return true;
    // disease chứa query hoặc query chứa disease (handle viết tắt: "asf" ↔ "dịch tả lợn châu phi (asf)")
    if (nd.includes(nq) || nq.includes(nd)) return true;
    return false;
  };

  // Nếu không có bài nào match disease_name → fallback tìm location (vd: tìm tỉnh thành)
  const byDisease = articles.filter(matchDisease);
  const byLocation = byDisease.length === 0
    ? articles.filter((a) => normalize(a.location).includes(nq))
    : [];

  const allMatched = byDisease.length > 0 ? byDisease : byLocation;

  // Sort: risk_level HIGH → MEDIUM → LOW, rồi mới nhất trước
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

  // Loại tìm kiếm để hiện hint phù hợp
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

// ── Main Header ──
const Header = () => {
  const [lastUpdated, setLastUpdated] = useState("Đang tải...");
  const [articles, setArticles] = useState([]);
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const [showOverlay, setShowOverlay] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const inputRef = useRef(null);

  // fetch articles 1 lần
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await articleService.getAllArticles();
        if (!data.length) { setLastUpdated("Chưa có dữ liệu"); return; }
        setArticles(data);
        const latest = data.map((a) => a.processed_at).filter(Boolean).sort().reverse()[0];
        setLastUpdated(latest ? (timeAgo(latest) || "Vừa cập nhật") : "Vừa cập nhật");
      } catch {
        setLastUpdated("Không thể kết nối");
      }
    };
    fetchData();
  }, []);

  // Gợi ý chỉ từ disease_name có thực trong DB
  useEffect(() => {
    if (!query.trim() || query.length < 2) { setSuggestions([]); return; }
    const normalize = (s) => (s || "").toLowerCase().replace(/[-\/().]/g, " ").replace(/\s+/g, " ").trim();
    const nq = normalize(query);
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
    // sort: tên bắt đầu bằng query lên trước
    sugg.sort((a, b) => {
      const na = normalize(a), nb = normalize(b);
      return (na.startsWith(nq) ? 0 : 1) - (nb.startsWith(nq) ? 0 : 1);
    });
    setSuggestions(sugg.slice(0, 6));
  }, [query, articles]);

  const handleSearch = useCallback((q = query) => {
    if (!q.trim()) return;
    setShowOverlay(true);
    setFocused(false);
    inputRef.current?.blur();
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch();
    if (e.key === "Escape") { setFocused(false); setQuery(""); }
  };

  const handleSelectSuggestion = (s) => {
    setQuery(s);
    handleSearch(s);
  };

  const closeOverlay = () => setShowOverlay(false);

  return (
    <>
      <header className="header">
        <h2 className="header-title">Phân tích Hệ thống (Sentinel)</h2>

        {/* Search */}
        <div className={`search-bar ${focused ? "focused" : ""}`}>
          <Search size={15} color="var(--text-muted)" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Tìm kiếm mầm bệnh, địa điểm..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setTimeout(() => setFocused(false), 150)}
            onKeyDown={handleKeyDown}
          />
          {query && (
            <button className="search-clear" onClick={() => { setQuery(""); setSuggestions([]); }}>
              <X size={13} />
            </button>
          )}
          {focused && query.length >= 2 && (
            <SearchDropdown
              suggestions={suggestions}
              query={query}
              onSelect={handleSelectSuggestion}
            />
          )}
        </div>

        <div className="header-actions">
          <span className="last-updated">Cập nhật: {lastUpdated}</span>
          <button className="icon-btn"><Bell size={18} /></button>
          <button className="icon-btn"><RotateCcw size={18} /></button>
          <button className="icon-btn"><Box size={18} /></button>
        </div>
      </header>

      {showOverlay && (
        <SearchOverlay
          query={query}
          articles={articles}
          onClose={closeOverlay}
        />
      )}
    </>
  );
};

export default Header;