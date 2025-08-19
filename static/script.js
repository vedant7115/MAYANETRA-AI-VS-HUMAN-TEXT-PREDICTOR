// Elements
const form = document.getElementById("predictForm");
const input = document.getElementById("textInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const resultPanel = document.getElementById("resultPanel");
const resultBadge = document.getElementById("resultBadge");
const meter = document.getElementById("meter");
const confidence = document.getElementById("confidence");
const toast = document.getElementById("toast");
const sampleBtn = document.getElementById("sampleBtn");
const clearBtn = document.getElementById("clearBtn");
const copyBtn = document.getElementById("copyBtn");
const wc = document.getElementById("wc");
const cc = document.getElementById("cc");
const saveHistory = document.getElementById("saveHistory");
const clearResult = document.getElementById("clearResult");
const historyList = document.getElementById("historyList");
const clearHistoryBtn = document.getElementById("clearHistory");
const themeToggle = document.getElementById("themeToggle");
const confettiCanvas = document.getElementById("confettiCanvas");

// Helpers
const showToast = (msg) => { toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 1800); };
const count = () => { const text = input.value;
    wc.textContent = (text.trim() ? text.trim().split(/\s+/).length : 0);
    cc.textContent = text.length; };
const percentToLabel = (p) => p >= 0.5 ? "🤖 AI Generated" : "🧑 Human Written";

// Simple confetti
const confetti = () => {
    const ctx = confettiCanvas.getContext('2d');
    const w = confettiCanvas.width = window.innerWidth;
    const h = confettiCanvas.height = window.innerHeight;
    const pieces = Array.from({ length: 80 }, () => ({
        x: Math.random() * w,
        y: -20 - Math.random() * h,
        s: 6 + Math.random() * 6,
        vy: 2 + Math.random() * 3,
        vx: -1 + Math.random() * 2,
        rot: Math.random() * Math.PI
    }));
    let t = 0;
    const loop = () => {
        ctx.clearRect(0, 0, w, h);
        pieces.forEach(p => {
            p.y += p.vy;
            p.x += p.vx;
            p.rot += 0.05;
            if (p.y > h + 20) p.y = -20;
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.rot);
            ctx.fillStyle = `hsl(${(t+p.x)%360}, 90%, 60%)`;
            ctx.fillRect(-p.s / 2, -p.s / 2, p.s, p.s);
            ctx.restore();
        });
        t += 2;
        if (t < 360 * 4) requestAnimationFrame(loop);
    };
    loop();
};

// Theme toggle (persist)
const THEME_KEY = "mayanetra-theme";
const setTheme = (d) => { document.documentElement.classList.toggle("light", d === "light");
    localStorage.setItem(THEME_KEY, d); };
setTheme(localStorage.getItem(THEME_KEY) || "dark");
themeToggle.addEventListener("click", () => setTheme(document.documentElement.classList.contains("light") ? "dark" : "light"));

// Live counters
input.addEventListener("input", count);
count();

// Sample & Clear
sampleBtn.addEventListener("click", () => {
    input.value = "The concept of artificial intelligence continues to evolve as new models and techniques are developed. With advancements in natural language processing, machines are increasingly capable of mimicking human communication.";
    count();
    showToast("Sample loaded");
});
clearBtn.addEventListener("click", () => { input.value = "";
    count();
    resultPanel.classList.add("hidden"); });

// Copy
copyBtn.addEventListener("click", async() => {
    await navigator.clipboard.writeText(input.value || "");
    showToast("Text copied");
});

// Submit (AJAX)
form.addEventListener("submit", async(e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) { showToast("Please enter some text"); return; }

    analyzeBtn.classList.add("loading");
    resultPanel.classList.add("hidden");

    try {
        const res = await fetch("/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
        const data = await res.json();

        if (data.error) { showToast(data.error);
            analyzeBtn.classList.remove("loading"); return; }

        // Optional: if backend returns probability, use it; else infer 0.65 for AI result, 0.35 for human
        const label = data.prediction || "Unknown";
        let p = 0.5;
        if (data.probability !== undefined) p = data.probability; // expecting 0..1
        else p = /AI/i.test(label) ? 0.78 : 0.22;

        // Update UI
        resultBadge.textContent = label;
        resultBadge.classList.toggle("good", p < 0.5);
        resultBadge.classList.toggle("bad", p >= 0.5);
        meter.style.width = `${Math.round(p*100)}%`;
        confidence.textContent = `Confidence: ${Math.round(p*100)}%`;

        resultPanel.classList.remove("hidden");
        confetti();
        showToast("Analysis complete");
    } catch (err) {
        showToast("Server error");
    } finally {
        analyzeBtn.classList.remove("loading");
    }
});

// History
const HIST_KEY = "mayanetra-history";
const renderHistory = () => {
    const items = JSON.parse(localStorage.getItem(HIST_KEY) || "[]");
    historyList.innerHTML = "";
    items.slice().reverse().forEach((it, idx) => {
        const div = document.createElement("div");
        div.className = "hist-item";
        div.innerHTML = `<div>${it.text.slice(0,80)}${it.text.length>80?"…":""}</div>
                     <div class="meta">${it.label} • ${new Date(it.ts).toLocaleTimeString()}</div>`;
        div.addEventListener("click", () => { input.value = it.text;
            count();
            showToast("Loaded from history"); });
        historyList.appendChild(div);
    });
};
renderHistory();

saveHistory.addEventListener("click", () => {
    if (!input.value.trim()) { showToast("Nothing to save"); return; }
    const items = JSON.parse(localStorage.getItem(HIST_KEY) || "[]");
    const label = resultBadge.textContent || "Unknown";
    items.push({ text: input.value, label, ts: Date.now() });
    localStorage.setItem(HIST_KEY, JSON.stringify(items));
    renderHistory();
    showToast("Saved to history");
});
clearHistoryBtn.addEventListener("click", () => { localStorage.removeItem(HIST_KEY);
    renderHistory();
    showToast("History cleared"); });
clearResult.addEventListener("click", () => resultPanel.classList.add("hidden"));

// Light theme tweaks (optional)
const style = document.createElement('style');
style.textContent = `
  .light body{background:#f3f6fb}
  .light .topbar{background:rgba(255,255,255,.7)}
  .light .card,.light .history{background:#ffffff;color:#0c1220}
  .light .form textarea,.light .ghost-btn{background:#fbfcff;color:#0c1220}
  .light .nav-link{color:#4a5568}
  .light .nav-link.active,.light .nav-link:hover{color:#0c1220}
`;
document.head.appendChild(style);