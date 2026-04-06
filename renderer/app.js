const input       = document.getElementById('commandInput');
const sendBtn     = document.getElementById('sendBtn');
const panel       = document.getElementById('responsePanel');
const statusBadge = document.getElementById('statusBadge');
const statusText  = document.getElementById('statusText');
const cpuBar      = document.getElementById('cpuBar');
const ramBar      = document.getElementById('ramBar');
const cpuValue    = document.getElementById('cpuValue');
const ramValue    = document.getElementById('ramValue');
const systemStatus = document.getElementById('systemStatus');
const clockDisplay = document.getElementById('clockDisplay');
const btnVoiceToggle = document.getElementById('btnVoiceToggle');
const voiceLabel = document.getElementById('voiceLabel');
const voiceIcon = document.querySelector('.voice-icon');
const btnAllowMic = document.getElementById('btnAllowMic');
const btnManualWake = document.getElementById('btnManualWake');

const micSelector = document.getElementById('micSelector');
const btnFixPrivacy = document.getElementById('btnFixPrivacy');

// State Manager
const APP_STATE = {
  IDLE: 'IDLE',
  LISTENING: 'LISTENING',
  PROCESSING: 'PROCESSING'
};

let currentState = APP_STATE.IDLE;
let isVoiceEnabled = true;
let currentAudio = null;
let wakeWords = ["jarvis", "jarvis wake up", "wake up jarvis"];

// Speech Recognition Setup (Fail-safe Browser Bridge)
const NativeSpeech = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (NativeSpeech) {
  recognition = new NativeSpeech();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(result => result[0].transcript.toLowerCase())
      .join('');
    
    // Check for any wake word in the transcript
    if (wakeWords.some(word => transcript.includes(word))) {
      if (currentState === APP_STATE.IDLE) {
        console.log("Failsafe Wake Detected:", transcript);
        activateJarvis();
        recognition.stop(); // Restart after activation
      }
    }
  };

  recognition.onend = () => { if (isVoiceEnabled) recognition.start(); };
}

// ── Audio Visualizer & Device Selection ───────────────────────

async function populateMicSelector() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const mics = devices.filter(d => d.kind === 'audioinput');
    micSelector.innerHTML = mics.map(m => `<option value="${m.deviceId}">${m.label || 'Unknown Microphone'}</option>`).join('');
  } catch (e) {
    console.error("Device enum failed:", e);
  }
}

let currentStream = null;
async function initVisualizer(deviceId = 'default') {
  const canvas = document.getElementById('micVisualizer');
  const ctx = canvas.getContext('2d');
  
  try {
    if (currentStream) currentStream.getTracks().forEach(t => t.stop());
    
    // Fix Handshake: If deviceId is 'default', let the browser pick.
    const audioConstraints = (deviceId && deviceId !== 'default') 
      ? { audio: { deviceId: { exact: deviceId } } } 
      : { audio: true };

    currentStream = await navigator.mediaDevices.getUserMedia(audioConstraints);
    
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(currentStream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    canvas.width = 140;
    canvas.height = 140;

    let rollingPeak = 30; 
    const PEAK_DECAY = 0.99; 
    let silentFrameCount = 0;
    let hasAlertedSilence = false;

    function draw() {
    requestAnimationFrame(draw);
    analyser.getByteFrequencyData(dataArray);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 60;
    const barCount = 40;
    
    // Dynamic Peak Normalization (Human Voice Range: first ~60 bins)
    let frameMax = 0;
    let sum = 0;
    for (let i = 0; i < 60; i++) {
        if (dataArray[i] > frameMax) frameMax = dataArray[i];
        sum += dataArray[i];
    }
    
    // TITAN MIC HEALTH TRACKER (Quiet background recovery)
    if (frameMax < 0.2) {
        silentFrameCount++;
        if (silentFrameCount > 900 && !hasAlertedSilence) { 
            console.warn("TITAN: Hardware Silence detected. Quietly resetting audio context...");
            hasAlertedSilence = true;
            setTimeout(() => { 
                hasAlertedSilence = false; 
                silentFrameCount = 0; 
                initVisualizer(); 
            }, 2000); 
        }
    } else { silentFrameCount = 0; }

    // Update rolling peak
    if (frameMax > rollingPeak) rollingPeak = frameMax;
    else rollingPeak *= PEAK_DECAY;
    if (rollingPeak < 20) rollingPeak = 20; 

    const micStatus = document.getElementById('micStatus');
    if (micStatus) {
        micStatus.innerText = `PHONETIC LEVEL: ${Math.round(rollingPeak)}`;
        micStatus.style.color = rollingPeak > 30 ? '#00ffcc' : '#ff3333';
    }

    // ── THE FIX: Define math before using it ──
    const normFactor = 255 / (rollingPeak + 1);
    const avgVolume = (sum / 60) * normFactor;

    // SHOUT DETECTION (Now 'Whisper' Detection)
    if (currentState === APP_STATE.IDLE && avgVolume > 15) { // Threshold lowered from 90 to 15
        console.log("PHONETIC TRIGGER: Vol", avgVolume);
        activateJarvis(); // Wake up on low volume voice detection
    }

    // Colors based on state
    let accent = '#00d4ff'; // Blue (Idle)
    if (currentState === APP_STATE.LISTENING) accent = '#00ffcc'; // Cyan
    if (currentState === APP_STATE.PROCESSING) accent = '#ffaa00'; // Amber
    if (avgVolume > 15 && currentState === APP_STATE.IDLE) accent = '#ff00ff'; // Magenta (Hearing)
    if (avgVolume > 240) accent = '#ff3333'; // Deep Peak (normalized)

    // Draw Central AI Ring
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius - 5, 0, Math.PI * 2);
    ctx.strokeStyle = accent;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Visual ring drawing with Spectrum Expansion
    for (let i = 0; i < barCount; i++) {
      const angle = (i / barCount) * Math.PI * 2;
      
      const dataIndex = Math.floor(i * 1.5) + 2; 
      let val = dataArray[dataIndex] || 0;
      val = Math.min(255, val * normFactor);

      const barHeight = (val / 255) * 45; 

      const x1 = centerX + Math.cos(angle) * radius;
      const y1 = centerY + Math.sin(angle) * radius;
      const x2 = centerX + Math.cos(angle) * (radius + barHeight);
      const y2 = centerY + Math.sin(angle) * (radius + barHeight);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = accent;
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.stroke();
    }
  }
    draw();
  } catch (err) {
    console.warn("Visualizer failed:", err);
    appendMessage('SYSTEM >', 'Microphone hardware not detected or blocked.', 'error');
  }
}

// ── Manual Controls ────────────────────────────────────────

btnAllowMic.addEventListener('click', () => {
  if (recognition) {
    try {
      recognition.start();
      btnAllowMic.style.display = 'none';
      appendMessage('SYSTEM >', 'Microphone initialized.', 'system');
    } catch (e) {
      console.log("Recognition already started or failed:", e);
    }
  }
});

btnManualWake.addEventListener('click', () => {
  if (currentState === APP_STATE.IDLE) activateJarvis();
});

// ── State Transitions ───────────────────────────────────────

function setUIState(state) {
  currentState = state;
  document.body.classList.remove('idle-mode');
  statusBadge.classList.remove('status-badge--idle', 'status-badge--listening', 'processing');

  switch (state) {
    case APP_STATE.IDLE:
      document.body.classList.add('idle-mode');
      statusBadge.classList.add('status-badge--idle');
      statusText.textContent = 'IDLE';
      systemStatus.textContent = 'AWAITING ACTIVATION';
      systemStatus.style.color = '';
      input.disabled = true;
      input.placeholder = "SAY 'JARVIS WAKE UP' TO ACTIVATE...";
      break;
    
    case APP_STATE.LISTENING:
      statusBadge.classList.add('status-badge--listening');
      statusText.textContent = 'LISTENING';
      systemStatus.textContent = 'LISTENING...';
      systemStatus.style.color = '#ff00ff';
      input.disabled = false;
      input.placeholder = "GIVE A COMMAND...";
      input.focus();
      break;

    case APP_STATE.PROCESSING:
      statusBadge.classList.add('processing');
      statusText.textContent = 'PROCESSING';
      systemStatus.textContent = 'PROCESSING...';
      systemStatus.style.color = '#ffaa00';
      input.disabled = true;
      break;
  }
}

async function activateJarvis() {
  if (currentState !== APP_STATE.IDLE) return;
  setUIState(APP_STATE.LISTENING);
  appendMessage('SYSTEM >', 'Wake word detected.', 'system');
  await sendCommand("__system_startup__", true);
}

// ── Actions ─────────────────────────────────────────────────

async function sendCommand(overrideText = null, isActivation = false) {
  const text = overrideText || input.value.trim();
  if (!text) return;

  if (!isActivation) {
    appendMessage('USER >', text, 'user');
    input.value = '';
    setUIState(APP_STATE.PROCESSING);
  }

  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

    let result;
    try {
      result = await window.jarvis.sendCommand({ 
        text: text, 
        voice: isVoiceEnabled 
      });

      if (result.action === 'exit') {
        appendMessage('JARVIS >', result.response, 'system');
        speakResponse(result.response, result.audio_base64);
        setTimeout(() => window.jarvis.close(), 2500);
        return;
      }

      speakResponse(result.response, result.audio_base64);
      await typeMessage('JARVIS >', result.response || 'System process complete.', 'system');

    } catch (err) {
      const errorMsg = 'AI core communication failed or timed out.';
      appendMessage('SYSTEM >', errorMsg, 'error');
      speakResponse(errorMsg);
      result = { action: 'error' };
    }

    // V6.4: Conversational Fluidity — Always maintain Listening state for follow-up questions
    if (result.action !== 'error') {
        setUIState(APP_STATE.LISTENING);
    } else {
        setTimeout(() => setUIState(APP_STATE.IDLE), 1000);
    }
}

// ── Components ──────────────────────────────────────────────

function speakResponse(text, base64Data = null) {
  if (!isVoiceEnabled || !text) return;

  // 1. Priority: ElevenLabs (base64)
  if (base64Data) {
    try {
      if (currentAudio) currentAudio.pause();
      const audioSrc = 'data:audio/mpeg;base64,' + base64Data;
      currentAudio = new Audio(audioSrc);
      currentAudio.onplay  = () => document.body.classList.add('speaking-active');
      currentAudio.onended = () => document.body.classList.remove('speaking-active');
      currentAudio.onerror = () => document.body.classList.remove('speaking-active');
      currentAudio.play().catch(e => {
        document.body.classList.remove('speaking-active');
        console.warn("ElevenLabs Audio blocked, falling back to System Voice.");
        fallbackToSystemVoice(text);
      });
      return;
    } catch (err) { 
        console.error("Audio play error:", err); 
        fallbackToSystemVoice(text);
        return;
    }
  }

  // 2. Fallback: Web Speech API (System Voice)
  fallbackToSystemVoice(text);
}

function fallbackToSystemVoice(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    // Find a good professional voice if possible
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Natural')) || voices[0];
    if (preferredVoice) utterance.voice = preferredVoice;
    
    utterance.rate = 1.1;
    utterance.pitch = 1.0;
    
    utterance.onstart = () => document.body.classList.add('speaking-active');
    utterance.onend   = () => document.body.classList.remove('speaking-active');
    
    window.speechSynthesis.cancel(); // Stop current speech
    window.speechSynthesis.speak(utterance);
}

async function typeMessage(prefix, text, type) {
  const msg = document.createElement('div');
  msg.className = `response-message response-message--${type}`;
  msg.innerHTML = `<span class="response-prefix">${prefix}</span><span class="response-text"></span>`;
  panel.appendChild(msg);
  const textSpan = msg.querySelector('.response-text');

  const chars = text.split('');
  for (let i = 0; i < chars.length; i++) {
    textSpan.textContent += chars[i];
    panel.scrollTop = panel.scrollHeight;
    await new Promise(r => setTimeout(r, 15));
  }
}

function appendMessage(prefix, text, type) {
  const msg = document.createElement('div');
  msg.className = `response-message response-message--${type}`;
  msg.innerHTML = `<span class="response-prefix">${prefix}</span><span class="response-text">${text}</span>`;
  panel.appendChild(msg);
  panel.scrollTop = panel.scrollHeight;
}

// ── System Initialization ─────────────────────────────────────

async function startSystem() {
  console.log("Activating System...");
  const overlay = document.getElementById('activationOverlay');
  if (overlay) overlay.style.display = 'none';

  // Enter IDLE mode first so the UI looks active
  setUIState(APP_STATE.IDLE);
  
  appendMessage('SYSTEM >', 'Neural link established. Systems online.', 'system');

  // Load mic features in background so they don't block the UI
  try {
    initVisualizer();
    if (recognition) {
        recognition.start();
        appendMessage('SYSTEM >', 'Voice Monitoring Active.', 'system');
    }
  } catch (err) {
    console.error("Mic init fail:", err);
    appendMessage('SYSTEM >', 'Voice hardware unavailable.', 'error');
  }
}

// ── Lifecycle ───────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', async () => {
  const config = await window.jarvis.getConfig();
  wakeWords = config.wakeWords;
  console.log("V6 Initialized. Monitoring for:", wakeWords);
  
  // Manual activation listener
  window.jarvis.onWakeJarvis(() => {
    console.log("Global Wake Triggered");
    if (currentState === APP_STATE.IDLE) activateJarvis();
  });

  // Stats & Clock
  initStatsAndClock();
});

function initStatsAndClock() {
  setInterval(async () => {
    try {
      const stats = await window.jarvis.getSystemStats();
      cpuBar.style.width = stats.cpu + '%';
      cpuValue.textContent = stats.cpu + '%';
      ramBar.style.width = stats.ram + '%';
      ramValue.textContent = stats.ram + '%';
    } catch {}
  }, 3000);

  setInterval(() => {
    clockDisplay.textContent = new Date().toLocaleTimeString();
  }, 1000);
}

// Controls
const safeAddListener = (id, event, fn) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener(event, fn);
};

safeAddListener('btnMinimize', 'click', () => window.jarvis.minimize());
safeAddListener('btnMaximize', 'click', () => window.jarvis.maximize());
safeAddListener('btnClose', 'click', () => window.jarvis.close());
safeAddListener('sendBtn', 'click', () => sendCommand());
safeAddListener('btnActivateSystem', 'click', startSystem);
safeAddListener('btnManualWake', 'click', () => { if (currentState === APP_STATE.IDLE) activateJarvis(); });
safeAddListener('btnAllowMic', 'click', () => recognition && recognition.start());

input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendCommand(); });

btnVoiceToggle.addEventListener('click', () => {
  isVoiceEnabled = !isVoiceEnabled;
  voiceLabel.textContent = isVoiceEnabled ? 'VOICE ON' : 'VOICE OFF';
  voiceIcon.textContent = isVoiceEnabled ? '🔊' : '🔇';
  if (!isVoiceEnabled && currentAudio) currentAudio.pause();
});

// ── Mic Selector & Hardware Restoration ────────────────────────
micSelector.addEventListener('change', (e) => {
    const deviceId = e.target.value;
    console.log("Switching hardware to:", deviceId);
    initVisualizer(deviceId);
});

btnFixPrivacy.addEventListener('click', () => {
    window.jarvis.openMicSettings();
});

// Update DOMContentLoaded to populate mics
window.addEventListener('DOMContentLoaded', async () => {
    populateMicSelector();
    // Re-check mics when permissions might have changed
    navigator.mediaDevices.ondevicechange = populateMicSelector;
    
    const config = await window.jarvis.getConfig();
    wakeWords = config.wakeWords || ["jarvis", "jarvis wake up"];
    console.log("V6 Initialized. Monitoring for:", wakeWords);
    
    window.jarvis.onWakeJarvis(() => {
        if (currentState === APP_STATE.IDLE) activateJarvis();
    });

    // ── V6 HISTORY RESTORATION ──
    try {
        const historyData = await window.jarvis.getChatHistory();
        if (historyData && historyData.history && historyData.history.length > 0) {
            appendMessage('SYSTEM >', 'Restoring previous conversation context...', 'system');
            historyData.history.forEach(msg => {
                const roleLabel = msg.role === 'user' ? 'USER >' : 'JARVIS >';
                const type = msg.role === 'user' ? 'user' : 'system';
                appendMessage(roleLabel, msg.content, type);
            });
            appendMessage('SYSTEM >', 'Context restored. Systems ready.', 'system');
        }
    } catch (e) {
        console.warn("History restoration failed:", e);
    }

    initStatsAndClock();
});
