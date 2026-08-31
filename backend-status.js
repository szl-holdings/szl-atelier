const STYLE_ID = "szl-runtime-witness-style";
const WITNESS_ID = "szl-runtime-witness";

function installStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    #${WITNESS_ID} {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 40;
      display: grid;
      grid-template-columns: 8px auto;
      align-items: center;
      gap: 9px;
      min-height: 36px;
      padding: 8px 12px;
      border: 1px solid rgba(199, 164, 77, 0.45);
      border-radius: 999px;
      background: rgba(12, 14, 13, 0.92);
      color: #f3ead0;
      box-shadow: 0 12px 38px rgba(0, 0, 0, 0.28);
      font: 700 10px/1.2 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      letter-spacing: 0.09em;
      text-decoration: none;
      text-transform: uppercase;
      backdrop-filter: blur(12px);
    }
    #${WITNESS_ID}::before {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #8d8a80;
      content: "";
      box-shadow: 0 0 0 4px rgba(141, 138, 128, 0.12);
    }
    #${WITNESS_ID}[data-state="ready"]::before {
      background: #d7b65c;
      box-shadow: 0 0 0 4px rgba(215, 182, 92, 0.14);
    }
    #${WITNESS_ID}[data-state="unavailable"] {
      border-color: rgba(196, 92, 76, 0.55);
      color: #f2c1b8;
    }
    #${WITNESS_ID}[data-state="unavailable"]::before {
      background: #c45c4c;
      box-shadow: 0 0 0 4px rgba(196, 92, 76, 0.14);
    }
    #${WITNESS_ID}:focus-visible {
      outline: 2px solid #d7b65c;
      outline-offset: 3px;
    }
    @media (max-width: 640px) {
      #${WITNESS_ID} {
        right: 10px;
        bottom: 10px;
        max-width: calc(100vw - 20px);
      }
    }
  `;
  document.head.append(style);
}

function mountWitness() {
  const existing = document.getElementById(WITNESS_ID);
  if (existing) return existing;
  const witness = document.createElement("a");
  witness.id = WITNESS_ID;
  witness.href = "/api/build-info";
  witness.target = "_blank";
  witness.rel = "noreferrer";
  witness.dataset.state = "checking";
  witness.setAttribute("aria-live", "polite");
  witness.textContent = "Python API checking";
  document.body.append(witness);
  return witness;
}

async function readJson(path) {
  const response = await fetch(path, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

async function witnessRuntime() {
  installStyle();
  const witness = mountWitness();
  try {
    const [health, readiness, build] = await Promise.all([
      readJson("/healthz"),
      readJson("/readyz"),
      readJson("/api/build-info"),
    ]);
    if (health.status !== "ok" || readiness.status !== "ready") {
      throw new Error("runtime contract did not report ready");
    }
    const records = Number(readiness.catalog_records || 0);
    const digest = String(build.release_manifest_sha256 || "unavailable").slice(0, 12);
    witness.dataset.state = "ready";
    witness.textContent = `Python ready · ${records} models`;
    witness.title = `FastAPI runtime observed. Release manifest SHA-256: ${digest}`;
  } catch (error) {
    witness.dataset.state = "unavailable";
    witness.textContent = "Python API unavailable";
    witness.title = error instanceof Error ? error.message : "Runtime check failed";
  }
}

void witnessRuntime();

