import "../styles/sessionDetail.css";

export default function SessionDetail() {
  return (
    <div className="session-container">

      {/* Status Banner */}
      <div className="session-banner">
        <div className="banner-left">
          <div className="check">✓</div>
          <div>
            <h2>Human verified</h2>
            <p>
              User: alice · Risk score: 0.012 · Model: autoencoder · Threshold: 0.05
            </p>
          </div>
        </div>

        <div className="banner-score">
          <div className="score-number">0.012</div>
          <div className="score-label">risk score</div>
        </div>
      </div>


      {/* Metrics row */}
      <div className="session-metrics">

        <div className="metric-card">
          <h3>Mouse Behavior</h3>
          <ul>
            <li>Total moves <span>142</span></li>
            <li>Total distance <span>3,840px</span></li>
            <li>Mean speed <span className="green">3.2 px/ms</span></li>
            <li>Direction changes <span>28</span></li>
            <li>Pause count <span>7</span></li>
          </ul>
        </div>

        <div className="metric-card">
          <h3>Keyboard Behavior</h3>
          <ul>
            <li>Total keystrokes <span>18</span></li>
            <li>Mean interval <span className="green">142ms</span></li>
            <li>Interval std dev <span>38ms</span></li>
            <li>Min interval <span>89ms</span></li>
            <li>Backspace ratio <span>0.11</span></li>
          </ul>
        </div>

        <div className="metric-card">
          <h3>Session Timing</h3>
          <ul>
            <li>Session duration <span>4,240ms</span></li>
            <li>Time to first action <span className="green">320ms</span></li>
            <li>Idle time ratio <span>0.12</span></li>
            <li>Click count <span>3</span></li>
            <li>Scroll count <span>1</span></li>
          </ul>
        </div>

      </div>


      {/* Timeline */}
      <div className="timeline-card">
        <h3>Event Timeline</h3>

        <div className="timeline-row">
          <span>0ms</span>
          <span>Page loaded — tracking initialized</span>
        </div>

        <div className="timeline-row">
          <span>320ms</span>
          <span>First mouse movement detected</span>
        </div>

        <div className="timeline-row">
          <span>1100ms</span>
          <span>Username field focused</span>
        </div>

        <div className="timeline-row">
          <span>1340ms</span>
          <span>First keystroke</span>
        </div>

        <div className="timeline-row">
          <span>2800ms</span>
          <span>Password field focused</span>
        </div>

        <div className="timeline-row">
          <span>4240ms</span>
          <span>Login submitted — analysis complete</span>
        </div>

      </div>

    </div>
  );
}