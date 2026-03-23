import streamlit as st
from PIL import Image
import io
import json
from agents.observer import run_observer
from agents.grader import run_grader
from utils.database import log_inspection, get_recent_inspections

# Page config
st.set_page_config(
    page_title="ReturnScan Inspector",
    page_icon="🔍",
    layout="wide"
)

# Header
st.title("ReturnScan Inspector")
st.caption("AI-powered returns grading — Observer → Grader pipeline")

# Layout: two columns
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Upload Item Photo")

    uploaded_file = st.file_uploader(
        "Take or upload a photo of the returned item",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded item", use_container_width=True)

        # Detect media type
        media_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp"
        }
        file_ext = uploaded_file.name.split(".")[-1].lower()
        media_type = media_type_map.get(file_ext, "image/jpeg")

        st.divider()

        # Run inspection button
        if st.button("Run Inspection", type="primary", use_container_width=True):

            # Reset image bytes for reading
            uploaded_file.seek(0)
            image_bytes = uploaded_file.read()

            # --- AGENT 1: OBSERVER ---
            with st.spinner("Agent 1 — Observer analyzing image..."):
                observer_result = run_observer(image_bytes, media_type)

            if not observer_result["success"]:
                st.error(f"Observer failed: {observer_result['error']}")
                st.stop()

            # --- AGENT 2: GRADER ---
            with st.spinner("Agent 2 — Grader applying adversarial review..."):
                grader_result = run_grader(observer_result["observer_output"])

            if not grader_result["success"]:
                st.error(f"Grader failed: {grader_result['error']}")
                st.stop()

            # --- LOG TO SUPABASE ---
            observer_output = observer_result["observer_output"]
            log_result = log_inspection(
                item_description=observer_output.get("product_type", "Unknown"),
                product_category=observer_output.get("product_category", "Unknown"),
                observer_output=observer_output,
                grade=grader_result["grade"],
                disposition=grader_result["disposition"],
                grader_reasoning=grader_result["reasoning"],
                confidence_level=grader_result["confidence"],
                raw_observer_response=observer_result["raw_response"],
                raw_grader_response=grader_result["raw_response"]
                flags=grader_result.get("flags", []),
            )

            if not log_result["success"]:
                st.warning(f"Inspection complete but logging failed: {log_result['error']}")

            # Store results in session state for display
            st.session_state["observer_result"] = observer_result
            st.session_state["grader_result"] = grader_result
            st.session_state["inspection_complete"] = True

with col_right:
    st.subheader("Inspection Results")

    if st.session_state.get("inspection_complete"):
        observer_result = st.session_state["observer_result"]
        grader_result = st.session_state["grader_result"]
        observer_output = observer_result["observer_output"]

        # Grade badge
        grade = grader_result["grade"]
        grade_colors = {
            "A": "🟢",
            "B": "🟡",
            "C": "🟠",
            "Scrap": "🔴"
        }
        grade_icon = grade_colors.get(grade, "⚪")

        st.markdown(f"## {grade_icon} Grade {grade}")
        st.markdown(f"**Disposition:** {grader_result['disposition']}")
        st.markdown(f"**Confidence:** {grader_result['confidence'].upper()}")
        st.markdown(f"**Value Recovery Potential:** {grader_result['estimated_value_recovery'].upper()}")

        st.divider()

        # Transparency panel — Chain of Thought
        with st.expander("🔍 Transparency Panel — Full Chain of Thought", expanded=True):

            st.markdown("#### Agent 1 — Observer Output")
            st.json(observer_output)

            st.markdown("#### Agent 2 — Adversarial Challenges Considered")
            for i, challenge in enumerate(grader_result["adversarial_challenges"], 1):
                st.markdown(f"**{i}.** {challenge}")

            st.markdown("#### Final Reasoning")
            st.markdown(grader_result["reasoning"])

            if grader_result["flags"]:
                st.markdown("#### ⚠️ Human Review Flags")
                for flag in grader_result["flags"]:
                    st.warning(flag)

    else:
        st.info("Upload an image and run inspection to see results here.")

# Recent inspections table
st.divider()
st.subheader("Recent Inspections")

recent = get_recent_inspections(limit=10)
if recent:
    # Build display table
    display_data = []
    for r in recent:
        display_data.append({
            "Time": r["created_at"][:19].replace("T", " "),
            "Item": r["item_description"],
            "Category": r["product_category"],
            "Grade": r["grade"],
            "Disposition": r["disposition"],
            "Confidence": r["confidence_level"]
        })

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )
else:
    st.caption("No inspections logged yet.")