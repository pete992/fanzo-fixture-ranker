/**
 * script.js
 * =========
 * Handles all interactivity for the FANZO Fixture Ranker.
 *
 * Responsibilities:
 *   - Triggering the /run pipeline via fetch()
 *   - Rendering the ranked fixture table
 *   - Toggling the score breakdown rows
 *   - Exporting the results as a CSV file
 */

// The current ranked fixture data — populated after a successful run.
let currentFixtures = [];

// ── Human-readable labels for each sub-score factor ──────────────────────────
const FACTOR_LABELS = {
  competition_tier: "Competition Tier",
  match_stakes:     "Match Stakes",
  derby_rivalry:    "Derby / Rivalry",
  team_popularity:  "Team Popularity",
  kickoff_time:     "Kick-off Time",
  betting_volume:   "Betting Volume",
};

// The weight each factor carries in the composite score (for display only)
const FACTOR_WEIGHTS = {
  competition_tier: "25%",
  match_stakes:     "20%",
  derby_rivalry:    "15%",
  team_popularity:  "15%",
  kickoff_time:     "15%",
  betting_volume:   "10%",
};


// ── Pipeline ──────────────────────────────────────────────────────────────────

/**
 * Called when the user clicks "Run".
 * POSTs to /run, shows a loading state, then renders results.
 */
async function runPipeline() {
  // Reset UI state
  showStatus("Fetching fixtures from FANZO…");
  hideError();
  hideResults();
  setRunButtonState("loading");
  disableExport();

  try {
    const response = await fetch("/run", { method: "POST" });
    const data = await response.json();

    if (!response.ok || data.error) {
      throw new Error(data.error || "Unexpected server error.");
    }

    currentFixtures = data.fixtures;
    hideStatus();
    renderResults(currentFixtures);

  } catch (err) {
    hideStatus();
    showError(err.message);
    setRunButtonState("ready");
  }
}


// ── Rendering ─────────────────────────────────────────────────────────────────

/**
 * Render the ranked fixture list into the table.
 */
function renderResults(fixtures) {
  const tbody = document.getElementById("fixture-tbody");
  tbody.innerHTML = "";

  if (!fixtures || fixtures.length === 0) {
    document.getElementById("empty-area").classList.remove("hidden");
    setRunButtonState("ready");
    return;
  }

  fixtures.forEach((fixture) => {
    // ── Main fixture row ──────────────────────────────────────────────────
    const row = document.createElement("tr");
    row.className = "fixture-row" + (fixture.rank <= 3 ? " rank-top" : "");
    row.dataset.rank = fixture.rank;
    row.setAttribute("aria-expanded", "false");
    row.onclick = () => toggleBreakdown(fixture.rank);

    // Channels HTML
    const channelHtml = fixture.channels.length
      ? fixture.channels
          .map((ch) => `<span class="channel-badge">${escapeHtml(ch)}</span>`)
          .join("")
      : '<span class="channel-badge">TBC</span>';

    row.innerHTML = `
      <td class="col-rank">
        <span class="rank-num">${fixture.rank}</span>
      </td>
      <td class="col-fixture">
        <span class="fixture-name">${escapeHtml(fixture.name)}</span>
        <span class="fixture-rationale">${escapeHtml(fixture.rationale)}</span>
      </td>
      <td class="col-competition">
        <span class="competition-name">${escapeHtml(fixture.competition)}</span>
      </td>
      <td class="col-kickoff">
        <span class="kickoff-time">${escapeHtml(fixture.kickoff_display)}</span>
      </td>
      <td class="col-channels">
        <div class="channel-list">${channelHtml}</div>
      </td>
      <td class="col-score">
        <span class="score-pill">
          ${fixture.composite_score}
          <span class="score-max">/100</span>
        </span>
      </td>
    `;

    tbody.appendChild(row);

    // ── Breakdown row (hidden by default) ─────────────────────────────────
    const breakdownRow = document.createElement("tr");
    breakdownRow.className = "breakdown-row hidden";
    breakdownRow.id = `breakdown-${fixture.rank}`;

    const factorsHtml = Object.entries(fixture.sub_scores)
      .map(([key, value]) => `
        <div class="breakdown-factor">
          <span class="factor-label">${FACTOR_LABELS[key] || key}</span>
          <div class="factor-bar-wrap">
            <div class="factor-bar" style="width: ${value}%"></div>
          </div>
          <span class="factor-score">${value}</span>
          <span class="factor-weight">· ${FACTOR_WEIGHTS[key] || ""} weight</span>
        </div>
      `)
      .join("");

    breakdownRow.innerHTML = `
      <td colspan="6">
        <div class="breakdown-inner">${factorsHtml}</div>
      </td>
    `;

    tbody.appendChild(breakdownRow);
  });

  // Show the results section
  document.getElementById("results-count").textContent =
    `Showing ${fixtures.length} fixtures`;
  document.getElementById("results-area").classList.remove("hidden");
  setRunButtonState("ready");
  enableExport();
}


/**
 * Toggle the score breakdown row for a given fixture rank.
 */
function toggleBreakdown(rank) {
  const breakdownRow = document.getElementById(`breakdown-${rank}`);
  const fixtureRow = document.querySelector(`.fixture-row[data-rank="${rank}"]`);

  if (!breakdownRow || !fixtureRow) return;

  const isOpen = !breakdownRow.classList.contains("hidden");

  if (isOpen) {
    breakdownRow.classList.add("hidden");
    fixtureRow.classList.remove("is-open");
    fixtureRow.setAttribute("aria-expanded", "false");
  } else {
    breakdownRow.classList.remove("hidden");
    fixtureRow.classList.add("is-open");
    fixtureRow.setAttribute("aria-expanded", "true");
  }
}


// ── CSV Export ────────────────────────────────────────────────────────────────

/**
 * Export the current ranked list as a CSV file.
 * The file is generated entirely client-side — no extra server round-trip needed.
 */
function exportCSV() {
  if (!currentFixtures || currentFixtures.length === 0) return;

  const headers = [
    "Rank",
    "Name",
    "Home Team",
    "Away Team",
    "Competition",
    "Sport",
    "Kick-off (UK)",
    "Channels",
    "Composite Score",
    "Competition Tier",
    "Match Stakes",
    "Derby / Rivalry",
    "Team Popularity",
    "Kick-off Time",
    "Betting Volume",
    "Rationale",
    "FANZO URL",
  ];

  const rows = currentFixtures.map((f) => [
    f.rank,
    f.name,
    f.home_team,
    f.away_team,
    f.competition,
    f.sport,
    f.kickoff_display,
    f.channels.join(" / "),
    f.composite_score,
    f.sub_scores.competition_tier,
    f.sub_scores.match_stakes,
    f.sub_scores.derby_rivalry,
    f.sub_scores.team_popularity,
    f.sub_scores.kickoff_time,
    f.sub_scores.betting_volume,
    f.rationale,
    f.fanzo_url,
  ]);

  const csvContent = [headers, ...rows]
    .map((row) =>
      row
        .map((cell) => {
          const str = String(cell ?? "");
          // Wrap in quotes if the value contains a comma, quote, or newline
          return str.includes(",") || str.includes('"') || str.includes("\n")
            ? `"${str.replace(/"/g, '""')}"`
            : str;
        })
        .join(",")
    )
    .join("\n");

  // Create a temporary link and trigger a download
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const timestamp = new Date().toISOString().slice(0, 10); // e.g. 2026-03-17
  link.href = url;
  link.download = `fanzo-fixtures-${timestamp}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}


// ── UI state helpers ──────────────────────────────────────────────────────────

function showStatus(message) {
  document.getElementById("status-text").textContent = message;
  document.getElementById("status-area").classList.remove("hidden");
}

function hideStatus() {
  document.getElementById("status-area").classList.add("hidden");
}

function showError(message) {
  document.getElementById("error-text").textContent = message;
  document.getElementById("error-area").classList.remove("hidden");
}

function hideError() {
  document.getElementById("error-area").classList.add("hidden");
}

function hideResults() {
  document.getElementById("results-area").classList.add("hidden");
  document.getElementById("empty-area").classList.add("hidden");
}

function setRunButtonState(state) {
  const btn = document.getElementById("run-btn");
  if (state === "loading") {
    btn.textContent = "Running…";
    btn.disabled = true;
  } else {
    btn.textContent = "Run";
    btn.disabled = false;
  }
}

function enableExport() {
  document.getElementById("export-btn").disabled = false;
}

function disableExport() {
  document.getElementById("export-btn").disabled = true;
}

/** Prevent XSS by escaping HTML special characters before inserting into the DOM. */
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
