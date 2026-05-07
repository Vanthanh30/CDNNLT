import React from "react";
import { Download, Eye } from "lucide-react";
import "./ReportLeftPanel.css";

const ReportLeftPanel = ({
  latestArticle,
  isHighRisk,
  isLoadingPdf,
  handlePreview,
  handleDownload,
}) => {
  return (
    <div className="report-left-panel">
      <div className="panel-card">
        {/* Header & Buttons */}
        <div className="report-header">
          <div className="header-titles">
            <h1>Tạo Báo cáo Rủi ro</h1>
            <p>
              Xem xét và đánh giá các chỉ số dịch tễ tổng hợp cùng dữ liệu giám
              sát.
            </p>
          </div>
          <div className="header-actions">
            <button
              className="btn-secondary"
              onClick={handlePreview}
              disabled={isLoadingPdf}
            >
              {isLoadingPdf ? (
                "ĐANG XỬ LÝ..."
              ) : (
                <>
                  <Eye size={16} /> XEM TRƯỚC
                </>
              )}
            </button>
            <button className="btn-export-main" onClick={handleDownload}>
              <Download size={16} /> XUẤT PDF
            </button>
          </div>
        </div>

        {/* Tóm tắt */}
        <div className="summary-header">
          <div className="summary-title-group">
            <h3>TÓM TẮT DỊCH TỄ</h3>
            <div
              className={`risk-badge ${isHighRisk ? "critical" : "warning"}`}
            >
              {isHighRisk ? "PHÁT HIỆN RỦI RO CẤP 3" : "PHÁT HIỆN RỦI RO CẤP 2"}
            </div>
          </div>
          <div className="meta-grid">
            <div className="meta-item">
              <span className="meta-label">MÃ HỒ SƠ</span>
              <span className="meta-value">
                #CS-{new Date().getFullYear()}-
                {latestArticle.article_id?.substring(0, 4).toUpperCase() ||
                  "9982"}
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-label">PHÒNG BAN</span>
              <span className="meta-value">Giám sát Dịch tễ</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">THỜI GIAN CẬP NHẬT</span>
              <span className="meta-value">
                {latestArticle.processed_at
                  ? new Date(latestArticle.processed_at).toLocaleDateString(
                      "vi-VN",
                    )
                  : "Hôm nay"}
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-label">HỆ THỐNG</span>
              <span className="meta-value">Sentinel Core V4.0</span>
            </div>
          </div>
        </div>

        {/* AI Quote & Tường thuật */}
        <div className="narrative-section">
          <div className="section-heading">
            <div className="bullet-point"></div>
            <h4>ĐÁNH GIÁ CHUYÊN MÔN TỰ ĐỘNG</h4>
          </div>
          <div className="narrative-content">
            <p>
              Thông qua luồng dữ liệu thời gian thực tại{" "}
              <strong>{latestArticle.location || "khu vực theo dõi"}</strong>,
              hệ thống Sentinel đã phát hiện chuỗi tín hiệu cảnh báo liên quan
              đến{" "}
              <strong>
                {latestArticle.disease_name || "mầm bệnh chưa xác định"}
              </strong>
              . Biến động bất thường này được AI tự động phân loại ở mức Rủi ro{" "}
              {latestArticle.risk_level === "HIGH" ? "Cao" : "Trung bình"}.
            </p>
            <div className="ai-quote-box">
              <span className="quote-label">⚡ TRÍCH XUẤT TỪ AI (NLP):</span>
              <p>
                "
                {latestArticle.summary ||
                  "Dữ liệu đang được tổng hợp và đánh giá..."}
                "
              </p>
            </div>
            <p className="bold-label" style={{ marginTop: "16px" }}>
              Khuyến nghị can thiệp:
            </p>
            <ul className="action-list">
              <li>
                Phân phối báo cáo này đến bộ phận y tế dự phòng tại{" "}
                {latestArticle.location || "địa phương"}.
              </li>
              <li>
                Kích hoạt bộ lọc giám sát tần suất cao cho từ khóa "
                {latestArticle.disease_name}".
              </li>
            </ul>
          </div>
        </div>

        {/* Chữ ký */}
        <div className="signature-section">
          <div className="section-heading">
            <div className="bullet-point"></div>
            <h4>CHỮ KÝ XÁC THỰC (ĐIỆN TỬ)</h4>
          </div>
          <div className="signature-box">
            <div className="sig-line">
              <span className="sig-text">Sentinel AI System</span>
              <span className="sig-hash">
                Hash: {latestArticle.article_id?.substring(0, 12) || "8F33E901"}
              </span>
            </div>
          </div>
          <div className="footer-warning">
            ĐÂY LÀ BẢN TÓM TẮT RỦI RO TỰ ĐỘNG • KHÔNG DÙNG LÀM KẾT LUẬN Y TẾ
            CUỐI CÙNG
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportLeftPanel;
