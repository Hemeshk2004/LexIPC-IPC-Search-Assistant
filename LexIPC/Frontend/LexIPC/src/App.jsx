import React, { useState } from "react";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);

    try {
      const res = await fetch("http://localhost:5008/process_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),   // Flask expects "query"
      });

      const data = await res.json();

      const botMsg = {
        sender: "bot",
        text: data.answer || data.error || "No response",
      };

      setMessages((msgs) => [...msgs, botMsg]);
    } catch (error) {
      setMessages((msgs) => [
        ...msgs,
        { sender: "bot", text: "Error: Could not reach server." },
      ]);
    }

    setInput("");
  };

  return (
    <div className="chat-container">
      <h2 className="h22">LexIPC Chat</h2>

      <div className="chat-box">
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>

      <div className="controls">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default App;
