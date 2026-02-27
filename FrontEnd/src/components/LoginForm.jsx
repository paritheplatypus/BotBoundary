import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";
import { apiFetch } from "../api/client";

// ── Replace with your EC2 instance's public IP or domain ──────────────────
const API_URL = "http://13.221.254.214:8000";
// ─────────────────────────────────────────────────────────────────────────

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
<<<<<<< Updated upstream
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
=======
  const [status, setStatus]     = useState(null);  // null | "loading" | "success" | "blocked"
  const [result, setResult]     = useState(null);
>>>>>>> Stashed changes

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setResult(null);

<<<<<<< Updated upstream
    setError(null);
    setStatus("Submitting...");

    const behavior = getBehaviorData();

    try {
      const result = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password, behavior }),
      });

      setStatus(
        `Decision: ${result.decision} | Risk: ${result.risk_score.toFixed(2)} | Model: ${result.model_used}`
      );

      // TODO: route to dashboard / challenge page.
      // For now, just show status.
    } catch (err) {
      setError(err.message || "Login failed");
      setStatus(null);
=======
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
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
      <button type="submit">Secure Login</button>

      {status && <p className="login-status">{status}</p>}
      {error && <p className="login-error">{error}</p>}
    </form>
=======
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
>>>>>>> Stashed changes
  );
}
