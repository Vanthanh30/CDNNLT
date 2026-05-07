import React, { useState, useEffect, useMemo } from "react";
import {
  X,
  Tag,
  TrendingUp,
  FileText,
  AlertTriangle,
  Activity,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import FloatingChat from "../../components/FloatingChat/FloatingChat";
import "./AnalyticsContent.css";

const API_BASE_URL = "http://localhost:8000";

const PALETTE = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#f97316",
];

// ===================== HELPERS =====================
const fmtDate = (d) => {
  if (!d) return "";
  const dt = new Date(d);
  return `${String(dt.getDate()).padStart(2, "0")}/${String(dt.getMonth() + 1).padStart(2, "0")}`;
};

const fmtDateFull = (d) => {
  if (!d) return "";
  const dt = new Date(d);
  return `${String(dt.getDate()).padStart(2, "0")}/${String(dt.getMonth() + 1).padStart(2, "0")}/${dt.getFullYear()}`;
};

// Parse date string từ processed_at / crawled_at
const parseDate = (raw) => {
  if (!raw) return null;
  const d = new Date(raw);
  return isNaN(d.getTime()) ? null : d;
};

// Lấy cutoff date theo timeRange (tính từ bây giờ)
const getCutoff = (days) => {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  if (days === 1) {
    return new Date(Date.now() - 24 * 60 * 60 * 1000);
  }
  return new Date(Date.now() - days * 24 * 60 * 60 * 1000);
};

// ===================== CUSTOM TOOLTIP =====================
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="ac-tooltip">
      <p className="ac-tooltip-label">{fmtDateFull(label)}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }} className="ac-tooltip-item">
          <span className="ac-tooltip-dot" style={{ background: p.color }} />
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
};

// ===================== STAT CARD =====================
const StatCard = ({ icon: Icon, label, value, sub, color }) => (
  <div className="ac-stat-card">
    <div className="ac-stat-icon" style={{ background: `${color}18`, color }}>
      <Icon size={18} />
    </div>
    <div className="ac-stat-body">
      <p className="ac-stat-label">{label}</p>
      <p className="ac-stat-value">{value}</p>
      {sub && <p className="ac-stat-sub">{sub}</p>}
    </div>
  </div>
);

// ===================== KEYWORDS MODAL =====================
const KeywordsModal = ({ keywords, onClose }) => {
  const max = keywords[0]?.count || 1;
  return (
    <div className="ac-modal-overlay" onClick={onClose}>
      <div className="ac-modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="ac-modal-header">
          <h3>
            <Tag size={15} style={{ marginRight: 8 }} />
            Tất cả loại bệnh ({keywords.length})
          </h3>
          <button className="ac-icon-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
        <div className="ac-modal-body">
          {keywords.length === 0 ? (
            <p className="ac-empty">Chưa có dữ liệu</p>
          ) : (
            keywords.map((kw, idx) => (
              <div key={idx} className="ac-kw-row">
                <div className="ac-kw-left">
                  <span
                    className="ac-dot"
                    style={{ background: PALETTE[idx % PALETTE.length] }}
                  />
                  <span className="ac-kw-name">{kw.keyword}</span>
                  <span className="ac-kw-count">{kw.count} bài</span>
                </div>
                <div className="ac-kw-bar-wrap">
                  <div
                    className="ac-kw-bar-fill"
                    style={{
                      width: `${Math.round((kw.count / max) * 100)}%`,
                      background: PALETTE[idx % PALETTE.length],
                    }}
                  />
                </div>
                <span className="ac-kw-pct">
                  {Math.round((kw.count / max) * 100)}%
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

// ===================== MAIN COMPONENT =====================
const AnalyticsContent = () => {
  const [timeRange, setTimeRange] = useState(7);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showKeywords, setShowKeywords] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE_URL}/articles`)
      .then((r) => r.json())
      .then((data) => setArticles(Array.isArray(data) ? data : []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // ── Analytics computation ──
  const { stats, analytics } = useMemo(() => {
    if (!articles.length) return { stats: null, analytics: null };

    const cutoff = getCutoff(timeRange);
    const cutoff7d = getCutoff(7);

    // Sử dụng processed_at để lọc
    const inRange = articles.filter((a) => {
      const d = parseDate(a.processed_at);
      return d && d >= cutoff;
    });

    const recent7d = articles.filter((a) => {
      const d = parseDate(a.processed_at);
      return d && d >= cutoff7d;
    }).length;

    // Disease counts toàn bộ
    const diseaseCounts = {};
    articles.forEach((a) => {
      if (a.disease_name)
        diseaseCounts[a.disease_name] =
          (diseaseCounts[a.disease_name] || 0) + 1;
    });
    const topEntries = Object.entries(diseaseCounts).sort(
      (a, b) => b[1] - a[1],
    );

    // Sources
    const uniqueSources = new Set(
      articles
        .map((a) => {
          try {
            return new URL(a.url || "").hostname.replace("www.", "");
          } catch {
            return null;
          }
        })
        .filter(Boolean),
    ).size;

    const computedStats = {
      total_articles: articles.length,
      in_range: inRange.length,
      unique_sources: uniqueSources,
      recent_7d: recent7d,
      top_keyword: topEntries[0]?.[0] || "N/A",
      top_keyword_count: topEntries[0]?.[1] || 0,
    };

    // Daily counts — group theo ngày
    const dayMap = {};
    inRange.forEach((a) => {
      const d = parseDate(a.processed_at);
      if (!d) return;
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      dayMap[key] = (dayMap[key] || 0) + 1;
    });

    // Tạo đủ tất cả ngày trong khoảng
    const allDays = [];
    const now = new Date();
    for (let i = timeRange - 1; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      d.setHours(0, 0, 0, 0);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      allDays.push({ date: key, count: dayMap[key] || 0 });
    }

    // Top diseases trong khoảng
    const rangeDiseases = {};
    inRange.forEach((a) => {
      if (a.disease_name)
        rangeDiseases[a.disease_name] =
          (rangeDiseases[a.disease_name] || 0) + 1;
    });
    const topKeywords = Object.entries(rangeDiseases)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([keyword, count]) => ({ keyword, count }));

    const top3 = topKeywords.slice(0, 3).map((k) => k.keyword);

    // Line chart data
    const lineMap = {};
    inRange.forEach((a) => {
      if (!a.disease_name || !top3.includes(a.disease_name)) return;
      const d = parseDate(a.processed_at);
      if (!d) return;
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      if (!lineMap[key]) lineMap[key] = {};
      lineMap[key][a.disease_name] = (lineMap[key][a.disease_name] || 0) + 1;
    });
    const lineData = allDays.map(({ date }) => ({
      date,
      ...Object.fromEntries(top3.map((k) => [k, lineMap[date]?.[k] || 0])),
    }));

    // Risk score
    const recentRatio = inRange.length / Math.max(articles.length, 1);
    const riskScore = Math.round(recentRatio * 100);

    return {
      stats: computedStats,
      analytics: {
        in_range: inRange.length,
        daily_counts: allDays,
        top_keywords: topKeywords,
        top3,
        line_data: lineData,
        risk_score: riskScore,
      },
    };
  }, [articles, timeRange]);

  const riskInfo =
    analytics?.risk_score > 60
      ? { text: "Cao", color: "#ef4444" }
      : analytics?.risk_score > 30
        ? { text: "Trung bình", color: "#f59e0b" }
        : { text: "Thấp", color: "#10b981" };

  const timeLabel = timeRange === 1 ? "24 giờ qua" : `${timeRange} ngày qua`;

  const forecastRows = (analytics?.top_keywords || [])
    .slice(0, 5)
    .map((kw, idx) => ({
      ...kw,
      pct: Math.round((kw.count / Math.max(analytics?.in_range || 1, 1)) * 100),
      status: idx < 2 ? "Tăng" : "Theo dõi",
      color: PALETTE[idx],
    }));

  const renderBarLabel = ({ x, y, width, value }) => {
    if (!value) return null;
    return (
      <text
        x={x + width / 2}
        y={y - 4}
        textAnchor="middle"
        fill="#94a3b8"
        fontSize={10}
      >
        {value}
      </text>
    );
  };

  return (
    <div className="ac-body">
      {showKeywords && (
        <KeywordsModal
          keywords={analytics?.top_keywords || []}
          onClose={() => setShowKeywords(false)}
        />
      )}

      {/* ── HEADER ── */}
      <div className="ac-header">
        <div className="ac-header-left">
          <h1 className="ac-title">Phân tích & Xu hướng Dịch bệnh</h1>
          <p className="ac-subtitle">
            {loading
              ? "Đang tải dữ liệu..."
              : `${analytics?.in_range ?? 0} bài trong ${timeLabel} · Tổng cộng ${stats?.total_articles ?? 0} bài`}
          </p>
        </div>
        <div className="ac-header-right">
          <div className="ac-time-tabs">
            {[
              { l: "24H", v: 1 },
              { l: "7 ngày", v: 7 },
              { l: "30 ngày", v: 30 },
            ].map((t) => (
              <button
                key={t.v}
                className={`ac-tab ${timeRange === t.v ? "active" : ""}`}
                onClick={() => setTimeRange(t.v)}
              >
                {t.l}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── STAT CARDS ── */}
      <div className="ac-stats-row">
        <StatCard
          icon={FileText}
          label="Bài trong kỳ"
          value={loading ? "…" : (analytics?.in_range ?? 0)}
          sub={timeLabel}
          color="#6366f1"
        />
        <StatCard
          icon={Activity}
          label="Tổng bài báo"
          value={loading ? "…" : (stats?.total_articles ?? 0)}
          sub="Đã thu thập"
          color="#10b981"
        />
        <StatCard
          icon={TrendingUp}
          label="Loại bệnh"
          value={loading ? "…" : (analytics?.top_keywords?.length ?? 0)}
          sub={`Trong ${timeLabel}`}
          color="#f59e0b"
        />
        <StatCard
          icon={AlertTriangle}
          label="Mức độ rủi ro"
          value={loading ? "…" : riskInfo.text}
          sub={`${analytics?.risk_score ?? 0}% tỷ lệ bài mới`}
          color={riskInfo.color}
        />
      </div>

      {/* ── MAIN GRID ── */}
      <div className="ac-grid">
        {/* Cột trái: 2 biểu đồ */}
        <div className="ac-col-main">
          {/* Bar chart: số bài theo ngày */}
          <div className="ac-panel">
            <div className="ac-panel-header">
              <h3>Số bài cào được theo ngày</h3>
              <span className="ac-panel-meta">{timeLabel}</span>
            </div>
            {loading ? (
              <div className="ac-skeleton" style={{ height: 220 }} />
            ) : analytics?.daily_counts?.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={analytics.daily_counts}
                  margin={{ top: 20, right: 8, left: -24, bottom: 0 }}
                  barSize={timeRange === 1 ? 40 : timeRange === 7 ? 28 : 12}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.05)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="date"
                    stroke="#4b5563"
                    tick={{ fill: "#6b7280", fontSize: 11 }}
                    tickFormatter={fmtDate}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="#4b5563"
                    tick={{ fill: "#6b7280", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    content={<CustomTooltip />}
                    cursor={{ fill: "rgba(255,255,255,0.03)" }}
                  />
                  <Bar
                    dataKey="count"
                    name="Bài báo"
                    fill="#6366f1"
                    radius={[4, 4, 0, 0]}
                    label={timeRange <= 7 ? renderBarLabel : false}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="ac-empty-chart">
                Không có dữ liệu trong khoảng này
              </div>
            )}
          </div>

          {/* Line chart: top 3 bệnh theo ngày */}
          <div className="ac-panel">
            <div className="ac-panel-header">
              <h3>Top bệnh theo ngày</h3>
              <div className="ac-legend">
                {(analytics?.top3 || []).map((kw, i) => (
                  <span key={i} className="ac-legend-item">
                    <span
                      className="ac-legend-dot"
                      style={{ background: PALETTE[i] }}
                    />
                    {kw}
                  </span>
                ))}
              </div>
            </div>
            {loading ? (
              <div className="ac-skeleton" style={{ height: 200 }} />
            ) : analytics?.line_data?.length > 0 &&
              analytics?.top3?.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart
                  data={analytics.line_data}
                  margin={{ top: 10, right: 8, left: -24, bottom: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.05)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="date"
                    stroke="#4b5563"
                    tick={{ fill: "#6b7280", fontSize: 11 }}
                    tickFormatter={fmtDate}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="#4b5563"
                    tick={{ fill: "#6b7280", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  {analytics.top3.map((kw, i) => (
                    <Line
                      key={kw}
                      type="monotone"
                      dataKey={kw}
                      stroke={PALETTE[i]}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4, strokeWidth: 0 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="ac-empty-chart">
                Không đủ dữ liệu để vẽ biểu đồ
              </div>
            )}
          </div>
        </div>

        {/* Cột phải: ranking + tags */}
        <div className="ac-col-side">
          <div className="ac-panel ac-panel-fill">
            <div className="ac-panel-header">
              <h3>Bệnh nổi bật</h3>
              <span className="ac-panel-meta">{timeLabel}</span>
            </div>
            {loading ? (
              <div className="ac-skeleton" style={{ height: 200 }} />
            ) : (analytics?.top_keywords || []).slice(0, 6).length === 0 ? (
              <p className="ac-empty">Không có dữ liệu</p>
            ) : (
              <div className="ac-rankings">
                {(analytics?.top_keywords || []).slice(0, 6).map((kw, idx) => {
                  const pct = Math.round(
                    (kw.count /
                      Math.max(analytics?.top_keywords?.[0]?.count || 1, 1)) *
                      100,
                  );
                  return (
                    <div key={idx} className="ac-rank-item">
                      <div className="ac-rank-top">
                        <div className="ac-rank-name">
                          <span
                            className="ac-dot"
                            style={{
                              background: PALETTE[idx % PALETTE.length],
                            }}
                          />
                          <span>{kw.keyword}</span>
                        </div>
                        <span className="ac-rank-count">{kw.count} bài</span>
                      </div>
                      <div className="ac-rank-bar">
                        <div
                          className="ac-rank-fill"
                          style={{
                            width: `${pct}%`,
                            background: PALETTE[idx % PALETTE.length],
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="ac-panel">
            <div className="ac-panel-header">
              <h3>Danh mục bệnh</h3>
            </div>
            <div className="ac-tags">
              {loading ? (
                <div className="ac-skeleton" style={{ height: 60 }} />
              ) : (
                (analytics?.top_keywords || []).slice(0, 8).map((kw, idx) => (
                  <span
                    key={idx}
                    className="ac-tag"
                    style={{ "--tag-color": PALETTE[idx % PALETTE.length] }}
                  >
                    {kw.keyword} <em>{kw.count}</em>
                  </span>
                ))
              )}
            </div>
            <button
              className="ac-expand-btn"
              onClick={() => setShowKeywords(true)}
            >
              Xem tất cả →
            </button>
          </div>
        </div>
      </div>

      {/* ── TABLE ── */}
      <div className="ac-panel ac-table-panel">
        <div className="ac-panel-header">
          <h3>Bảng chi tiết bệnh nổi bật</h3>
          <span className="ac-panel-meta">
            {timeLabel} · {analytics?.in_range || 0} bài
          </span>
        </div>
        <div className="ac-table-wrap">
          <table className="ac-table">
            <thead>
              <tr>
                <th>Tên bệnh</th>
                <th>Số bài</th>
                <th>Tỷ lệ</th>
                <th>Xu hướng</th>
                <th>Kỳ phân tích</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="ac-table-empty">
                    Đang tải...
                  </td>
                </tr>
              ) : forecastRows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="ac-table-empty">
                    Không có dữ liệu trong khoảng này
                  </td>
                </tr>
              ) : (
                forecastRows.map((row, idx) => (
                  <tr key={idx}>
                    <td>
                      <div className="ac-disease-name">
                        <span
                          className="ac-dot"
                          style={{ background: row.color }}
                        />
                        {row.keyword}
                      </div>
                    </td>
                    <td>
                      <strong>{row.count}</strong>
                    </td>
                    <td>
                      <div className="ac-pct-bar">
                        <div
                          className="ac-pct-fill"
                          style={{
                            width: `${row.pct}%`,
                            background: row.color,
                          }}
                        />
                        <span>{row.pct}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`ac-badge ${idx < 2 ? "red" : "blue"}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="ac-table-meta">{timeLabel}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── FLOATING AI CHATBOT ── */}
      <FloatingChat stats={stats} analytics={analytics} />
    </div>
  );
};

export default AnalyticsContent;
