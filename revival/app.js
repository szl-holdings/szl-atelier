(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const state = { catalog: null, selected: null, view: "operator" };
  const accent = {
    atelier: "var(--atelier)",
    mesh: "var(--mesh)",
    router: "var(--router)",
    uds: "var(--uds)",
  };

  async function loadCatalog() {
    const response = await fetch("./catalog.json", {
      cache: "no-store",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`catalog HTTP ${response.status}`);
    const text = await response.text();
    if (new TextEncoder().encode(text).byteLength > 131072) {
      throw new Error("catalog exceeds byte limit");
    }
    const catalog = JSON.parse(text);
    if (catalog.schema !== "szl.archive-revival-showcase/v2") {
      throw new Error("unsupported catalog schema");
    }
    const hash = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(text),
    );
    const digest = [...new Uint8Array(hash)]
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
    return { catalog, digest };
  }

  function node(tag, className, value) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (value !== undefined) element.textContent = String(value);
    return element;
  }

  function sourceURL(repository) {
    return `https://github.com/${repository}`;
  }

  function prURL(reference) {
    const match = /^([^#]+)#([1-9][0-9]*)$/.exec(reference || "");
    return match ? `https://github.com/${match[1]}/pull/${match[2]}` : null;
  }

  function hubURL(target) {
    return target ? `https://huggingface.co/spaces/${target}` : null;
  }

  function viewCopy(item) {
    const presentations = (item.presentation_surfaces || []).join(" and ");
    if (state.view === "developer") {
      return `${item.repository} retains its own backend, tests, release history, and runtime identity. Atelier reads and presents the capability; it does not copy implementation authority.`;
    }
    if (state.view === "investor") {
      return `${item.role}. The estate preserves one source owner and ${item.standalone_hub_target ? "one canonical Space" : `shared presentation through ${presentations}`}, reducing product sprawl without discarding differentiated capability.`;
    }
    return `${item.role}. Source state is ${item.source_state}. Hub state is ${item.hub_publication_state}; runtime state is ${item.runtime_state}. Unknown provider evidence remains unavailable rather than inferred.`;
  }

  function renderMetrics() {
    const governance = state.catalog.governance;
    $("#restored-count").textContent = governance.restored_source_owners;
    $("#tombstone-count").textContent = governance.consolidation_tombstones;
    $("#history-count").textContent = governance.immutable_historical_records;
    $("#peer-count").textContent = state.catalog.presentation.new_peer_spaces_created ? "YES" : "0";
  }

  function renderSources() {
    const root = $("#source-list");
    root.replaceChildren();
    state.catalog.source_authorities.forEach((item, index) => {
      const button = node("button", "source-card");
      button.type = "button";
      button.dataset.id = item.id;
      button.style.setProperty("--card-accent", accent[item.accent] || "var(--accent)");
      button.setAttribute("role", "listitem");
      button.setAttribute("aria-current", state.selected === item.id ? "true" : "false");

      const top = node("div", "source-card-top");
      top.append(node("span", "capability", item.capability.replaceAll("_", " ")));
      top.append(node("span", "index", String(index + 1).padStart(2, "0")));
      button.append(top);

      const middle = node("div");
      middle.append(node("h3", "", item.id));
      middle.append(node("p", "", item.role));
      button.append(middle);

      const sourceState = node("div", "source-state");
      sourceState.append(node("span", "", item.standalone_hub_target ? "CANONICAL SPACE" : "COMPOSED SURFACE"));
      sourceState.append(node("b", "", "SOURCE ACTIVE"));
      button.append(sourceState);
      button.addEventListener("click", () => selectSource(item.id));
      root.append(button);
    });
  }

  function addLink(root, label, href) {
    const anchor = node("a", "", label);
    anchor.href = href;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    root.append(anchor);
  }

  function renderDetail(item) {
    $("#detail-title").textContent = item.id;
    const root = $("#source-detail");
    root.className = "source-detail";
    root.style.setProperty("--selected-accent", accent[item.accent] || "var(--accent)");
    root.replaceChildren();

    const meta = node("div", "detail-meta");
    const cells = [
      ["Capability", item.capability],
      ["Source state", item.source_state],
      ["Hub state", item.hub_publication_state],
      ["Runtime state", item.runtime_state],
    ];
    for (const [label, value] of cells) {
      const cell = node("div");
      cell.append(node("span", "", label));
      cell.append(node("strong", "", value));
      meta.append(cell);
    }
    root.append(meta);
    root.append(node("p", "detail-copy", viewCopy(item)));

    const links = node("div", "detail-links");
    addLink(links, "Source repository ↗", sourceURL(item.repository));
    const evidence = Array.isArray(item.source_merge_evidence)
      ? item.source_merge_evidence
      : [item.source_merge_evidence];
    evidence.filter(Boolean).forEach((reference) => {
      const url = prURL(reference);
      if (url) addLink(links, `${reference} ↗`, url);
    });
    const hub = hubURL(item.standalone_hub_target);
    if (hub) addLink(links, "Canonical Hub surface ↗", hub);
    root.append(links);

    const truth = node("div", "truth-box");
    truth.append(node("code", "", item.standalone_hub_target
      ? "SOURCE_ACTIVE ≠ HUB_PUBLISHED ≠ RUNTIME_READY ≠ EXACT_READBACK_VERIFIED"
      : "SOURCE_ACTIVE · PRESENTED_IN_ATELIER · NO_NEW_PEER_SPACE"));
    root.append(truth);
  }

  function selectSource(id) {
    const item = state.catalog.source_authorities.find((row) => row.id === id);
    if (!item) return;
    state.selected = id;
    renderSources();
    renderDetail(item);
  }

  function renderTruthLadder() {
    const root = $("#truth-ladder");
    root.replaceChildren();
    state.catalog.truth_ladder.forEach((label, index) => {
      const item = node("li");
      item.append(node("small", "", String(index + 1).padStart(2, "0")));
      item.append(node("strong", "", label));
      root.append(item);
    });
  }

  function renderHistory() {
    const root = $("#history-list");
    root.replaceChildren();
    state.catalog.historical_records.forEach((repository) => {
      root.append(node("span", "", repository));
    });
  }

  function setView(view) {
    if (!new Set(["operator", "developer", "investor"]).has(view)) return;
    state.view = view;
    document.querySelectorAll("[data-view]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.view === view));
    });
    if (state.selected) selectSource(state.selected);
  }

  async function initialize() {
    try {
      const { catalog, digest } = await loadCatalog();
      state.catalog = catalog;
      renderMetrics();
      renderSources();
      renderTruthLadder();
      renderHistory();
      $("#registry-state").textContent = "CATALOG · SOURCE BOUND";
      $("#catalog-receipt").textContent = `catalog sha256 ${digest.slice(0, 16)}…`;
      selectSource(catalog.source_authorities[0].id);
    } catch (error) {
      $("#registry-state").textContent = `CATALOG · UNAVAILABLE · ${error.message}`;
      $("#source-list").textContent = "Archive revival catalog unavailable.";
    }
  }

  $("#enter").addEventListener("click", () => {
    $("#constellation").scrollIntoView({
      behavior: reducedMotion.matches ? "auto" : "smooth",
      block: "start",
    });
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
  initialize();
})();
