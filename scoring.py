"""
scoring.py - Score and Decision Logic for PotholeVerify
Aggregates points from heuristic checks, applies AI-detection penalties,
and assigns the final verification decision.

REDESIGNED SCORING: Pixel-level analysis is the core (75 pts max),
metadata (EXIF/GPS/timestamp) is a bonus (+25 pts max). This ensures
internet-downloaded images with stripped metadata can still pass if
they look like genuine, unedited photos.
"""

# ==========================================
# CONFIGURATION: Weights & Thresholds
# ==========================================

# --- METADATA BONUS (available when EXIF is present) ---
WEIGHT_CAMERA_EXIF = 10    # Bonus for genuine camera Make/Model
WEIGHT_GPS = 10            # Bonus for EXIF GPS match within 500m
WEIGHT_FRESHNESS = 5       # Bonus for capture timestamp within 48h
# Metadata subtotal: 25 pts max (bonus, not required)

# --- PIXEL-LEVEL CORE (works on ANY image) ---
WEIGHT_DUPLICATE = 15      # Points for no perceptual hash duplicate match
WEIGHT_ELA = 20            # Points for consistent Error Level Analysis
WEIGHT_NOISE = 20          # Points for uniform noise profile (no splicing)
WEIGHT_JPEG_QUALITY = 15   # Points for single-compression (no re-save)
WEIGHT_DIMENSIONS = 10     # Points for non-AI-typical resolution
# Pixel subtotal: 80 pts max (but we target 75 effective for real photos)

TOTAL_MAX_POINTS = 100     # Overall cap

# AI Generation Penalty
PENALTY_AI_TAG = -50       # Applied if AI keywords found in metadata

# Decision Thresholds (lowered since metadata is now bonus, not core)
THRESHOLD_ACCEPT = 60      # Score >= 60 -> Accept
THRESHOLD_REVIEW = 35      # Score 35-59 -> Review
                           # Score < 35  -> Reject

# Decision Labels
DECISION_ACCEPT = "Accept"
DECISION_REVIEW = "Review"
DECISION_REJECT = "Reject"


def compute_final_decision(checks: list[dict], ai_tag_found: bool) -> dict:
    """
    Compute total verification score and resulting decision.

    Parameters:
        checks: List of dicts representing each check result:
                [
                    {
                        "name": str,
                        "passed": bool | None,
                        "points": float | int,
                        "max_points": int,
                        "reason": str
                    },
                    ...
                ]
        ai_tag_found: Boolean flag indicating if AI generative signatures were detected.

    Returns:
        dict containing:
            - score: Clamped score [0, 100]
            - raw_score: Unclamped score including penalties
            - max_score: 100
            - decision: 'Accept' | 'Review' | 'Reject'
            - ai_tag_found: bool
            - checks: list of check summaries
    """
    raw_score = sum(c["points"] for c in checks)

    # Ensure final score is clamped between 0 and 100
    final_score = max(0, min(TOTAL_MAX_POINTS, raw_score))

    # Hard rule: If AI generation tag is found, reject immediately
    if ai_tag_found:
        decision = DECISION_REJECT
    elif final_score >= THRESHOLD_ACCEPT:
        decision = DECISION_ACCEPT
    elif final_score >= THRESHOLD_REVIEW:
        decision = DECISION_REVIEW
    else:
        decision = DECISION_REJECT

    return {
        "score": final_score,
        "raw_score": raw_score,
        "max_score": TOTAL_MAX_POINTS,
        "decision": decision,
        "ai_tag_found": ai_tag_found,
        "checks": checks,
    }


def get_decision_badge_html(decision: str) -> str:
    """Return an HTML badge corresponding to the decision."""
    color_map = {
        DECISION_ACCEPT: ("#166534", "#dcfce7", "#22c55e"),  # Green text, bg, border
        DECISION_REVIEW: ("#854d0e", "#fef9c3", "#eab308"),  # Yellow/Orange text, bg, border
        DECISION_REJECT: ("#991b1b", "#fee2e2", "#ef4444"),  # Red text, bg, border
    }
    text_color, bg_color, border_color = color_map.get(
        decision, ("#1f2937", "#f3f4f6", "#9ca3af")
    )

    return (
        f'<span style="'
        f'display: inline-block; '
        f'padding: 6px 16px; '
        f'font-size: 1.1rem; '
        f'font-weight: 700; '
        f'letter-spacing: 0.05em; '
        f'color: {text_color}; '
        f'background-color: {bg_color}; '
        f'border: 2px solid {border_color}; '
        f'border-radius: 9999px;'
        f'">{decision.upper()}</span>'
    )
