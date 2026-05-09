import React, { useState, useEffect, useRef } from "react";
import { Bot, Send, X, Link as LinkIcon } from "lucide-react";
import "./FloatingChat.css";

// ── SUB-COMPONENT: BÓNG TIN NHẮN ──────────────────────────────
const MessageBubble = ({ msg }) => {
  // Hàm render text đơn giản có hỗ trợ xuống dòng và in đậm (Markdown cơ bản của GPT)
  const renderText = (text) => {
    return text.split("\n").map((line, lineIndex) => (
      <React.Fragment key={lineIndex}>
        {line
          .split(/(\*\*[^*]+\*\*)/g)
          .map((part, i) =>
            part.startsWith("**") ? (
              <strong key={i}>{part.slice(2, -2)}</strong>
            ) : (
              <span key={i}>{part}</span>
            ),
          )}
        {lineIndex !== text.split("\n").length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <div className={`ac-msg ${msg.role}`}>
      {msg.role === "ai" && (
        <div className="ac-msg-avatar">
          <Bot size={12} />
        </div>
      )}
      <div className="ac-msg-bubble-wrap">
        <div className="ac-msg-bubble">{renderText(msg.text)}</div>

        {/* 🟢 Danh sách nguồn tham khảo */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="ac-msg-sources">
            <p className="source-title">
              <LinkIcon size={10} /> Nguồn tham khảo:
            </p>
            <ul>
              {msg.sources.map((src, idx) => (
                <li key={idx}>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    title={src.title}
                  >
                    {src.title.length > 40
                      ? src.title.substring(0, 40) + "..."
                      : src.title}
                  </a>
                  <span className="source-risk">
                    ({src.disease_name} - Rủi ro {src.risk_level})
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// ── MAIN COMPONENT: KHUNG CHAT TỔNG ──────────────────────────────
const FloatingChat = ({ stats }) => {
  const [showChat, setShowChat] = useState(false);
  const [closing, setClosing] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);

  const bottomRef = useRef(null);
  const textareaRef = useRef(null); // Ref để điều khiển chiều cao ô nhập liệu

  // Khởi tạo lời chào
  useEffect(() => {
    const timer = setTimeout(() => {
      setMessages([
        {
          id: 1,
          role: "ai",
          text: `Xin chào! Tôi là Sentinel AI.\n\nĐã phân tích **${stats?.total_articles || 0} bài báo**. Bệnh nổi bật: **${stats?.top_keyword || "N/A"}**.\n\nBạn muốn hỏi gì về tình hình dịch bệnh?`,
        },
      ]);
    }, 0);
    return () => clearTimeout(timer);
  }, [stats]);

  // Cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    if (showChat) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, typing, showChat]);

  // 🟢 HÀM TỰ ĐỘNG THAY ĐỔI CHIỀU CAO TEXTAREA
  const handleInput = (e) => {
    setInput(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto"; // Reset để đo lại
      el.style.height = `${el.scrollHeight}px`; // Nới rộng theo nội dung
    }
  };

  // 🟢 HÀM GỌI API (SEARCH NỘI BỘ VÀ TỰ SINH CÂU TRẢ LỜI)
  const send = async (quickText) => {
    const text = quickText || input.trim();
    if (!text || typing) return;

    setInput("");

    // Reset lại chiều cao textarea sau khi gửi
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text }]);
    setTyping(true);

    try {
      const response = await fetch(
        `http://localhost:8000/internal/search?question=${encodeURIComponent(text)}`,
      );
      if (!response.ok) throw new Error("Lỗi kết nối API");

      const rows = await response.json();

      let answerText = "";
      let sourcesData = [];

      if (!rows || rows.length === 0) {
        answerText =
          "❌ Không tìm thấy dữ liệu báo cáo nào phù hợp với câu hỏi của bạn.";
      } else {
        const resultObj = {};
        rows.forEach((row) => {
          const disease = row.disease_name || "Bệnh chưa xác định";
          const location = row.location || "Nhiều địa phương";
          if (!resultObj[disease]) resultObj[disease] = [];
          resultObj[disease].push(location);
        });

        const answerParts = [];
        for (const [disease, locations] of Object.entries(resultObj)) {
          const uniqueLocations = [...new Set(locations)];
          answerParts.push(
            `📌 Dịch bệnh **${disease}** hiện đang xuất hiện tại: ${uniqueLocations.join(", ")}`,
          );
        }

        answerText =
          "Dựa trên dữ liệu hệ thống ghi nhận được:\n\n" +
          answerParts.join("\n\n");
        sourcesData = rows.map((row) => ({
          title: row.title,
          url: row.url,
          disease_name: row.disease_name,
          location: row.location,
          risk_level: row.risk_level,
        }));
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "ai",
          text: answerText,
          sources: sourcesData,
        },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "ai",
          text: "Xin lỗi, không thể kết nối tới máy chủ Sentinel.",
        },
      ]);
    } finally {
      setTyping(false);
    }
  };

  const closeChat = () => {
    setClosing(true);
    setTimeout(() => {
      setShowChat(false);
      setClosing(false);
    }, 220);
  };

  return (
    <>
      <button
        className={`ac-fab ${showChat ? "active" : ""}`}
        onClick={() => setShowChat(!showChat)}
      >
        <Bot size={17} />
        <span>Sentinel AI</span>
      </button>

      {showChat && (
        <div className={`ac-chat-box ${closing ? "closing" : ""}`}>
          {/* Header */}
          <div className="ac-chat-header">
            <div className="ac-bot-info">
              <div className="ac-bot-avatar">
                <Bot size={16} />
              </div>
              <div>
                <p className="ac-bot-name">Sentinel AI</p>
                <p className="ac-bot-status">● Đang hoạt động</p>
              </div>
            </div>
            <button className="ac-icon-btn" onClick={closeChat}>
              <X size={15} />
            </button>
          </div>

          {/* Messages Area */}
          <div className="ac-chat-messages">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}

            {typing && (
              <div className="ac-msg ai">
                <div className="ac-msg-avatar">
                  <Bot size={12} />
                </div>
                <div className="ac-msg-bubble typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick Buttons */}
          <div className="ac-quick-btns">
            {[
              "Tình hình dịch tả lợn?",
              "Sốt xuất huyết ở đâu?",
              "Mức độ rủi ro?",
            ].map((q, i) => (
              <button key={i} className="ac-quick" onClick={() => send(q)}>
                {q}
              </button>
            ))}
          </div>

          {/* Input Area */}
          <div className="ac-chat-input">
            <textarea
              ref={textareaRef}
              placeholder="Hỏi AI về dịch bệnh..."
              value={input}
              onChange={handleInput}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              rows={1}
            />
            <button
              className="ac-send-btn"
              onClick={() => send()}
              disabled={typing || !input.trim()}
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default FloatingChat;
