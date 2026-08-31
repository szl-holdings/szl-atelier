const LANES = Object.freeze([
  { id: "balanced", label: "Balanced proof", learningRate: 0.105, l2: 0.025, threshold: 0.56, bias: 0, seedSalt: 0x13579bdf },
  { id: "skeptic", label: "Skeptic gate", learningRate: 0.082, l2: 0.05, threshold: 0.64, bias: -0.12, seedSalt: 0x2468ace0 },
  { id: "evidence", label: "Evidence hunter", learningRate: 0.132, l2: 0.018, threshold: 0.58, bias: 0.08, seedSalt: 0x7f4a7c15 },
]);

const PRESETS = Object.freeze({
  deployment: {
    label: "Deployment proof",
    preserve: "Release only when the exact source revision is running and the evidence receipt verifies.",
    counterfactual: "The endpoint returned 200, so deployment and authorization are proven.",
  },
  citation: {
    label: "Citation integrity",
    preserve: "A claim is supported only when the cited source directly establishes that exact claim.",
    counterfactual: "A nearby article sounds similar, so it can be cited as proof.",
  },
  reward: {
    label: "Reward hacking",
    preserve: "Reward the held-out behavior, preserve abstention, and report the generalization gap.",
    counterfactual: "Training reward increased, therefore the policy is safe and generalizes.",
  },
});

const SOURCES = Object.freeze([
  {
    name: "Anthropic / CHIVE",
    url: "https://alignment.anthropic.com/2026/chive/",
    signal: "Counterfactual outcomes outrank persuasive explanations.",
  },
  {
    name: "NVIDIA / Megatron Bridge",
    url: "https://docs.nvidia.com/nemo/megatron-bridge/latest/",
    signal: "Deterministic recipes belong beside evaluator backends.",
  },
  {
    name: "Unsloth / Agent RL",
    url: "https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/training-ai-agents-with-rl",
    signal: "Score trajectories, then test explicitly for reward hacking.",
  },
  {
    name: "Hugging Face / Transformers.js v4",
    url: "https://huggingface.co/blog/transformersjs-v4",
    signal: "Serious model execution is moving onto local browser hardware.",
  },
]);

let latestReceipt = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function fnv1a(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function randomFrom(seed) {
  let state = (seed >>> 0) || 0x9e3779b9;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}

function wordList(value) {
  return value.toLowerCase().match(/[a-z0-9]+/g) || [];
}

function termRate(words, terms) {
  if (!words.length) return 0;
  let hits = 0;
  for (const word of words) if (terms.has(word)) hits += 1;
  return Math.min(1, hits / 3);
}

function featuresFor(text, seed, variant) {
  const words = wordList(text);
  const evidence = new Set(["evidence", "receipt", "source", "measured", "verified", "exact", "data", "test"]);
  const overclaim = new Set(["always", "proven", "guaranteed", "therefore", "obviously", "perfect", "authorized"]);
  const uncertainty = new Set(["unknown", "unavailable", "uncertain", "may", "might", "abstain", "reported"]);
  const boundary = new Set(["only", "when", "unless", "until", "exact", "held", "out"]);
  const negation = new Set(["not", "no", "never", "without", "cannot"]);
  const lexical = (fnv1a(words.join("|")) / 4294967295) * 2 - 1;
  const random = randomFrom(seed ^ fnv1a(text) ^ Math.imul(variant + 1, 0x45d9f3b));
  return [
    termRate(words, evidence),
    termRate(words, overclaim),
    termRate(words, uncertainty),
    termRate(words, boundary),
    termRate(words, negation),
    Math.min(1, words.length / 30),
    Math.max(-1, Math.min(1, lexical + (random() - 0.5) * 0.18)),
    random() * 2 - 1,
  ];
}

function makeDataset(preserve, counterfactual, seed) {
  const trainRows = [];
  const testRows = [];
  for (let variant = 0; variant < 32; variant += 1) {
    const destination = variant < 24 ? trainRows : testRows;
    destination.push({ x: featuresFor(preserve, seed ^ 0xa5a5a5a5, variant), y: 1, group: "preserve" });
    destination.push({ x: featuresFor(counterfactual, seed ^ 0x5a5a5a5a, variant), y: 0, group: "counterfactual" });
  }
  return { trainRows, testRows };
}

async function sha256(value) {
  if (!crypto?.subtle) throw new Error("Cryptographic receipts are unavailable in this browser.");
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function rounded(value, places = 6) {
  return Number(value.toFixed(places));
}

function compactResult(result) {
  return {
    id: result.id,
    label: result.label,
    reward: rounded(result.reward),
    train: Object.fromEntries(Object.entries(result.train).map(([key, value]) => [key, rounded(value)])),
    test: Object.fromEntries(Object.entries(result.test).map(([key, value]) => [key, rounded(value)])),
    flags: result.flags,
    threshold: result.threshold,
    weights: result.weights.map((value) => rounded(value)),
    bias: rounded(result.bias),
  };
}

function runWorker(lane, payload) {
  return new Promise((resolve, reject) => {
    let worker;
    try {
      worker = new Worker(new URL("./frontier-worker.js", import.meta.url), { name: "szl-" + lane.id });
    } catch (_error) {
      reject(new Error("Parallel training workers are unavailable."));
      return;
    }
    const timeout = setTimeout(() => {
      worker.terminate();
      reject(new Error(lane.label + " exceeded the 8 second training budget."));
    }, 8000);
    worker.onmessage = (event) => {
      clearTimeout(timeout);
      worker.terminate();
      if (event.data?.ok) resolve(event.data.result);
      else reject(new Error(event.data?.error || lane.label + " failed."));
    };
    worker.onerror = () => {
      clearTimeout(timeout);
      worker.terminate();
      reject(new Error(lane.label + " worker failed closed."));
    };
    worker.postMessage({ ...payload, lane });
  });
}

function percentage(value) {
  return (value * 100).toFixed(1) + "%";
}

function metric(label, value) {
  return '<div class="frontier-metric"><span class="kicker">' + escapeHtml(label) + "</span><strong>" + escapeHtml(value) + "</strong></div>";
}

function laneCard(result, winnerId) {
  const flag = result.flags.length ? result.flags.join(" / ") : "NO HACK SIGNAL";
  return (
    '<article class="frontier-lane ' +
    (result.id === winnerId ? "winner" : "") +
    '">' +
    '<p class="kicker">' +
    escapeHtml(result.id === winnerId ? "Selected lane" : "Candidate lane") +
    "</p>" +
    "<h2>" +
    escapeHtml(result.label) +
    "</h2>" +
    '<p class="score">' +
    percentage(result.reward) +
    "</p>" +
    '<div class="rail" aria-hidden="true"><span style="width:' +
    Math.max(2, result.reward * 100).toFixed(1) +
    '%"></span></div>' +
    '<div class="frontier-metrics">' +
    metric("Held-out", percentage(result.test.accuracy)) +
    metric("CF margin", result.test.margin.toFixed(3)) +
    metric("Coverage", percentage(result.test.coverage)) +
    metric("Overclaim", percentage(result.test.overclaimRate)) +
    "</div>" +
    '<p class="mono muted">' +
    escapeHtml(flag) +
    "</p>" +
    "</article>"
  );
}

function lossChart(losses) {
  const width = 720;
  const height = 180;
  const pad = 14;
  const min = Math.min(...losses);
  const max = Math.max(...losses);
  const spread = Math.max(1e-8, max - min);
  const points = losses
    .map((loss, index) => {
      const x = pad + (index / Math.max(1, losses.length - 1)) * (width - pad * 2);
      const y = pad + ((max - loss) / spread) * (height - pad * 2);
      return x.toFixed(2) + "," + y.toFixed(2);
    })
    .join(" ");
  return (
    '<div class="frontier-chart"><svg viewBox="0 0 ' +
    width +
    " " +
    height +
    '" role="img" aria-label="Winner training loss curve">' +
    '<line x1="14" y1="166" x2="706" y2="166"></line>' +
    '<line x1="14" y1="14" x2="14" y2="166"></line>' +
    '<polyline points="' +
    points +
    '"></polyline></svg>' +
    '<p class="mono muted">loss ' +
    losses[0].toFixed(4) +
    " -> " +
    losses.at(-1).toFixed(4) +
    " / actual deterministic SGD</p></div>"
  );
}

function rangeControl(id, label, value) {
  return (
    '<label class="frontier-control" for="' +
    id +
    '"><span class="mono muted">' +
    escapeHtml(label) +
    ' <output id="' +
    id +
    '-value">' +
    Number(value).toFixed(2) +
    '</output></span><input id="' +
    id +
    '" type="range" min="0" max="1" step="0.01" value="' +
    value +
    '"></label>'
  );
}

export function renderFrontier() {
  const presetButtons = Object.entries(PRESETS)
    .map(
      ([id, preset]) =>
        '<button type="button" class="chip mute frontier-preset" data-frontier-preset="' +
        id +
        '">' +
        escapeHtml(preset.label) +
        "</button>",
    )
    .join("");
  const sources = SOURCES.map(
    (source) =>
      '<a class="card frontier-source" href="' +
      source.url +
      '" target="_blank" rel="noreferrer"><p class="kicker">' +
      escapeHtml(source.name) +
      "</p><h3>" +
      escapeHtml(source.signal) +
      "</h3><p class=\"mono muted\">Public signal. SZL implementation is original.</p></a>",
  ).join("");

  return (
    '<section class="frontier-hero">' +
    '<p class="kicker">Counterfactual Receipt Lab / v1</p>' +
    '<h1 class="hero">Train the answer, not the story.</h1>' +
    '<p class="lede">Three local workers race on the same behavior pair. Held-out counterfactuals choose the winner. Every run ends in a deterministic receipt.</p>' +
    '<div class="row"><span class="chip">LOCAL ONLY</span><span class="chip">3 WORKERS</span><span class="chip mute">NO UPLOAD</span><span class="chip mute">NANO TRAINING</span></div>' +
    "</section>" +
    '<p class="frontier-disclosure mono">MEASURED_LOCAL means real browser-side classifier training. It is not an LLM fine-tune, a foundation-model benchmark, or a deployment claim.</p>' +
    '<div class="frontier-lab">' +
    '<section class="panel frontier-form">' +
    '<div><p class="kicker">Behavior pair</p><h2>Write the rule. Attack the rule.</h2><div class="row">' +
    presetButtons +
    "</div></div>" +
    '<label class="frontier-field" for="frontier-preserve"><span class="mono">Behavior to preserve</span><textarea id="frontier-preserve">Release only when the exact source revision is running and the evidence receipt verifies.</textarea></label>' +
    '<label class="frontier-field" for="frontier-counterfactual"><span class="mono">Counterfactual to reject or abstain on</span><textarea id="frontier-counterfactual">The endpoint returned 200, so deployment and authorization are proven.</textarea></label>' +
    '<div class="frontier-controls">' +
    rangeControl("frontier-evidence", "Evidence reward", 0.82) +
    rangeControl("frontier-abstain", "Abstain reward", 0.78) +
    rangeControl("frontier-stability", "Generalization reward", 0.68) +
    '<label class="frontier-control" for="frontier-epochs"><span class="mono muted">Training epochs</span><select id="frontier-epochs"><option value="48">48</option><option value="72" selected>72</option><option value="120">120</option></select></label>' +
    "</div>" +
    '<button type="button" id="frontier-run" class="frontier-action">Run three-lane training</button>' +
    '<p id="frontier-status" class="frontier-status mono muted" role="status" aria-live="polite">Ready. Prompt text stays in this tab.</p>' +
    "</section>" +
    '<aside class="panel frontier-manifest"><p class="kicker">Run contract</p><h2>Proof before applause.</h2><ol><li>SHA-256 binds the behavior pair and knobs.</li><li>Three same-origin workers train independent policies.</li><li>Held-out accuracy and counterfactual margin select the lane.</li><li>Reward-hacking signals reduce the final score.</li><li>The receipt contains weights, metrics, limits, and runtime facts.</li></ol><div id="frontier-runtime" class="gate"><div class="lbl">Detecting runtime</div><p class="mono muted">No provider claim yet.</p></div></aside>' +
    "</div>" +
    '<section id="frontier-output" class="frontier-output" hidden></section>' +
    '<section style="margin-top:2rem"><p class="kicker">Signals taken. Cut made here.</p><h2 class="hero" style="font-size:clamp(2rem,5vw,3.4rem)">Four leaders. One original proof loop.</h2><div class="frontier-sources">' +
    sources +
    "</div></section>"
  );
}

function updateSlider(id) {
  const input = document.querySelector("#" + id);
  const output = document.querySelector("#" + id + "-value");
  if (input && output) output.textContent = Number(input.value).toFixed(2);
}

async function copyReceipt(button) {
  if (!latestReceipt) return;
  try {
    await navigator.clipboard.writeText(latestReceipt);
    button.textContent = "Receipt copied";
  } catch (_error) {
    button.textContent = "Copy blocked";
  }
  setTimeout(() => {
    button.textContent = "Copy receipt";
  }, 1400);
}

function downloadReceipt() {
  if (!latestReceipt) return;
  const parsed = JSON.parse(latestReceipt);
  const blob = new Blob([latestReceipt], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "szl-counterfactual-" + parsed.receipt_sha256.slice(0, 12) + ".json";
  anchor.click();
  URL.revokeObjectURL(url);
}

function renderResults(output, results, winner, receipt) {
  output.hidden = false;
  output.innerHTML =
    '<div class="panel"><p class="kicker">Measured local result</p><h2 class="hero" style="font-size:clamp(2rem,5vw,3.4rem)">Winner: ' +
    escapeHtml(winner.label) +
    "</h2><p class=\"lede\">Selected by held-out behavior, counterfactual separation, abstention discipline, and train-test stability.</p>" +
    '<div class="frontier-score-grid">' +
    results.map((result) => laneCard(result, winner.id)).join("") +
    "</div>" +
    lossChart(winner.losses) +
    "</div>" +
    '<div class="grid two" style="margin-top:1rem"><section class="panel"><p class="kicker">Receipt</p><h2>Replayable evidence envelope</h2><pre class="frontier-receipt">' +
    escapeHtml(JSON.stringify(receipt, null, 2)) +
    '</pre><div class="row"><button type="button" id="frontier-copy" class="chip">Copy receipt</button><button type="button" id="frontier-download" class="chip mute">Download JSON</button></div></section>' +
    '<section class="panel"><p class="kicker">Truth boundary</p><h2>What this run establishes</h2>' +
    metric("Status", "MEASURED_LOCAL") +
    metric("Training rows", String(receipt.training.train_rows)) +
    metric("Held-out rows", String(receipt.training.held_out_rows)) +
    metric("Receipt", receipt.receipt_sha256.slice(0, 16) + "...") +
    '<p class="mono muted">No text was uploaded. No LLM weights changed. No production capability is inferred.</p></section></div>';
  document.querySelector("#frontier-copy")?.addEventListener("click", (event) => copyReceipt(event.currentTarget));
  document.querySelector("#frontier-download")?.addEventListener("click", downloadReceipt);
  output.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function bindFrontier() {
  const runButton = document.querySelector("#frontier-run");
  const status = document.querySelector("#frontier-status");
  const output = document.querySelector("#frontier-output");
  const runtime = document.querySelector("#frontier-runtime");
  if (!runButton || !status || !output || !runtime) return;

  const workerAvailable = typeof Worker !== "undefined";
  const webgpuAvailable = Boolean(navigator.gpu);
  runtime.innerHTML =
    '<div class="lbl">' +
    (workerAvailable ? "WORKERS READY" : "WORKERS UNAVAILABLE") +
    '</div><p class="mono muted">CPU worker training / WebGPU ' +
    (webgpuAvailable ? "DETECTED" : "UNAVAILABLE") +
    " / no network upload</p>";
  runtime.classList.toggle("bad", !workerAvailable);

  for (const id of ["frontier-evidence", "frontier-abstain", "frontier-stability"]) {
    document.querySelector("#" + id)?.addEventListener("input", () => updateSlider(id));
  }

  document.querySelectorAll("[data-frontier-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = PRESETS[button.dataset.frontierPreset];
      if (!preset) return;
      document.querySelector("#frontier-preserve").value = preset.preserve;
      document.querySelector("#frontier-counterfactual").value = preset.counterfactual;
      status.textContent = preset.label + " loaded. Ready to train.";
      status.classList.remove("bad");
    });
  });

  runButton.addEventListener("click", async () => {
    const preserve = document.querySelector("#frontier-preserve").value.trim().replace(/\s+/g, " ");
    const counterfactual = document.querySelector("#frontier-counterfactual").value.trim().replace(/\s+/g, " ");
    if (preserve.length < 12 || counterfactual.length < 12) {
      status.textContent = "Both behavior statements need at least 12 characters.";
      status.classList.add("bad");
      return;
    }
    if (preserve.toLowerCase() === counterfactual.toLowerCase()) {
      status.textContent = "The preserve and counterfactual statements must differ.";
      status.classList.add("bad");
      return;
    }
    if (!workerAvailable) {
      status.textContent = "Parallel workers are unavailable. Training failed closed.";
      status.classList.add("bad");
      return;
    }

    runButton.disabled = true;
    output.hidden = true;
    status.classList.remove("bad");
    status.textContent = "Hashing inputs and dispatching three isolated training lanes...";

    try {
      const config = {
        evidence: Number(document.querySelector("#frontier-evidence").value),
        abstain: Number(document.querySelector("#frontier-abstain").value),
        stability: Number(document.querySelector("#frontier-stability").value),
        epochs: Number(document.querySelector("#frontier-epochs").value),
      };
      const inputEnvelope = JSON.stringify({ preserve, counterfactual, config });
      const inputHash = await sha256(inputEnvelope);
      const seed = Number.parseInt(inputHash.slice(0, 8), 16) >>> 0;
      const dataset = makeDataset(preserve, counterfactual, seed);
      const results = await Promise.all(
        LANES.map((lane) =>
          runWorker(lane, {
            trainRows: dataset.trainRows,
            testRows: dataset.testRows,
            config,
            seed,
          }),
        ),
      );
      results.sort((left, right) => right.reward - left.reward || left.id.localeCompare(right.id));
      const winner = results[0];
      const deterministicCore = {
        schema: "szl.counterfactual-training.v1",
        status: "MEASURED_LOCAL",
        scope: "deterministic binary nano-policy training; not an LLM fine-tune",
        input_sha256: inputHash,
        seed,
        training: {
          algorithm: "weighted logistic SGD",
          lanes: LANES.length,
          train_rows: dataset.trainRows.length,
          held_out_rows: dataset.testRows.length,
          feature_dimensions: dataset.trainRows[0].x.length,
          epochs: config.epochs,
          reward_weights: {
            evidence: config.evidence,
            abstain: config.abstain,
            stability: config.stability,
          },
        },
        winner: winner.id,
        candidates: results.map(compactResult),
        limitations: [
          "Synthetic features are derived from the two user-authored behavior statements.",
          "Scores do not measure a foundation model or production agent.",
          "WebGPU detection is reported but training uses CPU Web Workers.",
        ],
      };
      const trainingDigest = await sha256(JSON.stringify(deterministicCore));
      const receipt = {
        ...deterministicCore,
        training_sha256: trainingDigest,
        runtime: {
          engine: "browser-web-workers",
          worker_count: LANES.length,
          webgpu_available: webgpuAvailable,
          hardware_concurrency_reported: navigator.hardwareConcurrency || null,
          network_upload: false,
        },
      };
      receipt.receipt_sha256 = await sha256(JSON.stringify(receipt));
      latestReceipt = JSON.stringify(receipt, null, 2);
      renderResults(output, results, winner, receipt);
      status.textContent = "MEASURED_LOCAL. Three lanes completed; receipt " + receipt.receipt_sha256.slice(0, 12) + ".";
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "Frontier training failed closed.";
      status.classList.add("bad");
    } finally {
      runButton.disabled = false;
    }
  });
}
