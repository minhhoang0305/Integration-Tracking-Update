const state = { reviews: [], selected: null, detail: null };
const $ = (selector, root = document) => root.querySelector(selector);
const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" })[char]);
const severityClass = value => `severity-${String(value || "Unknown").toLowerCase()}`;
const statusClass = value => `status-${String(value || "").toLowerCase()}`;
const formatDate = value => value ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";

async function request(path, options) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.message || `Request failed (${response.status})`);
  return response.status === 204 ? null : response.json();
}

function filteredReviews() {
  const status = $("#status-filter").value;
  const severity = $("#severity-filter").value;
  return state.reviews.filter(item => (!status || item.proposal.status === status) && (!severity || item.proposal.impactSeverity === severity));
}

function renderList() {
  const list = $("#proposal-list"), items = filteredReviews();
  $("#list-state").textContent = items.length ? `${items.length} proposal${items.length === 1 ? "" : "s"}` : "No proposals match these filters.";
  list.innerHTML = items.map(({ proposal, affectedActionsCount, newActionsCount }) => `<button class="proposal ${proposal.id === state.selected ? "selected" : ""}" data-id="${proposal.id}"><span class="proposal-title"><span>${escapeHtml(proposal.provider)} / ${escapeHtml(proposal.integrationId)}</span><span class="badge ${severityClass(proposal.impactSeverity)}">${escapeHtml(proposal.impactSeverity)}</span></span><small class="${statusClass(proposal.status)}">${escapeHtml(proposal.status)} · ${affectedActionsCount} affected · ${newActionsCount} new</small><small>${formatDate(proposal.updatedAt)}</small></button>`).join("");
  list.querySelectorAll("[data-id]").forEach(button => button.addEventListener("click", () => selectProposal(button.dataset.id)));
}

async function loadReviews() {
  $("#list-state").textContent = "Loading proposals…";
  try { state.reviews = await request("/api/reviews"); renderList(); if (state.selected) await selectProposal(state.selected); }
  catch (error) { $("#list-state").textContent = `Could not load proposals: ${error.message}`; }
}

function table(actions) {
  if (!actions?.length) return `<p class="muted">No actions in this category.</p>`;
  return `<div class="table-wrap"><table><thead><tr><th>Action</th><th>Method</th><th>Endpoint</th><th>Impact</th><th>Severity</th><th>Evidence</th></tr></thead><tbody>${actions.map(action => `<tr><td>${escapeHtml(action.name)}</td><td>${escapeHtml(action.method)}</td><td><code>${escapeHtml(action.endpoint)}</code></td><td>${escapeHtml(action.impactType)}</td><td><span class="badge ${severityClass(action.severity)}">${escapeHtml(action.severity)}</span></td><td>${escapeHtml(action.evidenceStatus)}</td></tr>`).join("")}</tbody></table></div>`;
}

function pretty(value) { return value ? JSON.stringify(value, null, 2) : "No data available."; }
function card(title, content) { return `<article class="section-card"><h3>${title}</h3>${content}</article>`; }
function renderLineDiff(model) {
  if (!model?.hunks?.length) return "";
  const lines = model.hunks.flatMap(hunk => [{ kind: "hunk", text: `@@ -${hunk.oldStart},${hunk.oldCount} +${hunk.newStart},${hunk.newCount} @@` }, ...hunk.lines]);
  const unified = `<pre class="line-diff">${lines.map(line => line.kind === "hunk" ? escapeHtml(line.text) : `<span class="diff-${line.kind}">${escapeHtml(line.kind === "deleted" ? "-" : line.kind === "inserted" ? "+" : " ")}${String(line.oldLine || "").padStart(4)} ${String(line.newLine || "").padStart(4)} ${escapeHtml(line.text)}</span>`).join("\n")}</pre>`;
  const pairs = model.hunks.flatMap(hunk => hunk.lines).reduce((rows, line) => { if (line.kind === "unchanged") rows.push([line, line]); else if (line.kind === "deleted") { const previous = rows.at(-1); if (previous && previous[1] === null) previous[0] = line; else rows.push([line, null]); } else { const previous = rows.at(-1); if (previous && previous[0] === null) previous[1] = line; else rows.push([null, line]); } return rows; }, []);
  const sideBySide = `<div class="side-diff">${pairs.map(([oldLine, newLine]) => `<div class="diff-cell diff-${oldLine?.kind || "empty"}">${oldLine ? `${oldLine.oldLine} ${escapeHtml(oldLine.text)}` : ""}</div><div class="diff-cell diff-${newLine?.kind || "empty"}">${newLine ? `${newLine.newLine} ${escapeHtml(newLine.text)}` : ""}</div>`).join("")}</div>`;
  return `<div class="diff-toolbar"><button class="button secondary diff-mode active" data-diff-mode="unified">Unified</button><button class="button secondary diff-mode" data-diff-mode="side">Side-by-side</button></div><div data-diff-view="unified">${unified}</div><div data-diff-view="side" hidden>${sideBySide}</div>`;
}

function renderDetail() {
  const detail = $("#detail"), data = state.detail;
  if (!data) return;
  const root = $("#detail-template").content.firstElementChild.cloneNode(true);
  $("#provider", root).textContent = data.proposal.provider;
  $("#integration", root).textContent = data.proposal.integrationId;
  $("#proposal-status", root).innerHTML = `<span class="${statusClass(data.proposal.status)}">${escapeHtml(data.proposal.status)}</span> · Updated ${formatDate(data.proposal.updatedAt)}`;
  const impact = data.impact || {};
  $("#metrics", root).innerHTML = [[impact.overallSeverity || data.proposal.impactSeverity, "Overall severity"], [impact.affectedActions?.length || 0, "Affected actions"], [impact.newActions?.length || 0, "New actions"], [impact.integrationConfigChanges?.length || 0, "Config changes"]].map(([value, label]) => `<div class="metric"><strong>${escapeHtml(value)}</strong><span>${label}</span></div>`).join("");
  const canDecide = ["Pending", "NeedsReview"].includes(data.proposal.status);
  root.querySelectorAll("[data-action]").forEach(button => { button.disabled = !canDecide; button.addEventListener("click", () => openDecision(button.dataset.action)); });
  const panels = $("#panels", root);
  const resolution = data.evidence?.resolution;
  const source = resolution?.integration ? `Folder: ${resolution.integration.folder} · ${resolution.reason}` : resolution?.reason || "No resolution evidence available.";
  $("[data-panel=overview]", panels).innerHTML = card("Summary", `<p>${escapeHtml(data.evidence?.label || data.evidence?.summary || "Review the proposed manifest before applying a Git change.")}</p>`) + card("Integration resolution", `<p>${escapeHtml(source)}</p><pre>${escapeHtml(pretty(resolution))}</pre>`) + card("Configuration changes", table((impact.integrationConfigChanges || []).map(change => ({ name: change.property, method: "—", endpoint: change.reason, impactType: "ConfigChange", severity: change.severity, evidenceStatus: "Manifest" }))));
  $("[data-panel=impact]", panels).innerHTML = card("Affected existing actions", table(impact.affectedActions)) + card("New actions", table(impact.newActions));
  $("[data-panel=manifest]", panels).innerHTML = card("Diff", renderLineDiff(data.artifacts?.diffModel) || `<pre>${escapeHtml(data.artifacts?.diff || "No diff artifact available.")}</pre>`) + card("Current manifest", `<pre>${escapeHtml(pretty(data.originalManifest))}</pre>`) + card("Proposed manifest", `<pre>${escapeHtml(pretty(data.artifacts?.proposedManifest))}</pre>`);
  $("[data-panel=evidence]", panels).innerHTML = card("Evidence", `<pre>${escapeHtml(pretty(data.evidence))}</pre>`) + card("Changelog", `<pre>${escapeHtml(data.artifacts?.changelog || "No changelog artifact available.")}</pre>`);
  root.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => { root.querySelectorAll(".tab").forEach(item => item.classList.toggle("active", item === tab)); root.querySelectorAll("[data-panel]").forEach(panel => panel.hidden = panel.dataset.panel !== tab.dataset.tab); }));
  root.querySelectorAll("[data-diff-mode]").forEach(button => button.addEventListener("click", () => { const mode = button.dataset.diffMode; root.querySelectorAll(".diff-mode").forEach(item => item.classList.toggle("active", item === button)); root.querySelectorAll("[data-diff-view]").forEach(view => view.hidden = view.dataset.diffView !== mode); }));
  detail.replaceChildren(root);
}

async function selectProposal(id) {
  state.selected = id; renderList();
  $("#detail").innerHTML = `<div class="empty"><p>Loading proposal…</p></div>`;
  try { state.detail = await request(`/api/reviews/${encodeURIComponent(id)}`); renderDetail(); }
  catch (error) { $("#detail").innerHTML = `<div class="empty"><h2>Could not load proposal</h2><p>${escapeHtml(error.message)}</p></div>`; }
}

function openDecision(decision) {
  const dialog = $("#decision-dialog");
  $("#decision").value = decision; $("#decision-title").textContent = `${decision === "approve" ? "Approve" : "Reject"} proposal`; $("#decision-submit").textContent = decision === "approve" ? "Approve" : "Reject"; $("#decision-error").hidden = true; dialog.showModal();
}

$("#decision-form").addEventListener("submit", async event => {
  event.preventDefault(); const decision = $("#decision").value, error = $("#decision-error");
  try { await request(`/api/reviews/${encodeURIComponent(state.selected)}/${decision}`, { method: "POST", body: JSON.stringify({ adminIdentity: $("#admin-identity").value.trim(), note: $("#decision-note").value.trim() || null }) }); $("#decision-dialog").close(); await loadReviews(); }
  catch (exception) { error.textContent = exception.message; error.hidden = false; }
});
$("#decision-cancel").addEventListener("click", () => $("#decision-dialog").close());
$("#refresh").addEventListener("click", loadReviews); $("#status-filter").addEventListener("change", renderList); $("#severity-filter").addEventListener("change", renderList);
loadReviews();
