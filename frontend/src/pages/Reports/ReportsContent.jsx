import React from "react";
import { Download, TrendingUp } from "lucide-react";
import { useArticles } from "../../hooks/useArticles";
import FloatingChat from "../../components/FloatingChat/FloatingChat";
import "./ReportsContent.css";

const ReportsContent = () => {
  const { currentArticles, articles } = useArticles();

  // Lấy bài viết mới nhất làm tâm điểm của báo cáo
  const latestArticle = currentArticles[0] || {};
  const isHighRisk = latestArticle.risk_level === "HIGH";
  const chatStats = React.useMemo(() => {
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

  return (
    <div className="risk-report-container">
      {/* Bao bọc toàn bộ bằng Grid */}
      <div className="report-grid">
        {/* =========================================
            CỘT BÊN TRÁI (LEFT PANEL)
        ============================================= */}
        <div className="report-left-panel">
          {/* 🟢 Khối thẻ panel-card bao bọc toàn bộ khối nội dung, bao gồm cả Header */}
          <div className="panel-card">
            {/* Header đã nằm bên trong, kế thừa nền liền mạch */}
            <div className="report-header">
              <div className="header-titles">
                <h1>Tạo Báo cáo Rủi ro</h1>
                <p>
                  Xem xét và đánh giá các chỉ số dịch tễ tổng hợp cùng dữ liệu
                  giám sát đã xác minh.
                </p>
              </div>
              <button className="btn-export-main">
                <Download size={18} /> XUẤT BÁO CÁO
              </button>
            </div>

            <div className="summary-header">
              <div className="summary-title-group">
                <h3>TÓM TẮT DỊCH TỄ</h3>
                <div
                  className={`risk-badge ${isHighRisk ? "critical" : "warning"}`}
                >
                  {isHighRisk
                    ? "PHÁT HIỆN RỦI RO CẤP 3"
                    : "PHÁT HIỆN RỦI RO CẤP 2"}
                </div>
              </div>

              <div className="meta-grid">
                <div className="meta-item">
                  <span className="meta-label">MÃ HỒ SƠ</span>
                  <span className="meta-value">
                    #CS-2026-
                    {latestArticle.article_id?.substring(0, 4).toUpperCase() ||
                      "9982"}
                  </span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">PHÒNG BAN</span>
                  <span className="meta-value">Giám sát Dịch tễ</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">THỜI GIAN (UTC)</span>
                  <span className="meta-value">
                    {new Date()
                      .toISOString()
                      .replace("T", " ")
                      .substring(0, 16)}
                  </span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">HỆ THỐNG</span>
                  <span className="meta-value">Sentinel Core V4.0</span>
                </div>
              </div>
            </div>

            <div className="narrative-section">
              <div className="section-heading">
                <div className="bullet-point"></div>
                <h4>QUAN SÁT LÂM SÀNG & TƯỜNG THUẬT</h4>
              </div>
              <div className="narrative-content">
                <p>
                  Dựa trên dữ liệu thu thập từ khu vực{" "}
                  <strong>{latestArticle.location || "chưa xác định"}</strong>,
                  hệ thống ghi nhận sự xuất hiện của{" "}
                  <strong>
                    {latestArticle.disease_name || "mầm bệnh không rõ"}
                  </strong>
                  .
                  {latestArticle.summary ||
                    "Hệ thống AI đánh giá đây là một sự kiện dịch tễ cần được theo dõi sát sao."}
                </p>

                <p className="bold-label">Biện pháp đã ghi nhận:</p>
                <ul>
                  <li>Tăng cường lấy mẫu bệnh phẩm và giám sát biến động.</li>
                  <li>
                    Kích hoạt hệ thống báo cáo liên tục mỗi 15 phút tại khu vực
                    bị ảnh hưởng.
                  </li>
                </ul>

                <p className="bold-label">Khuyến nghị chính:</p>
                <p className="recommendation-text">
                  Cần lập tức thực hiện khoanh vùng và lấy mẫu xét nghiệm diện
                  rộng (PCR) tại {latestArticle.location || "khu vực này"} để
                  loại trừ khả năng bùng phát diện rộng của{" "}
                  {latestArticle.disease_name || "dịch bệnh"}.
                </p>
              </div>
            </div>

            <div className="signature-section">
              <div className="section-heading">
                <div className="bullet-point"></div>
                <h4>CHỮ KÝ XÁC THỰC (ĐIỆN TỬ)</h4>
              </div>
              <div className="signature-box">
                <div className="sig-line">
                  <span className="sig-text">Electronic Signature Encoded</span>
                  <span className="sig-hash">Sentinel Hash: 8F33...E901</span>
                </div>
              </div>
              <div className="footer-warning">
                ĐÂY LÀ BẢN TÓM TẮT RỦI RO TỰ ĐỘNG • CHỈ DÙNG ĐỂ XEM TRƯỚC •
                KHÔNG DÙNG LÀM KẾT LUẬN CUỐI CÙNG NẾU THIẾU SỰ PHÊ DUYỆT CỦA
                CHUYÊN GIA
              </div>
            </div>
          </div>
        </div>

        {/* =========================================
            CỘT BÊN PHẢI (RIGHT PANEL)
        ============================================= */}
        <div className="report-right-panel">
          <div className="forecast-header">
            <h2>Dự báo Xu hướng</h2>
            <p>
              Mô hình Học máy (Machine Learning) dự phóng diễn biến trong 72 giờ
              tới dựa trên sự thay đổi dịch tễ học khu vực.
            </p>
          </div>

          {/* Khối 1: Biểu đồ */}
          <div className="chart-card">
            <div className="chart-top">
              <span className="chart-title">
                <TrendingUp size={14} /> DỰ PHÓNG DỊCH BỆNH
              </span>
              <span className="chart-badge">+12% Dự đoán</span>
            </div>
            <div className="bar-chart-area">
              <div className="bar-col">
                <div className="bar b1"></div>
                <span>T2</span>
              </div>
              <div className="bar-col">
                <div className="bar b2"></div>
                <span>T3</span>
              </div>
              <div className="bar-col">
                <div className="bar b3"></div>
                <span>T4</span>
              </div>
              <div className="bar-col">
                <div className="bar b4"></div>
                <span>T5</span>
              </div>
              <div className="bar-col">
                <div className="bar b5"></div>
                <span>T6</span>
              </div>
              <div className="bar-col">
                <div className="bar b6"></div>
                <span>T7</span>
              </div>
              <div className="bar-col">
                <div className="bar b7"></div>
                <span>CN</span>
              </div>
            </div>
          </div>

          {/* Khối 2: Phân tích yếu tố */}
          <div className="factors-card">
            <div className="section-heading small">
              <div className="bullet-point"></div>
              <h4>PHÂN TÍCH YẾU TỐ RỦI RO</h4>
            </div>

            <div className="factor-item">
              <div className="factor-labels">
                <span>Tác động môi trường / Thời tiết</span>
                <span>84%</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill coral"
                  style={{ width: "84%" }}
                ></div>
              </div>
            </div>

            <div className="factor-item">
              <div className="factor-labels">
                <span>Tỉ lệ tiêm chủng / Miễn dịch</span>
                <span>62%</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill teal"
                  style={{ width: "62%" }}
                ></div>
              </div>
            </div>

            <div className="factor-item">
              <div className="factor-labels">
                <span>Mật độ dân số & Giao thương</span>
                <span>45%</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill blue"
                  style={{ width: "45%" }}
                ></div>
              </div>
            </div>
          </div>

          {/* Khối 3: Thông tin đầu ra */}
          <div className="insights-card">
            <div className="section-heading small">
              <div className="bullet-point"></div>
              <h4>THÔNG TIN DỰ BÁO ĐẦU RA</h4>
            </div>

            <ul className="insight-list">
              <li>
                <span className="dot red"></span>
                <p>
                  <strong>Cảnh báo Điểm nóng:</strong> Khu vực{" "}
                  {latestArticle.location || "đang theo dõi"} cho thấy mức tăng
                  22% trong các báo cáo về{" "}
                  {latestArticle.disease_name || "bệnh truyền nhiễm"}. Khuyến
                  nghị nâng mức cảnh báo lên Cấp độ 2.
                </p>
              </li>
              <li>
                <span className="dot teal"></span>
                <p>
                  <strong>Hành động Phòng ngừa:</strong> Triển khai đội phản ứng
                  nhanh đến khu vực trung tâm trước sáng thứ Tư để giảm nhẹ rủi
                  ro đạt đỉnh vào thứ Sáu theo dự phóng.
                </p>
              </li>
            </ul>

            <button className="btn-export-data">
              XUẤT GÓI DỮ LIỆU <Download size={14} />
            </button>
          </div>
        </div>
      </div>
      <FloatingChat
        stats={chatStats}
        analytics={{
          top_keywords: chatStats.top_keyword
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
