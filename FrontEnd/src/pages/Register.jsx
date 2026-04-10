import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Register() {
  const [username, setUsername]   = useState("");
  const [password, setPassword]   = useState("");
  const [confirm,  setConfirm]    = useState("");
  const [status,   setStatus]     = useState(null);
  const [message,  setMessage]    = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();

    if (password !== confirm) {
      setStatus("error");
      setMessage("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setStatus("error");
      setMessage("Password must be at least 6 characters");
      return;
    }

    setStatus("loading");

    try {
      const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || "Registration failed");

      setStatus("success");
      setMessage("Account created! Redirecting to login...");
      setTimeout(() => navigate("/"), 1500);

    } catch (err) {
      setStatus("error");
      setMessage(err.message);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="brand-title">CacheMeOutside</h1>
        <p className="subtitle">Create your account</p>
        <p className="register">
          Already have an account? <a href="/">Login</a>
        </p>

        <form className="login-form" onSubmit={handleRegister}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={status === "loading" || status === "success"}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={status === "loading" || status === "success"}
            required
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            disabled={status === "loading" || status === "success"}
            required
          />
          <button type="submit" disabled={status === "loading" || status === "success"}>
            {status === "loading" ? "Creating account..." : "Register"}
          </button>
        </form>

        {status === "success" && (
          <div className="auth-result auth-result--pass">{message}</div>
        )}
        {status === "error" && (
          <div className="auth-result auth-result--error">{message}</div>
        )}
      </div>
    </div>
  );
}
