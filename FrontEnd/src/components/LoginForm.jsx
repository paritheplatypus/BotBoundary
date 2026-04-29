import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus]     = useState(null);
  const [result, setResult]     = useState(null);
  const [behavior, setBehavior] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setResult(null);

    const behaviorData = getBehaviorData();
    setBehavior(behaviorData);

    const payload = {
      username,
      behavior: behaviorData,
      registered_user: false,
    };

    try {
      console.log("FULL PAYLOAD:", JSON.stringify(payload, null, 2));
      const res = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("BACKEND ERROR FULL:", err);
        console.error("DETAIL:", err.detail);
        throw new Error(
            typeof err.detail === "string"
              ? err.detail
              : JSON.stringify(err.detail, null, 2)
        );
      }

      const data = await res.json();
      setResult(data);
      setStatus(data.is_bot ? "blocked" : "success");

      // Notify parent so BehaviorStats becomes visible
      if (onLogin) onLogin(behaviorData, data);

    } catch (err) {
      console.error("Auth error:", err);
      setStatus("error");
      setResult({ error: err.message });
    }
  };

  return (
    <div>
      <form className="login-form" onSubmit={handleSubmit}>
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
      </form>

      {status === "error" && (
        <div className="auth-result auth-result--error">
          <span>⚠️ Could not reach auth service</span>
          {result?.error && <small>{result.error}</small>}
        </div>
      )}
    </div>
  );
}
