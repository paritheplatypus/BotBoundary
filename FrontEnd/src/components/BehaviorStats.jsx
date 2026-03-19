export default function BehaviorStats({ visible, behavior, result }) {
  if (!visible || !behavior) return null;

  const mouse    = behavior.mouse    || {};
  const keyboard = behavior.keyboard || {};
  const timing   = behavior.timing   || {};
  const interaction = behavior.interaction || {};

  const riskScore   = result?.risk_score ?? 0;
  const isBot       = result?.is_bot ?? false;
  const model       = result?.model ?? "unknown";
  const riskPercent = Math.min(riskScore * 100, 100).toFixed(1);

  const riskColor = isBot
    ? "#ef4444"
    : riskScore > 0.3
    ? "#f59e0b"
    : "#22c55e";

  const riskLabel = isBot
    ? "High risk"
    : riskScore > 0.3
    ? "Medium risk"
    : "Low risk";

  return (
    <div className="behavior-panel">
      <div className="behavior-title">Behavioral Signals</div>

      <div className="behavior-row">
        <span>Mouse movement</span>
        <span className="value green">
          {mouse.total_moves ?? 0} events captured
        </span>
      </div>

      <div className="behavior-row">
        <span>Keystroke rhythm</span>
        <span className="value green">
          {keyboard.total_keystrokes ?? 0} keystrokes logged
        </span>
      </div>

      <div className="behavior-row">
        <span>Session timing</span>
        <span className="value orange">
          {((timing.session_duration_ms ?? 0) / 1000).toFixed(1)}s elapsed
        </span>
      </div>

      <div className="behavior-row">
        <span>Interaction pattern</span>
        <span className="value blue">
          {interaction.click_count ?? 0} clicks · {interaction.scroll_count ?? 0} scrolls
        </span>
      </div>

      <div className="behavior-row">
        <span>Paste detected</span>
        <span className={`value ${keyboard.paste_detected ? "orange" : "green"}`}>
          {keyboard.paste_detected ? "Yes" : "No"}
        </span>
      </div>

      <div className="risk-section">
        <div className="risk-header">
          <span>Risk score</span>
          <span className="value" style={{ color: riskColor }}>
            {riskScore.toFixed(4)} — {riskLabel}
          </span>
        </div>
        <div className="risk-bar">
          <div
            className="risk-fill"
            style={{
              width: `${riskPercent}%`,
              background: `linear-gradient(90deg, #22c55e, ${riskColor})`,
            }}
          />
        </div>
      </div>

      {result && (
        <div
          className="auth-result"
          style={{
            marginTop: "12px",
            background: isBot
              ? "rgba(239,68,68,0.12)"
              : "rgba(34,197,94,0.12)",
            border: `1px solid ${isBot ? "rgba(239,68,68,0.3)" : "rgba(34,197,94,0.3)"}`,
            color: isBot ? "#f87171" : "#4ade80",
            borderRadius: "10px",
            padding: "12px 14px",
            fontSize: "13px",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 3 }}>
            {isBot ? "🚫 Suspicious activity detected" : "✓ Human verified"}
          </div>
          <div style={{ fontSize: 11, opacity: 0.75 }}>
            Model: {model} · Session: {result.session_id?.slice(0, 8) ?? "—"}
          </div>
        </div>
      )}
    </div>
  );
}
