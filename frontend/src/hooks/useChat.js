import { useState } from "react";

export const useChat = (initialAiMessage) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "ai",
      text: initialAiMessage,
      time: new Date().toLocaleTimeString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const sendMessage = () => {
    if (!inputValue.trim()) return;

    // 1. Thêm tin nhắn của User
    const newUserMsg = {
      id: Date.now(),
      sender: "user",
      text: inputValue,
      time: new Date().toLocaleTimeString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
    setMessages((prev) => [...prev, newUserMsg]);
    setInputValue("");
    setIsTyping(true);

    // 2. Giả lập AI suy nghĩ và trả lời sau 1.5 giây
    setTimeout(() => {
      const newAiMsg = {
        id: Date.now() + 1,
        sender: "ai",
        text: "Hệ thống đã ghi nhận yêu cầu. Tôi đang tiến hành truy xuất chéo dữ liệu từ các nguồn báo chí khác để xác minh thông tin này...",
        time: new Date().toLocaleTimeString("vi-VN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setMessages((prev) => [...prev, newAiMsg]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  return {
    messages,
    inputValue,
    setInputValue,
    sendMessage,
    handleKeyPress,
    isTyping,
  };
};
