import { useState } from "react";
import { getBehaviorData } from "../behavior/behaviorTracker";

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const behavior = getBehaviorData();

    console.log("LOGIN PAYLOAD:", {
      username,
      password,
      behavior,
    });
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
    </form>
  );
}