import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "../styles/sessiondetail.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function fmt(val, decimals = 2) {
  if (val === undefined || val === null) return "—";
  return typeof val === "number" ? val.toFixed(decimals) : val;
}

function hydrateBehaviorFromEvents(events) {
  if (!Array.isArray(events)) return null;

  const behavior = {};
  for (const event of events) {
    if (
      ["mouse", "keyboard", "interaction", "timing", "environment"].includes(
        event?.eventType
      ) &&
      event?.eventData &&
      typeof event.eventData === "object"
    ) {
      behavior[event.eventType] = event.eventData;
    }
  }

  return Object.keys(behavior).length ? behavior : null;
}

export default function SessionDetail() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [behavior, setBehavior] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
          if (typeof data.behaviorPayload === "string") {
            try {
              setBehavior(JSON.parse(data.behaviorPayload));
            } catch {
              setBehavior(null);
            }
          } else if (typeof data.behaviorPayload === "object") {
            setBehavior(data.behaviorPayload);
          }
        } else {
          setBehavior(hydrateBehaviorFromEvents(data.behaviorEvents));
        }

        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [sessionId]);

  if (loading) return <div>Loading session...</div>;

  if (error)
    return (
      <div>
        <div>{error}</div>
        <button
          onClick={() => navigate("/dashboard")}
          style={{
            color: "#38bdf8",
            background: "none",
            border: "none",
            cursor: "pointer",
          }}
        >
          ← Back to dashboard
        </button>
      </div>
    );

  if (!session) return null;

  const risk = parseFloat(session.mlScore) || 0;
  const isBot = session.isBot === true;
  const status = isBot ? "bot" : session.isBot === false ? "human" : "pending";

  const mouse = behavior?.mouse || {};
  const kb = behavior?.keyboard || {};
  const timing = behavior?.timing || {};
  const inter = behavior?.interaction || {};

  function timeAgo(ts) {
    if (!ts) return "—";
    const diff = Date.now() - ts;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins} minutes ago`;
    return `${Math.floor(mins / 60)} hours ago`;
  }

  return (
    <div>
      <button
        onClick={() => navigate("/dashboard")}
        style={{
          color: "#64748b",
          background: "none",
          border: "none",
          cursor: "pointer",
          fontSize: 13,
          marginBottom: 16,
          padding: 0,
        }}
      >
        ← Back to dashboard
      </button>

      <div>{isBot ? "✕" : "✓"}</div>
      <h2>{isBot ? "Bot detected" : "Human verified"}</h2>

      <div>
        Session: {session.sessionId?.slice(0, 8)} · Model: {session.model ?? "mock"} · Threshold: {fmt(session.threshold, 3)} · {timeAgo(session.completedAt)}
      </div>

      <div>{risk.toFixed(4)}</div>
      <div>risk score</div>

      <h3>Mouse Behavior</h3>
      <ul>
        <li>Total moves {fmt(mouse.total_moves, 0)}</li>
        <li>Total distance {fmt(mouse.total_distance, 0)}px</li>
        <li>Mean speed {fmt(mouse.mean_speed)} px/ms</li>
        <li>Direction changes {fmt(mouse.direction_changes, 0)}</li>
        <li>Pause count {fmt(mouse.pause_count, 0)}</li>
        <li>Movement entropy {fmt(mouse.movement_entropy)}</li>
      </ul>

      <h3>Keyboard Behavior</h3>
      <ul>
        <li>Total keystrokes {fmt(kb.total_keystrokes, 0)}</li>
        <li>Mean interval {fmt(kb.mean_interval_ms, 0)}ms</li>
        <li>Interval std dev {fmt(kb.interval_std_ms, 0)}ms</li>
        <li>Min interval {fmt(kb.min_interval_ms, 0)}ms</li>
        <li>Backspace ratio {fmt(kb.backspace_ratio)}</li>
        <li>Paste detected {kb.paste_detected ? "Yes" : "No"}</li>
      </ul>

      <h3>Session Timing</h3>
      <ul>
        <li>Session duration {fmt(timing.session_duration_ms, 0)}ms</li>
        <li>Time to first action {fmt(timing.time_to_first_action_ms, 0)}ms</li>
        <li>Idle time ratio {fmt(timing.idle_time_ratio)}</li>
        <li>Click count {fmt(inter.click_count, 0)}</li>
        <li>Scroll count {fmt(inter.scroll_count, 0)}</li>
        <li>Focus changes {fmt(inter.focus_changes, 0)}</li>
      </ul>

      <h3>Session Info</h3>
      <ul>
        <li>Session ID {session.sessionId}</li>
        <li>User ID {session.userId}</li>
        <li>Status {session.status}</li>
        <li>Risk score {risk.toFixed(4)}</li>
        <li>Verdict {status}</li>
        <li>Created {session.createdAt ? new Date(session.createdAt).toLocaleString() : "—"}</li>
        <li>Completed {session.completedAt ? new Date(session.completedAt).toLocaleString() : "—"}</li>
        <li>Behavior events {Array.isArray(session.behaviorEvents) ? session.behaviorEvents.length : 0}</li>
      </ul>
    </div>
  );
}
