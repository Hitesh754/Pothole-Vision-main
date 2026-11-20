"""
app.py - Streamlit UI for PotholeVerify
A lightweight verification MVP that evaluates whether an uploaded pothole photo
is a genuine, real-camera photo (and not AI-generated, duplicated, or spliced).

REDESIGNED: Pixel-level analysis is the core scoring mechanism. EXIF metadata
is treated as bonus points, so images downloaded from the internet (with
stripped metadata) can still pass if they look like genuine, unedited photos.
"""

import os
import io
import time
import uuid
import streamlit as st
import pandas as pd
from PIL import Image

import checks
import scoring
import db

# ==========================================
# Page Configuration & Styling
# ==========================================
st.set_page_config(
    page_title="PotholeVerify - Photo Authenticity MVP",
    page_icon="🕳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for crisp, readable UI
st.markdown(
    """
    <style>
    .check-pass { color: #166534; font-weight: 600; }
    .check-fail { color: #991b1b; font-weight: 600; }
    .check-unknown { color: #854d0e; font-weight: 600; }
    .stTable td { vertical-align: middle; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize database tables on startup
db.init_db()

# ==========================================
# Sidebar: Information & Prototype Notice
# ==========================================
with st.sidebar:
    st.title("🕳️ PotholeVerify")
    st.caption("College Project MVP • Photo Authenticity Verifier")

    st.warning("⚠️ **Heuristic prototype, not 100% accurate.**")

    st.markdown("---")
    st.markdown("### 🔬 Pixel Analysis (Core)")
    st.markdown(
        f"""
        - **ELA**: Compression consistency (+{scoring.WEIGHT_ELA})
        - **Noise Uniformity**: Splice detection (+{scoring.WEIGHT_NOISE})
        - **JPEG Quality**: Double-compression check (+{scoring.WEIGHT_JPEG_QUALITY})
        - **Duplicate (pHash)**: Reuse detection (+{scoring.WEIGHT_DUPLICATE})
        - **Dimensions**: AI-resolution check (+{scoring.WEIGHT_DIMENSIONS})
        """
    )

    st.markdown("### 📎 Metadata Bonus")
    st.markdown(
        f"""
        - **Camera EXIF**: Make/Model (+{scoring.WEIGHT_CAMERA_EXIF})
        - **GPS Match**: Within 500m (+{scoring.WEIGHT_GPS})
        - **Freshness**: Within 48h (+{scoring.WEIGHT_FRESHNESS})
        
        *Missing metadata = 0 bonus, **not** a penalty.*
        """
    )

    st.markdown("---")
    st.markdown("### 🎯 Decision Boundaries")
    st.markdown(
        f"""
        - 🟢 **Accept**: Score ≥ {scoring.THRESHOLD_ACCEPT}
        - 🟡 **Review**: Score {scoring.THRESHOLD_REVIEW} – {scoring.THRESHOLD_ACCEPT - 1}
        - 🔴 **Reject**: Score < {scoring.THRESHOLD_REVIEW} (or AI tag detected)
        """
    )
    st.markdown(
        "*AI signatures (Midjourney, DALL-E, etc.) trigger an immediate **Reject** regardless of score.*"
    )


# ==========================================
# Main Interface: Tabs
# ==========================================
tab_submit, tab_admin = st.tabs(["📤 Submit Report", "🛡️ Admin Review"])

# ------------------------------------------
# TAB 1: Submit Report
# ------------------------------------------
with tab_submit:
    st.subheader("Submit Pothole Verification Report")
    st.write(
        "Upload a road photo to verify its authenticity. "
        "Works with **any image** — web downloads, screenshots, or direct camera photos."
    )

    col_input1, col_input2 = st.columns([1.2, 1])

    with col_input1:
        uploaded_file = st.file_uploader(
            "Choose a Pothole Photo (JPEG or PNG)",
            type=["jpg", "jpeg", "png"],
            help="Upload any image. Photos with original camera EXIF get bonus points, "
                 "but pixel-level analysis works on all images.",
        )

    with col_input2:
        st.write("📍 **Reported Incident Location** (for GPS bonus)")
        lat_col, lon_col = st.columns(2)
        with lat_col:
            user_lat = st.number_input(
                "Latitude",
                value=12.971600,
                format="%.6f",
                step=0.000100,
                help="Decimal degrees (e.g., 12.971600)",
            )
        with lon_col:
            user_lon = st.number_input(
                "Longitude",
                value=77.594600,
                format="%.6f",
                step=0.000100,
                help="Decimal degrees (e.g., 77.594600)",
            )

    submit_button = st.button(
        "🔍 Analyze & Verify Image", type="primary", use_container_width=True
    )

    if submit_button:
        if not uploaded_file:
            st.error("Please upload an image before submitting.")
        else:
            with st.spinner("Running pixel forensics, metadata scan, and duplicate check..."):
                # Always read original unresized bytes
                image_bytes = uploaded_file.getvalue()
                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                except Exception as e:
                    st.error(f"Failed to read image file: {e}")
                    st.stop()

                # Fetch active hashes for duplicate check
                known_hashes = db.get_known_hashes()

                # === METADATA BONUS CHECKS ===
                # Check 1: Camera EXIF & AI Generator tags
                c1_passed, c1_pts, c1_reason, ai_tag_found = checks.check_camera_exif(
                    image_bytes, pil_img
                )

                # Check 2: GPS Proximity (bonus)
                c2_passed, c2_pts, c2_reason = checks.check_gps(
                    image_bytes, pil_img, user_lat, user_lon
                )

                # Check 3: Freshness (bonus)
                c3_passed, c3_pts, c3_reason = checks.check_freshness(
                    image_bytes, pil_img
                )

                # === PIXEL-LEVEL CORE CHECKS ===
                # Check 4: Duplicate Check (pHash)
                c4_passed, c4_pts, c4_reason, phash_str = checks.check_duplicate(
                    pil_img, known_hashes
                )

                # Check 5: Error Level Analysis (ELA)
                c5_passed, c5_pts, c5_reason, ela_heatmap = checks.check_ela(pil_img)

                # Check 6: Noise Consistency Analysis (NEW)
                c6_passed, c6_pts, c6_reason = checks.check_noise_consistency(pil_img)

                # Check 7: JPEG Quality / Double-Compression (NEW)
                c7_passed, c7_pts, c7_reason = checks.check_jpeg_quality_consistency(
                    pil_img, image_bytes
                )

                # Check 8: AI-Typical Dimensions (NEW)
                c8_passed, c8_pts, c8_reason = checks.check_image_dimensions(pil_img)

                # Structure check results (pixel-level first, then metadata bonus)
                check_records = [
                    {
                        "name": "1. ELA (Compression)",
                        "passed": c5_passed,
                        "points": c5_pts,
                        "max_points": scoring.WEIGHT_ELA,
                        "reason": c5_reason,
                        "category": "pixel",
                    },
                    {
                        "name": "2. Noise Uniformity",
                        "passed": c6_passed,
                        "points": c6_pts,
                        "max_points": scoring.WEIGHT_NOISE,
                        "reason": c6_reason,
                        "category": "pixel",
                    },
                    {
                        "name": "3. JPEG Quality Check",
                        "passed": c7_passed,
                        "points": c7_pts,
                        "max_points": scoring.WEIGHT_JPEG_QUALITY,
                        "reason": c7_reason,
                        "category": "pixel",
                    },
                    {
                        "name": "4. Duplicate Check (pHash)",
                        "passed": c4_passed,
                        "points": c4_pts,
                        "max_points": scoring.WEIGHT_DUPLICATE,
                        "reason": c4_reason,
                        "category": "pixel",
                    },
                    {
                        "name": "5. Image Dimensions",
                        "passed": c8_passed,
                        "points": c8_pts,
                        "max_points": scoring.WEIGHT_DIMENSIONS,
                        "reason": c8_reason,
                        "category": "pixel",
                    },
                    {
                        "name": "6. Camera EXIF / AI Scan",
                        "passed": c1_passed,
                        "points": c1_pts,
                        "max_points": scoring.WEIGHT_CAMERA_EXIF,
                        "reason": c1_reason,
                        "category": "metadata",
                    },
                    {
                        "name": "7. GPS Proximity",
                        "passed": c2_passed,
                        "points": c2_pts,
                        "max_points": scoring.WEIGHT_GPS,
                        "reason": c2_reason,
                        "category": "metadata",
                    },
                    {
                        "name": "8. Freshness (48h)",
                        "passed": c3_passed,
                        "points": c3_pts,
                        "max_points": scoring.WEIGHT_FRESHNESS,
                        "reason": c3_reason,
                        "category": "metadata",
                    },
                ]

                # Compute final score and decision
                result = scoring.compute_final_decision(check_records, ai_tag_found)
                final_score = result["score"]
                decision = result["decision"]

                # Save file to uploads folder
                file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                if not file_ext:
                    file_ext = ".jpg"
                unique_filename = f"{uuid.uuid4().hex[:8]}_{int(time.time())}{file_ext}"
                saved_image_path = os.path.join(db.UPLOADS_DIR, unique_filename)

                with open(saved_image_path, "wb") as f:
                    f.write(image_bytes)

                # Store report in database
                report_id = db.save_report(
                    image_path=saved_image_path,
                    phash=phash_str,
                    lat=user_lat,
                    lon=user_lon,
                    score=final_score,
                    decision=decision,
                    reasons=check_records,
                )

            # --------------------------------------
            # Render Results
            # --------------------------------------
            st.markdown("---")
            st.subheader("Verification Results")

            # Top summary banner
            summary_col1, summary_col2, summary_col3 = st.columns([1, 1, 2])

            with summary_col1:
                st.metric(
                    label="Final Score",
                    value=f"{final_score:.0f} / {scoring.TOTAL_MAX_POINTS}",
                )

            with summary_col2:
                st.write("**Decision Status**")
                st.markdown(
                    scoring.get_decision_badge_html(decision), unsafe_allow_html=True
                )

            with summary_col3:
                if ai_tag_found:
                    st.error(
                        "🚨 **Hard Reject Rule**: Generative AI metadata keywords were detected in the file."
                    )
                elif decision == scoring.DECISION_ACCEPT:
                    st.success(
                        f"✅ Report meets authenticity criteria (Score ≥ {scoring.THRESHOLD_ACCEPT}). Stored as verified."
                    )
                elif decision == scoring.DECISION_REVIEW:
                    st.info(
                        f"⚠️ Moderate confidence (Score {scoring.THRESHOLD_REVIEW}–{scoring.THRESHOLD_ACCEPT-1}). Queued for manual admin review."
                    )
                else:
                    st.error(
                        f"❌ Authenticity checks failed (Score < {scoring.THRESHOLD_REVIEW}). Report rejected."
                    )

            # Table of individual checks — grouped
            st.markdown("### 🔬 Pixel-Level Analysis (Core)")

            pixel_rows = []
            metadata_rows = []
            for c in check_records:
                passed_val = c["passed"]
                if passed_val is True:
                    status_display = "✅ PASS"
                elif passed_val is False:
                    status_display = "❌ FAIL"
                else:
                    status_display = "⚠️ N/A"

                pts_display = f"{c['points']:+d} / {c['max_points']}" if c["points"] < 0 else f"{c['points']} / {c['max_points']}"

                row = {
                    "Check": c["name"],
                    "Status": status_display,
                    "Points": pts_display,
                    "Reason / Analysis": c["reason"],
                }

                if c.get("category") == "metadata":
                    metadata_rows.append(row)
                else:
                    pixel_rows.append(row)

            st.dataframe(
                pd.DataFrame(pixel_rows), use_container_width=True, hide_index=True
            )

            st.markdown("### 📎 Metadata Bonus Checks")
            st.caption("These provide bonus points when EXIF data is available. Missing metadata = 0 bonus, **not** a penalty.")
            st.dataframe(
                pd.DataFrame(metadata_rows), use_container_width=True, hide_index=True
            )

            # Side-by-side Image & ELA Heatmap
            st.markdown("### 🔬 Visual Error Level Analysis (ELA)")
            st.caption(
                "Original photo compared against re-saved JPEG (Quality 90) difference heatmap. "
                "Uniform darkness = consistent compression. Bright clusters = potential edits or splicing."
            )

            img_col1, img_col2 = st.columns(2)
            with img_col1:
                st.image(
                    pil_img,
                    caption="Original Uploaded Image",
                    use_container_width=True,
                )

            with img_col2:
                st.image(
                    ela_heatmap,
                    caption="Amplified ELA Heatmap (15x scale)",
                    use_container_width=True,
                )


# ------------------------------------------
# TAB 2: Admin Review
# ------------------------------------------
with tab_admin:
    st.subheader("Manual Review Queue")
    st.write(
        f"Inspect flagged reports that received a **Review** decision "
        f"(score between {scoring.THRESHOLD_REVIEW} and {scoring.THRESHOLD_ACCEPT - 1})."
    )

    # Fetch pending reviews from SQLite
    pending_items = db.get_pending_reviews()

    if not pending_items:
        st.success("🎉 No reports currently pending review. All clear!")
    else:
        st.info(f"📋 **{len(pending_items)} report(s)** awaiting manual approval.")

        for item in pending_items:
            item_id = item["id"]
            with st.expander(
                f"Report #{item_id} — Score: {item['score']:.0f}/100 — Submitted: {item['created_at'][:19]}",
                expanded=True,
            ):
                rev_col_img, rev_col_details = st.columns([1, 1.2])

                with rev_col_img:
                    if os.path.exists(item["image_path"]):
                        st.image(
                            item["image_path"],
                            caption=f"Report #{item_id} Photo",
                            use_container_width=True,
                        )
                    else:
                        st.warning("Original image file missing from server storage.")

                with rev_col_details:
                    st.markdown(
                        f"""
                        **Report ID:** `{item_id}`  
                        **Reported Location:** `{item['lat']:.6f}, {item['lon']:.6f}`  
                        **Perceptual Hash:** `{item['phash']}`  
                        **Score:** `{item['score']:.0f}/100`  
                        **Current Status:** `{item['decision']}`
                        """
                    )

                    st.markdown("**Check Breakdown:**")
                    for c in item["reasons"]:
                        status_icon = (
                            "✅"
                            if c["passed"] is True
                            else ("❌" if c["passed"] is False else "⚠️")
                        )
                        st.markdown(
                            f"- {status_icon} **{c['name']}** ({c['points']}/{c['max_points']} pts): *{c['reason']}*"
                        )

                    st.markdown("---")
                    btn_col1, btn_col2 = st.columns(2)

                    with btn_col1:
                        if st.button(
                            f"✅ Approve #{item_id}",
                            key=f"approve_{item_id}",
                            type="primary",
                            use_container_width=True,
                        ):
                            db.update_report_decision(item_id, scoring.DECISION_ACCEPT)
                            st.success(f"Report #{item_id} Approved successfully!")
                            time.sleep(0.5)
                            st.rerun()

                    with btn_col2:
                        if st.button(
                            f"❌ Reject #{item_id}",
                            key=f"reject_{item_id}",
                            use_container_width=True,
                        ):
                            db.update_report_decision(item_id, scoring.DECISION_REJECT)
                            st.warning(f"Report #{item_id} Rejected.")
                            time.sleep(0.5)
                            st.rerun()
