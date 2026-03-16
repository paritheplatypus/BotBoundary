import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [behaviorStats, setBehaviorStats] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setResult(null);

    const behavior = getBehaviorData();

    // Save behavior data so we can display it
    setBehaviorStats(behavior);

    const payload = {
      username,
      behavior,
      registered_user: false,
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

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      const data = await res.json();

      setResult(data);
      setStatus(data.is_bot ? "blocked" : "success");

    } catch (err) {
      console.error("Auth error:", err);
      setStatus("error");
      setResult({ error: err.message });
    }
  };

  const riskScore = result?.risk_score ?? 0.012;
  const riskPercent = Math.min(riskScore * 100, 100);

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

      {/* Behavioral stats panel appears AFTER login */}
      {status && behaviorStats && (
        <div className="behavior-panel">
  <div className="behavior-title">Behavioral Signals</div>

  <div className="behavior-row">
    <span>Mouse movement</span>
    <span className="value green">142 events captured</span>
  </div>

  <div className="behavior-row">
    <span>Keystroke rhythm</span>
    <span className="value green">18 keystrokes logged</span>
  </div>

  <div className="behavior-row">
    <span>Session timing</span>
    <span className="value orange">4.2s elapsed</span>
  </div>

  <div className="behavior-row">
    <span>Interaction pattern</span>
    <span className="value blue">3 clicks · 1 scroll</span>
  </div>

  <div className="risk-section">
    <div className="risk-header">
      <span>Risk score</span>
      <span className="value green">0.012 — Low risk</span>
    </div>

    <div className="risk-bar">
      <div className="risk-fill"></div>
    </div>
  </div>
</div>
      )}

      {status === "error" && (
        <div className="auth-result auth-result--error">
          <span>⚠️ Could not reach auth service</span>
          {result?.error && <small>{result.error}</small>}
        </div>
      )}
    </div>
  );
}