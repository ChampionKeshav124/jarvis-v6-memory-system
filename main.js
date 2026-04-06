// ═══════════════════════════════════════════════════════════════
//  JARVIS V5 — Electron Main Process
//  BYTEFORGE SYSTEM
//  Manages window lifecycle, Python IPC bridge, and system stats
// ═══════════════════════════════════════════════════════════════

const { app, BrowserWindow, ipcMain, dialog, session, globalShortcut } = require('electron');
const path = require('path');
const { spawn, execSync, exec } = require('child_process');
const os = require('os');

// Check for Administrative Elevation (Required for system control)
let isElevated = false;
try {
  if (os.platform() === 'win32') {
    // 'net session' requires admin privileges on Windows to succeed
    execSync('net session', { stdio: 'ignore' });
    isElevated = true;
  } else {
    isElevated = process.getuid && process.getuid() === 0;
  }
} catch (e) {
  isElevated = false;
}

// Show Warning if not elevated (runs once on app ready)
app.whenReady().then(() => {
  if (!isElevated) {
    dialog.showMessageBox({
      type: 'warning',
      title: 'JARVIS: High-Level Elevation Required',
      message: 'Administrative Access is Limited.',
      detail: 'To physically control applications like Steam, JARVIS needs full Administrative Authority. \n\nTACTICAL CHECKLIST:\n1. Close JARVIS and VS Code/Terminal.\n2. Search Start Menu for "PowerShell" or "VS Code".\n3. Right-click it & select "Run as Administrator".\n4. Type "npm run dev" to reboot with full power.',
      buttons: ['I Understand (Continue User-Mode)', 'Exit to restart correctly'],
      defaultId: 0
    }).then(result => {
      if (result.response === 1) app.quit();
    });
  }
});

let mainWindow;

// ── Window Creation ─────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 720,
    minWidth: 820,
    minHeight: 620,
    frame: false,
    transparent: false,
    backgroundColor: '#06060a',
    title: 'JARVIS V5',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      devTools: true // Enable for troubleshooting
    },
    // Frameless + rounded corners usually need some margin or specific CSS
  });

  // Register Global Hotkey
  const ret = globalShortcut.register('Alt+Space', () => {
    console.log('Alt+Space is pressed');
    mainWindow.webContents.send('wake-jarvis');
    mainWindow.show();
    mainWindow.focus();
  });

  if (!ret) { console.log('shortcut registration failed'); }

  // Spawn Native Windows Speech Listener (V4.3)
  const ps = spawn('powershell.exe', ['-ExecutionPolicy', 'Bypass', '-File', path.join(__dirname, 'speech_listener.ps1')]);

  ps.stdout.on('data', (data) => {
    const output = data.toString();
    console.log(`PS-STDOUT: ${output}`);
    if (output.includes('WAKE_DETECTED')) {
      mainWindow.webContents.send('wake-jarvis');
      mainWindow.show();
      mainWindow.focus();
    }
  });

  ps.stderr.on('data', (data) => console.log(`PS-STDERR: ${data}`));

  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    if (permission === 'media') {
      callback(true); // Always allow microphone for JARVIS
    } else {
      callback(false);
    }
  });

  // Bypass autoplay restrictions
  app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── Python Bridge ───────────────────────────────────────────
// Spawns python/jarvis.py per command and returns JSON response
let lastCommandTime = 0;
const COMMAND_COOLDOWN = 4500; // 4.5 seconds

ipcMain.handle('send-command', async (_event, payload) => {
  const now = Date.now();
  if (now - lastCommandTime < COMMAND_COOLDOWN) {
    return { response: "Syncing systems, please stand by...", action: "throttled" };
  }
  lastCommandTime = now;

  return new Promise((resolve) => {
    const scriptPath = path.join(__dirname, 'python', 'jarvis.py');
    const { text, voice } = payload;

    let args = [scriptPath, text];
    if (voice) args.push('--voice');

    const proc = spawn('python', args, {
      cwd: path.join(__dirname, 'python'),
    });

    // Timeout logic (V8) - Increased to 300s for heavy RAG and long generations
    const timeoutId = setTimeout(() => {
      if (proc.exitCode === null) proc.kill();
      console.error(`[TIMEOUT] Python core did not respond within 300s. Last stderr: ${stderr}`);
      resolve({ response: 'The AI core is taking too long to process this request. Please try a shorter command or check your connection.', action: null });
    }, 300000);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });

    proc.on('close', (code) => {
      clearTimeout(timeoutId);
      if (stderr) console.warn('[Python stderr]', stderr);

      const trimmedOutput = stdout.trim();
      try {
        resolve(JSON.parse(trimmedOutput));
      } catch (err) {
        console.error('[JSON Parse Error] Python sent non-JSON output:', trimmedOutput);
        resolve({
          response: trimmedOutput || 'I encountered an internal processing error. The AI core sent an empty response.',
          action: null,
        });
      }
    });

    proc.on('error', (err) => {
      clearTimeout(timeoutId);
      console.error('[Spawn Error]', err.message);
      resolve({
        response: 'Failed to reach AI core. Ensure Python is installed and accessible.',
        action: null,
      });
    });
  });
});

ipcMain.handle('get-chat-history', async () => {
  return new Promise((resolve) => {
    const scriptPath = path.join(__dirname, 'python', 'jarvis.py');
    const proc = spawn('python', [scriptPath, '--get-history'], {
      cwd: path.join(__dirname, 'python'),
    });

    let stdout = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.on('close', () => {
      try {
        resolve(JSON.parse(stdout.trim()));
      } catch (err) {
        resolve({ history: [] });
      }
    });
  });
});

// ── Real System Stats ───────────────────────────────────────
// Returns actual CPU and RAM usage from the OS
ipcMain.handle('get-system-stats', async () => {
  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const ramPercent = Math.round(((totalMem - freeMem) / totalMem) * 100);

  // CPU usage: compare idle vs total over a 500ms sample
  const cpuPercent = await new Promise((resolve) => {
    const cpus1 = os.cpus();
    setTimeout(() => {
      const cpus2 = os.cpus();
      let idleDiff = 0, totalDiff = 0;
      for (let i = 0; i < cpus2.length; i++) {
        const t1 = cpus1[i].times, t2 = cpus2[i].times;
        const total1 = t1.user + t1.nice + t1.sys + t1.idle + t1.irq;
        const total2 = t2.user + t2.nice + t2.sys + t2.idle + t2.irq;
        idleDiff += t2.idle - t1.idle;
        totalDiff += total2 - total1;
      }
      resolve(totalDiff === 0 ? 0 : Math.round(100 - (idleDiff / totalDiff) * 100));
    }, 500);
  });

  return { cpu: cpuPercent, ram: ramPercent };
});

// ── Config Provider ─────────────────────────────────────────
ipcMain.handle('get-config', async () => {
  try {
    const configPath = path.join(__dirname, 'config.py');
    const fs = require('fs');
    const content = fs.readFileSync(configPath, 'utf8');

    // Simple regex to extract WAKE_WORDS list
    const wakeMatch = content.match(/WAKE_WORDS\s*=\s*\[(.*?)\]/s);
    let wakeWords = ["jarvis wake up", "jarvis uth jao", "wake up daddy's home"];
    if (wakeMatch) {
      wakeWords = wakeMatch[1].split(',').map(s => s.trim().replace(/['"]/g, ''));
    }

    return { wakeWords };
  } catch (err) {
    return { wakeWords: ["jarvis wake up", "jarvis uth jao", "wake up daddy's home"] };
  }
});

// ── Window Controls (frameless) ─────────────────────────────
ipcMain.on('win-minimize', () => mainWindow?.minimize());
ipcMain.on('win-maximize', () => {
  if (mainWindow) mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
});
ipcMain.on('win-close', () => mainWindow?.close());
ipcMain.on('open-mic-settings', () => {
  exec('start ms-settings:privacy-microphone');
});

// ── App Lifecycle ───────────────────────────────────────────
app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
