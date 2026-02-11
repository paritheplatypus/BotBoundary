// src/behavior/behaviorTracker.js

let mouseMoves = [];
let keyTimes = [];
let backspaceCount = 0;

let clickCount = 0;
let scrollCount = 0;
let focusChanges = 0;

let startTime = null;
let firstActionTime = null;
let lastActionTime = null;
let idleTimeMs = 0;

let pauseCount = 0;
let lastMouseTime = null;
const PAUSE_THRESHOLD_MS = 250;

let pasteDetected = false;

export function initBehaviorTracking() {
  resetState();

  startTime = performance.now();
  lastActionTime = startTime;

  document.addEventListener("mousemove", handleMouseMove);
  document.addEventListener("keydown", handleKeyDown, true);
  document.addEventListener("focusin", handleFocus, true);
  document.addEventListener("click", handleClick, true);
  document.addEventListener("scroll", handleScroll, true);
  document.addEventListener("paste", handlePaste, true);
}

function resetState() {
  mouseMoves = [];
  keyTimes = [];
  backspaceCount = 0;

  clickCount = 0;
  scrollCount = 0;
  focusChanges = 0;

  firstActionTime = null;
  lastActionTime = null;
  idleTimeMs = 0;

  pauseCount = 0;
  lastMouseTime = null;

  pasteDetected = false;
}

function recordAction(now) {
  if (!firstActionTime) firstActionTime = now;

  if (lastActionTime != null) {
    const gap = now - lastActionTime;
    if (gap > 300) idleTimeMs += gap;
  }

  lastActionTime = now;
}

function handleMouseMove(e) {
  const now = performance.now();
  recordAction(now);

  if (lastMouseTime && now - lastMouseTime > PAUSE_THRESHOLD_MS) {
    pauseCount++;
  }
  lastMouseTime = now;

  mouseMoves.push({
    x: e.clientX,
    y: e.clientY,
    t: now,
  });
}

function handleKeyDown(e) {
  const now = performance.now();
  recordAction(now);

  keyTimes.push(now);

  if (e.key === "Backspace") backspaceCount++;
}

function handleFocus() {
  const now = performance.now();
  recordAction(now);
  focusChanges++;
}

function handleClick() {
  const now = performance.now();
  recordAction(now);
  clickCount++;
}

function handleScroll() {
  const now = performance.now();
  recordAction(now);
  scrollCount++;
}

function handlePaste() {
  const now = performance.now();
  recordAction(now);
  pasteDetected = true;
}

// ---- Math Helpers ----
function mean(arr) {
  if (!arr.length) return 0;
  return arr.reduce((s, v) => s + v, 0) / arr.length;
}

function std(arr) {
  if (arr.length < 2) return 0;
  const m = mean(arr);
  const variance = arr.reduce((s, v) => s + (v - m) ** 2, 0) / arr.length;
  return Math.sqrt(variance);
}

function entropy(values) {
  if (!values.length) return 0;
  const total = values.reduce((a, b) => a + b, 0);
  if (total === 0) return 0;

  let ent = 0;
  for (let v of values) {
    const p = v / total;
    if (p > 0) ent -= p * Math.log2(p);
  }
  return ent;
}

function computeMouseFeatures(sessionDuration) {
  let totalDistance = 0;
  let speeds = [];
  let directionChanges = 0;

  let prevDx = null;
  let prevDy = null;

  for (let i = 1; i < mouseMoves.length; i++) {
    const a = mouseMoves[i - 1];
    const b = mouseMoves[i];

    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dt = b.t - a.t;

    const dist = Math.sqrt(dx * dx + dy * dy);
    totalDistance += dist;

    if (dt > 0) speeds.push(dist / dt);

    if (prevDx !== null && prevDy !== null) {
      const flipX = dx * prevDx < 0;
      const flipY = dy * prevDy < 0;
      if (flipX || flipY) directionChanges++;
    }

    prevDx = dx;
    prevDy = dy;
  }

  const normalizedDistance =
    window.innerWidth > 0
      ? totalDistance / window.innerWidth
      : totalDistance;

  return {
    total_moves: mouseMoves.length,
    total_distance: totalDistance,
    normalized_distance: normalizedDistance,
    mean_speed: mean(speeds),
    speed_std: std(speeds),
    max_speed: speeds.length ? Math.max(...speeds) : 0,
    direction_changes: directionChanges,
    pause_count: pauseCount,
    movement_entropy: entropy(speeds),
  };
}

function computeKeyboardFeatures() {
  let intervals = [];

  for (let i = 1; i < keyTimes.length; i++) {
    intervals.push(keyTimes[i] - keyTimes[i - 1]);
  }

  return {
    total_keystrokes: keyTimes.length,
    mean_interval_ms: mean(intervals),
    interval_std_ms: std(intervals),
    min_interval_ms: intervals.length ? Math.min(...intervals) : 0,
    max_interval_ms: intervals.length ? Math.max(...intervals) : 0,
    backspace_ratio:
      keyTimes.length > 0 ? backspaceCount / keyTimes.length : 0,
    paste_detected: pasteDetected,
  };
}

export function getBehaviorData() {
  const endTime = performance.now();
  const sessionDuration = startTime
    ? endTime - startTime
    : 0;

  const interactionRate =
    sessionDuration > 0
      ? (clickCount + scrollCount + focusChanges) /
        sessionDuration
      : 0;

  return {
    mouse: computeMouseFeatures(sessionDuration),

    keyboard: computeKeyboardFeatures(),

    interaction: {
      click_count: clickCount,
      scroll_count: scrollCount,
      focus_changes: focusChanges,
      mouse_keyboard_ratio:
        keyTimes.length > 0
          ? mouseMoves.length / keyTimes.length
          : mouseMoves.length,
      interaction_rate: interactionRate,
    },

    timing: {
      session_duration_ms: sessionDuration,
      time_to_first_action_ms:
        firstActionTime && startTime
          ? firstActionTime - startTime
          : 0,
      idle_time_ratio:
        sessionDuration > 0
          ? idleTimeMs / sessionDuration
          : 0,
    },

    environment: {
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
      timezone_offset: new Date().getTimezoneOffset(),
      device_pixel_ratio: window.devicePixelRatio,
    },
  };
}