import React from "react";
import {
  Activity,
  CheckSquare,
  Bold,
  Italic,
  List,
  MoreVertical,
  Bot,
  Send,
  Sparkles,
} from "lucide-react";
import { useArticles } from "../../hooks/useArticles";
import { useChat } from "../../hooks/useChat"; // Import Hook Chat
import "./ReportsContent.css";

const ReportsContent = () => {
  const { currentArticles, totalArticlesCount } = useArticles();

  // Bài mới nhất làm trọng tâm báo cáo
  const latestArticle = currentArticles[0];

  // Lấy 3 bài tiếp theo làm "Lịch sử báo cáo" (tránh bài đầu tiên)
  const historyArticles = currentArticles.slice(1, 4);

  // Khởi tạo Chat Hook với câu chào dựa trên dữ liệu thật
  const initialAiMessage = `Xin chào! Tôi vừa phân tích xong ${totalArticlesCount || "các"} bài báo. Hệ thống phát hiện mật độ từ khóa "${latestArticle?.keywords?.split(",")[0] || "dịch bệnh"}" đang tăng. Bạn có muốn tôi tạo phần "Khuyến nghị can thiệp" không?`;

  const {
    messages,
    inputValue,
    setInputValue,
    sendMessage,
    handleKeyPress,
    isTyping,
  } = useChat(initialAiMessage);

  return (
    <div className="reports-inner-body">
      <div className="reports-header">
        <h1>Tạo Báo cáo Cảnh báo Dịch tễ</h1>
        <p>
          Tổng hợp các tín hiệu mạng xã hội, báo chí và phân tích NLP thành hồ
          sơ rủi ro hoàn chỉnh.
        </p>
      </div>

      <div className="reports-grid">
        <div className="left-column">
          {/* Metrics Row (Giữ nguyên như cũ) */}
          <div className="metrics-row">
            <div className="metric-card">
              <div className="card-title">
                <Activity size={14} /> CHỈ SỐ THEO DÕI TỰ ĐỘNG
              </div>
              <div className="bio-item">
                <span className="bio-label">TỐC ĐỘ XUẤT BẢN TIN TỨC</span>
                <div className="bio-value-row">
                  <div>
                    <span className="bio-value">12</span>
                    <span className="bio-unit">Bài/giờ</span>
                  </div>
                  <span className="status-badge stable">ỔN ĐỊNH</span>
                </div>
              </div>
              <div className="bio-item">
                <span className="bio-label">TỈ LỆ LAN TRUYỀN TỪ KHÓA (AI)</span>
                <div className="bio-value-row">
                  <div>
                    <span className="bio-value">91</span>
                    <span className="bio-unit">%</span>
                  </div>
                  <span className="status-badge critical">CẢNH BÁO</span>
                </div>
              </div>
            </div>
            <div className="metric-card">
              <div className="card-title">
                <CheckSquare size={14} /> AI ĐỀ XUẤT HÀNH ĐỘNG
              </div>
              <div className="ai-rec-box">
                Khuyến nghị kiểm tra chéo nguồn tin y tế địa phương ngay lập tức
                do tỷ lệ từ khóa rủi ro tăng cao.
              </div>
              <div className="ai-rec-subtext">
                Hệ thống NLP phát hiện sự tập trung bất thường của các bài viết
                liên quan.
              </div>
            </div>
          </div>

          {/* Editor Section */}
          <div>
            <h2 className="section-title">Bản nháp Báo cáo Tự động</h2>
            <div className="editor-container">
              <div className="editor-toolbar">
                <div className="toolbar-tools">
                  <button>
                    <Bold size={16} />
                  </button>
                  <button>
                    <Italic size={16} />
                  </button>
                  <button>
                    <List size={16} />
                  </button>
                </div>
                <div className="toolbar-actions">
                  <span className="word-count">Độ dài: 142 từ</span>
                  <button className="btn-generate">AI TẠO BẢN THẢO</button>
                </div>
              </div>
              <div
                className="editor-content"
                contentEditable="true"
                suppressContentEditableWarning={true}
              >
                <p>
                  Dựa trên dữ liệu cào tự động từ hệ thống, chúng tôi ghi nhận
                  sự kiện đáng chú ý sau:
                </p>
                <br />
                <p style={{ color: "#0ea5e9", fontWeight: "bold" }}>
                  {latestArticle
                    ? `Tiêu điểm: ${latestArticle.title}`
                    : "Chưa có dữ liệu bài báo mới."}
                </p>
                <br />
                <p>
                  Các từ khóa được phát hiện bao gồm:{" "}
                  <strong>{latestArticle?.keywords || "N/A"}</strong>.
                </p>
                <p>
                  Biện pháp đề xuất: Chuyển thông tin tới bộ phận y tế dự phòng
                  để xác minh.
                </p>
              </div>
            </div>
          </div>

          {/* History Section - ĐÃ ĐƯA DỮ LIỆU THẬT VÀO */}
          <div>
            <h2 className="section-title">Lịch sử Báo cáo (Dữ liệu cũ)</h2>
            <div className="history-grid">
              {historyArticles.length > 0 ? (
                historyArticles.map((art, index) => {
                  // Tạo màu trạng thái giả định dựa trên index
                  const statusClass =
                    index === 0 ? "complete" : index === 1 ? "urgent" : "draft";
                  const statusText =
                    index === 0
                      ? "HOÀN TẤT"
                      : index === 1
                        ? "KHẨN CẤP"
                        : "BẢN NHÁP";

                  return (
                    <div className="history-card" key={art.id}>
                      <div className="h-card-header">
                        <span className={`h-status ${statusClass}`}>
                          {statusText}
                        </span>
                        <span className="h-time">
                          {new Date(art.created_at).toLocaleDateString("vi-VN")}
                        </span>
                      </div>
                      <div
                        className="h-title"
                        style={{
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {art.title}
                      </div>
                      <div className="h-desc">
                        Từ khóa: {art.keywords || "Chung"}
                      </div>
                    </div>
                  );
                })
              ) : (
                <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
                  Đang tải lịch sử...
                </p>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN (CHAT) - SỬ DỤNG USECHAT HOOK */}
        <div className="right-column">
          <div className="chat-panel">
            <div className="chat-header">
              <div className="chat-bot-info">
                <div className="bot-avatar">
                  <Bot size={20} />
                </div>
                <div className="bot-details">
                  <h3>Trợ lý Sentinel AI</h3>
                  <span className="bot-status">
                    <span className="dot"></span> ĐANG SẴN SÀNG
                  </span>
                </div>
              </div>
              <MoreVertical size={18} color="#94a3b8" />
            </div>

            <div
              className="chat-body"
              style={{ overflowY: "auto", maxHeight: "400px" }}
            >
              {/* Render danh sách tin nhắn động */}
              {messages.map((msg) => (
                <div key={msg.id} className={`msg-wrapper ${msg.sender}`}>
                  <div className="msg-bubble">{msg.text}</div>
                  <span className="msg-time">
                    {msg.time} • {msg.sender === "ai" ? "SENTINEL" : "BẠN"}
                  </span>
                </div>
              ))}

              {isTyping && (
                <div className="processing-text">
                  <Sparkles size={12} className="spinning" /> Sentinel đang xử
                  lý...
                </div>
              )}

              {/* Cửa sổ Insight Tĩnh */}
              {!isTyping && messages.length === 1 && (
                <div className="insight-card">
                  <div className="insight-header">
                    <Sparkles size={12} /> INSIGHT Y TẾ
                  </div>
                  <div className="insight-text">
                    Nguồn tin:{" "}
                    <a
                      href={latestArticle?.link}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: "#0ea5e9" }}
                    >
                      {latestArticle?.link || "N/A"}
                    </a>
                  </div>
                  <div className="insight-actions">
                    <button className="btn-action primary">
                      THÊM VÀO BÁO CÁO
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="chat-input-area">
              <div className="input-box">
                <input
                  type="text"
                  placeholder="Nhập câu hỏi để AI phân tích..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                />
                <button className="send-btn" onClick={sendMessage}>
                  <Send size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsContent;
