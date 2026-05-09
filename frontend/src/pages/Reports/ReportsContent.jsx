import React from "react";
import { X } from "lucide-react";
import { useArticles } from "../../hooks/useArticles";
import { useReportData } from "../../hooks/useReportData";
import FloatingChat from "../../components/FloatingChat/FloatingChat";
import ReportLeftPanel from "../../components/ReportPanel/ReportLeftPanel";
import ReportRightPanel from "../../components/ReportPanel/ReportRightPanel";
import "./ReportsContent.css";

const ReportsContent = () => {
  const { currentArticles, articles } = useArticles();

  const {
    latestArticle,
    isHighRisk,
    reportData,
    chatStats,
    previewUrl,
    setPreviewUrl,
    isLoadingPdf,
    handlePreview,
    handleDownload,
  } = useReportData(articles, currentArticles);

  return (
    <div className="risk-report-container">
      {/* MODAL XEM TRƯỚC PDF */}
      {previewUrl && (
        <div className="pdf-modal-overlay" onClick={() => setPreviewUrl(null)}>
          <div className="pdf-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="pdf-modal-header">
              <h3>Bản xem trước Báo cáo PDF</h3>
              <div className="pdf-modal-actions">
                <button
                  className="btn-close-modal"
                  onClick={() => setPreviewUrl(null)}
                >
                  <X size={18} />
                </button>
              </div>
            </div>
            <div className="pdf-modal-body">
              <iframe
                src={previewUrl}
                title="PDF Preview"
                className="pdf-iframe"
              />
            </div>
          </div>
        </div>
      )}

      {/* LƯỚI GIAO DIỆN CHÍNH */}
      <div className="report-grid">
        <ReportLeftPanel
          latestArticle={latestArticle}
          isHighRisk={isHighRisk}
          isLoadingPdf={isLoadingPdf}
          handlePreview={handlePreview}
          handleDownload={handleDownload}
        />

        <ReportRightPanel
          articlesCount={articles.length}
          chartData={reportData.chartData}
          factors={reportData.factors}
          insights={reportData.insights}
          latestArticle={latestArticle}
          handleDownload={handleDownload}
        />
      </div>

      {/* CHATBOT */}
      <FloatingChat
        stats={chatStats}
        analytics={{
          top_keywords:
            chatStats.top_keyword !== "N/A"
              ? [
                  {
                    keyword: chatStats.top_keyword,
                    count: chatStats.top_keyword_count,
                  },
                ]
              : [],
        }}
      />
    </div>
  );
};

export default ReportsContent;
