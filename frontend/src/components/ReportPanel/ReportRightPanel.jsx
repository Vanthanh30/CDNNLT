import React, { useMemo, useState, useCallback } from "react";
import { AlertTriangle, TrendingUp, RefreshCw, MapPin, Activity, Calendar, RotateCcw, CheckCircle, Loader } from "lucide-react";
import { useForecast } from "../../hooks/useForecast";
import "./ReportRightPanel.css";

/* ── helpers ── */
const RISK_META = {
  HIGH: { label: "CAO", color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.3)" },
  MEDIUM: { label: "TB", color: "#f59e0b", bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.3)" },
  LOW: { label: "THẤP", color: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "rgba(34,197,94,0.3)" },
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
  s ? new Date(s).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" }) : "–";

/* ── mini sparkline (pure SVG) ── */
const Sparkline = ({ values = [], color = "#38bdf8", height = 36, width = 120 }) => {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1 || 1)) * width;
      const y = height - (v / max) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");
  const lastPt = pts.split(" ").at(-1)?.split(",");
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {lastPt && <circle cx={lastPt[0]} cy={lastPt[1]} r="3" fill={color} />}
    </svg>
  );
};

/* ── bar chart ── */
const ForecastBarChart = ({ forecast = [], history = [] }) => {
  const historyTail = history.slice(-7);
  const combined = [
    ...historyTail.map((h) => ({ date: h.date, value: h.signal_cases, type: "history" })),
    ...forecast.map((f) => ({ date: f.date, value: f.predicted_cases, type: "forecast" })),
  ];
  if (!combined.length) return null;
  const max = Math.max(...combined.map((d) => d.value), 1);

  /* chỉ show nhãn ở vị trí đầu, giữa, cuối tránh chồng chéo */
  const labelIndices = new Set([0, Math.floor(combined.length / 2), combined.length - 1]);

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
      {/* date axis riêng, không nằm trong bar-col */}
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

/* ── disease pill ── */
const DiseasePill = ({ disease, active, onClick }) => {
  const rm = riskMeta(disease.risk_level);
  return (
    <button
      className={`rp-pill ${active ? "rp-pill--active" : ""}`}
      style={active ? { borderColor: rm.color, color: rm.color, background: rm.bg } : {}}
      onClick={onClick}
    >
      <span className="rp-pill-dot" style={{ background: rm.color }} />
      {disease.disease_name}
    </button>
  );
};

/* ── region list ── */
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

/* ── retrain button states ── */
const RETRAIN_STATES = {
  idle: { label: "CẬP NHẬT & DỰ BÁO LẠI", icon: RotateCcw, color: null },
  scraping: { label: "Đang thu thập dữ liệu...", icon: Loader, color: "#38bdf8" },
  training: { label: "Đang huấn luyện mô hình...", icon: Loader, color: "#f59e0b" },
  done: { label: "Hoàn tất! Đã cập nhật dự báo", icon: CheckCircle, color: "#22c55e" },
  error: { label: "Lỗi – Thử lại", icon: AlertTriangle, color: "#ef4444" },
};

const BASE_URL = import.meta.env.VITE_FORECAST_API_URL || "http://localhost:8010";

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
    if (retrainState === "scraping" || retrainState === "training") return;
    setRetrainState("scraping");
    try {
      /* Bước 1: trigger scraping nếu có endpoint, nếu không bỏ qua */
      const scrapeUrl = `${BASE_URL}/scrape`;
      try {
        const scrapeRes = await fetch(scrapeUrl, { method: "POST" });
        if (!scrapeRes.ok) throw new Error("no scrape endpoint");
      } catch {
        /* endpoint không bắt buộc, tiếp tục train */
      }

      setRetrainState("training");

      /* Bước 2: train lại từng bệnh đang hiển thị */
      const diseases = summary?.diseases ?? [];
      const trainTasks =
        diseases.length > 0
          ? diseases.map((d) =>
            fetch(`${BASE_URL}/train`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ disease_name: d.disease_name }),
            })
          )
          : [fetch(`${BASE_URL}/train`, { method: "POST" })];

      await Promise.allSettled(trainTasks);

      /* Bước 3: load lại dự báo */
      await refetch();
      setRetrainState("done");
      setTimeout(() => setRetrainState("idle"), 3000);
    } catch (err) {
      console.error("Retrain error:", err);
      setRetrainState("error");
      setTimeout(() => setRetrainState("idle"), 4000);
    }
  }, [retrainState, summary, refetch]);

  const activeDiseaseData = useMemo(
    () => summary?.diseases?.find((d) => d.disease_name === selectedDisease),
    [summary, selectedDisease]
  );

  const rm = riskMeta(summary?.highest_risk_level);
  const rs = RETRAIN_STATES[retrainState];
  const RetrainIcon = rs.icon;
  const isRetraining = retrainState === "scraping" || retrainState === "training";

  /* ── loading ── */
  if (loading)
    return (
      <div className="report-right-panel rp-center">
        <div className="rp-spinner" />
        <p className="rp-muted">Đang tải dự báo...</p>
      </div>
    );

  /* ── error ── */
  if (error)
    return (
      <div className="report-right-panel rp-center">
        <AlertTriangle size={32} color="#ef4444" />
        <p className="rp-muted">Lỗi kết nối dịch vụ dự báo</p>
        <button className="rp-btn-retry" onClick={refetch}>
          <RefreshCw size={14} /> Thử lại
        </button>
      </div>
    );

  /* ── no data ── */
  if (!summary)
    return (
      <div className="report-right-panel rp-center">
        <Activity size={28} color="#475569" />
        <p className="rp-muted">Chưa có dữ liệu dự báo</p>
      </div>
    );

  return (
    <div className="report-right-panel">

      {/* ── HEADER ── */}
      <div className="rp-header">
        <div>
          <h2 className="rp-title">Dự báo Dịch bệnh</h2>
          <p className="rp-subtitle">7–14 ngày tới · AI Signal Model v5</p>
        </div>
        <button className="rp-btn-refresh" onClick={refetch} title="Làm mới">
          <RefreshCw size={14} />
        </button>
      </div>

      {/* ── RISK BANNER ── */}
      <div className="rp-risk-banner" style={{ borderColor: rm.border, background: rm.bg }}>
        <div className="rp-risk-left">
          <span className="rp-risk-badge" style={{ color: rm.color, border: `1px solid ${rm.border}` }}>
            {rm.label}
          </span>
          <div>
            <div className="rp-risk-label">Mức rủi ro tổng thể</div>
            <div className="rp-risk-total">{fmt(summary.total_predicted_7d)} ca dự báo / 7 ngày</div>
          </div>
        </div>
        <Calendar size={20} color={rm.color} style={{ opacity: 0.6 }} />
      </div>

      {/* ── DISEASE SELECTOR ── */}
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

      {/* ── DETAIL PANEL ── */}
      {activeDiseaseData && (
        <div className="rp-detail-card">
          {/* stat row */}
          <div className="rp-stats-row">
            <div className="rp-stat">
              <span className="rp-stat-val" style={{ color: riskMeta(activeDiseaseData.risk_level).color }}>
                {fmt(activeDiseaseData.predicted_total_7d)}
              </span>
              <span className="rp-stat-lbl">Ca / 7 ngày</span>
            </div>
            <div className="rp-stat">
              <span className="rp-stat-val">{fmt(activeDiseaseData.predicted_peak)}</span>
              <span className="rp-stat-lbl">Đỉnh dự báo</span>
            </div>
            <div className="rp-stat">
              <span
                className="rp-stat-val"
                style={{ color: confMeta(activeDiseaseData.confidence).color }}
              >
                {confMeta(activeDiseaseData.confidence).label}
              </span>
              <span className="rp-stat-lbl">Độ tin cậy</span>
            </div>
            <div className="rp-stat">
              <span className="rp-stat-val">{activeDiseaseData.observed_days ?? "–"}</span>
              <span className="rp-stat-lbl">Ngày quan sát</span>
            </div>
          </div>

          {/* sparkline */}
          <div className="rp-spark-row">
            <span className="rp-section-label">
              <TrendingUp size={11} /> DỰ BÁO 7 NGÀY
            </span>
            <Sparkline
              values={activeDiseaseData.daily_forecast?.map((d) => d.predicted_cases) ?? []}
              color={riskMeta(activeDiseaseData.risk_level).color}
              width={130}
            />
          </div>

          {/* 14-day bar chart */}
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
                <span className="rp-legend-dot" style={{ background: "#334155" }} />
                Lịch sử
              </span>
              <span>
                <span className="rp-legend-dot" style={{ background: "#38bdf8" }} />
                Dự báo
              </span>
            </div>
          </div>

          {/* risk message */}
          <div
            className="rp-alert-msg"
            style={{ borderLeft: `3px solid ${riskMeta(activeDiseaseData.risk_level).color}` }}
          >
            <AlertTriangle size={13} color={riskMeta(activeDiseaseData.risk_level).color} />
            <p>{activeDiseaseData.risk_message}</p>
          </div>

          {/* regions */}
          {activeDiseaseData.regions?.length > 0 && (
            <div>
              <span className="rp-section-label">
                <MapPin size={11} /> KHU VỰC ẢNH HƯỞNG
              </span>
              <RegionList regions={activeDiseaseData.regions} />
            </div>
          )}

          {/* model meta */}
          <div className="rp-meta-row">
            <span>
              Phương pháp: <em>{activeDiseaseData.method?.replace(/_/g, " ")}</em>
            </span>
            {activeDiseaseData.mae != null && (
              <span>
                MAE: <em>{activeDiseaseData.mae.toFixed(2)}</em>
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── RETRAIN BUTTON ── */}
      <button
        className={`btn-retrain ${isRetraining ? "btn-retrain--busy" : ""} ${retrainState === "done" ? "btn-retrain--done" : ""} ${retrainState === "error" ? "btn-retrain--error" : ""}`}
        onClick={handleRetrain}
        disabled={isRetraining}
      >
        <RetrainIcon
          size={14}
          className={isRetraining ? "rp-spin-icon" : ""}
          color={rs.color ?? undefined}
        />
        <span>{rs.label}</span>
      </button>
    </div>
  );
};

export default ReportRightPanel;