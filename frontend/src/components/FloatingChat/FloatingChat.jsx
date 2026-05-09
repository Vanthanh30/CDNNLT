import React, { useState, useEffect, useRef } from "react";
import { Bot, Send, X, Link as LinkIcon, Copy, Edit2 } from "lucide-react";
import "./FloatingChat.css";

// ── SUB-COMPONENT: BÓNG TIN NHẮN ──────────────────────────────
const MessageBubble = ({
  msg,
  onCopy,
  isEditing,
  editText,
  setEditText,
  onEditStart,
  onSaveEdit,
  onCancelEdit,
}) => {
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

  // 🟢 GIAO DIỆN KHI ĐANG CHỈNH SỬA (INLINE EDIT)
  if (isEditing) {
    return (
      <div className={`ac-msg ${msg.role}`}>
        <div className="ac-msg-bubble-wrap edit-mode">
          <textarea
            className="ac-edit-textarea"
            value={editText}
            onChange={(e) => {
              setEditText(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            autoFocus
            rows={1}
          />
          <div className="ac-edit-actions">
            <button className="ac-btn-cancel" onClick={onCancelEdit}>
              Hủy
            </button>
            <button
              className="ac-btn-save"
              onClick={() => onSaveEdit(msg.id, editText)}
            >
              Gửi lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 🟢 GIAO DIỆN TIN NHẮN BÌNH THƯỜNG
  return (
    <div className={`ac-msg ${msg.role}`}>
      {msg.role === "ai" && (
        <div className="ac-msg-avatar">
          <Bot size={12} />
        </div>
      )}

      <div className="ac-msg-bubble-wrap">
        <div className="ac-msg-bubble">{renderText(msg.text)}</div>

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

      <div className="ac-msg-actions">
        <button title="Copy" onClick={() => onCopy(msg.text)}>
          <Copy size={12} />
        </button>
        {msg.role === "user" && (
          <button
            title="Chỉnh sửa"
            onClick={() => onEditStart(msg.id, msg.text)}
          >
            <Edit2 size={12} />
          </button>
        )}
      </div>
    </div>
  );
};

// ── MAIN COMPONENT ──────────────────────────────
const FloatingChat = ({ stats }) => {
  const [showChat, setShowChat] = useState(false);
  const [closing, setClosing] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);

  // 🟢 STATES CHO TÍNH NĂNG INLINE EDIT
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

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

  useEffect(() => {
    if (showChat) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing, showChat]);

  const handleInput = (e) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleCopy = (text) => navigator.clipboard.writeText(text);

  // 🟢 CÁC HÀM XỬ LÝ CHỈNH SỬA TIN NHẮN
  const handleEditStart = (id, text) => {
    setEditingId(id);
    setEditText(text);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditText("");
  };

  // Hàm Gửi lại tin nhắn đã sửa
  const handleSaveEdit = async (msgId, newText) => {
    if (!newText.trim() || typing) return;

    setEditingId(null); // Tắt chế độ Edit

    // Tìm vị trí của tin nhắn được sửa
    const msgIndex = messages.findIndex((m) => m.id === msgId);
    if (msgIndex === -1) return;

    // Cắt bỏ tin nhắn cũ và toàn bộ các tin nhắn sau đó (giống ChatGPT)
    const updatedMessages = messages.slice(0, msgIndex);

    // Thêm tin nhắn user mới cập nhật vào
    const newUserMsg = { id: Date.now(), role: "user", text: newText.trim() };
    setMessages([...updatedMessages, newUserMsg]);
    setTyping(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: newText.trim() }),
      });

      if (!response.ok) throw new Error("Lỗi API Chat");
      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "ai",
          text: data.answer,
          sources: data.sources,
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

  // Hàm Gửi tin nhắn mới như bình thường
  const send = async (quickText) => {
    const text = quickText || input.trim();
    if (!text || typing) return;

    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text }]);
    setTyping(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      if (!response.ok) throw new Error("Lỗi API Chat");
      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "ai",
          text: data.answer,
          sources: data.sources,
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
              <MessageBubble
                key={msg.id}
                msg={msg}
                onCopy={handleCopy}
                // Truyền props cho Inline Edit
                isEditing={editingId === msg.id}
                editText={editText}
                setEditText={setEditText}
                onEditStart={handleEditStart}
                onSaveEdit={handleSaveEdit}
                onCancelEdit={handleCancelEdit}
              />
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
            {["Tình hình dịch tả lợn?", "Sốt xuất huyết ở đâu?"].map((q, i) => (
              <button key={i} className="ac-quick" onClick={() => send(q)}>
                {q}
              </button>
            ))}
          </div>

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
