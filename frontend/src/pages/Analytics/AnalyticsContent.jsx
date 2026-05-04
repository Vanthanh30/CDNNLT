import React, { useState, useEffect, useRef } from "react";
import { MoreVertical, ChevronDown, Zap, X, Send, Bot, Tag } from "lucide-react";
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import "./AnalyticsContent.css";

const API_BASE_URL = "http://localhost:8000";
const OPENAI_KEY = ""; // Bạn cần set OpenAI key ở đây nếu muốn dùng AI
const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#a855f7"];

// ===================== KEYWORDS MODAL =====================
const KeywordsModal = ({ keywords, onClose }) => {
  const max = Math.max(...keywords.map(k => k.count), 1);
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3><Tag size={16} /> Tất cả Từ khóa ({keywords.length})</h3>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          {keywords.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>Chưa có từ khóa</p>
          ) : keywords.map((kw, idx) => (
            <div key={idx} className="kw-row">
              <div className="kw-info">
                <span className="kw-dot" style={{ background: COLORS[idx % COLORS.length] }}></span>
                <span className="kw-name">{kw}</span>
                <span className="kw-count">-</span>
              </div>
              <div className="kw-bar-wrap">
                <div className="kw-bar-fill" style={{
                  width: `${Math.round((idx + 1) / keywords.length * 100)}%`,
                  background: COLORS[idx % COLORS.length],
                }}></div>
              </div>
              <span className="kw-pct">{Math.round((idx + 1) / keywords.length * 100)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ===================== CHAT BUBBLE (góc phải) =====================
const ChatBubble = ({ articles, onClose, setShowChat }) => {
  const [isClosing, setIsClosing] = useState(false);
  const [messages, setMessages] = useState([{
    id: 1, role: "ai",
    text: `Xin chào! Tôi là Sentinel AI.\n\nĐã phân tích **${articles?.length || 0} bài báo** về dịch bệnh.\n\nBạn muốn hỏi gì về tình hình dịch bệnh?`,
  }]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const buildContext = () => {
    const articlesText = (articles || [])
      .slice(0, 5)
      .map(a => `${a.title}: ${a.disease_name || 'N/A'} tại ${a.location || 'N/A'}`)
      .join("\n");

    return `Bạn là Sentinel AI - trợ lý phân tích dịch bệnh Việt Nam. Dữ liệu từ hệ thống:
Tổng bài phân tích: ${articles?.length || 0}
Các bài gần đây:
${articlesText || 'Chưa có dữ liệu'}

Hãy trả lời ngắn gọn bằng tiếng Việt dựa trên dữ liệu trên. Nếu không có thông tin thì nói rõ.`;
  };

  const sendMessage = async (quickText) => {
    const userText = quickText || input.trim();
    if (!userText || isTyping) return;
    setInput("");

    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text: userText }]);
    setIsTyping(true);

    try {
      if (!OPENAI_KEY) {
        throw new Error("OpenAI key chưa được cấu hình");
      }

      const contents = [
        {
          role: "system",
          content: buildContext(),
        },
      ];

      messages.slice(1).forEach((m) => {
        contents.push({
          role: m.role === "ai" ? "assistant" : "user",
          content: m.text,
        });
      });

      contents.push({
        role: "user",
        content: userText,
      });

      const res = await fetch(
        "https://api.openai.com/v1/chat/completions",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${OPENAI_KEY}`,
          },
          body: JSON.stringify({
            model: "gpt-4o-mini",
            messages: contents,
            max_tokens: 500,
            temperature: 0.7,
          }),
        }
      );

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(`API error: ${errData?.error?.message || "Unknown"}`);
      }

      const data = await res.json();
      const aiText = data?.choices?.[0]?.message?.content || "Không nhận được phản hồi từ AI.";
      setMessages((prev) => [...prev, { id: Date.now() + 1, role: "ai", text: aiText }]);
    } catch (err) {
      console.error("AI error:", err);
      setMessages((prev) => [...prev, { id: Date.now() + 1, role: "ai", text: `Lỗi: ${err.message}` }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
      if (setShowChat) setShowChat(false);
    }, 250);
  };

  const renderText = (text) =>
    text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : <span key={i}>{part}</span>
    );

  return (
    <div className={`chat-bubble-box ${isClosing ? "bubble-closing" : ""}`}>
      <div className="chat-bubble-header">
        <div className="chat-bot-info">
          <div className="bot-avatar"><Bot size={18} /></div>
          <div>
            <h3>Sentinel AI</h3>
            <span className="bot-online">● GPT-4o Mini</span>
          </div>
        </div>
        <button className="modal-close" onClick={handleClose}><X size={16} /></button>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-msg ${msg.role}`}>
            {msg.role === "ai" && <div className="msg-avatar"><Bot size={13} /></div>}
            <div className="msg-bubble">{renderText(msg.text)}</div>
          </div>
        ))}
        {isTyping && (
          <div className="chat-msg ai">
            <div className="msg-avatar"><Bot size={13} /></div>
            <div className="msg-bubble typing"><span /><span /><span /></div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="quick-questions">
        {["Các bệnh được phát hiện?", "Vùng dịch nào nhiều?", "Bài mới nhất?"].map((q, i) => (
          <button key={i} className="quick-btn" onClick={() => sendMessage(q)}>{q}</button>
        ))}
      </div>

      <div className="chat-input-row">
        <textarea
          className="chat-textarea"
          placeholder="Hỏi về tình hình dịch bệnh... (Enter để gửi)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
          rows={1}
        />
        <button className="chat-send-btn" onClick={() => sendMessage()} disabled={isTyping || !input.trim()}>
          <Send size={16} />
        </button>
      </div>
    </div>
  );
};

// ===================== MAIN COMPONENT =====================
const AnalyticsContent = () => {
  const [timeRange, setTimeRange] = useState(7);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showKeywords, setShowKeywords] = useState(false);
  const [showChat, setShowChat] = useState(false);

  // Fetch articles từ backend
  useEffect(() => {
    const fetchArticles = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/articles`);
        const data = await res.json();
        setArticles(Array.isArray(data) ? data : []);
        console.log("✅ Articles fetched:", data?.length || 0);
      } catch (err) {
        console.error("❌ Articles fetch error:", err);
        setArticles([]);
      } finally {
        setLoading(false);
      }
    };
    fetchArticles();
  }, []);

  // Lọc bài viết theo thời gian
  const getFilteredArticles = () => {
    const now = new Date();
    const cutoffDate = new Date(now.getTime() - timeRange * 24 * 60 * 60 * 1000);

    return articles.filter(a => {
      if (!a.processed_at) return true;
      const articleDate = new Date(a.processed_at);
      return articleDate >= cutoffDate;
    });
  };

  const filteredArticles = getFilteredArticles();

  // Tính toán các chỉ số
  const totalInRange = filteredArticles.length;
  const uniqueDiseases = [...new Set(filteredArticles.map(a => a.disease_name).filter(Boolean))];
  const uniqueLocations = [...new Set(filteredArticles.map(a => a.location).filter(Boolean))];

  // Đếm tần suất mỗi bệnh
  const diseaseFreq = {};
  filteredArticles.forEach(a => {
    if (a.disease_name) {
      diseaseFreq[a.disease_name] = (diseaseFreq[a.disease_name] || 0) + 1;
    }
  });
  const topDiseases = Object.entries(diseaseFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, count]) => ({ name, count }));

  // Đếm tần suất mỗi vị trí
  const locationFreq = {};
  filteredArticles.forEach(a => {
    if (a.location) {
      locationFreq[a.location] = (locationFreq[a.location] || 0) + 1;
    }
  });
  const topLocations = Object.entries(locationFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, count]) => ({ name, count }));

  // Đếm tần suất risk level
  const riskFreq = { LOW: 0, MEDIUM: 0, HIGH: 0 };
  filteredArticles.forEach(a => {
    const risk = a.risk_level || 'LOW';
    if (risk in riskFreq) riskFreq[risk]++;
  });

  // Tính chỉ số rủi ro (%)
  const highRiskPercent = totalInRange > 0 ? Math.round((riskFreq.HIGH / totalInRange) * 100) : 0;
  const getRisk = (v) => v > 50 ? { text: "Cao", color: "#ef4444" } : v > 20 ? { text: "Trung bình", color: "#f59e0b" } : { text: "Thấp", color: "#10b981" };
  const risk = getRisk(highRiskPercent);

  // Dữ liệu cho biểu đồ (theo ngày)
  const dailyData = {};
  filteredArticles.forEach(a => {
    const date = a.processed_at?.split('T')[0] || new Date().toISOString().split('T')[0];
    dailyData[date] = (dailyData[date] || 0) + 1;
  });
  const chartData = Object.entries(dailyData)
    .sort((a, b) => new Date(a[0]) - new Date(b[0]))
    .map(([date, count]) => ({ date, count }));

  const predictors = topDiseases.slice(0, 3).map((d, idx) => ({
    name: d.name,
    value: totalInRange > 0 ? Math.round((d.count / totalInRange) * 100) : 0,
    count: d.count,
    color: COLORS[idx],
  }));

  const forecastData = topDiseases.slice(0, 5).map((d, idx) => ({
    id: idx,
    name: d.name,
    count: d.count,
    percentage: totalInRange > 0 ? Math.round((d.count / totalInRange) * 100) : 0,
    status: d.count > Math.max(...topDiseases.map(x => x.count / 2)) ? "Escalating" : "Monitoring",
    color: idx < 2 ? "#ef4444" : "#10b981",
  }));

  const timeLabel = timeRange === 1 ? "24 Giờ" : timeRange === 7 ? "7 Ngày" : "30 Ngày";

  const formatDate = (d) => {
    if (!d) return "";
    const dt = new Date(d + "T00:00:00");
    return `${dt.getDate()}/${dt.getMonth() + 1}`;
  };

  return (
    <div className="analytics-inner-body">
      {/* Keywords Modal */}
      {showKeywords && (
        <KeywordsModal keywords={uniqueDiseases} onClose={() => setShowKeywords(false)} />
      )}

      {/* Chat Bubble */}
      {showChat && (
        <ChatBubble articles={filteredArticles} onClose={() => setShowChat(false)} setShowChat={setShowChat} />
      )}

      {/* HEADER */}
      <div className="analytics-header">
        <div>
          <h1 className="main-title">Phân tích Xu hướng & Dự đoán</h1>
          <p className="subtitle">
            {loading ? "Đang tải dữ liệu..." : `${totalInRange} bài viết trong ${timeLabel} | Tổng: ${articles.length} bài`}
          </p>
        </div>
        <div className="filter-card">
          <div className="time-filters">
            {[{ l: "24 Giờ", v: 1 }, { l: "7 Ngày", v: 7 }, { l: "30 Ngày", v: 30 }].map((t) => (
              <button key={t.v} className={`filter-btn ${timeRange === t.v ? "active" : ""}`} onClick={() => setTimeRange(t.v)}>{t.l}</button>
            ))}
          </div>
          <button className="region-select"><span>Việt Nam</span><ChevronDown size={14} /></button>
        </div>
      </div>

      {/* MAIN GRID */}
      <div className="analytics-grid">
        <div className="panel chart-panel">
          <div className="panel-header">
            <h3>Số bài viết theo ngày ({timeLabel})</h3>
            <button className="more-btn"><MoreVertical size={16} /></button>
          </div>
          <div className="chart-main">
            {loading ? (
              <div className="chart-placeholder">Đang tải biểu đồ...</div>
            ) : chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="date" stroke="#94a3b8" style={{ fontSize: "11px" }} tickFormatter={formatDate} />
                  <YAxis stroke="#94a3b8" style={{ fontSize: "11px" }} />
                  <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #334155", borderRadius: "8px" }} labelFormatter={(v) => `Ngày ${formatDate(v)}`} formatter={(v) => [`${v} bài`, "Số bài"]} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="chart-placeholder">Không có dữ liệu trong khoảng thời gian này</div>
            )}

            {!loading && topDiseases.length > 0 && chartData.length > 1 && (
              <>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", margin: "20px 0 8px", fontWeight: 600 }}>Top bệnh được phát hiện</div>
                <ResponsiveContainer width="100%" height={160}>
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="date" stroke="#94a3b8" style={{ fontSize: "10px" }} tickFormatter={formatDate} />
                    <YAxis stroke="#94a3b8" style={{ fontSize: "10px" }} />
                    <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #334155", borderRadius: "8px" }} labelFormatter={(v) => `Ngày ${formatDate(v)}`} />
                    <Legend wrapperStyle={{ fontSize: "11px" }} />
                    {topDiseases.slice(0, 3).map((d, idx) => (
                      <Line key={d.name} type="monotone" dataKey="count" stroke={COLORS[idx]} dot={false} strokeWidth={2} name={d.name} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </>
            )}

            <div className="stats-row">
              <div className="stat"><div className="stat-label">Bài viết trong kỳ</div><div className="stat-value up">{loading ? "..." : totalInRange}</div></div>
              <div className="stat"><div className="stat-label">Chỉ số Rủi ro</div><div className="stat-value" style={{ color: risk.color }}>{risk.text}</div></div>
              <div className="stat"><div className="stat-label">Bệnh duy nhất</div><div className="stat-value warn">{loading ? "..." : uniqueDiseases.length}</div></div>
            </div>
          </div>
        </div>

        <div className="side-column">
          <div className="panel predictor-panel">
            <div className="panel-header"><h3>Top Bệnh ({timeLabel})</h3></div>
            {loading ? <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>Đang tải...</p>
              : predictors.map((p, idx) => (
                <div key={idx} className="predictor-item">
                  <div className="p-info">
                    <span><span className="dot" style={{ backgroundColor: p.color }}></span>{p.name}</span>
                    <span className="p-weight">{p.value}%</span>
                  </div>
                  <div className="p-bar"><div className="fill" style={{ width: `${p.value}%`, backgroundColor: p.color }}></div></div>
                  <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "4px" }}>{p.count} bài viết</div>
                </div>
              ))}
          </div>

          <div className="panel sentiment-panel">
            <div className="panel-header"><h3>Tất cả Bệnh</h3></div>
            <div className="sentiment-tags">
              {loading ? <p style={{ fontSize: "11px" }}>Đang tải...</p>
                : uniqueDiseases.slice(0, 6).map((disease, idx) => {
                  const types = ["blue", "green", "orange", "", "blue", "green"];
                  const count = diseaseFreq[disease] || 0;
                  return <span key={idx} className={`tag ${types[idx]}`}>{disease} ({count})</span>;
                })}
            </div>
            <button className="expand-btn" onClick={() => setShowKeywords(true)}>Xem thêm →</button>
          </div>
        </div>
      </div>

      {/* TABLE */}
      <div className="panel forecast-panel">
        <div className="panel-header">
          <h3>Bảng Bệnh Nổi Bật</h3>
          <span className="forecast-meta">{timeLabel} | {totalInRange} bài viết</span>
        </div>
        <div className="table-responsive">
          <table className="custom-table">
            <thead><tr><th>Bệnh</th><th>Số bài</th><th>Tỷ lệ</th><th>Mức độ</th><th>Kỳ phân tích</th><th>Hành động</th></tr></thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" style={{ textAlign: "center", color: "var(--text-muted)" }}>Đang tải...</td></tr>
              ) : forecastData.length === 0 ? (
                <tr><td colSpan="6" style={{ textAlign: "center", color: "var(--text-muted)" }}>Không có dữ liệu</td></tr>
              ) : forecastData.map((row) => (
                <tr key={row.id}>
                  <td><div className="pathogen-name"><span className="status-indicator" style={{ backgroundColor: row.color }}></span>{row.name}</div></td>
                  <td>{row.count} bài</td>
                  <td><span className="prediction-badge">+{row.percentage}%</span></td>
                  <td><span className={`badge ${row.status === "Escalating" ? "red" : "blue"}`}>{row.status}</span></td>
                  <td style={{ fontSize: "12px" }}>{timeLabel}</td>
                  <td><a href="#" className="action-link" onClick={(e) => e.preventDefault()}>Chi tiết</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* FLOATING AI BUTTON */}
      <button
        className="floating-ai-btn"
        onClick={() => setShowChat(!showChat)}
      >
        <Zap size={18} />
        <span>AI Assistant</span>
      </button>
    </div>
  );
};

export default AnalyticsContent;