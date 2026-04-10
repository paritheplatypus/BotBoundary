import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setResult(null);

    const behaviorData = getBehaviorData();
    const payload = {
      username: username.trim(),
      password,
      behavior: behaviorData,
      registered_user: true,
    };

    try {
      const res = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || `Server error ${res.status}`);
      }

      setResult(data);
      setStatus(data.is_bot ? "blocked" : "success");
      if (onLogin) onLogin(behaviorData, data);
    } catch (err) {
      console.error("Auth error:", err);
      setStatus("error");
      setResult({ error: err.message });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        disabled={status === "loading"}
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={status === "loading"}
        required
      />
      <button type="submit" disabled={status === "loading"}>
        {status === "loading" ? "Analyzing…" : "Secure Login"}
      </button>

      {status === "error" && (
        <div className="error-message">
          ⚠️ Could not reach auth service
          {result?.error ? <div>{result.error}</div> : null}
        </div>
      )}
    </form>
  );
}
