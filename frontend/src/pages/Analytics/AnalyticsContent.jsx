import React from "react";
import { Sparkles, MoreHorizontal, Globe } from "lucide-react";
import { useArticles } from "../../hooks/useArticles";
import "./AnalyticsContent.css";

const AnalyticsContent = () => {
  const { currentArticles, uniqueOptions, isLoading } = useArticles();

  // Lấy tối đa 6 Tags có thật từ Database, nếu chưa có data thì dùng biến tĩnh dự phòng
  const cloudTags = uniqueOptions?.tags?.slice(0, 6) || [];
  const defaultTags = [
    "CÚM A",
    "COVID-19",
    "HÔ HẤP",
    "ĐƯỜNG RUỘT",
    "SỐT XUẤT HUYẾT",
  ];
  const displayTags = cloudTags.length > 0 ? cloudTags : defaultTags;

  return (
    <div className="analytics-inner-body">
      {/* HEADER */}
      <div className="analytics-header">
        <div>
          <h1 className="main-title">Phân tích & Dự báo Xu hướng</h1>
          <p className="subtitle">
            Hệ thống đo lường dữ liệu dịch tễ học chính xác V2.4
          </p>
        </div>

        <div className="filter-card">
          <div className="time-filters">
            <button className="filter-btn">24 Giờ</button>
            <button className="filter-btn active">7 Ngày</button>
            <button className="filter-btn">30 Ngày</button>
          </div>
          <div className="region-select">
            <Globe size={14} /> Việt Nam
          </div>
        </div>
      </div>

      <div className="analytics-grid">
        {/* LEFT PANEL */}
        <div className="panel chart-main">
          <div className="panel-header">
            <h3>Bản đồ Mật độ Từ khóa</h3>
            <MoreHorizontal size={18} color="#94a3b8" />
          </div>

          {/* Hiển thị Từ khóa thật từ Database */}
          <div className="keyword-cloud">
            {displayTags.map((tag, idx) => (
              <span
                key={idx}
                className={`node ${idx === 0 ? "highlight" : "dim"}`}
              >
                {tag}
              </span>
            ))}
          </div>

          <div className="stats-row">
            <div className="stat">
              <span className="stat-label">Tốc độ Gia tăng</span>
              <span className="stat-value up">+14.2%</span>
            </div>
            <div className="stat" style={{ textAlign: "center" }}>
              <span className="stat-label">Cường độ Tín hiệu</span>
              <span className="stat-value">Cao (0.88)</span>
            </div>
            <div className="stat" style={{ textAlign: "right" }}>
              <span className="stat-label">Chỉ số Bất thường</span>
              <span className="stat-value warn">Trung bình</span>
            </div>
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div className="side-column">
          <div className="panel">
            <h3>Chỉ số Tác động Môi trường</h3>
            {[
              {
                name: "Độ ẩm không khí",
                val: 82,
                weight: "0.82",
                color: "#10b981",
              },
              {
                name: "Mật độ di chuyển",
                val: 74,
                weight: "0.74",
                color: "#6366f1",
              },
              {
                name: "Mức độ ô nhiễm",
                val: 51,
                weight: "0.51",
                color: "#f87171",
              },
            ].map((item, i) => (
              <div key={i} className="predictor-item">
                <div className="p-info">
                  <span>
                    <span
                      className="dot"
                      style={{ background: item.color }}
                    ></span>
                    {item.name}
                  </span>
                  <span className="p-weight">Trọng số: {item.weight}</span>
                </div>
                <div className="p-bar">
                  <div
                    className="fill"
                    style={{ width: `${item.val}%`, background: item.color }}
                  ></div>
                </div>
              </div>
            ))}
          </div>

          <div className="panel">
            <h3>Cụm Cảm xúc (Sentiment)</h3>
            <div className="sentiment-tags">
              <span className="tag blue">Bình thường</span>
              <span className="tag green">Quan tâm nhẹ</span>
              <span className="tag orange">Lo lắng</span>
              <span className="tag">Hoang mang</span>
              <span className="tag">Phẫn nộ</span>
            </div>
            <button className="expand-btn">Mở rộng ↗</button>
          </div>
        </div>
      </div>

      {/* TABLE - Dữ liệu thực từ Database */}
      <div className="panel">
        <div className="panel-header" style={{ marginBottom: "20px" }}>
          <h3>🛰 Điểm nóng Báo chí Mới nhất</h3>
          <span
            style={{
              fontSize: "10px",
              color: "#64748b",
              fontWeight: "600",
              letterSpacing: "0.5px",
            }}
          >
            DỮ LIỆU THỜI GIAN THỰC TỪ CRAWLER
          </span>
        </div>

        <div className="table-responsive">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Nội dung / Từ khóa chính</th>
                <th>Mức độ nghiêm trọng (AI)</th>
              <th>Thời gian xuất bản</th>
              <th>Trạng thái Nguồn</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td
                  colSpan="5"
                  style={{ textAlign: "center", padding: "20px" }}
                >
                  Đang tải dữ liệu...
                </td>
              </tr>
            ) : currentArticles.length === 0 ? (
              <tr>
                <td
                  colSpan="5"
                  style={{ textAlign: "center", padding: "20px" }}
                >
                  Chưa có dữ liệu
                </td>
              </tr>
            ) : (
              // Thêm 'idx' (index) vào hàm map để tính toán thanh bar
              currentArticles.slice(0, 4).map((art, idx) => (
                <tr key={art.id}>
                  <td>
                    <strong>
                      {art.keywords
                        ? art.keywords.split(",")[0].toUpperCase()
                        : "TIN TỨC CHUNG"}
                    </strong>
                    <br />
                    <span
                      style={{
                        fontSize: "11px",
                        color: "#64748b",
                        display: "inline-block",
                        maxWidth: "300px",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {art.title}
                    </span>
                  </td>
                  <td>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <div className="p-bar" style={{ width: "80px" }}>
                        {/* ĐÃ SỬA LỖI TẠI ĐÂY: Dùng thuật toán giả ngẫu nhiên cố định dựa vào idx thay vì Math.random() */}
                        <div
                          className="fill"
                          style={{
                            width: `${((idx * 23) % 50) + 40}%`,
                            background: "#ef4444",
                          }}
                        ></div>
                      </div>
                      <span style={{ fontSize: "12px" }}>Cao</span>
                    </div>
                  </td>
                  <td>
                    {new Date(art.created_at).toLocaleDateString("vi-VN")}
                  </td>
                  <td>
                    <span className="badge blue">ĐÃ XÁC MINH</span>
                  </td>
                  <td>
                    <a
                      href={art.link}
                      target="_blank"
                      rel="noreferrer"
                      className="action-link"
                    >
                      Đọc bài gốc
                    </a>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        </div>
      </div>

      {/* FLOAT BUTTON */}
      <div className="floating-ai-btn">
        <Sparkles size={18} />
        <span>Hỏi Sentinel AI</span>
      </div>
    </div>
  );
};

export default AnalyticsContent;
