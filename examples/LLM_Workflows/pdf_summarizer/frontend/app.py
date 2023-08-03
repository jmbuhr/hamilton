import base64
from pathlib import Path

import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


@st.cache_data
def pdf_to_base64(uploaded_file: UploadedFile) -> str:
    """Display the PDF as an embedded b64 string in a markdown component"""
    base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return f'<embed src="data:application/pdf;base64,{base64_pdf}" width=600 height=800 type="application/pdf">'


def post_pdf(uploaded_file: UploadedFile) -> requests.Response:
    """POST request to `http://fastapi_server` which exists in the Docker stack"""
    server_url = "http://fastapi_server:8080/summarize"
    files = {"pdf_file": uploaded_file}
    response = requests.post(server_url, files=files)
    return response


def set_output_filename_state(filename: str) -> None:
    """Set the output filename in the streamlit state"""
    filename = Path(filename)
    st.session_state["ouput_filename"] = f"summary_{filename.stem}.txt"


def set_summary_state(summary: str) -> None:
    """Set the summary in the streamlit state"""
    st.session_state["summary"] = summary


def summarize_callback(uploaded_file: UploadedFile) -> None:
    """`Summarize` button callback; handle input validation and logic"""
    # is None when button is pressed without any file selected
    if uploaded_file is None:
        return

    response = post_pdf(uploaded_file)
    if response.status_code != requests.codes.ok:
        # this will display the status code in the `Summary` UI
        set_summary_state(f"Requests error. Receive status code: {response.status_code}")
        return

    # parse FastAPI response as JSON and set streamlit state
    content = response.json()
    set_output_filename_state(uploaded_file.name)
    set_summary_state(content["summary"])


def app() -> None:
    """Streamlit entrypoint for PDF Summarize frontend"""
    st.set_page_config(
        page_title="PDF-Summarizer",
        page_icon="📝",
        layout="centered",
        menu_items={"Get help": None, "Report a bug": None},
    )
    st.title("PDF-Summarizer 📝")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="hidden")
        st.button(
            "Summarize",
            on_click=summarize_callback,
            args=(uploaded_file,),
            type="primary",
            use_container_width=True,
        )

        # could be a successful requests or status code
        if summary := st.session_state.get("summary", None):
            with st.expander("Summary", expanded=False):
                st.write(summary)

        # is True only after a successful request
        if output_name := st.session_state.get("ouput_filename", None):
            st.download_button(
                "Download Summary", data=summary, file_name=output_name, use_container_width=True
            )

    with col2:
        if uploaded_file:
            pdf_display = pdf_to_base64(uploaded_file)
            st.markdown(pdf_display, unsafe_allow_html=True)


if __name__ == "__main__":
    # run as a script to test streamlit app locally
    app()
