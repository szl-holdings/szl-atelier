"use strict";

const capabilityState = {
  items: [],
  audience: "all",
};

const capabilityRoot = document.querySelector("#capability-fabric");
const capabilityGrid = document.querySelector("#capability-grid");
const capabilityStatus = document.querySelector("#capability-state");
const capabilityFilters = document.querySelector("#capability-filters");
const SOURCE_PREFIX = "https://github.com/szl-holdings/";

function capabilityText(value) {
  return document.createTextNode(String(value ?? "UNAVAILABLE"));
}

function capabilityElement(tag, options = {}) {
  const element = document.createElement(tag);
  if (options.className) element.className = options.className;
  if (options.text !== undefined) element.append(capabilityText(options.text));
  return element;
}

function safeSourceUrl(value) {
  if (typeof value !== "string" || !value.startsWith(SOURCE_PREFIX)) return null;
  try {
    const url = new URL(value);
    if (
      url.protocol !== "https:" ||
      url.hostname !== "github.com" ||
      url.username ||
      url.password ||
      !url.pathname.startsWith("/szl-holdings/")
    ) {
      return null;
    }
    return url.href;
  } catch (_error) {
    return null;
  }
}

function stateChip(value, measured = false) {
  const chip = capabilityElement("span", {
    className: `state-chip${measured ? " measured" : ""}`,
    text: value,
  });
  return chip;
}

function listBlock(title, values) {
  const wrapper = capabilityElement("section");
  const heading = capabilityElement("h4", { text: title });
  const list = capabilityElement("ul");
  const rows = Array.isArray(values) ? values : [];
  for (const value of rows) {
    const item = capabilityElement("li", { text: value });
    list.append(item);
  }
  if (!rows.length) list.append(capabilityElement("li", { text: "UNAVAILABLE" }));
  wrapper.append(heading, list);
  return wrapper;
}

function capabilityCard(item) {
  const card = capabilityElement("article", { className: "capability-card" });
  card.tabIndex = 0;
  card.dataset.audiences = Array.isArray(item.audiences)
    ? item.audiences.join(" ")
    : "";

  const header = capabilityElement("header");
  const titleWrap = capabilityElement("div");
  const category = capabilityElement("div", {
    className: "category",
    text: item.category,
  });
  const title = capabilityElement("h3", { text: item.name });
  titleWrap.append(category, title);
  const sourceState = stateChip(item.source_state, item.source_state === "MERGED");
  header.append(titleWrap, sourceState);

  const description = capabilityElement("p", { text: item.one_liner });
  const source = capabilityElement("code", {
    text: `${item.source_repository}@${String(item.introduced_revision || "UNAVAILABLE").slice(0, 12)}`,
  });

  const states = capabilityElement("div", { className: "card-row" });
  states.append(
    stateChip(item.commercial_role),
    stateChip(item.hub_publication_state),
    stateChip(item.runtime_state),
  );

  const details = capabilityElement("div", { className: "capability-details" });
  details.append(
    listBlock("Measured in source", item.measured_properties),
    listBlock("Excluded authority", item.excluded_authority),
    listBlock("Source API", item.api),
  );

  const actions = capabilityElement("div", { className: "card-row" });
  const sourceUrl = safeSourceUrl(item.source_url);
  if (sourceUrl) {
    const link = capabilityElement("a", { text: "Inspect exact source" });
    link.href = sourceUrl;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    actions.append(link);
  } else {
    actions.append(stateChip("SOURCE_LINK_UNAVAILABLE"));
  }
  const proof = capabilityElement("span", {
    className: "state-chip",
    text: `PR #${item.source_pull_request ?? "UNAVAILABLE"}`,
  });
  actions.append(proof);

  card.append(header, description, source, states, details, actions);
  return card;
}

function renderCapabilities() {
  if (!capabilityGrid) return;
  capabilityGrid.replaceChildren();
  const visible = capabilityState.items.filter((item) => {
    if (capabilityState.audience === "all") return true;
    return Array.isArray(item.audiences) && item.audiences.includes(capabilityState.audience);
  });
  if (!visible.length) {
    capabilityGrid.append(
      capabilityElement("p", {
        className: "fabric-empty",
        text: "No source-owned capability matches this audience.",
      }),
    );
    return;
  }
  for (const item of visible) capabilityGrid.append(capabilityCard(item));
}

function bindCapabilityFilters() {
  if (!capabilityFilters) return;
  capabilityFilters.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-audience]");
    if (!button || !capabilityFilters.contains(button)) return;
    const audience = button.dataset.audience;
    const allowed = new Set(["all", "operator", "developer", "investor", "researcher"]);
    if (!allowed.has(audience)) return;
    capabilityState.audience = audience;
    capabilityFilters.querySelectorAll("button[data-audience]").forEach((row) => {
      row.setAttribute("aria-pressed", String(row === button));
    });
    renderCapabilities();
  });
}

function validateCapabilityPayload(payload) {
  if (!payload || payload.schema !== "szl.atelier.capability-fabric/v1") {
    throw new Error("CAPABILITY_SCHEMA_MISMATCH");
  }
  if (!Array.isArray(payload.items) || payload.items.length !== 2) {
    throw new Error("CAPABILITY_COUNT_MISMATCH");
  }
  const seen = new Set();
  for (const item of payload.items) {
    if (!item || typeof item.slug !== "string" || seen.has(item.slug)) {
      throw new Error("CAPABILITY_IDENTITY_INVALID");
    }
    seen.add(item.slug);
    if (item.source_state !== "MERGED") throw new Error("SOURCE_STATE_UNVERIFIED");
    if (!/^[0-9a-f]{40}$/.test(String(item.introduced_revision || ""))) {
      throw new Error("SOURCE_REVISION_INVALID");
    }
    if (!String(item.hub_publication_state || "").startsWith("UNAVAILABLE_")) {
      throw new Error("HUB_STATE_OVERCLAIM");
    }
    if (!String(item.runtime_state || "").startsWith("UNAVAILABLE_")) {
      throw new Error("RUNTIME_STATE_OVERCLAIM");
    }
  }
  return payload.items;
}

async function loadCapabilityFabric() {
  if (!capabilityRoot || !capabilityGrid || !capabilityStatus) return;
  capabilityStatus.textContent = "Reading exact source receipts";
  try {
    const response = await fetch("/api/capabilities", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`CAPABILITY_HTTP_${response.status}`);
    const payload = await response.json();
    capabilityState.items = validateCapabilityPayload(payload);
    renderCapabilities();
    capabilityStatus.textContent = `${capabilityState.items.length} source-owned capabilities`;
    capabilityStatus.dataset.state = "ready";
  } catch (error) {
    capabilityStatus.textContent = "Capability evidence unavailable";
    capabilityStatus.dataset.state = "error";
    capabilityGrid.replaceChildren(
      capabilityElement("p", {
        className: "fabric-empty",
        text: `Fail closed: ${String(error.message || error)}`,
      }),
    );
  }
}

bindCapabilityFilters();
loadCapabilityFabric();
