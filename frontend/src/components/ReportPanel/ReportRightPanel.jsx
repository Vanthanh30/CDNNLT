import React, { useMemo, useState, useCallback } from "react";
import {
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  MapPin,
  Activity,
  Calendar,
  RotateCcw,
  CheckCircle,
  Loader,
} from "lucide-react";
import { useForecast } from "../../hooks/useForecast";
import "./ReportRightPanel.css";

/* ── helpers ── */
const RISK_META = {
  HIGH: {
    label: "CAO",
    color: "#ef4444",
    bg: "rgba(239,68,68,0.12)",
    border: "rgba(239,68,68,0.3)",
  },
  MEDIUM: {
    label: "TB",
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.12)",
    border: "rgba(245,158,11,0.3)",
  },
  LOW: {
    label: "THẤP",
    color: "#22c55e",
    bg: "rgba(34,197,94,0.12)",
    border: "rgba(34,197,94,0.3)",
  },
};

const CONF_META = {
  HIGH: { label: "Cao", color: "#22c55e" },
  MEDIUM: { label: "TB", color: "#f59e0b" },
  LOW: { label: "Thấp", color: "#ef4444" },
};

const riskMeta = (lvl) => RISK_META[lvl] || RISK_META.LOW;
const confMeta = (lvl) => CONF_META[lvl] || CONF_META.LOW;

const fmt = (n) => (n ?? 0).toLocaleString("vi-VN");
const fmtDate = (s) =>
  s
    ? new Date(s).toLocaleDateString("vi-VN", {
        day: "2-digit",
        month: "2-digit",
      })
    : "–";

const BASE_URL =
  import.meta.env.VITE_FORECAST_API_URL || "http://localhost:8010";

const RETRAIN_STATES = {
  idle: { label: "CẬP NHẬT & DỰ BÁO LẠI", icon: RotateCcw },
  scraping: {
    label: "Đang thu thập dữ liệu...",
    icon: Loader,
    color: "#38bdf8",
  },
  training: {
    label: "Đang huấn luyện mô hình...",
    icon: Loader,
    color: "#f59e0b",
  },
  done: {
    label: "Hoàn tất! Đã cập nhật dự báo",
    icon: CheckCircle,
    color: "#22c55e",
  },
  error: { label: "Lỗi – Thử lại", icon: AlertTriangle, color: "#ef4444" },
};

/* ── mini sparkline (Giao diện Gradient của bạn) ── */
const Sparkline = ({ data = [], color = "#38bdf8", height = 70 }) => {
  if (!data.length) return null;

  const values = data.map((d) => d.predicted_cases);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const width = 400;

  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1 || 1)) * width;
    const y = height - ((v - min) / range) * (height - 15) - 5;
    return `${x},${y}`;
  });

  const polylinePts = pts.join(" ");
  const polygonPts = `0,${height} ${polylinePts} ${width},${height}`;
  const colorId = color.replace("#", "");

  return (
    <div className="rp-spark-container" style={{ width: "100%" }}>
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        style={{ overflow: "visible", marginTop: "8px" }}
      >
        <defs>
          <linearGradient id={`grad-${colorId}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <polygon points={polygonPts} fill={`url(#grad-${colorId})`} />
        <polyline
          points={polylinePts}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {pts.length > 0 && (
          <circle
            cx={pts.at(-1)?.split(",")[0]}
            cy={pts.at(-1)?.split(",")[1]}
            r="5"
            fill={color}
            stroke="#1e293b"
            strokeWidth="2"
          />
        )}
      </svg>
      <div
        className="rp-spark-axis"
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "8px",
          fontSize: "10px",
          color: "#64748b",
          fontWeight: 600,
        }}
      >
        <span>{fmtDate(data[0]?.date)}</span>
        <span>{fmtDate(data[Math.floor(data.length / 2)]?.date)}</span>
        <span>{fmtDate(data[data.length - 1]?.date)}</span>
      </div>
    </div>
  );
};

/* ── bar chart (Cấu trúc Clean của bạn bè) ── */
const ForecastBarChart = ({ forecast = [], history = [] }) => {
  const combined = [
    ...history
      .slice(-7)
      .map((h) => ({ date: h.date, value: h.signal_cases, type: "history" })),
    ...forecast.map((f) => ({
      date: f.date,
      value: f.predicted_cases,
      type: "forecast",
    })),
  ];

  if (!combined.length) return null;

  const max = Math.max(...combined.map((d) => d.value), 1);
  const labelIndices = new Set([
    0,
    Math.floor(combined.length / 2),
    combined.length - 1,
  ]);

  return (
    <div className="rp-bar-chart-outer">
      <div className="rp-bar-chart">
        {combined.map((d, i) => {
          const pct = Math.max((d.value / max) * 100, 3);
          const color =
            d.type === "history"
              ? "#334155"
              : d.value > max * 0.7
                ? "#ef4444"
                : d.value > max * 0.35
                  ? "#38bdf8"
                  : "#0ea5e9";

          return (
            <div
              key={i}
              className="rp-bar-col"
              title={`${fmtDate(d.date)}: ${fmt(Math.round(d.value))}`}
            >
              <div
                className="rp-bar"
                style={{
                  height: `${pct}%`,
                  backgroundColor: color,
                  opacity: d.type === "history" ? 0.5 : 1,
                }}
              />
            </div>
          );
        })}
      </div>

      <div className="rp-bar-axis">
        {combined.map((d, i) => (
          <div key={i} className="rp-axis-cell">
            {labelIndices.has(i) && (
              <span className="rp-bar-label">{fmtDate(d.date)}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const DiseasePill = ({ disease, active, onClick }) => {
  const rm = riskMeta(disease.risk_level);
  return (
    <button
      className={`rp-pill ${active ? "rp-pill--active" : ""}`}
      style={
        active
          ? { borderColor: rm.color, color: rm.color, background: rm.bg }
          : {}
      }
      onClick={onClick}
    >
      <span className="rp-pill-dot" style={{ background: rm.color }} />
      {disease.disease_name}
    </button>
  );
};

const RegionList = ({ regions = [] }) => (
  <div className="rp-regions">
    {regions.slice(0, 4).map((r, i) => (
      <div key={i} className="rp-region-row">
        <MapPin size={11} />
        <span className="rp-region-name">{r.region_name}</span>
        <span className="rp-region-cases">{fmt(r.total_cases)} ca</span>
      </div>
    ))}
  </div>
);

/* ══════════════════════════════════════════════════════
   MAIN COMPONENT
══════════════════════════════════════════════════════ */
const ReportRightPanel = () => {
  const {
    summary,
    loading,
    error,
    selectedDisease,
    setSelectedDisease,
    detailForecast,
    detailLoading,
    refetch,
  } = useForecast({ topN: 3 });

  const [retrainState, setRetrainState] = useState("idle");

  const handleRetrain = useCallback(async () => {
    if (["scraping", "training"].includes(retrainState)) return;
    setRetrainState("scraping");

    try {
      // 🟢 Fix lỗi ESLint "Empty block statement" bằng cách bỏ biến e/err và thêm comment
      try {
        await fetch(`${BASE_URL}/scrape`, { method: "POST" });
      } catch {
        /* Bỏ qua nếu không có API scrape */
      }

      setRetrainState("training");

      const diseases = summary?.diseases ?? [];
      const trainTasks = diseases.length
        ? diseases.map((d) =>
            fetch(`${BASE_URL}/train`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ disease_name: d.disease_name }),
            }),
          )
        : [fetch(`${BASE_URL}/train`, { method: "POST" })];

      await Promise.allSettled(trainTasks);
      await refetch();

      setRetrainState("done");
      setTimeout(() => setRetrainState("idle"), 3000);
    } catch {
      // 🟢 Fix lỗi ESLint
      setRetrainState("error");
      setTimeout(() => setRetrainState("idle"), 4000);
    }
  }, [retrainState, summary, refetch]);

  const activeDisease = useMemo(
    () => summary?.diseases?.find((d) => d.disease_name === selectedDisease),
    [summary, selectedDisease],
  );

  const rm = riskMeta(summary?.highest_risk_level);
  const rs = RETRAIN_STATES[retrainState];
  const RetrainIcon = rs.icon;
  const isBusy = ["scraping", "training"].includes(retrainState);

  if (loading) {
    return (
      <div className="report-right-panel rp-center">
        <div className="rp-spinner" />
        <p className="rp-muted">Đang tải dự báo...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="report-right-panel rp-center">
        <AlertTriangle size={32} color="#ef4444" />
        <p className="rp-muted">
          {error ? "Lỗi kết nối dịch vụ dự báo" : "Chưa có dữ liệu dự báo"}
        </p>
        <button className="rp-btn-retry" onClick={refetch}>
          <RefreshCw size={14} /> Thử lại
        </button>
      </div>
    );
  }

  return (
    <div className="report-right-panel">
      <div className="rp-header">
        <div>
          <h2 className="rp-title">Dự báo Dịch bệnh</h2>
          <p className="rp-subtitle">7–14 ngày tới · AI Signal Model v5</p>
        </div>
        <button className="rp-btn-refresh" onClick={refetch} title="Làm mới">
          <RefreshCw size={14} />
        </button>
      </div>

      <div
        className="rp-risk-banner"
        style={{ borderColor: rm.border, background: rm.bg }}
      >
        <div className="rp-risk-left">
          <span
            className="rp-risk-badge"
            style={{ color: rm.color, border: `1px solid ${rm.border}` }}
          >
            {rm.label}
          </span>
          <div>
            <div className="rp-risk-label">Mức rủi ro tổng thể</div>
            <div className="rp-risk-total">
              {fmt(summary.total_predicted_7d)} ca dự báo / 7 ngày
            </div>
          </div>
        </div>
        <Calendar size={20} color={rm.color} style={{ opacity: 0.6 }} />
      </div>

      <div className="rp-pills">
        {summary.diseases.map((d) => (
          <DiseasePill
            key={d.disease_name}
            disease={d}
            active={d.disease_name === selectedDisease}
            onClick={() => setSelectedDisease(d.disease_name)}
          />
        ))}
      </div>

      {activeDisease && (
        <div className="rp-detail-card">
          <div className="rp-stats-row">
            <div className="rp-stat">
              <span
                className="rp-stat-val"
                style={{ color: riskMeta(activeDisease.risk_level).color }}
              >
                {fmt(activeDisease.predicted_total_7d)}
              </span>
              <span className="rp-stat-lbl">Ca / 7 ngày</span>
            </div>
            <div className="rp-stat">
              <span className="rp-stat-val">
                {fmt(activeDisease.predicted_peak)}
              </span>
              <span className="rp-stat-lbl">Đỉnh dự báo</span>
            </div>
            <div className="rp-stat">
              <span
                className="rp-stat-val"
                style={{ color: confMeta(activeDisease.confidence).color }}
              >
                {confMeta(activeDisease.confidence).label}
              </span>
              <span className="rp-stat-lbl">Độ tin cậy</span>
            </div>
            <div className="rp-stat">
              <span className="rp-stat-val">
                {activeDisease.observed_days ?? "–"}
              </span>
              <span className="rp-stat-lbl">Ngày quan sát</span>
            </div>
          </div>

          <div className="rp-spark-row">
            <span className="rp-section-label">
              <TrendingUp size={11} /> XU HƯỚNG DỰ BÁO 7 NGÀY
            </span>
            {/* 🟢 Render Sparkline Gradient truyền data */}
            <Sparkline
              data={activeDisease.daily_forecast ?? []}
              color={riskMeta(activeDisease.risk_level).color}
              height={70}
            />
          </div>

          <div className="rp-chart-section">
            <span className="rp-section-label">
              <Activity size={11} /> BIỂU ĐỒ 14 NGÀY (Lịch sử + Dự báo)
            </span>
            {detailLoading ? (
              <div className="rp-chart-loading">
                <div className="rp-spinner rp-spinner--sm" />
              </div>
            ) : (
              <ForecastBarChart
                forecast={detailForecast?.forecast ?? []}
                history={detailForecast?.history ?? []}
              />
            )}
            <div className="rp-chart-legend">
              <span>
                <span
                  className="rp-legend-dot"
                  style={{ background: "#334155" }}
                />{" "}
                Lịch sử
              </span>
              <span>
                <span
                  className="rp-legend-dot"
                  style={{ background: "#38bdf8" }}
                />{" "}
                Dự báo
              </span>
            </div>
          </div>

          <div
            className="rp-alert-msg"
            style={{
              borderLeft: `3px solid ${riskMeta(activeDisease.risk_level).color}`,
            }}
          >
            <AlertTriangle
              size={13}
              color={riskMeta(activeDisease.risk_level).color}
            />
            <p>{activeDisease.risk_message}</p>
          </div>

          {activeDisease.regions?.length > 0 && (
            <div>
              <span className="rp-section-label">
                <MapPin size={11} /> KHU VỰC ẢNH HƯỞNG
              </span>
              <RegionList regions={activeDisease.regions} />
            </div>
          )}

          {/* 🟢 Meta Row khôi phục Data gốc và MAE N/A */}
          <div className="rp-meta-row">
            <span>
              Thuật toán: <em>{activeDisease.method?.replace(/_/g, " ")}</em>
            </span>
            <span>
              MAE:{" "}
              <em>
                {activeDisease.mae != null
                  ? activeDisease.mae.toFixed(2)
                  : "N/A"}
              </em>
            </span>
            {activeDisease.wape != null && (
              <span>
                Lệch: <em>{(activeDisease.wape * 100).toFixed(1)}%</em>
              </span>
            )}
            <span>
              Dữ liệu:{" "}
              <em>
                {fmt(activeDisease.history_total_cases)} ca /{" "}
                {fmt(activeDisease.event_count)} tin
              </em>
            </span>
          </div>
        </div>
      )}

      <button
        className={`btn-retrain ${isBusy ? "btn-retrain--busy" : ""} ${retrainState === "done" ? "btn-retrain--done" : ""} ${retrainState === "error" ? "btn-retrain--error" : ""}`}
        onClick={handleRetrain}
        disabled={isBusy}
      >
        <RetrainIcon
          size={14}
          className={isBusy ? "rp-spin-icon" : ""}
          color={rs.color}
        />
        <span>{rs.label}</span>
      </button>
    </div>
  );
};

export default ReportRightPanel;
