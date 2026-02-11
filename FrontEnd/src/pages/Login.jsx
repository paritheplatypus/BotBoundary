import { useEffect } from "react";
import LoginForm from "../components/LoginForm";
import { initBehaviorTracking } from "../behavior/behaviorTracker";
import "../styles/login.css";

export default function Login() {
  useEffect(() => {
    initBehaviorTracking();
  }, []);

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="brand-title">CacheMeOutside</h1>
        <p className="subtitle">
          Intelligent Behavioral Authentication
        </p>

        <LoginForm />
      </div>
    </div>
  );
}