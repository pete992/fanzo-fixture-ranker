"""
app.py
======
Flask web application for the FANZO Fixture Interest Ranker.

Routes:
    GET  /       — Serves the main single-page UI
    POST /run    — Runs the full pipeline and returns ranked fixtures as JSON
"""

import logging
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, jsonify, request

from scraper import fetch_fanzo_fixtures
from scorer import rank_fixtures
from enrichment import fetch_all_standings

# Configure logging so errors appear in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run():
    """
    Trigger the full ranking pipeline:
      1. Scrape FANZO for next 7 days of UK-televised fixtures
      2. Score each fixture across six factors
      3. Return the top 20 ranked fixtures as JSON

    Returns:
        200  { "fixtures": [ ... ] }   — success
        500  { "error": "..." }        — scraping or scoring failure
    """
    logger.info("Pipeline triggered")

    try:
        # Step 1: Fetch fixtures from FANZO
        fixtures = fetch_fanzo_fixtures()

        if not fixtures:
            return jsonify({
                "error": "No fixtures found for the next 7 days. "
                         "FANZO may be unavailable or have no upcoming fixtures listed."
            }), 500

        logger.info("Fetched %d fixtures, now scoring...", len(fixtures))

        # Step 2: Fetch live league standings for dynamic match stakes scoring.
        # This is best-effort — if it fails, scoring falls back to keyword inference.
        try:
            standings = fetch_all_standings()
            logger.info("Fetched live standings for %d teams", len(standings))
        except Exception as exc:
            logger.warning("Standings fetch failed, using keyword stakes fallback: %s", exc)
            standings = {}

        # Step 3: Score and rank
        ranked = rank_fixtures(fixtures, top_n=20, standings=standings)

        # Step 3: Serialise for JSON
        # datetime objects are not JSON-serialisable, so we format them as strings
        output = []
        for fixture in ranked:
            kickoff_dt = fixture["kickoff"]
            output.append({
                "rank":            fixture["rank"],
                "name":            fixture["name"],
                "home_team":       fixture["home_team"],
                "away_team":       fixture["away_team"],
                "competition":     fixture["competition"],
                "sport":           fixture["sport"],
                # Two formats: one for display, one for CSV export
                "kickoff_display": kickoff_dt.strftime("%-d %b %Y, %H:%M") + " UK",
                "kickoff_iso":     kickoff_dt.isoformat(),
                "channels":        fixture["channels"],
                "composite_score": fixture["composite_score"],
                "sub_scores":      fixture["sub_scores"],
                "rationale":       fixture["rationale"],
                "fanzo_url":       fixture.get("fanzo_url", ""),
            })

        logger.info("Returning %d ranked fixtures", len(output))
        return jsonify({"fixtures": output})

    except Exception as exc:
        logger.exception("Pipeline failed")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    # Run in debug mode when executed directly (not via a production server)
    app.run(debug=True, host="0.0.0.0", port=5000)
