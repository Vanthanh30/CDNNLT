import { useMemo, useState } from "react";
import { reportService } from "../services/api";

export const useReportData = (articles, currentArticles) => {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoadingPdf, setIsLoadingPdf] = useState(false);

  const latestArticle = currentArticles[0] || {};
  const isHighRisk = latestArticle.risk_level === "HIGH";

  // 1. Tính toán Dữ liệu Báo cáo
  const reportData = useMemo(() => {
    if (!articles || articles.length === 0)
      return { chartData: [], factors: {}, insights: {} };

    // Biểu đồ 7 ngày
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      const dateStr = d.toISOString().split("T")[0];
      const label = d
        .toLocaleDateString("vi-VN", { weekday: "short" })
        .replace("Th ", "T");
      return { dateStr, label: label === "CN" ? "CN" : label, count: 0 };
    });

    articles.forEach((a) => {
      if (!a.processed_at) return;
      const aDate = new Date(a.processed_at).toISOString().split("T")[0];
      const dayIndex = last7Days.findIndex((d) => d.dateStr === aDate);
      if (dayIndex !== -1) last7Days[dayIndex].count += 1;
    });

    const maxCount = Math.max(...last7Days.map((d) => d.count), 1);
    const chartData = last7Days.map((d) => ({
      ...d,
      heightPct: Math.round((d.count / maxCount) * 100),
    }));

    // Yếu tố rủi ro
    const total = articles.length;
    const factors = {
      highRiskPct: Math.round(
        (articles.filter((a) => a.risk_level === "HIGH").length / total) * 100,
      ),
      infectedPct: Math.round(
        (articles.filter((a) => a.cases_infected > 0).length / total) * 100,
      ),
      deadPct: Math.round(
        (articles.filter((a) => a.cases_dead > 0).length / total) * 100,
      ),
    };

    // Top bệnh
    const diseaseCounts = {};
    articles.forEach((a) => {
      if (a.disease_name)
        diseaseCounts[a.disease_name] =
          (diseaseCounts[a.disease_name] || 0) + 1;
    });
    const topDisease = Object.entries(diseaseCounts).sort(
      (a, b) => b[1] - a[1],
    )[0];

    return {
      chartData,
      factors,
      insights: { topDisease: topDisease?.[0] || "Chưa rõ" },
    };
  }, [articles]);

  // 2. Tính toán cho Chatbot
  const chatStats = useMemo(() => {
    if (!articles || !articles.length)
      return { total_articles: 0, top_keyword: "N/A", top_keyword_count: 0 };
    const counts = {};
    articles.forEach((a) => {
      if (a.disease_name)
        counts[a.disease_name] = (counts[a.disease_name] || 0) + 1;
    });
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    return {
      total_articles: articles.length,
      top_keyword: top?.[0] || "N/A",
      top_keyword_count: top?.[1] || 0,
    };
  }, [articles]);

  // 3. Xử lý logic PDF
  const handlePreview = async () => {
    setIsLoadingPdf(true);
    try {
      const blob = await reportService.downloadWeeklyReport();
      const fileUrl = window.URL.createObjectURL(blob);
      setPreviewUrl(fileUrl);
    } catch (error) {
      console.error(error);
      alert("Hệ thống chưa sẵn sàng tạo báo cáo. Vui lòng thử lại sau!");
    } finally {
      setIsLoadingPdf(false);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await reportService.downloadWeeklyReport();
      const fileUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = fileUrl;
      link.download = `Sentinel_Bao_Cao_${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(fileUrl);
    } catch (error) {
      console.error("Chi tiết lỗi tải PDF:", error);
      alert("Lỗi tải xuống báo cáo!");
    }
  };

  return {
    latestArticle,
    isHighRisk,
    reportData,
    chatStats,
    previewUrl,
    setPreviewUrl,
    isLoadingPdf,
    handlePreview,
    handleDownload,
  };
};
