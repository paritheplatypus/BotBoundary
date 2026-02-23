import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";
import { apiFetch, setAuthToken, clearAuthToken } from "../api/client";

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError(null);
    setStatus("Submitting...");

    const behavior = getBehaviorData();

    try {
      const result = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password, behavior }),
      });

      // In bearer mode, the API returns an access_token only on allow.
      if (result?.access_token) {
        setAuthToken(result.access_token);
      } else {
        clearAuthToken();
      }

      setStatus(
        `Decision: ${result.decision} | Risk: ${result.risk_score.toFixed(2)} | Model: ${result.model_used}`
      );

      // TODO: route to dashboard / challenge page.
      // For now, just show status.
    } catch (err) {
      setError(err.message || "Login failed");
      setStatus(null);
    }
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button type="submit">Secure Login</button>

      {status && <p className="login-status">{status}</p>}
      {error && <p className="login-error">{error}</p>}
    </form>
  );
}