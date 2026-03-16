export default function BehaviorStats({ visible }) {
  if (!visible) return null;

  return (
    <div className="behavior-panel">
      <h3>Behavioral Signals</h3>

      <div className="signal">
        <span>Mouse movement</span>
        <span className="value">142 events captured</span>
      </div>

      <div className="signal">
        <span>Keystroke rhythm</span>
        <span className="value">18 keystrokes logged</span>
      </div>

      <div className="signal">
        <span>Session timing</span>
        <span className="value">4.2s elapsed</span>
      </div>

      <div className="signal">
        <span>Interaction pattern</span>
        <span className="value">3 clicks · 1 scroll</span>
      </div>

      <div className="risk">
        <div>Risk score</div>
        <div className="risk-bar">
          <div className="risk-fill"></div>
        </div>
        <p className="risk-text">0.012 — Low risk</p>
      </div>

      <div className="verified">
        ✓ Human verified  
        <br />
        Model: autoencoder — No anomalies detected
      </div>
    </div>
  );
}