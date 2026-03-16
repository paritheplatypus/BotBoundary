import { useEffect, useState } from "react";
import LoginForm from "../components/LoginForm";
import BehaviorStats from "../components/BehaviorStats";
import { initBehaviorTracking } from "../behavior/behaviorTracker";
import "../styles/login.css";

export default function Login() {
  const [showStats, setShowStats] = useState(false);

  useEffect(() => {
    initBehaviorTracking();
  }, []);

  const handleLogin = () => {
    setShowStats(true);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="brand-title">CacheMeOutside</h1>

        <p className="subtitle">
          Intelligent Behavioral Authentication
        </p>

        <LoginForm onLogin={handleLogin} />

        <BehaviorStats visible={showStats} />
      </div>
    </div>
  );
}