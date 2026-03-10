import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState(null); // null | "loading" | "success" | "blocked" | "error"
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setResult(null);

    const behavior = getBehaviorData();

    const payload = {
      username,
      behavior,
      registered_user: false, // set to true once user has a trained OCSVM profile
    };

    try {
	const res = await fetch(`${API_URL}/analyze`, {
  	method: "POST",
  	headers: { 
    	"Content-Type": "application/json",
    	"ngrok-skip-browser-warning": "true"
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

      {/* Result feedback */}
      {status === "success" && result && (
        <div className="auth-result auth-result--pass">
          <span>✅ Human verified</span>
          <small>Risk score: {result.risk_score?.toFixed(4)} · Model: {result.model}</small>
        </div>
      )}

      {status === "blocked" && result && (
        <div className="auth-result auth-result--fail">
          <span>🚫 Suspicious activity detected</span>
          <small>Risk score: {result.risk_score?.toFixed(4)} · Model: {result.model}</small>
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
