#!/usr/bin/env python
"""
Unified Streamlit interface for Agentic CS Scholars System.
Provides web interface for data collection, dashboard visualization, and natural language queries.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime
from pathlib import Path
import sys
from src.utils.config import Config

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.WebScraperAgent import WebScraperAgent
from src.agents.EnrichmentAgent import EnrichmentAgent
from src.agents.NLQAgent import NLQAgent
from src.utils.DataManager import DataManager


st.set_page_config(
    page_title="Agentic CS Scholars",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "researchers" not in st.session_state:
        st.session_state.researchers = []
    if "collection_status" not in st.session_state:
        st.session_state.collection_status = None
    if "collection_logs" not in st.session_state:
        st.session_state.collection_logs = []


def log_message(msg: str, type: str = "info"):
    """Add message to collection logs."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.collection_logs.append({
        "timestamp": timestamp,
        "message": msg,
        "type": type
    })


def run_data_collection(url: str, mode: str):
    """Execute data collection pipeline."""
    log_message(f"Starting data collection from: {url}", "info")
    
    if mode in ["full", "collect_only"]:
        log_message("Initializing WebScraperAgent...", "info")
        scraper = WebScraperAgent()
        
        log_message(f"Fetching data from URL...", "info")
        result = scraper.execute({"url": url, "max_retries": 3})
        
        if result.get("status") != "success":
            log_message(f"Collection failed: {result.get('error')}", "error")
            return None
        
        researchers = result.get("data", [])
        log_message(f"Collected {len(researchers)} researchers", "success")
        
        # Save using DataManager
        dm = DataManager()
        dm.save_data(researchers)
        log_message(f"Data saved to {dm.json_path}", "success")
        
        return researchers
    
    return None


def render_collection_page():
    """Render the data collection page."""
    st.header("Data Collection")
    st.markdown("Collect researcher data from CNPq Lattes platform")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url = st.text_input(
            "CNPq Page URL",
            placeholder="http://plsql1.cnpq.br/divulg/RESULTADO_PQ_102003.prc_comp_cmt_links?...",
            help="Paste the complete URL from CNPq results page"
        )
    
    with col2:
        mode = st.selectbox(
            "Collection Mode",
            options=["collect_only"],
            format_func=lambda x: "Collect Only (CNPq data)"
        )
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        start_button = st.button("Start Collection", type="primary", use_container_width=True)
    
    with col_btn2:
        if st.button("Clear Logs", use_container_width=True):
            st.session_state.collection_logs = []
            st.rerun()
    
    if start_button and url:
        with st.spinner("Collecting data... This may take a few minutes."):
            researchers = run_data_collection(url, mode)
            
            if researchers:
                st.session_state.researchers = researchers
                st.session_state.data_loaded = True
                st.session_state.collection_status = "success"
                st.success(f"Successfully collected {len(researchers)} researchers!")
            else:
                st.session_state.collection_status = "failed"
                st.error("Collection failed. Check logs for details.")
    
    st.subheader("Execution Logs")
    log_container = st.container(height=300)
    
    with log_container:
        for log in st.session_state.collection_logs:
            if log["type"] == "error":
                st.error(f"[{log['timestamp']}] {log['message']}")
            elif log["type"] == "success":
                st.success(f"[{log['timestamp']}] {log['message']}")
            else:
                st.info(f"[{log['timestamp']}] {log['message']}")
    
    if st.session_state.collection_status == "success":
        st.balloons()
        st.info("Go to the 'Dashboard' tab to visualize the data.")


def render_dashboard_page():
    """Render the dashboard visualization page."""
    st.header("Data Dashboard")
    
    dm = DataManager()
    data = dm.load_data()
    
    if not data:
        st.warning("No data available. Please go to 'Data Collection' tab first.")
        return
    
    st.session_state.researchers = data
    st.session_state.data_loaded = True
    
    df = pd.DataFrame(data)
    
    st.subheader("Filters")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if "uf" in df.columns:
            uf_options = ["All"] + sorted(df["uf"].dropna().unique().tolist())
            selected_uf = st.selectbox("UF Filter", uf_options)
        else:
            selected_uf = "All"
    
    with col_f2:
        if "nivel_bolsa" in df.columns:
            level_options = ["All"] + sorted(df["nivel_bolsa"].dropna().unique().tolist())
            selected_level = st.selectbox("Scholarship Level", level_options)
        else:
            selected_level = "All"
    
    with col_f3:
        if "instituicao" in df.columns:
            inst_search = st.text_input("Institution contains", placeholder="Type institution name...")
        else:
            inst_search = ""
    
    filtered_df = df.copy()
    if selected_uf != "All":
        filtered_df = filtered_df[filtered_df["uf"] == selected_uf]
    if selected_level != "All":
        filtered_df = filtered_df[filtered_df["nivel_bolsa"] == selected_level]
    if inst_search:
        filtered_df = filtered_df[filtered_df["instituicao"].str.contains(inst_search, case=False, na=False)]
    
    st.subheader("Key Metrics")
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    with col_m1:
        st.metric("Total Researchers", len(filtered_df))
    with col_m2:
        st.metric("Unique Institutions", filtered_df["instituicao"].nunique() if "instituicao" in filtered_df else 0)
    with col_m3:
        st.metric("Unique UF", filtered_df["uf"].nunique() if "uf" in filtered_df else 0)
    with col_m4:
        avg_year = filtered_df["ano_doutorado"].mean() if "ano_doutorado" in filtered_df else 0
        st.metric("Avg PhD Year", f"{avg_year:.0f}" if avg_year else "N/A")
    with col_m5:
        if "sexo" in filtered_df.columns:
            gender_counts = filtered_df["sexo"].value_counts()
            most_common = gender_counts.index[0] if len(gender_counts) > 0 else "N/A"
            st.metric("Most Common Gender", most_common)
    
    tab1, tab2, tab3 = st.tabs(["Charts", "Data Table", "Statistics"])
    
    with tab1:
        col_ch1, col_ch2 = st.columns(2)
        
        with col_ch1:
            if "uf" in filtered_df.columns:
                uf_counts = filtered_df["uf"].value_counts().head(10)
                fig_uf = px.bar(uf_counts, title="Researchers by UF", labels={"value": "Count", "index": "UF"})
                st.plotly_chart(fig_uf, use_container_width=True)
        
        with col_ch2:
            if "sexo" in filtered_df.columns:
                gender_counts = filtered_df["sexo"].value_counts()
                fig_gender = px.pie(gender_counts, title="Gender Distribution", values=gender_counts.values, names=gender_counts.index)
                st.plotly_chart(fig_gender, use_container_width=True)
        
        col_ch3, col_ch4 = st.columns(2)
        
        with col_ch3:
            if "nivel_bolsa" in filtered_df.columns:
                level_counts = filtered_df["nivel_bolsa"].value_counts()
                fig_level = px.bar(level_counts, title="Scholarship Level Distribution")
                st.plotly_chart(fig_level, use_container_width=True)
        
        with col_ch4:
            if "ano_doutorado" in filtered_df.columns:
                fig_year = px.histogram(filtered_df, x="ano_doutorado", title="PhD Year Distribution")
                st.plotly_chart(fig_year, use_container_width=True)
    
    with tab2:
        display_cols = ["nome", "sexo", "instituicao", "uf", "nivel_bolsa", "area_atuacao", "ano_doutorado"]
        available_cols = [c for c in display_cols if c in filtered_df.columns]
        
        st.dataframe(
            filtered_df[available_cols],
            use_container_width=True,
            height=500
        )
    
    with tab3:
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            if "instituicao" in filtered_df.columns:
                st.subheader("Top 10 Institutions")
                st.dataframe(filtered_df["instituicao"].value_counts().head(10), use_container_width=True)
        
        with col_s2:
            if "area_atuacao" in filtered_df.columns:
                st.subheader("Top 10 Research Areas")
                st.dataframe(filtered_df["area_atuacao"].value_counts().head(10), use_container_width=True)
    
    st.subheader("Export Data")
    col_exp1, col_exp2 = st.columns(2)
    
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    col_exp1.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"researchers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    json_data = filtered_df.to_json(orient="records", indent=2, force_ascii=False).encode("utf-8")
    col_exp2.download_button(
        label="Download JSON",
        data=json_data,
        file_name=f"researchers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )


def render_manual_editor_page():
    """Render manual data editor for gender and Google Scholar updates."""
    st.header("Manual Data Editor")
    st.markdown("Manually update gender or Google Scholar URL when automation fails")
    
    dm = DataManager()
    data = dm.load_data()
    
    if not data:
        st.warning("No data available. Please collect data first.")
        return
    
    df = pd.DataFrame(data)
    
    st.subheader("Select Researcher")
    
    selected_name = st.selectbox("Researcher Name", df["nome"].tolist())
    researcher = df[df["nome"] == selected_name].iloc[0]
    
    st.subheader("Current Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Name:**", researcher.get("nome", ""))
        st.write("**Institution:**", researcher.get("instituicao", ""))
        st.write("**UF:**", researcher.get("uf", ""))
        st.write("**Scholarship Level:**", researcher.get("nivel_bolsa", ""))
    
    with col2:
        st.write("**Research Area:**", researcher.get("area_atuacao", ""))
        st.write("**PhD Year:**", researcher.get("ano_doutorado", ""))
        current_gender = researcher.get("sexo", "Nao informado")
        current_google = researcher.get("google_scholar", "")
    
    st.markdown("---")
    st.subheader("Edit Fields")
    
    new_gender = st.selectbox(
        "Gender",
        options=["Masculino", "Feminino", "Nao informado"],
        index=["Masculino", "Feminino", "Nao informado"].index(current_gender)
    )
    
    new_google = st.text_input("Google Scholar URL", value=current_google)
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("Save Changes", type="primary", use_container_width=True):
            if new_gender != current_gender:
                if dm.update_field(selected_name, "sexo", new_gender):
                    st.success(f"Gender updated to {new_gender}")
                else:
                    st.error("Failed to update gender")
            
            if new_google != current_google:
                if dm.update_field(selected_name, "google_scholar", new_google):
                    st.success("Google Scholar URL updated")
                else:
                    st.error("Failed to update Google Scholar URL")
            
            st.rerun()
    
    with col_btn2:
        if st.button("Refresh Data", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    st.subheader("Bulk Statistics")
    
    stats = dm.get_statistics()
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Total Researchers", stats["total"])
    with col_s2:
        st.metric("Unique Institutions", stats["unique_institutions"])
    with col_s3:
        st.metric("Unique UF", stats["unique_uf"])
    
    if stats["gender_distribution"]:
        st.write("**Gender Distribution:**")
        for gender, count in stats["gender_distribution"].items():
            st.write(f"- {gender}: {count}")


def render_nlq_page():
    """Render the natural language query page."""
    st.header("Natural Language Query")
    st.markdown("Ask questions about the researcher dataset in plain English or Portuguese")
    
    dm = DataManager()
    data = dm.load_data()
    
    if not data:
        st.warning("No data available. Please go to 'Data Collection' tab first.")
        return
    
    st.markdown("---")
    
    col_q1, col_q2 = st.columns([3, 1])
    
    with col_q1:
        question = st.text_area(
            "Your Question",
            placeholder="Example: How many researchers have scholarship level 1A? or List all researchers from USP",
            height=100
        )
    
    with col_q2:
        st.markdown("###")
        st.markdown("###")
        ask_button = st.button("Ask", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    if ask_button and question:
        with st.spinner("Analyzing and generating response..."):
            nlq_agent = NLQAgent()
            result = nlq_agent.execute({"question": question})
            
            if result.get("status") == "success":
                st.subheader("Answer")
                
                answer = result.get("answer", "")
                
                st.markdown(
                    f"""
                    <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 4px solid #4CAF50;">
                        <p style="font-size: 16px; color: #e0e0e0;">{answer}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                with st.expander("Query Details"):
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.metric("Response Time", f"{result.get('duration_ms', 0):.0f} ms")
                    with col_d2:
                        st.metric("Question Length", f"{len(question)} characters")
            else:
                st.error(f"Query failed: {result.get('error', 'Unknown error')}")
    
    st.markdown("---")
    st.subheader("Example Questions")
    
    examples = [
        "How many researchers are in the dataset?",
        "List all researchers from Universidade de Sao Paulo",
        "Show researchers with scholarship level 1A",
        "What is the distribution of researchers by gender?",
        "Which institutions have the most researchers?",
        "Show me researchers who completed PhD after 2015"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                st.session_state.example_question = example
                st.rerun()
    
    if "example_question" in st.session_state:
        st.info(f"Selected: {st.session_state.example_question}")
        st.session_state.example_question = None


def main():
    """Main entry point for Streamlit application."""
    init_session_state()
    
    st.title("Agentic CS Scholars System")
    st.markdown("*Multi-agent system for collecting, enriching, and querying CNPq researcher data*")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Data Collection",
        "Dashboard",
        "NLQ Assistant",
        "Manual Editor"
    ])
    
    with tab1:
        render_collection_page()
    
    with tab2:
        render_dashboard_page()
    
    with tab3:
        render_nlq_page()
    
    with tab4:
        render_manual_editor_page()
    
    st.markdown("---")
    st.caption(f"LLM: {Config.OPENAI_MODEL} | CNPq Lattes Data")


if __name__ == "__main__":
    main()