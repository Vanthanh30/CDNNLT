import React, { useState, useEffect, useRef } from "react";
import { Bot, Send, X } from "lucide-react";
import "./FloatingChat.css"; // File CSS chứa style của Bot

const FloatingChat = ({ stats, analytics }) => {
  const [showChat, setShowChat] = useState(false);
  const [closing, setClosing] = useState(false);

  // Khởi tạo tin nhắn chào mừng dựa trên props truyền vào
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef(null);

  // Cập nhật câu chào khi có dữ liệu mới
  useEffect(() => {
    const timer = setTimeout(() => {
      setMessages([
        {
          id: 1,
          role: "ai",
          text: `Xin chào! Tôi là Sentinel AI.\n\nĐã phân tích **${stats?.total_articles || 0} bài báo**. Bệnh nổi bật: **${stats?.top_keyword || "N/A"}** (${stats?.top_keyword_count || 0} bài).\n\nBạn muốn hỏi gì?`,
        },
      ]);
    }, 0);

    // Dọn dẹp timer
    return () => clearTimeout(timer);
  }, [stats]);

  // Tự động cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    if (showChat) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, typing, showChat]);

  // Xử lý gửi tin nhắn
  const send = async (quickText) => {
    const text = quickText || input.trim();
    if (!text || typing) return;

    setInput("");
    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text }]);
    setTyping(true);

    // Giả lập AI trả lời (Sau này nối API Backend vào đây)
    setTimeout(() => {
      const kws = (analytics?.top_keywords || [])
        .slice(0, 3)
        .map((k) => `${k.keyword} (${k.count} bài)`)
        .join(", ");
      const reply = `Dựa trên dữ liệu:\n- Tổng bài: **${stats?.total_articles || 0}**\n- Bệnh nổi bật: **${kws || "chưa có"}**\n- Bài 7 ngày gần đây: **${stats?.recent_7d || 0}**`;

      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: "ai", text: reply },
      ]);
      setTyping(false);
    }, 1200);
  };

  // Hiệu ứng đóng khung chat mượt mà
  const closeChat = () => {
    setClosing(true);
    setTimeout(() => {
      setShowChat(false);
      setClosing(false);
    }, 220);
  };

  // Render chữ in đậm
  const renderText = (text) =>
    text
      .split(/(\*\*[^*]+\*\*)/g)
      .map((part, i) =>
        part.startsWith("**") ? (
          <strong key={i}>{part.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{part}</span>
        ),
      );

  return (
    <>
      {/* ── NÚT BẤM (FAB) ── */}
      <button
        className={`ac-fab ${showChat ? "active" : ""}`}
        onClick={() => setShowChat(!showChat)}
      >
        <Bot size={17} />
        <span>Sentinel AI</span>
      </button>

      {/* ── KHUNG CHAT ── */}
      {showChat && (
        <div className={`ac-chat-box ${closing ? "closing" : ""}`}>
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

          <div className="ac-chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`ac-msg ${msg.role}`}>
                {msg.role === "ai" && (
                  <div className="ac-msg-avatar">
                    <Bot size={12} />
                  </div>
                )}
                <div className="ac-msg-bubble">{renderText(msg.text)}</div>
              </div>
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

          <div className="ac-quick-btns">
            {[
              "Bệnh nào nhiều nhất?",
              "7 ngày gần đây?",
              "Khu vực đáng lo?",
            ].map((q, i) => (
              <button key={i} className="ac-quick" onClick={() => send(q)}>
                {q}
              </button>
            ))}
          </div>

          <div className="ac-chat-input">
            <textarea
              placeholder="Hỏi về dịch bệnh... (Enter gửi)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              rows={1}
            />
            <button onClick={() => send()} disabled={typing || !input.trim()}>
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default FloatingChat;
