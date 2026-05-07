import React from "react";
import { Download, TrendingUp } from "lucide-react";
import "./ReportRightPanel.css";

const ReportRightPanel = ({
  articlesCount,
  chartData,
  factors,
  insights,
  latestArticle,
  handleDownload,
}) => {
  return (
    <div className="report-right-panel">
      {/* Header */}
      <div className="forecast-header">
        <h2>Dự báo Xu hướng</h2>
        <p>
          Phân tích từ {articlesCount || 0} tín hiệu mạng xã hội và báo chí gần
          đây.
        </p>
      </div>

      {/* Widget Biểu đồ */}
      <div className="chart-card">
        <div className="chart-top">
          <span className="chart-title">
            <TrendingUp size={14} /> TẦN SUẤT XUẤT HIỆN TIN TỨC (7 NGÀY)
          </span>
          {/* 🟢 Khôi phục Badge +12% Dự đoán */}
          <span className="chart-badge">+12% Dự đoán</span>
        </div>
        <div className="bar-chart-area">
          {chartData?.map((day, idx) => (
            <div className="bar-col" key={idx}>
              <div
                className="bar"
                style={{
                  height: `${Math.max(day.heightPct || 0, 5)}%`, // Ép chiều cao tối thiểu 5% để luôn hiện thanh
                  backgroundColor:
                    day.heightPct > 70
                      ? "#ef4444"
                      : day.heightPct > 30
                        ? "#38bdf8"
                        : "#475569",
                }}
                title={`${day.count} bài`}
              ></div>
              <span>{day.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Widget Yếu tố Rủi ro */}
      <div className="factors-card">
        <div className="section-heading small">
          <div className="bullet-point"></div>
          <h4>THỐNG KÊ TỶ TRỌNG SỰ KIỆN</h4>
        </div>
        <div className="factor-item">
          <div className="factor-labels">
            <span>Tỉ lệ tin báo động ĐỎ (Mức rủi ro cao)</span>
            <span>{factors?.highRiskPct || 0}%</span>
          </div>
          <div className="progress-track">
            <div
              className="progress-fill coral"
              style={{ width: `${factors?.highRiskPct || 0}%` }}
            ></div>
          </div>
        </div>
        <div className="factor-item">
          <div className="factor-labels">
            <span>Tỉ lệ tin có ghi nhận ca lây nhiễm</span>
            <span>{factors?.infectedPct || 0}%</span>
          </div>
          <div className="progress-track">
            <div
              className="progress-fill teal"
              style={{ width: `${factors?.infectedPct || 0}%` }}
            ></div>
          </div>
        </div>
        <div className="factor-item">
          <div className="factor-labels">
            <span>Tỉ lệ tin có ca tử vong</span>
            <span>{factors?.deadPct || 0}%</span>
          </div>
          <div className="progress-track">
            <div
              className="progress-fill blue"
              style={{ width: `${factors?.deadPct || 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Widget Insight */}
      <div className="insights-card">
        <div className="section-heading small">
          <div className="bullet-point"></div>
          <h4>THÔNG TIN PHÂN TÍCH ĐẦU RA</h4>
        </div>
        <ul className="insight-list">
          <li>
            <span className="dot red"></span>
            <p>
              <strong>Cảnh báo Điểm nóng:</strong> Bệnh{" "}
              <strong>{insights?.topDisease}</strong> đang là tâm điểm chú ý của
              truyền thông. Đề nghị rà soát dữ liệu.
            </p>
          </li>
          <li>
            <span className="dot teal"></span>
            <p>
              <strong>Tình trạng bài mới nhất:</strong> Sự kiện tại{" "}
              <strong>{latestArticle?.location || "địa phương"}</strong> hiện
              được xếp loại Rủi ro{" "}
              {latestArticle?.risk_level === "HIGH" ? "Cao" : "Trung bình"}.
            </p>
          </li>
        </ul>
        <button className="btn-export-data" onClick={handleDownload}>
          TẢI GÓI DỮ LIỆU BÁO CÁO (PDF) <Download size={14} />
        </button>
      </div>
    </div>
  );
};

export default ReportRightPanel;
