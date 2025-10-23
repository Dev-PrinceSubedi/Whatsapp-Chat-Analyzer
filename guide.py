import streamlit as st
from pathlib import Path

def show_guide():

    st.markdown("""
        <style>
            div.block-container {
                padding-top: 1rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # Simple centered heading (no extra space)
    st.markdown("""
        <div style='text-align: center; margin-top: -1rem;'>
            <h1 style='font-weight: bold; margin-bottom: 0;'>
                <span style='color: #25D366;'>WhatsApp</span> Chat_Analyzer
            </h1>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # How to Export Section
    st.markdown("### How to Export Your WhatsApp Chat")

    tab1, tab2 = st.tabs(["Android", "iOS"])

    with tab1:
        st.markdown("""
        1. Open WhatsApp and go to the chat you want to export  
        2. Tap the **three dots** (⋮) in the top right corner  
        3. Select **More → Export chat**  
        4. Choose **Without Media** (recommended for faster processing)  
        5. Save the `.txt` file to your device
        """)

    with tab2:
        st.markdown("""
        1. Open WhatsApp and go to the chat you want to export  
        2. Tap the **chat name** at the top  
        3. Scroll down and tap **Export Chat**  
        4. Choose **Without Media** (recommended for faster processing)  
        5. Save or share the `.txt` file
        """)

    st.divider()

    # Demo File Section
    st.markdown("### Try with a Demo File")
    st.info("👉 Download this sample chat file to test the analyzer.")

    demo_file_path = Path(__file__).parent / "chat_file.txt"

    if not demo_file_path.exists():
        st.warning("⚠️ Demo chat file not found! Please add 'chat_file.txt' in the same folder as guide.py.")
        return

    try:
        with open(demo_file_path, "r", encoding="utf-8") as f:
            demo_content = f.read()
    except Exception as e:
        st.error(f"❌ Error reading demo file: {e}")
        return

    st.download_button(
        label=" Download Demo Chat File",
        data=demo_content.encode("utf-8"),
        file_name="whatsapp_demo_chat.txt",
        mime="text/plain",
        use_container_width=True,
        key="demo_download",
    )
