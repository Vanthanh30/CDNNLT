import React, { useState, useEffect, useMemo } from "react";
import { X, Tag, TrendingUp, FileText, AlertTriangle, Activity } from "lucide-react";
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import FloatingChat from "../../components/FloatingChat/FloatingChat";
import "./AnalyticsContent.css";

const API_BASE_URL = "http://localhost:8000";

const PALETTE = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316"];

const TIME_OPTIONS = [
  { label: "24H", value: 1 },
  { label: "7 ngày", value: 7 },
  { label: "30 ngày", value: 30 },
];

const TABLE_COLS = ["Tên bệnh", "Số bài", "Tỷ lệ", "Xu hướng", "Kỳ phân tích"];

const fmt2 = (n) => String(n).padStart(2, "0");

const fmtDate = (d) => {
  if (!d) return "";
  const dt = new Date(d);
  return `${fmt2(dt.getDate())}/${fmt2(dt.getMonth() + 1)}`;
};

const fmtHour = (h) => {
  if (h === undefined || h === null) return "";
  return `${fmt2(h)}:00`;
};

const fmtDateFull = (d) => {
  if (!d) return "";
  const dt = new Date(d);
  return `${fmt2(dt.getDate())}/${fmt2(dt.getMonth() + 1)}/${dt.getFullYear()}`;
};

const parseDate = (raw) => {
  if (!raw) return null;
  const d = new Date(raw);
  return isNaN(d.getTime()) ? null : d;
};

const getCutoff = (days) => new Date(Date.now() - days * 24 * 60 * 60 * 1000);

const dateKey = (d) =>
  `${d.getFullYear()}-${fmt2(d.getMonth() + 1)}-${fmt2(d.getDate())}`;

const hostname = (url) => {
  try { return new URL(url).hostname.replace("www.", ""); }
  catch { return null; }
};
const getArticleDate = (article) => {
  const candidates = [
    article.published_at,
    article.event_date,
    article.processed_at,
    article.crawled_at,
  ];

  for (const raw of candidates) {
    if (!raw) continue;
    const d = new Date(raw);
    if (!isNaN(d.getTime())) return d;
  }
  return null;
};

const HourTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="ac-tooltip">
      <p className="ac-tooltip-label">{fmtHour(label)}</p>
      {payload.map((p, i) => (
        <p key={i} className="ac-tooltip-item" style={{ color: p.color }}>
          <span className="ac-tooltip-dot" style={{ background: p.color }} />
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="ac-tooltip">
      <p className="ac-tooltip-label">{fmtDateFull(label)}</p>
      {payload.map((p, i) => (
        <p key={i} className="ac-tooltip-item" style={{ color: p.color }}>
          <span className="ac-tooltip-dot" style={{ background: p.color }} />
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
};

const HBarTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="ac-tooltip">
      <p className="ac-tooltip-label">{p.payload.name}</p>
      <p className="ac-tooltip-item" style={{ color: p.fill }}>
        <span className="ac-tooltip-dot" style={{ background: p.fill }} />
        Số bài: <strong>{p.value}</strong>
      </p>
    </div>
  );
};

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
            keywords.map((kw, idx) => {
              const pct = Math.round((kw.count / max) * 100);
              const color = PALETTE[idx % PALETTE.length];
              return (
                <div key={idx} className="ac-kw-row">
                  <div className="ac-kw-left">
                    <span className="ac-dot" style={{ background: color }} />
                    <span className="ac-kw-name">{kw.keyword}</span>
                    <span className="ac-kw-count">{kw.count} bài</span>
                  </div>
                  <div className="ac-kw-bar-wrap">
                    <div className="ac-kw-bar-fill" style={{ width: `${pct}%`, background: color }} />
                  </div>
                  <span className="ac-kw-pct">{pct}%</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

const BarLabel = ({ x, y, width, value }) => {
  if (!value || width < 20) return null;
  return (
    <text x={x + width / 2} y={y - 5} textAnchor="middle" fill="#94a3b8" fontSize={10}>
      {value}
    </text>
  );
};

const computeAnalytics = (articles, timeRange) => {
  if (!articles.length) return { stats: null, analytics: null };

  const cutoff = getCutoff(timeRange);

  const inRange = articles.filter((a) => {
    const d = getArticleDate(a);
    return d && d >= cutoff;
  });

  const uniqueSources = new Set(articles.map((a) => hostname(a.url)).filter(Boolean)).size;

  const diseaseCounts = {};
  articles.forEach((a) => {
    if (a.disease_name) diseaseCounts[a.disease_name] = (diseaseCounts[a.disease_name] || 0) + 1;
  });
  const topEntries = Object.entries(diseaseCounts).sort((a, b) => b[1] - a[1]);

  const stats = {
    total_articles: articles.length,
    in_range: inRange.length,
    unique_sources: uniqueSources,
    top_keyword: topEntries[0]?.[0] || "N/A",
    top_keyword_count: topEntries[0]?.[1] || 0,
  };

  let hourlyData = null;
  if (timeRange === 1) {
    const hourMap = {};
    inRange.forEach((a) => {
      const d = getArticleDate(a);
      if (!d) return;
      const h = d.getHours();
      hourMap[h] = (hourMap[h] || 0) + 1;
    });
    hourlyData = Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      count: hourMap[h] || 0,
    }));
  }

  const dayMapActual = {};
  inRange.forEach((a) => {
    const d = getArticleDate(a);
    if (!d) return;
    const k = dateKey(d);
    dayMapActual[k] = (dayMapActual[k] || 0) + 1;
  });

  const now = new Date();
  const allDays = Array.from({ length: timeRange }, (_, i) => {
    const d = new Date(now);
    d.setDate(d.getDate() - (timeRange - 1 - i));
    d.setHours(0, 0, 0, 0);
    const k = dateKey(d);
    return { date: k, count: dayMapActual[k] || 0 };
  });

  const rangeDiseases = {};
  inRange.forEach((a) => {
    if (a.disease_name) rangeDiseases[a.disease_name] = (rangeDiseases[a.disease_name] || 0) + 1;
  });
  const topKeywords = Object.entries(rangeDiseases)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([keyword, count]) => ({ keyword, count }));

  const hbarData = topKeywords.slice(0, 7).map((kw, idx) => ({
    name: kw.keyword,
    count: kw.count,
    color: PALETTE[idx % PALETTE.length],
  }));

  const top3 = topKeywords.slice(0, 3).map((k) => k.keyword);

  const lineMap = {};
  inRange.forEach((a) => {
    if (!a.disease_name || !top3.includes(a.disease_name)) return;
    const d = getArticleDate(a);
    if (!d) return;
    const k = dateKey(d);
    if (!lineMap[k]) lineMap[k] = {};
    lineMap[k][a.disease_name] = (lineMap[k][a.disease_name] || 0) + 1;
  });
  const lineData = allDays.map(({ date }) => ({
    date,
    ...Object.fromEntries(top3.map((k) => [k, lineMap[date]?.[k] || 0])),
  }));

  const riskScore = Math.round((inRange.length / Math.max(articles.length, 1)) * 100);

  return {
    stats,
    analytics: {
      in_range: inRange.length,
      daily_counts: allDays,
      hourly_counts: hourlyData,
      hbar_data: hbarData,
      top_keywords: topKeywords,
      top3,
      line_data: lineData,
      risk_score: riskScore,
    },
  };
};

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

  const { stats, analytics } = useMemo(
    () => computeAnalytics(articles, timeRange),
    [articles, timeRange],
  );

  const riskInfo = useMemo(() => {
    const score = analytics?.risk_score ?? 0;
    if (score > 60) return { text: "Cao", color: "#ef4444" };
    if (score > 30) return { text: "Trung bình", color: "#f59e0b" };
    return { text: "Thấp", color: "#10b981" };
  }, [analytics?.risk_score]);

  const timeLabel = timeRange === 1 ? "24 giờ qua" : `${timeRange} ngày qua`;
  const is24H = timeRange === 1;

  const forecastRows = useMemo(
    () =>
      (analytics?.top_keywords || []).slice(0, 5).map((kw, idx) => ({
        ...kw,
        pct: Math.round((kw.count / Math.max(analytics?.in_range || 1, 1)) * 100),
        status: idx < 2 ? "Tăng" : "Theo dõi",
        color: PALETTE[idx],
      })),
    [analytics],
  );

  const hasBarData = is24H
    ? analytics?.hourly_counts?.some((d) => d.count > 0)
    : analytics?.daily_counts?.some((d) => d.count > 0);

  const hasLineData =
    !is24H &&
    analytics?.line_data?.length > 0 &&
    analytics?.top3?.length > 0 &&
    analytics.line_data.some((d) => analytics.top3.some((k) => d[k] > 0));

  const hasHbarData = is24H && (analytics?.hbar_data || []).length > 0;

  const hbarHeight = Math.max(180, (analytics?.hbar_data?.length || 0) * 42 + 24);

  return (
    <div className="ac-body">
      {showKeywords && (
        <KeywordsModal
          keywords={analytics?.top_keywords || []}
          onClose={() => setShowKeywords(false)}
        />
      )}

      <div className="ac-header">
        <div>
          <h1 className="ac-title">Phân tích & Xu hướng Dịch bệnh</h1>
          <p className="ac-subtitle">
            {loading
              ? "Đang tải dữ liệu..."
              : `${analytics?.in_range ?? 0} bài trong ${timeLabel} · Tổng cộng ${stats?.total_articles ?? 0} bài`}
          </p>
        </div>
        <div className="ac-time-tabs">
          {TIME_OPTIONS.map(({ label, value }) => (
            <button
              key={value}
              className={`ac-tab${timeRange === value ? " active" : ""}`}
              onClick={() => setTimeRange(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

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

      <div className="ac-grid">
        <div className="ac-col-main">

          <div className="ac-panel">
            <div className="ac-panel-header">
              <h3>{is24H ? "Số bài cào được theo giờ" : "Số bài cào được theo ngày"}</h3>
              <span className="ac-panel-meta">{timeLabel}</span>
            </div>
            {loading ? (
              <div className="ac-skeleton" style={{ height: 220 }} />
            ) : hasBarData ? (
              is24H ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart
                    data={analytics.hourly_counts}
                    margin={{ top: 12, right: 8, left: -20, bottom: 0 }}
                    barSize={16}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis
                      dataKey="hour"
                      stroke="#4b5563"
                      tick={{ fill: "#6b7280", fontSize: 10 }}
                      tickFormatter={fmtHour}
                      axisLine={false}
                      tickLine={false}
                      interval={2}
                    />
                    <YAxis
                      stroke="#4b5563"
                      tick={{ fill: "#6b7280", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      allowDecimals={false}
                      width={28}
                    />
                    <Tooltip content={<HourTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar dataKey="count" name="Bài báo" radius={[4, 4, 0, 0]}>
                      {analytics.hourly_counts.map((entry, idx) => (
                        <Cell key={idx} fill={entry.count > 0 ? "#6366f1" : "rgba(99,102,241,0.15)"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart
                    data={analytics.daily_counts}
                    margin={{ top: timeRange === 7 ? 24 : 12, right: 8, left: -20, bottom: 0 }}
                    barSize={timeRange === 7 ? 32 : 8}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#4b5563"
                      tick={{ fill: "#6b7280", fontSize: 11 }}
                      tickFormatter={fmtDate}
                      axisLine={false}
                      tickLine={false}
                      interval={timeRange === 30 ? 4 : 0}
                    />
                    <YAxis
                      stroke="#4b5563"
                      tick={{ fill: "#6b7280", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      allowDecimals={false}
                      width={28}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar
                      dataKey="count"
                      name="Bài báo"
                      fill="#6366f1"
                      radius={[4, 4, 0, 0]}
                      label={timeRange === 7 ? <BarLabel /> : false}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )
            ) : (
              <div className="ac-empty-chart">Không có dữ liệu trong khoảng này</div>
            )}
          </div>

          <div className="ac-panel">
            <div className="ac-panel-header">
              <h3>{is24H ? "Phân bố bệnh trong 24 giờ" : "Top bệnh theo ngày"}</h3>
              {!is24H && (
                <div className="ac-legend">
                  {(analytics?.top3 || []).map((kw, i) => (
                    <span key={i} className="ac-legend-item">
                      <span className="ac-legend-dot" style={{ background: PALETTE[i] }} />
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {loading ? (
              <div className="ac-skeleton" style={{ height: 220 }} />
            ) : is24H ? (
              hasHbarData ? (
                <ResponsiveContainer width="100%" height={hbarHeight}>
                  <BarChart
                    data={analytics.hbar_data}
                    layout="vertical"
                    margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
                    barSize={18}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                    <XAxis
                      type="number"
                      stroke="#4b5563"
                      tick={{ fill: "#6b7280", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      stroke="#4b5563"
                      tick={{ fill: "#cbd5e1", fontSize: 12 }}
                      axisLine={false}
                      tickLine={false}
                      width={165}
                    />
                    <Tooltip content={<HBarTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar
                      dataKey="count"
                      name="Bài báo"
                      radius={[0, 4, 4, 0]}
                      label={{ position: "right", fill: "#94a3b8", fontSize: 11, formatter: (v) => v }}
                    >
                      {analytics.hbar_data.map((entry, idx) => (
                        <Cell key={idx} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="ac-empty-chart">Không có dữ liệu bệnh trong 24 giờ này</div>
              )
            ) : hasLineData ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart
                  data={analytics.line_data}
                  margin={{ top: 10, right: 12, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="#4b5563"
                    tick={{ fill: "#6b7280", fontSize: 11 }}
                    tickFormatter={fmtDate}
                    axisLine={false}
                    tickLine={false}
                    interval={timeRange === 30 ? 4 : 0}
                  />
                  <YAxis
                    stroke="#4b5563"
                    tick={{ fill: "#6b7280", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                    width={28}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  {analytics.top3.map((kw, i) => (
                    <Line
                      key={kw}
                      type="monotone"
                      dataKey={kw}
                      name={kw}
                      stroke={PALETTE[i]}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4, strokeWidth: 0 }}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="ac-empty-chart">
                {analytics?.top3?.length === 0
                  ? "Không có bệnh nào trong khoảng này"
                  : "Không đủ dữ liệu để vẽ biểu đồ"}
              </div>
            )}
          </div>
        </div>

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
                {analytics.top_keywords.slice(0, 6).map((kw, idx) => {
                  const color = PALETTE[idx % PALETTE.length];
                  const pct = Math.round(
                    (kw.count / Math.max(analytics.top_keywords[0].count, 1)) * 100,
                  );
                  return (
                    <div key={idx} className="ac-rank-item">
                      <div className="ac-rank-top">
                        <div className="ac-rank-name">
                          <span className="ac-dot" style={{ background: color }} />
                          {kw.keyword}
                        </div>
                        <span className="ac-rank-count">{kw.count} bài</span>
                      </div>
                      <div className="ac-rank-bar">
                        <div className="ac-rank-fill" style={{ width: `${pct}%`, background: color }} />
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
                  <span key={idx} className="ac-tag" style={{ "--tag-color": PALETTE[idx % PALETTE.length] }}>
                    {kw.keyword} <em>{kw.count}</em>
                  </span>
                ))
              )}
            </div>
            <button className="ac-expand-btn" onClick={() => setShowKeywords(true)}>
              Xem tất cả →
            </button>
          </div>
        </div>
      </div>

      <div className="ac-panel">
        <div className="ac-panel-header">
          <h3>Bảng chi tiết bệnh nổi bật</h3>
          <span className="ac-panel-meta">{timeLabel} · {analytics?.in_range || 0} bài</span>
        </div>
        <div className="ac-table-wrap">
          <table className="ac-table">
            <thead>
              <tr>{TABLE_COLS.map((col) => <th key={col}>{col}</th>)}</tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="ac-table-empty">Đang tải...</td></tr>
              ) : forecastRows.length === 0 ? (
                <tr><td colSpan={5} className="ac-table-empty">Không có dữ liệu trong khoảng này</td></tr>
              ) : (
                forecastRows.map((row, idx) => (
                  <tr key={idx}>
                    <td>
                      <div className="ac-disease-name">
                        <span className="ac-dot" style={{ background: row.color }} />
                        {row.keyword}
                      </div>
                    </td>
                    <td><strong>{row.count}</strong></td>
                    <td>
                      <div className="ac-pct-bar">
                        <div><div className="ac-pct-fill" style={{ width: `${row.pct}%`, background: row.color }} /></div>
                        <span>{row.pct}%</span>
                      </div>
                    </td>
                    <td><span className={`ac-badge ${idx < 2 ? "red" : "blue"}`}>{row.status}</span></td>
                    <td className="ac-table-meta">{timeLabel}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <FloatingChat stats={stats} analytics={analytics} />
    </div>
  );
};

export default AnalyticsContent;