import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    setStatus("loading");

    try {
      const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      setStatus("success");
      setMessage("Account created successfully!");
      setUsername("");
      setPassword("");

    } catch (err) {
      console.error(err);
      setStatus("error");
      setMessage(err.message);
    }
  };

  return (
    <div className="auth-container">
      <h2>Create Account</h2>

      <form className="login-form" onSubmit={handleRegister}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Creating..." : "Register"}
        </button>
      </form>

      {status === "success" && (
        <div className="auth-result success">{message}</div>
      )}

      {status === "error" && (
        <div className="auth-result error">{message}</div>
      )}
    </div>
  );
}