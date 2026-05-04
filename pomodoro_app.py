#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pomodoro Timer - Flask + Frontend + PWA
- Repeticiones, descanso largo configurable, notificaciones, tema claro/oscuro
- Wake Lock (mantener pantalla activa) con toggle
- PWA: manifest + service worker + iconos
- Sonido de alarma: Beep configurable (duración) o archivo subido (mp3/wav)

Docker:
  docker build -t pomodoro:latest .
  docker run --rm -p 8081:8080 --name pomodoro pomodoro:latest
"""
from flask import Flask, Response
import base64, os, argparse

app = Flask(__name__)

INDEX_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pomodoro Timer</title>
  <meta name="theme-color" content="#0f172a">
  <link rel="manifest" href="/manifest.webmanifest">
  <link rel="icon" sizes="192x192" href="/icon-192.png">
  <link rel="icon" sizes="512x512" href="/icon-512.png">
  <style>
    :root {
      --bg: #0f172a;
      --panel: #111827;
      --accent: #22d3ee;
      --accent-2: #2563eb;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --danger: #ef4444;
      --ok: #10b981;
      --warn: #f59e0b;
    }
    body.light {
      --bg: #f4f7fb;
      --panel: #ffffff;
      --accent: #0891b2;
      --accent-2: #2563eb;
      --text: #0f172a;
      --muted: #64748b;
      --danger: #dc2626;
      --ok: #059669;
      --warn: #d97706;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", "Noto Sans", sans-serif;
      background: radial-gradient(1200px 800px at 20% 10%, #0b1220, var(--bg));
      color: var(--text);
      min-height: 100vh;
      display: grid;
      place-items: center;
      transition: background-color .2s ease;
    }
    body.light { background: var(--bg); }
    .card {
      width: min(860px, 96vw);
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.35);
      backdrop-filter: blur(4px);
    }
    body.light .card {
      background: var(--panel);
      border: 1px solid rgba(15,23,42,0.08);
      box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    }
    h1 { margin: 0 0 8px 0; letter-spacing: 0.4px; font-weight: 700; font-size: 28px; }
    p.sub { margin: 0 0 18px 0; color: var(--muted); font-size: 14px; }
    .display { font-variant-numeric: tabular-nums; font-size: clamp(44px, 8vw, 72px); text-align: center; margin: 12px 0 6px 0; letter-spacing: 1px; }
    .phase { text-align: center; font-size: 14px; color: var(--muted); margin-bottom: 16px; min-height: 20px; }
    .row { display: grid; gap: 10px; }
    @media(min-width: 860px) {
      .row-2 { grid-template-columns: 1fr 1fr; }
      .row-3 { grid-template-columns: 1fr 1fr 1fr; }
      .row-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
      .row-5 { grid-template-columns: repeat(5, 1fr); }
    }
    .btn {
      appearance: none;
      border: 1px solid rgba(255,255,255,0.12);
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
      color: var(--text);
      padding: 12px 14px;
      border-radius: 12px;
      cursor: pointer;
      font-weight: 600;
      font-size: 15px;
      transition: transform .06s ease, border-color .2s ease;
      width: 100%;
    }
    body.light .btn { background: #f8fafc; border-color: rgba(15,23,42,0.12); }
    .btn:hover { transform: translateY(-1px); border-color: rgba(255,255,255,0.25); }
    body.light .btn:hover { border-color: rgba(15,23,42,0.25); }
    .btn:active { transform: translateY(0); }
    .btn.primary { border-color: rgba(34, 211, 238, .55); }
    .btn.danger  { border-color: rgba(239, 68, 68, .55); }
    .btn.ok      { border-color: rgba(16, 185, 129, .55); }
    .btn.warn    { border-color: rgba(245, 158, 11, .55); }
    .input {
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 12px;
      color: var(--text);
      padding: 10px 12px;
      width: 100%;
      font-size: 14px;
    }
    body.light .input { background: #ffffff; border-color: rgba(15,23,42,0.12); }
    .muted { color: var(--muted); }
    .hint { font-size: 12px; color: var(--muted); text-align: center; margin-top: 10px; }
    .footer { margin-top: 14px; text-align:center; color: var(--muted); font-size: 12px; }
    .pill { display:inline-flex; align-items:center; gap:8px; padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); font-size: 12px; }
    body.light .pill { background: #f1f5f9; border: 1px solid rgba(15,23,42,0.08); }
    .dot { width:8px; height:8px; border-radius:50%; background: var(--accent); display:inline-block; }
    .small { font-size: 12px; }
    .switch { display:flex; gap:10px; align-items:center; justify-content:flex-end; }
    .switch input { transform: scale(1.2); }
    .file { font-size: 12px; color: var(--muted); }
    /* Bigger alarm input for better visibility */
    #alarmSec{
      max-width: 240px;   /* was ~110px */
      min-width: 160px;
      font-size: 20px;
      padding: 12px 14px;
      height: 48px;
      text-align: center;
      font-variant-numeric: tabular-nums; /* keeps digits aligned */
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="switch" style="margin-bottom:6px;">
      <label class="muted small" for="themeToggle">Tema claro</label>
      <input id="themeToggle" type="checkbox" />
    </div>

    <h1>Pomodoro Timer (PWA)</h1>
    <p class="sub">Pomodoro con repeticiones, descanso largo configurable, notificaciones, tema claro/oscuro, Wake Lock y sonido personalizado.</p>

    <div class="display" id="time">00:00</div>
    <div class="phase" id="phase"><span class="pill"><span class="dot"></span> Listo</span></div>

    <div class="row row-5" style="margin-bottom:10px;">
      <button class="btn primary" id="btnPomodoro" title="25 min trabajo → descanso">Pomodoro</button>
      <button class="btn ok" id="btnPause">Pausar</button>
      <button class="btn danger" id="btnReset">Reiniciar</button>
      <button class="btn warn" id="btnShort" title="Descanso 5:00 (no usa repeticiones)">Descanso 5:00</button>
      <button class="btn" id="btnLong" title="Descanso 15:00 (no usa repeticiones)">Descanso 15:00</button>
    </div>

    <div class="row row-5" style="margin-bottom:10px; align-items:end;">
      <div>
        <label for="longEvery" class="muted small">Descanso largo cada N ciclos</label>
        <input class="input" id="longEvery" type="number" min="1" max="99" step="1" value="4" inputmode="numeric" />
      </div>
      <div>
        <label for="longMin" class="muted small">Duración descanso largo (min)</label>
        <input class="input" id="longMin" type="number" min="1" max="120" step="1" value="15" inputmode="numeric" />
      </div>
      <div>
        <label for="reps" class="muted small">Repeticiones (≥1)</label>
        <input class="input" id="reps" type="number" min="1" max="999" step="1" value="1" inputmode="numeric" pattern="\\d+" />
      </div>
      <div style="display:flex; gap:8px; flex-direction:column;">
        <label class="muted small">Sonido</label>
        <div style="display:flex; gap:8px; align-items:center;">
          <button class="btn" id="btnSoundBeep">Beep</button>
          <input id="soundFile" type="file" accept="audio/*" style="max-width:220px;" />
          <input class="input" id="alarmSec" type="number" min="1" max="60" step="1"
                 value="7" title="Duración de la alarma (segundos)";" />
        </div>
        <span id="soundName" class="file">Actual: Beep (~7s)</span>
      </div>
      <div style="display:flex; gap:10px; align-items:center; justify-content:flex-end;">
        <label for="wakeToggle" class="muted small">Mantener pantalla activa</label>
        <input id="wakeToggle" type="checkbox" />
      </div>
    </div>

    <div class="row row-4" style="align-items:end;">
      <div>
        <label for="min" class="muted">Minutos</label>
        <input class="input" id="min" type="number" min="0" max="999" step="1" value="10" inputmode="numeric" />
      </div>
      <div>
        <label for="sec" class="muted">Segundos</label>
        <input class="input" id="sec" type="number" min="0" max="59" step="1" value="0" inputmode="numeric" />
      </div>
      <div>
        <label class="muted">&nbsp;</label>
        <button class="btn ok" id="btnStartCustom">Iniciar Personalizado</button>
      </div>
      <div></div>
    </div>

    <div class="hint">Instálala (PWA) desde el navegador. Notificaciones nativas (HTTPS/localhost). Alarma Beep configurable o tu archivo (cortado a la duración). Wake Lock evita que la pantalla se apague durante los bloques.</div>
    <div class="footer">Flask + JS · PWA · Sin assets externos</div>
  </div>

<script>
(() => {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(console.error);
    });
  }

  // Theme
  const themeToggle = document.getElementById('themeToggle');
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (savedTheme) {
    document.body.classList.toggle('light', savedTheme === 'light');
    themeToggle.checked = savedTheme === 'light';
  } else {
    const useLight = !prefersDark;
    document.body.classList.toggle('light', useLight);
    themeToggle.checked = useLight;
  }
  themeToggle.addEventListener('change', () => {
    document.body.classList.toggle('light', themeToggle.checked);
    localStorage.setItem('theme', themeToggle.checked ? 'light' : 'dark');
  });

  // Wake Lock
  const wakeToggle = document.getElementById('wakeToggle');
  let wakeLock = null;
  async function requestWakeLock() {
    try {
      if ('wakeLock' in navigator && wakeToggle.checked) {
        wakeLock = await navigator.wakeLock.request('screen');
        wakeLock.addEventListener('release', () => { wakeLock = null; });
      }
    } catch(e) {}
  }
  async function releaseWakeLock() { try { if (wakeLock) await wakeLock.release(); } catch(e) {} wakeLock=null; }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && wakeToggle.checked) requestWakeLock();
  });

  // Audio + custom
  let audioCtx = null;
  function ensureAudioCtx() {
    if (!audioCtx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) audioCtx = new AC();
    }
    if (audioCtx && audioCtx.state === 'suspended') { audioCtx.resume(); }
  }
  function playBeep(startTime, duration, freq) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.001, startTime);
    gain.gain.exponentialRampToValueAtTime(0.25, startTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(startTime);
    osc.stop(startTime + duration + 0.05);
  }
  function playBeepAlarm(durationSec) {
    ensureAudioCtx();
    if (!audioCtx) return;
    const now = audioCtx.currentTime;
    const total = Math.max(1, durationSec | 0);
    let t = 0.0, high = true;
    while (t < total) {
      const freq = high ? 880 : 660;
      playBeep(now + t, 0.22, freq);
      t += 0.35; high = !high;
    }
  }

  const soundFile = document.getElementById('soundFile');
  const btnSoundBeep = document.getElementById('btnSoundBeep');
  const soundName = document.getElementById('soundName');
  const alarmSecInput = document.getElementById('alarmSec');

  let customAudio = null, useCustom = false, customUrl = null;
  let alarmLenSec = parseInt(localStorage.getItem('alarmLenSec') || '7', 10);
  if (!Number.isFinite(alarmLenSec) || alarmLenSec < 1) alarmLenSec = 7;
  alarmSecInput.value = alarmLenSec;

  alarmSecInput.addEventListener('input', () => {
    const v = Math.max(1, Math.min(60, parseInt(alarmSecInput.value || '7', 10)));
    alarmLenSec = v;
    alarmSecInput.value = v;
    localStorage.setItem('alarmLenSec', String(v));
    if (!useCustom) soundName.textContent = `Actual: Beep (~${v}s)`;
  });

  btnSoundBeep.addEventListener('click', () => {
    useCustom = false;
    soundName.textContent = `Actual: Beep (~${alarmLenSec}s)`;
    if (customAudio) { try { customAudio.pause(); } catch(e) {} }
  });
  soundFile.addEventListener('change', () => {
    const f = soundFile.files && soundFile.files[0];
    if (!f) return;
    if (customUrl) URL.revokeObjectURL(customUrl);
    customUrl = URL.createObjectURL(f);
    customAudio = new Audio(customUrl);
    customAudio.preload = 'auto';
    customAudio.crossOrigin = 'anonymous';
    soundName.textContent = 'Actual: ' + (f.name || 'Archivo personalizado');
    useCustom = true;
  });
  function playAlarm() {
    if (useCustom && customAudio) {
      try {
        customAudio.currentTime = 0;
        const p = customAudio.play();
        setTimeout(() => { try { customAudio.pause(); } catch(e) {} }, alarmLenSec * 1000);
        if (p && p.catch) p.catch(() => { playBeepAlarm(alarmLenSec); });
      } catch(e) { playBeepAlarm(alarmLenSec); }
    } else {
      playBeepAlarm(alarmLenSec);
    }
  }

  // Notifications
  let notifyEnabled = false;
  let titleBlinkTimer = null;
  const originalTitle = document.title;
  function tryEnableNotifications() {
    if (notifyEnabled) return;
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') {
      Notification.requestPermission().then(p => { notifyEnabled = (p === 'granted'); });
    } else {
      notifyEnabled = (Notification.permission === 'granted');
    }
  }
  function blinkTitle(msg, durationMs=8000) {
    clearInterval(titleBlinkTimer);
    let shown = false;
    document.title = msg;
    titleBlinkTimer = setInterval(() => { document.title = shown ? msg : originalTitle; shown = !shown; }, 800);
    setTimeout(() => { clearInterval(titleBlinkTimer); document.title = originalTitle; }, durationMs);
  }
  function notify(title, body) {
    if (navigator.serviceWorker && navigator.serviceWorker.controller && Notification.permission === 'granted') {
      navigator.serviceWorker.controller.postMessage({type:'notify', title, body});
    } else if ('Notification' in window && Notification.permission === 'granted') {
      try { new Notification(title, { body }); } catch(e) { blinkTitle(`${title} — ${body}`); }
    } else {
      blinkTitle(`${title} — ${body}`);
    }
  }
  window.addEventListener('click', tryEnableNotifications, { once: true });

  // Timer state
  const $time = document.getElementById('time');
  const $phase = document.getElementById('phase');
  const $btnPomodoro = document.getElementById('btnPomodoro');
  const $btnPause = document.getElementById('btnPause');
  const $btnReset = document.getElementById('btnReset');
  const $btnShort = document.getElementById('btnShort');
  const $btnLong = document.getElementById('btnLong');
  const $btnStartCustom = document.getElementById('btnStartCustom');
  const $min = document.getElementById('min');
  const $sec = document.getElementById('sec');
  const $reps = document.getElementById('reps');
  const $longEvery = document.getElementById('longEvery');
  const $longMin = document.getElementById('longMin');

  const savedEvery = localStorage.getItem('longEvery');
  const savedLongMin = localStorage.getItem('longMin');
  if (savedEvery) $longEvery.value = savedEvery;
  if (savedLongMin) $longMin.value = savedLongMin;
  $longEvery.addEventListener('change', () => localStorage.setItem('longEvery', String(Math.max(1, parseInt($longEvery.value||'4', 10)))));
  $longMin.addEventListener('change', () => localStorage.setItem('longMin', String(Math.max(1, parseInt($longMin.value||'15', 10)))));

  let intervalId = null, endAt = 0, remainingMs = 0, paused = false;
  let currentPhase = 'idle';
  let repsLeft = 0, customSeconds = 0, cyclesCompleted = 0, cyclesTotal = 0;

  function fmt(ms) {
    const total = Math.max(0, Math.round(ms / 1000));
    const m = Math.floor(total / 60);
    const s = total % 60;
    return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
  }
  function setPhase(label, colorVar, extra='') {
    const suffix = extra ? ` ${extra}` : '';
    $phase.innerHTML = `<span class="pill"><span class="dot" style="background:${colorVar};"></span> ${label}${suffix}</span>`;
  }
  function sanitInt(v, fallback, min=1) {
    const n = parseInt(String(v).replace(/[^0-9]/g, ''), 10);
    if (!Number.isFinite(n)) return fallback;
    return Math.max(min, n);
  }
  $reps.addEventListener('input', () => {
    const clean = String($reps.value).replace(/[^0-9]/g, '');
    $reps.value = clean === '' ? '1' : String(Math.max(1, parseInt(clean, 10)));
  });

  function tick() {
    const now = Date.now();
    const left = endAt - now;
    if (left <= 0) {
      clearInterval(intervalId);
      intervalId = null;
      $time.textContent = '00:00';
      playAlarm();
      onTimerEnd();
      return;
    }
    $time.textContent = fmt(left);
  }

  let onTimerEnd = () => {};

  function startTimer(seconds, phaseLabel, phaseColor, onEndCb) {
    clearInterval(intervalId);
    paused = false;
    remainingMs = seconds * 1000;
    endAt = Date.now() + remainingMs;
    intervalId = setInterval(tick, 250);
    setPhase(phaseLabel, phaseColor, phaseLabel === 'Trabajo' && cyclesTotal ? `(${cyclesCompleted+1}/${cyclesTotal})` : '');
    $time.textContent = fmt(remainingMs);
    onTimerEnd = onEndCb || (() => {});
    if (phaseLabel !== 'Pausado' && wakeToggle.checked) requestWakeLock();
  }

  function finishAll() {
    setPhase('Listo', 'var(--accent)');
    currentPhase = 'idle'; repsLeft = 0;
    notify('Completado', 'Secuencia finalizada');
    releaseWakeLock();
  }

  function stopTimer(resetPhase=true) {
    clearInterval(intervalId);
    intervalId = null; paused = false;
    endAt = 0; remainingMs = 0;
    $time.textContent = '00:00';
    if (resetPhase) {
      cyclesCompleted = 0; cyclesTotal = 0;
      setPhase('Listo', 'var(--accent)');
      currentPhase = 'idle';
      releaseWakeLock();
    }
  }

  function pauseResume() {
    if (intervalId && !paused) {
      paused = true; remainingMs = Math.max(0, endAt - Date.now());
      clearInterval(intervalId); intervalId = null;
      setPhase('Pausado', 'var(--warn)'); $btnPause.textContent = 'Reanudar';
      releaseWakeLock();
    } else if (!intervalId && paused) {
      paused = false; endAt = Date.now() + remainingMs;
      intervalId = setInterval(tick, 250);
      const label = (currentPhase === 'work') ? 'Trabajo' :
                    (currentPhase === 'break') ? 'Descanso' :
                    (currentPhase === 'custom') ? 'Personalizado' : 'Listo';
      const color = (currentPhase === 'work') ? 'var(--accent)' :
                    (currentPhase === 'break') ? 'var(--accent-2)' :
                    (currentPhase === 'custom') ? 'var(--ok)' : 'var(--accent)';
      setPhase(label, color, label === 'Trabajo' && cyclesTotal ? `(${cyclesCompleted+1}/${cyclesTotal})` : '');
      $btnPause.textContent = 'Pausar';
      if (wakeToggle.checked) requestWakeLock();
    }
  }

  function startPomodoroCycles(cycles) {
    cyclesTotal = cycles; cyclesCompleted = 0; repsLeft = cycles;
    notify('Inicio', `Pomodoro x${cycles}`); startWork();
  }
  function startWork() {
    currentPhase = 'work'; $btnPause.textContent = 'Pausar';
    startTimer(25 * 60, 'Trabajo', 'var(--accent)', () => {
      const longEvery = sanitInt($longEvery.value, 4);
      const longMin = sanitInt($longMin.value, 15);
      const upcomingIndex = cyclesCompleted + 1;
      const isLong = (upcomingIndex % longEvery === 0);
      const breakSeconds = (isLong ? longMin : 5) * 60;
      notify('Fin de trabajo', `Empieza descanso ${isLong ? longMin + ' min (largo)' : '5 min (corto)'}`);
      startBreak(breakSeconds);
    });
  }
  function startBreak(durationSeconds) {
    currentPhase = 'break'; $btnPause.textContent = 'Pausar';
    startTimer(durationSeconds, 'Descanso', 'var(--accent-2)', () => {
      cyclesCompleted += 1; repsLeft -= 1;
      notify('Fin de descanso', repsLeft > 0 ? 'Vuelve el trabajo' : 'Secuencia completada');
      if (repsLeft > 0) { startWork(); } else { finishAll(); }
    });
  }
  function startCustomRepeats(seconds, cycles) {
    customSeconds = seconds; repsLeft = cycles; currentPhase = 'custom';
    cyclesTotal = 0; $btnPause.textContent = 'Pausar';
    notify('Inicio', `Personalizado ${seconds}s x${cycles}`);
    const again = () => {
      repsLeft -= 1;
      notify('Fin de bloque', repsLeft > 0 ? `Quedan ${repsLeft}` : 'Listo');
      if (repsLeft > 0) { startTimer(customSeconds, 'Personalizado', 'var(--ok)', again); }
      else { finishAll(); }
    };
    startTimer(customSeconds, 'Personalizado', 'var(--ok)', again);
  }

  // Buttons
  $btnPomodoro.addEventListener('click', () => {
    ensureAudioCtx(); tryEnableNotifications();
    const cycles = sanitInt($reps.value, 1);
    startPomodoroCycles(cycles);
  });
  $btnShort.addEventListener('click', () => {
    ensureAudioCtx(); tryEnableNotifications();
    currentPhase = 'break'; $btnPause.textContent = 'Pausar';
    startTimer(5 * 60, 'Descanso', 'var(--accent-2)');
  });
  $btnLong.addEventListener('click', () => {
    ensureAudioCtx(); tryEnableNotifications();
    currentPhase = 'break'; $btnPause.textContent = 'Pausar';
    startTimer(15 * 60, 'Descanso', 'var(--accent-2)');
  });
  $btnStartCustom.addEventListener('click', () => {
    ensureAudioCtx(); tryEnableNotifications();
    const m = Math.max(0, parseInt($min.value || '0', 10));
    const s = Math.max(0, parseInt($sec.value || '0', 10));
    let total = m * 60 + s; if (total <= 0) total = 1;
    const cycles = sanitInt($reps.value, 1);
    startCustomRepeats(total, cycles);
  });
  $btnPause.addEventListener('click', () => { ensureAudioCtx(); if (!intervalId && !paused) return; pauseResume(); });
  $btnReset.addEventListener('click', () => { stopTimer(true); });

  stopTimer(true);
})();
</script>

</body>
</html>
"""

SW_JS = """self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open('pomodoro-v1');
    await cache.addAll(['/', '/manifest.webmanifest']);
  })());
  self.skipWaiting();
});
self.addEventListener('activate', event => { event.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.pathname === '/' || url.pathname === '/manifest.webmanifest') {
    event.respondWith((async () => {
      const cache = await caches.open('pomodoro-v1');
      const cached = await cache.match(event.request);
      try {
        const fresh = await fetch(event.request);
        cache.put(event.request, fresh.clone());
        return fresh;
      } catch (e) {
        return cached || Response.error();
      }
    })());
  }
});
self.addEventListener('message', event => {
  const data = event.data || {};
  if (data.type === 'notify' && self.registration && self.registration.showNotification) {
    const title = data.title || 'Pomodoro';
    const body = data.body || '';
    self.registration.showNotification(title, { body });
  }
});
"""

MANIFEST = """{
  "name": "Pomodoro Timer",
  "short_name": "Pomodoro",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#0f172a",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}"""

PNG_192 = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADAAAAAAACp8Z5cAAAAGXRFWHRTb2Z0d2FyZQBwYWludC5uZXQgNC4yLjE1ZEdYUgAAAExJREFUeNrtwQENAAAAwqD3T20ON6AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHgB0wABQ3GoswAAAABJRU5ErkJggg=="
PNG_512 = "iVBORw0KGgoAAAANSUhEUgAAAQgAAAEIAQAAAAA3m8XGAAAAGXRFWHRTb2Z0d2FyZQBwYWludC5uZXQgNC4yLjE1ZEdYUgAAAEFJREFUeNrtwQEBAAAAgiD/r25IQAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPgBKMABkz7v1kAAAAASUVORK5CYII="

@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")

@app.route("/sw.js")
def sw():
    return Response(SW_JS, mimetype="application/javascript")

@app.route("/manifest.webmanifest")
def manifest():
    return Response(MANIFEST, mimetype="application/manifest+json")

@app.route("/icon-192.png")
def icon192():
    return Response(base64.b64decode(PNG_192), mimetype="image/png")

@app.route("/icon-512.png")
def icon512():
    return Response(base64.b64decode(PNG_512), mimetype="image/png")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Run Pomodoro web app (PWA)")
  parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
  parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
  args = parser.parse_args()
  app.run(host=args.host, port=args.port, debug=False)
