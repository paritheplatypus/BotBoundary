import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";

// ── Replace with your EC2 instance's public IP or domain ──────────────────
const API_URL = "http://13.221.254.214:8000";
// ─────────────────────────────────────────────────────────────────────────

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus]     = useState(null);  // null | "loading" | "success" | "blocked"
  const [result, setResult]     = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setResult(null);

    // Collect behavioral data at the moment of submit
    const behavior = getBehaviorData();

    try {
      const response = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, behavior }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);

      if (data.is_bot) {
        setStatus("blocked");
      } else {
        setStatus("success");
      }

    } catch (err) {
      console.error("Login request failed:", err);
      setStatus("error");
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
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={status === "loading"}
        />

        <button type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Analyzing..." : "Secure Login"}
        </button>
      </form>

      {/* Status messages shown below the form */}
      {status === "success" && (
        <p style={{ color: "green", marginTop: "1rem" }}>
          ✅ Login successful. Welcome, {username}!
          {result && <span> (Risk score: {result.risk_score.toFixed(3)})</span>}
        </p>
      )}

      {status === "blocked" && (
        <p style={{ color: "red", marginTop: "1rem" }}>
          🚫 Suspicious activity detected. Access denied.
          {result && <span> (Risk score: {result.risk_score.toFixed(3)})</span>}
        </p>
      )}

      {status === "error" && (
        <p style={{ color: "orange", marginTop: "1rem" }}>
          ⚠️ Could not reach the server. Please try again.
        </p>
      )}
    </div>
  );
}
