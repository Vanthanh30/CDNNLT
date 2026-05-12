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
    reportData,
    chatStats,
    previewUrl,
    isLoadingPdf,
    handlePreview,
    handleDownload,
  } = useReportData(articles, currentArticles);

  return (
    <div className="risk-report-container">
      {/* LƯỚI GIAO DIỆN CHÍNH */}
      <div className="report-grid">
        <ReportLeftPanel
          isLoadingPdf={isLoadingPdf}
          handlePreview={handlePreview}
          handleDownload={handleDownload}
          previewUrl={previewUrl}
        />

        <ReportRightPanel
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
