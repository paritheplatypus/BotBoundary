import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus]     = useState(null);
  const [result, setResult]     = useState(null);
  const [behavior, setBehavior] = useState(null);

  const validateBehavior = (b) => {
    const required = ["mouse", "keyboard", "interaction", "timing", "environment"];
    const missing = required.filter(k => !(k in b));

    if (missing.length > 0) {
      console.error("❌ MISSING BEHAVIOR KEYS:", missing);
      return false;
    }

    console.log("✅ Behavior structure keys OK:", Object.keys(b));
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    console.log("🚀 NEW SUBMISSION TRIGGERED"); // sanity check
    setStatus("loading");
    setResult(null);

    const behaviorData = getBehaviorData();

    console.log("📊 RAW BEHAVIOR DATA:", behaviorData);
    console.log("📊 TYPE:", typeof behaviorData);

    if (!behaviorData || typeof behaviorData !== "object") {
      console.error("❌ behaviorData is invalid");
      setStatus("error");
      return;
    }

    validateBehavior(behaviorData);
    setBehavior(behaviorData);

    const payload = {
      username,
      password,
      behavior: behaviorData,
      registered_user: false,
    };

    console.log("📦 FULL PAYLOAD:", payload);
    console.log("📦 STRINGIFIED:", JSON.stringify(payload, null, 2));

    try {
      console.log(`🌐 Sending request to: ${API_URL}/analyze`);

      const res = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify(payload),
      });

      console.log("📡 RESPONSE STATUS:", res.status);

      let rawText = await res.text();
      console.log("📡 RAW RESPONSE TEXT:", rawText);

      let parsed;
      try {
        parsed = JSON.parse(rawText);
      } catch {
        console.warn("⚠️ Response is not JSON");
      }

      if (!res.ok) {
        console.error("❌ BACKEND ERROR FULL:", parsed);
        console.error("❌ DETAIL:", parsed?.detail);

        throw new Error(
          typeof parsed?.detail === "string"
            ? parsed.detail
            : JSON.stringify(parsed?.detail, null, 2)
        );
      }

      console.log("✅ PARSED RESPONSE:", parsed);

      setResult(parsed);
      setStatus(parsed.is_bot ? "blocked" : "success");

      if (onLogin) onLogin(behaviorData, parsed);

    } catch (err) {
      console.error("🔥 FINAL ERROR:", err);
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