import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "../styles/sessiondetail.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function fmt(val, decimals = 2) {
  if (val === undefined || val === null) return "—";
  return typeof val === "number" ? val.toFixed(decimals) : val;
}

export default function SessionDetail() {
  const { sessionId } = useParams();
  const navigate      = useNavigate();
  const [session, setSession] = useState(null);
  const [behavior, setBehavior] = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  useEffect(() => {
    if (!sessionId) return;
    fetch(`${API_URL}/sessions/${sessionId}`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    })
      .then((r) => {
        if (!r.ok) throw new Error("Session not found");
        return r.json();
      })
      .then((data) => {
        setSession(data);
        if (data.behaviorPayload) {
          try {
            setBehavior(JSON.parse(data.behaviorPayload));
          } catch {
            setBehavior(null);
          }
        }
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [sessionId]);

  if (loading) return (
    <div className="session-container">
      <p style={{ color: "#475569", padding: "20px 0" }}>Loading session...</p>
    </div>
  );

  if (error) return (
    <div className="session-container">
      <p style={{ color: "#f87171", padding: "20px 0" }}>{error}</p>
      <button onClick={() => navigate("/dashboard")} style={{ color: "#38bdf8", background: "none", border: "none", cursor: "pointer" }}>
        ← Back to dashboard
      </button>
    </div>
  );

  if (!session) return null;

  const risk    = parseFloat(session.mlScore) || 0;
  const isBot   = session.isBot === true;
  const status  = isBot ? "bot" : session.isBot === false ? "human" : "pending";
  const mouse   = behavior?.mouse       || {};
  const kb      = behavior?.keyboard    || {};
  const timing  = behavior?.timing      || {};
  const inter   = behavior?.interaction || {};

  function timeAgo(ts) {
    if (!ts) return "—";
    const diff = Date.now() - ts;
    const mins = Math.floor(diff / 60000);
    if (mins < 1)  return "just now";
    if (mins < 60) return `${mins} minutes ago`;
    return `${Math.floor(mins / 60)} hours ago`;
  }

  return (
    <div className="session-container">

      <button
        onClick={() => navigate("/dashboard")}
        style={{ color: "#64748b", background: "none", border: "none", cursor: "pointer", fontSize: 13, marginBottom: 16, padding: 0 }}
      >
        ← Back to dashboard
      </button>

      <div className={`session-banner ${isBot ? "session-banner--bot" : ""}`}>
        <div className="banner-left">
          <div className="check" style={{ background: isBot ? "#7f1d1d" : "#16a34a" }}>
            {isBot ? "✕" : "✓"}
          </div>
          <div>
            <h2 style={{ color: isBot ? "#f87171" : "#2dff7a" }}>
              {isBot ? "Bot detected" : "Human verified"}
            </h2>
            <p>
              Session: {session.sessionId?.slice(0, 8)} · Model: {session.model ?? "mock"} ·
              Threshold: {fmt(session.threshold, 3)} · {timeAgo(session.completedAt)}
            </p>
          </div>
        </div>
        <div className="banner-score">
          <div className="score-number" style={{ color: isBot ? "#f87171" : "#2dff7a" }}>
            {risk.toFixed(4)}
          </div>
          <div className="score-label">risk score</div>
        </div>
      </div>

      <div className="session-metrics">

        <div className="metric-card">
          <h3>Mouse Behavior</h3>
          <ul>
            <li>Total moves       <span>{fmt(mouse.total_moves, 0)}</span></li>
            <li>Total distance    <span>{fmt(mouse.total_distance, 0)}px</span></li>
            <li>Mean speed        <span className="green">{fmt(mouse.mean_speed)} px/ms</span></li>
            <li>Direction changes <span>{fmt(mouse.direction_changes, 0)}</span></li>
            <li>Pause count       <span>{fmt(mouse.pause_count, 0)}</span></li>
            <li>Movement entropy  <span>{fmt(mouse.movement_entropy)}</span></li>
          </ul>
        </div>

        <div className="metric-card">
          <h3>Keyboard Behavior</h3>
          <ul>
            <li>Total keystrokes  <span>{fmt(kb.total_keystrokes, 0)}</span></li>
            <li>Mean interval     <span className="green">{fmt(kb.mean_interval_ms, 0)}ms</span></li>
            <li>Interval std dev  <span>{fmt(kb.interval_std_ms, 0)}ms</span></li>
            <li>Min interval      <span>{fmt(kb.min_interval_ms, 0)}ms</span></li>
            <li>Backspace ratio   <span>{fmt(kb.backspace_ratio)}</span></li>
            <li>Paste detected    <span className={kb.paste_detected ? "orange" : "green"}>{kb.paste_detected ? "Yes" : "No"}</span></li>
          </ul>
        </div>

        <div className="metric-card">
          <h3>Session Timing</h3>
          <ul>
            <li>Session duration      <span>{fmt(timing.session_duration_ms, 0)}ms</span></li>
            <li>Time to first action  <span className="green">{fmt(timing.time_to_first_action_ms, 0)}ms</span></li>
            <li>Idle time ratio       <span>{fmt(timing.idle_time_ratio)}</span></li>
            <li>Click count           <span>{fmt(inter.click_count, 0)}</span></li>
            <li>Scroll count          <span>{fmt(inter.scroll_count, 0)}</span></li>
            <li>Focus changes         <span>{fmt(inter.focus_changes, 0)}</span></li>
          </ul>
        </div>

      </div>

      <div className="timeline-card">
        <h3>Session Info</h3>
        <div className="timeline-row"><span>Session ID</span><span>{session.sessionId}</span></div>
        <div className="timeline-row"><span>User ID</span><span>{session.userId}</span></div>
        <div className="timeline-row"><span>Status</span><span>{session.status}</span></div>
        <div className="timeline-row"><span>Risk score</span><span style={{ color: isBot ? "#f87171" : "#22c55e" }}>{risk.toFixed(4)}</span></div>
        <div className="timeline-row"><span>Verdict</span><span style={{ color: isBot ? "#f87171" : "#22c55e" }}>{status}</span></div>
        <div className="timeline-row"><span>Created</span><span>{session.createdAt ? new Date(session.createdAt).toLocaleString() : "—"}</span></div>
        <div className="timeline-row"><span>Completed</span><span>{session.completedAt ? new Date(session.completedAt).toLocaleString() : "—"}</span></div>
      </div>

    </div>
  );
}
