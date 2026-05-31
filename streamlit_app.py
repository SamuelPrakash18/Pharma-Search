from __future__ import annotations

import streamlit as st

from backend_app.models import MedicineDetailResponse, MedicineDetailRequest, SearchRequest
from backend_app.services import format_detail_response, get_vector_search_service


st.set_page_config(page_title="AI Medical Intelligence System", page_icon="💊", layout="wide")


@st.cache_resource
def get_service():
    return get_vector_search_service()


def render_result_card(result) -> None:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.subheader(result.name)
            st.caption(f"Similarity score: {result.score:.3f}")
            st.write(result.explanation)
            st.write(f"**Composition:** {result.composition}")
            st.write(f"**Uses:** {result.uses}")
            if result.side_effects:
                st.write(f"**Side effects:** {result.side_effects}")
        with right:
            if result.image_url:
                st.image(result.image_url, use_column_width=True)


def main() -> None:
    st.title("AI Medical Intelligence System")
    st.write("Semantic medicine search, similarity ranking, and rule-based medicine insights.")

    service = get_service()

    query = st.text_input("Search medicine, composition, usage, or side effect", placeholder="e.g. fever medicine, amoxicillin, cough syrup")
    top_k = st.slider("Top results", min_value=1, max_value=10, value=5)

    if st.button("Search", type="primary") and query.strip():
        results = service.search(query=query, top_k=top_k)
        st.subheader("Search Results")
        if not results:
            st.info("No matches found.")
        for result in results:
            render_result_card(result)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        medicine_name = st.text_input("Medicine name for details", placeholder="e.g. Augmentin 625 Duo Tablet")
        if st.button("Get Details") and medicine_name.strip():
            record = service.details(medicine_name)
            if record is None:
                st.error("Medicine not found.")
            else:
                detail = format_detail_response(record)
                st.subheader(detail.name)
                st.write(f"**Composition:** {detail.composition}")
                st.write(f"**Uses:** {detail.uses}")
                st.write(f"**Side effects:** {detail.side_effects}")
                st.write(f"**Safety note:** {detail.safety_note}")
                if detail.image_url:
                    st.image(detail.image_url, use_column_width=True)

    with col2:
        recommendation_name = st.text_input("Medicine name for similar recommendations", placeholder="e.g. Azithral 500 Tablet")
        if st.button("Recommend Similar Medicines") and recommendation_name.strip():
            results = service.recommend(recommendation_name, top_k=top_k)
            st.subheader("Similar Medicines")
            if not results:
                st.info("No similar medicines found.")
            for result in results:
                render_result_card(result)


if __name__ == "__main__":
    main()
