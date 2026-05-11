import React from "react";
import { Download, Eye } from "lucide-react";
import "./ReportLeftPanel.css";

const ReportLeftPanel = ({
  isLoadingPdf,
  handlePreview,
  handleDownload,
  previewUrl, // 🟢 Thêm biến này để nhận link PDF từ Component cha
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

        {/* 🟢 KHUNG HIỂN THỊ TRỰC TIẾP (EMBEDDED PREVIEW) */}
        <div className="pdf-preview-container">
          {previewUrl ? (
            <iframe
              src={previewUrl}
              title="PDF Preview"
              className="embedded-pdf-iframe"
            />
          ) : (
            <div className="empty-preview-state">
              <div className="empty-icon-wrapper">
                <Eye size={32} />
              </div>
              <p>Chưa có dữ liệu hiển thị.</p>
              <span>
                Vui lòng bấm <strong>XEM TRƯỚC</strong> để tải và xem bản nháp
                báo cáo PDF trực tiếp tại đây.
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportLeftPanel;
