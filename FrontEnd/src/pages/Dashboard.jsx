import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/dashboard.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function timeAgo(ts) {
  if (!ts) return "—";
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function initials(userId) {
  return userId ? userId.slice(0, 2).toUpperCase() : "??";
}

export default function Dashboard() {
  const [sessions, setSessions]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API_URL}/sessions?limit=20`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    })
      .then((r) => r.json())
      .then((data) => {
        setSessions(data.sessions || []);
        setLoading(false);
      })
      .catch((e) => {
        setError("Could not load sessions");
        setLoading(false);
      });
  }, []);

  const completed  = sessions.filter((s) => s.status === "completed");
  const bots       = completed.filter((s) => s.isBot === true);
  const humans     = completed.filter((s) => s.isBot === false);
  const avgRisk    = completed.length
    ? (completed.reduce((sum, s) => sum + (parseFloat(s.mlScore) || 0), 0) / completed.length).toFixed(3)
    : "—";
  const humanPct   = completed.length
    ? Math.round((humans.length / completed.length) * 100)
    : 0;

  const arcTotal   = 251;
  const greenLen   = Math.round((humans.length / (completed.length || 1)) * arcTotal);
  const redLen     = Math.round((bots.length  / (completed.length || 1)) * arcTotal);

  return (
    <div className="dashboard-container">

      <div className="stat-grid">
        <div className="stat-card">
          <p>Total sessions</p>
          <h2>{completed.length}</h2>
          <span className="stat-good">All time</span>
        </div>
        <div className="stat-card">
          <p>Bots blocked</p>
          <h2 className="danger">{bots.length}</h2>
          <span className="stat-up">
            {completed.length ? ((bots.length / completed.length) * 100).toFixed(1) : 0}% of traffic
          </span>
        </div>
        <div className="stat-card">
          <p>Avg risk score</p>
          <h2>{avgRisk}</h2>
          <span className="stat-good">Completed sessions</span>
        </div>
        <div className="stat-card">
          <p>Human sessions</p>
          <h2 className="good">{humanPct}%</h2>
          <span className="stat-good">{humans.length} confirmed</span>
        </div>
      </div>

      <div className="dashboard-panels">

        <div className="sessions-panel">
          <h3>RECENT SESSIONS</h3>

          {loading && <p style={{ color: "#475569", fontSize: 13, padding: "12px 0" }}>Loading...</p>}
          {error   && <p style={{ color: "#f87171", fontSize: 13, padding: "12px 0" }}>{error}</p>}

          {!loading && sessions.length === 0 && (
            <p style={{ color: "#475569", fontSize: 13, padding: "12px 0" }}>No sessions yet.</p>
          )}

          {sessions.map((s) => {
            const risk   = parseFloat(s.mlScore) || 0;
            const status = s.isBot === true ? "bot" : s.isBot === false ? "human" : "review";
            return (
              <div
                key={s.sessionId}
                className="session-row"
                style={{ cursor: "pointer" }}
                onClick={() => navigate(`/session/${s.sessionId}`)}
              >
                <div className="session-user">
                  <div className={`avatar ${status === "bot" ? "red" : status === "review" ? "yellow" : "blue"}`}>
                    {initials(s.userId)}
                  </div>
                  <div>
                    <p className="username">{s.userId?.slice(0, 8) ?? "unknown"}</p>
                    <span className="time">{timeAgo(s.completedAt || s.createdAt)}</span>
                  </div>
                </div>

                <div className="risk">
                  <div className="risk-bar">
                    <div
                      className={`risk-fill ${status}`}
                      style={{ width: `${Math.min(risk * 100, 100)}%` }}
                    />
                  </div>
                  <span className="risk-score">{risk.toFixed(3)}</span>
                </div>

                <div className={`badge ${status}`}>{status}</div>
              </div>
            );
          })}
        </div>

        <div className="breakdown-panel">
          <h3>SESSION BREAKDOWN</h3>

          <div className="gauge">
            <svg viewBox="0 0 200 110" className="gauge-svg">
              <path d="M20 100 A80 80 0 0 1 180 100" stroke="#334155" strokeWidth="12" fill="none" />
              <path
                d="M20 100 A80 80 0 0 1 180 100"
                stroke="#22c55e"
                strokeWidth="12"
                strokeDasharray={`${greenLen} ${arcTotal}`}
                fill="none"
              />
              <path
                d="M20 100 A80 80 0 0 1 180 100"
                stroke="#ef4444"
                strokeWidth="12"
                strokeDasharray={`${redLen} ${arcTotal}`}
                strokeDashoffset={-greenLen}
                fill="none"
              />
            </svg>
            <div className="gauge-center">
              <div className="gauge-number">{humanPct}%</div>
              <div className="gauge-label">Confirmed human</div>
            </div>
          </div>

          <div className="legend">
            <div className="legend-row">
              <div className="legend-left"><span className="dot human"></span>Human</div>
              <div className="legend-right">{humans.length} sessions</div>
            </div>
            <div className="legend-row">
              <div className="legend-left"><span className="dot bot"></span>Bot</div>
              <div className="legend-right">{bots.length} sessions</div>
            </div>
            <div className="legend-row">
              <div className="legend-left"><span className="dot review"></span>Pending</div>
              <div className="legend-right">{sessions.length - completed.length} sessions</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
