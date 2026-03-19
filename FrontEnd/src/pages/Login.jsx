import { useEffect, useState } from "react";
import LoginForm from "../components/LoginForm";
import BehaviorStats from "../components/BehaviorStats";
import { initBehaviorTracking } from "../behavior/behaviorTracker";
import "../styles/login.css";

export default function Login() {
  const [showStats, setShowStats]   = useState(false);
  const [behavior, setBehavior]     = useState(null);
  const [result, setResult]         = useState(null);

  useEffect(() => {
    initBehaviorTracking();
  }, []);

  const handleLogin = (behaviorData, apiResult) => {
    setBehavior(behaviorData);
    setResult(apiResult);
    setShowStats(true);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="brand-title">CacheMeOutside</h1>
        <p className="subtitle">Intelligent Behavioral Authentication</p>
        <p className="register">
          Don't have an account? <a href="/register">Register</a>
        </p>

        <LoginForm onLogin={handleLogin} />

        <BehaviorStats
          visible={showStats}
          behavior={behavior}
          result={result}
        />
      </div>
    </div>
  );
}
