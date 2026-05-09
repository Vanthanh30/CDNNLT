import React, { useState, useEffect, useRef } from "react";
import { Bot, Send, X, Link as LinkIcon } from "lucide-react"; // Thêm icon Link
import "./FloatingChat.css";

const FloatingChat = ({ stats }) => {
  const [showChat, setShowChat] = useState(false);
  const [closing, setClosing] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef(null);

  // Khởi tạo lời chào dựa trên dữ liệu thật của trang hiện tại
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

  // 🟢 HÀM GỌI API THẬT
  const send = async (quickText) => {
    const text = quickText || input.trim();
    if (!text || typing) return;

    setInput("");
    // In câu hỏi của người dùng ra màn hình
    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text }]);
    setTyping(true);

    try {
      // Gọi xuống API Gateway (đảm bảo BE của bạn đang chạy ở cổng 8000)
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      if (!response.ok) throw new Error("Lỗi kết nối API Chat");

      const data = await response.json();

      // In câu trả lời của AI và danh sách Nguồn tham khảo
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "ai",
          text: data.answer,
          sources: data.sources, // 🟢 Lưu lại sources từ Backend
        },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "ai",
          text: "Xin lỗi, hiện tại tôi không thể kết nối tới máy chủ Sentinel. Vui lòng kiểm tra lại mạng hoặc thử lại sau.",
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
                <div className="ac-msg-bubble-wrap">
                  <div className="ac-msg-bubble">{renderText(msg.text)}</div>

                  {/* 🟢 RENDER DANH SÁCH NGUỒN THAM KHẢO NẾU CÓ */}
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
              "Tình hình dịch tả lợn?",
              "Sốt xuất huyết ở đâu?",
              "Mức độ rủi ro hiện tại?",
            ].map((q, i) => (
              <button key={i} className="ac-quick" onClick={() => send(q)}>
                {q}
              </button>
            ))}
          </div>

          <div className="ac-chat-input">
            <textarea
              placeholder="Hỏi AI về dịch bệnh... (Enter để gửi)"
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
