import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { articleService } from "../../services/api";
import "./RightPanel.css";

// ── SVG Icons ────────────────────────────────────────────────────────────────
const IconPin = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
    <circle cx="12" cy="10" r="3" />
  </svg>
);

const IconVirus = () => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
  </svg>
);

const IconClose = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const IconExternal = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

const IconGlobe = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

// ── helpers ───────────────────────────────────────────────────────────────────
function formatRelative(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins} phút trước`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} giờ trước`;
  return `${Math.floor(hrs / 24)} ngày trước`;
}

function buildDays(n = 7) {
  const days = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dow = d.getDay();
    days.push({
      label: dow === 0 ? "CN" : `T${dow + 1}`,
      sub: `${d.getDate()}/${d.getMonth() + 1}`,
      isToday: i === 0,
    });
  }
  return days;
}

const RISK = {
  HIGH: { label: "NHIỀU TIN", cls: "tag-high" },
  MEDIUM: { label: "VÀI TIN", cls: "tag-mid" },
  LOW: { label: "ÍT TIN", cls: "tag-low" },
};
const TABS = ["Nhiều tin", "Vài tin", "Ít tin"];
const RISK_KEYS = ["HIGH", "MEDIUM", "LOW"];
const RISK_COLORS = { HIGH: "#f97316", MEDIUM: "#eab308", LOW: "#3b82f6" };

const RightPanel = ({ selectedLocation = null, onClearLocation }) => {
  const navigate = useNavigate();
  const [allArticles, setAllArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [dayIdx, setDayIdx] = useState(6);
  const days = buildDays(7);

  useEffect(() => {
    (async () => {
      try {
        const data = await articleService.getAllArticles();
        setAllArticles(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    setActiveTab(0);
  }, [selectedLocation]);

  const isLocationMode = !!selectedLocation;
  const sourceArticles = isLocationMode
    ? (selectedLocation.allArticles || [])
    : allArticles;

  const counts = RISK_KEYS.map(
    (r) => sourceArticles.filter((a) => a.risk_level === r).length
  );
  const total = sourceArticles.length;

  const listArticles = sourceArticles.filter(
    (a) => a.risk_level === RISK_KEYS[activeTab]
  );

  const withLoc = listArticles.filter((a) => a.location);
  const withoutLoc = listArticles.filter((a) => !a.location);

  const diseaseMap = sourceArticles.reduce((acc, a) => {
    if (!a.disease_name) return acc;
    if (!acc[a.disease_name]) acc[a.disease_name] = { total: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    acc[a.disease_name].total += 1;
    if (a.risk_level) acc[a.disease_name][a.risk_level] = (acc[a.disease_name][a.risk_level] || 0) + 1;
    return acc;
  }, {});
  const diseaseList = Object.entries(diseaseMap)
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, 6)
    .map(([name, data]) => {
      const dominantRisk = ["HIGH", "MEDIUM", "LOW"].reduce((best, r) =>
        (data[r] || 0) > (data[best] || 0) ? r : best, "LOW"
      );
      return [name, data.total, dominantRisk];
    });
  const maxDis = diseaseList[0]?.[1] || 1;

  return (
    <div className="rp-root">
      {/* Location header */}
      {isLocationMode && (
        <div className="rp-loc-header">
          <div className="rp-loc-info">
            <span className="rp-loc-pin-icon"><IconPin /></span>
            <div>
              <div className="rp-loc-name">{selectedLocation.name}</div>
              <div className="rp-loc-sub">{selectedLocation.count} bài viết tại khu vực này</div>
            </div>
          </div>
          <button className="rp-loc-close" onClick={onClearLocation} title="Quay lại toàn quốc">
            <IconClose />
          </button>
        </div>
      )}

      {/* Disease tags */}
      {isLocationMode && selectedLocation.diseases?.length > 0 && (
        <div className="rp-loc-diseases">
          {selectedLocation.diseases.map((d, i) => (
            <span key={i} className="rp-dis-tag">
              <IconVirus /> {d}
            </span>
          ))}
        </div>
      )}

      {/* Date bar (non-location mode) */}
      {!isLocationMode && (
        <div className="rp-datebar">
          <span className="rp-updated">Updated 0s ago</span>
          <div className="rp-days">
            {days.map((d, i) => (
              <button
                key={i}
                className={`rp-day${i === dayIdx ? " active" : ""}${d.isToday ? " today" : ""}`}
                onClick={() => setDayIdx(i)}
              >
                <span className="rp-day-lbl">{d.isToday ? "Hôm nay" : d.label}</span>
                <span className="rp-day-sub">{d.sub}</span>
                <span className="rp-day-dot" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="rp-stats-row">
        <div className="rp-stats-boxes">
          {TABS.map((lbl, i) => (
            <button
              key={i}
              className={`rp-stat rp-stat-${["high", "mid", "low"][i]}${activeTab === i ? " active" : ""}`}
              onClick={() => setActiveTab(i)}
            >
              <span className="rp-stat-num">{counts[i]}</span>
              <span className="rp-stat-lbl">{lbl}</span>
            </button>
          ))}
        </div>
        <span className="rp-total-note">{total} tin{isLocationMode ? " tại đây" : " gần đây"}</span>
      </div>

      {/* Articles section */}
      <div className="rp-section">
        <div className="rp-sec-head">
          <span className="rp-sec-title">Báo chí đưa tin</span>
          <span className="rp-badge">{total}</span>
        </div>

        <div className="rp-tabs">
          {TABS.map((lbl, i) => (
            <button
              key={i}
              className={`rp-tab${activeTab === i ? " active" : ""}`}
              onClick={() => setActiveTab(i)}
            >
              {lbl}
            </button>
          ))}
        </div>

        {!isLocationMode && (
          <div className="rp-col-head">
            <span>Có vị trí ({withLoc.length})</span>
            <span><IconGlobe /> Toàn quốc / chưa rõ ({withoutLoc.length})</span>
          </div>
        )}

        {loading ? (
          <p className="rp-empty">Đang tải dữ liệu...</p>
        ) : listArticles.length === 0 ? (
          <p className="rp-empty">Không có bài trong mục này</p>
        ) : isLocationMode ? (
          <div className="rp-single-col">
            {listArticles.slice(0, 8).map((art) => (
              <ArticleCard key={art.article_id} art={art} />
            ))}
          </div>
        ) : (
          <div className="rp-two-col">
            <div className="rp-col">
              {withLoc.slice(0, 5).map((art) => (
                <ArticleCard key={art.article_id} art={art} />
              ))}
            </div>
            <div className="rp-col">
              {withoutLoc.slice(0, 5).map((art) => (
                <ArticleCard key={art.article_id} art={art} />
              ))}
            </div>
          </div>
        )}

        {listArticles.length - (isLocationMode ? 8 : 10) > 0 && (
          <button className="rp-see-more" onClick={() => navigate("/search")}>
            Xem thêm ({listArticles.length - (isLocationMode ? 8 : 10)} mục)
          </button>
        )}
      </div>

      {/* Disease frequency section */}
      <div className="rp-section">
        <div className="rp-sec-head">
          <span className="rp-sec-title">Bệnh được nhắc nhiều</span>
          {isLocationMode && (
            <span className="rp-sec-badge-loc">tại {selectedLocation.name}</span>
          )}
        </div>
        <div className="rp-dis-hdr">
          <span>BỆNH</span>
          <span>SỐ TIN</span>
        </div>
        {loading ? (
          <p className="rp-empty">Đang tải...</p>
        ) : diseaseList.length === 0 ? (
          <p className="rp-empty">Chưa có dữ liệu</p>
        ) : (
          diseaseList.map(([name, count, risk]) => {
            const color = RISK_COLORS[risk] || "#3b82f6";
            return (
              <div className="rp-dis-row" key={name}>
                <span className="rp-dis-name">{name}</span>
                <div className="rp-dis-right">
                  <div className="rp-dis-bar-wrap">
                    <div
                      className="rp-dis-bar"
                      style={{ width: `${Math.round((count / maxDis) * 100)}%`, background: color }}
                    />
                  </div>
                  <span className="rp-dis-count" style={{ color }}>{count}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

const ArticleCard = ({ art }) => {
  const risk = RISK[art.risk_level] || RISK.LOW;
  return (
    <a href={art.url || "#"} target="_blank" rel="noreferrer" className="rp-card">
      <span className={`rp-risk-tag ${risk.cls}`}>{risk.label}</span>
      <div className="rp-card-disease">
        {art.disease_name || "Cập nhật chung"}
      </div>
      <div className="rp-card-meta">
        {art.location ? `Vietnam · ${art.location}` : "Vietnam"}
        {art.processed_at ? ` · ${formatRelative(art.processed_at)}` : ""}
      </div>
      <div className="rp-card-src">
        <IconExternal /> pipeline.web
      </div>
    </a>
  );
};

export default RightPanel;