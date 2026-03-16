import "../styles/dashboard.css";

export default function Dashboard() {
  const stats = {
    totalSessions: 1284,
    botsBlocked: 147,
    avgRisk: 0.08,
    falsePositive: "0.3%",
  };

const sessions = [
  { user: "alice", initials: "AL", color: "blue", risk: 0.04, status: "human" },
  { user: "unknown", initials: "??", color: "red", risk: 0.89, status: "bot" },
  { user: "bob", initials: "BO", color: "blue", risk: 0.07, status: "human" },
  { user: "unknown", initials: "??", color: "red", risk: 0.95, status: "bot" },
  { user: "carol", initials: "CA", color: "yellow", risk: 0.31, status: "review" },
];

  return (
    <div className="dashboard-container">

      {/* Stat cards */}
      <div className="stat-grid">

        <div className="stat-card">
          <p>Total sessions</p>
          <h2>{stats.totalSessions}</h2>
          <span className="stat-up">↑ 12% this week</span>
        </div>

        <div className="stat-card">
          <p>Bots blocked</p>
          <h2 className="danger">{stats.botsBlocked}</h2>
          <span className="stat-up">↑ 3 today</span>
        </div>

        <div className="stat-card">
          <p>Avg human risk score</p>
          <h2>{stats.avgRisk}</h2>
          <span className="stat-good">✓ improving</span>
        </div>

        <div className="stat-card">
          <p>False positive rate</p>
          <h2 className="good">{stats.falsePositive}</h2>
          <span className="stat-good">↓ 0.1% this week</span>
        </div>

      </div>

      {/* Bottom panels */}
      <div className="dashboard-panels">

        {/* Recent sessions */}
        <div className="sessions-panel">
          <h3>RECENT SESSIONS</h3>

          {sessions.map((s, i) => (
            <div key={i} className="session-row">

              <div className="session-user">
               <div className={`avatar ${s.color}`}>
                {s.initials}
                </div>

                <div>
                  <p className="username">{s.user}</p>
                  <span className="time">{s.time}</span>
                </div>
              </div>

              <div className="risk">
                <div className="risk-bar">
                  <div
                    className={`risk-fill ${s.status}`}
                    style={{ width: `${s.risk * 100}%` }}
                  />
                </div>
                <span className="risk-score">{s.risk}</span>
              </div>

              <div className={`badge ${s.status}`}>
                {s.status}
              </div>

            </div>
          ))}
        </div>

        {/* Breakdown */}
        <div className="breakdown-panel">
          <h3>SESSION BREAKDOWN</h3>

         <div className="gauge">

  <svg viewBox="0 0 200 110" className="gauge-svg">

    {/* background arc */}
    <path
      d="M20 100 A80 80 0 0 1 180 100"
      stroke="#334155"
      strokeWidth="12"
      fill="none"
    />

    {/* green */}
    <path
      d="M20 100 A80 80 0 0 1 180 100"
      stroke="#22c55e"
      strokeWidth="12"
      strokeDasharray="160 251"
      fill="none"
    />

    {/* orange */}
    <path
      d="M20 100 A80 80 0 0 1 180 100"
      stroke="#f59e0b"
      strokeWidth="12"
      strokeDasharray="40 251"
      strokeDashoffset="-160"
      fill="none"
    />

    {/* red */}
    <path
      d="M20 100 A80 80 0 0 1 180 100"
      stroke="#ef4444"
      strokeWidth="12"
      strokeDasharray="30 251"
      strokeDashoffset="-200"
      fill="none"
    />

  </svg>

  <div className="gauge-center">
    <div className="gauge-number">77%</div>
    <div className="gauge-label">Confirmed human</div>
  </div>

</div>

          <div className="legend">

  <div className="legend-row">
    <div className="legend-left">
      <span className="dot human"></span>
      Human
    </div>
    <div className="legend-right">988 sessions</div>
  </div>

  <div className="legend-row">
    <div className="legend-left">
      <span className="dot bot"></span>
      Bot
    </div>
    <div className="legend-right">147 sessions</div>
  </div>

  <div className="legend-row">
    <div className="legend-left">
      <span className="dot review"></span>
      Under review
    </div>
    <div className="legend-right">149 sessions</div>
  </div>

</div>

        </div>

      </div>
    </div>
  );
}