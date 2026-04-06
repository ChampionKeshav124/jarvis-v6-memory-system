const gracefulFs = require('graceful-fs');
const path = require('node:path');
const readline = require('node:readline');
const process = require('node:process');

// Patch fs to be more resilient as per graceful-fs documentation
const fs = gracefulFs.promises;

/**
 * Jarvis - Assistant with integrated conversation logging.
 */
class Jarvis {
    constructor() {
        // Ensure logs are relative to the script location regardless of where the .bat is run from
        this.logDir = path.resolve(__dirname, 'logs');
        this.logFile = path.join(this.logDir, 'conversations.json');
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            prompt: 'Jarvis> '
        });
    }

    /**
     * Initializes logging infrastructure.
     */
    async initialize() {
        try {
            await fs.mkdir(this.logDir, { recursive: true });
            try {
                const stats = await fs.stat(this.logFile);
                if (stats.size === 0) throw new Error('Empty file');
                await fs.access(this.logFile);
            } catch {
                // Create initial empty log if not exists
                await fs.writeFile(this.logFile, JSON.stringify([], null, 2));
            }
        } catch (error) {
            console.error('[System] Initialization Error:', error.message);
        }
    }

    /**
     * Records a new turn in the conversation log.
     */
    async logConversation(userText, assistantText) {
        try {
            let logs = [];
            try {
                const data = await fs.readFile(this.logFile, 'utf8');
                logs = data ? JSON.parse(data) : [];
            } catch (e) {
                logs = []; // Reset if JSON is corrupt
            }

            logs.push({
                id: logs.length + 1,
                timestamp: new Date().toLocaleString(),
                user: userText,
                assistant: assistantText
            });

            // Keep only last 50 entries to prevent file bloat
            if (logs.length > 50) logs.shift();

            await fs.writeFile(this.logFile, JSON.stringify(logs, null, 2));
        } catch (error) {
            console.error('[System] Logging Error:', error.message);
        }
    }

    /**
     * Accesses and displays the logs.
     */
    async showLogs() {
        try {
            const data = await fs.readFile(this.logFile, 'utf8');
            const logs = data ? JSON.parse(data) : [];

            if (logs.length === 0) {
                console.log('\n[System] No logs recorded yet.\n');
                return;
            }

            console.log('\n--- 📜 JARVIS CONVERSATION HISTORY ---');
            logs.forEach(entry => {
                console.log(`[${entry.timestamp}]`);
                console.log(`USER: ${entry.user}`);
                console.log(`Jarvis: ${entry.assistant}\n`);
            });
            console.log('--------------------------------------\n');
        } catch (error) {
            console.log('[System] Error accessing logs. Data might be corrupted.');
        }
    }

    async start() {
        await this.initialize();
        console.log('Jarvis Online. (Commands: "show logs", "access history", "exit")');
        this.rl.prompt();

        this.rl.on('line', async (line) => {
            const input = line.trim();
            if (!input) return this.rl.prompt();

            if (input.toLowerCase() === 'exit') return this.rl.close();

            const logCommands = ['show logs', 'access logs', 'display history', 'access history', 'read logs'];
            if (logCommands.some(cmd => input.toLowerCase().includes(cmd))) {
                await this.showLogs();
            } else {
                const response = `I have recorded your message: "${input}"`;
                console.log(response);
                await this.logConversation(input, response);
            }
            this.rl.prompt();
        }).on('close', () => process.exit(0));
    }
}

const jarvis = new Jarvis();
jarvis.start();