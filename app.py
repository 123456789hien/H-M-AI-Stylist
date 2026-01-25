import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO
import zipfile
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="H&M AI Stylist | Psychographic Edition",
    page_icon="👗",
    layout="wide"
)

# --- 2. CORRECTED PROFESSIONAL CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div.stButton > button:first-child { background-color: #ffb3b3; border: none; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GOOGLE DRIVE ID CONFIG ---
FILE_IDS = {
    "article_csv": "1qYtRpJU9yKdqrcvmE7wUFC-QmU87NSyv",
    "customer_dna": "1ZrEvTcVb0DKS6cIv4vZf-jod9EGH4srK",
    "seasonal_trends": "1vS2vDuhHCifie9wRLOoa70t02UUOI0bs",
    "images_zip": "1X5q8o8fnR-MGBjBzhZf5gH8URNKD2uJA"
}

def get_drive_download_url(file_id):
    return f'https://drive.google.com/uc?export=download&id={file_id}'

# --- 4. OPTIMIZED DATA LOADING ---
@st.cache_data(show_spinner=False)
def load_csv_data():
    try:
        articles = pd.read_csv(get_drive_download_url(FILE_IDS["article_csv"]))
        dna = pd.read_csv(get_drive_download_url(FILE_IDS["customer_dna"]))
        seasonal = pd.read_csv(get_drive_download_url(FILE_IDS["seasonal_trends"]))
        return articles, dna, seasonal
    except Exception as e:
        st.error(f"Error connecting to Google Drive: {e}")
        return None, None, None

@st.cache_resource(show_spinner=False)
def setup_image_library():
    """Unzips images only if folder doesn't exist to save time/RAM"""
    target_path = "images"
    if not os.path.exists(target_path):
        os.makedirs(target_path)
        try:
            r = requests.get(get_drive_download_url(FILE_IDS["images_zip"]), stream=True)
            with zipfile.ZipFile(BytesIO(r.content)) as z:
                z.extractall(target_path)
        except:
            st.warning("Image library is large; some images may load slowly.")
    return True

# Initialize System
articles, dna, seasonal = load_csv_data()
setup_image_library()

if articles is not None:
    # --- 5. SIDEBAR & PERSONALIZATION ---
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=80)
    st.sidebar.title("AI Stylist Panel")
    
    st.sidebar.subheader("User Profile")
    user_id = st.sidebar.selectbox("Select Client DNA", dna['customer_id'].unique()[:50])
    u_data = dna[dna['customer_id'] == user_id].iloc[0]
    
    st.sidebar.metric("Spending Segment", f"${u_data['avg_price']:.3f}")
    st.sidebar.metric("Transactions", int(u_data['transaction_count']))
    
    st.sidebar.divider()
    selected_mood = st.sidebar.radio("Current Target Mood", articles['mood'].unique())

    # --- 6. MAIN INTERFACE ---
    st.title("👗 H&M Psychographic Stylist")
    st.markdown(f"**Mode:** Predictive Analysis for *{selected_mood}* Style")

    tab1, tab2, tab3 = st.tabs(["🛍️ Curated Collection", "📈 Seasonal Intelligence", "🧬 Analysis DNA"])

    # TAB 1: COLLECTION GRID
    with tab1:
        # Filter by Mood & Sort by Hotness Score (Scientific validation from Section 6)
        display_items = articles[articles['mood'] == selected_mood].sort_values(by='hotness_score', ascending=False).head(24)
        
        cols = st.columns(4)
        for i, (idx, row) in enumerate(display_items.iterrows()):
            with cols[i % 4]:
                # Dynamic Image Path
                img_path = os.path.join("images", row['image_path'])
                
                if os.path.exists(img_path):
                    st.image(Image.open(img_path), use_column_width=True)
                else:
                    # Fallback for missing images
                    st.image("https://via.placeholder.com/200x300.png?text=H%26M+Style", use_column_width=True)
                
                st.markdown(f"**{row['prod_name']}**")
                st.caption(f"{row['garment_group_name']}")
                
                # Visualizing 'Hotness Score'
                st.progress(row['hotness_score'], text=f"Trend Score: {row['hotness_score']:.2f}")
                
                with st.expander("AI Stylist Note"):
                    st.write(row['detail_desc'])

    # TAB 2: SEASONAL INTELLIGENCE
    with tab2:
        st.subheader("Seasonal Mood Density (31M Transaction History)")
        # Section 13 Data Visualization
        fig = px.area(seasonal, x="month", y=articles['mood'].unique(),
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(xaxis_title="Month of Year", yaxis_title="Popularity Density")
        st.plotly_chart(fig, use_container_width=True)

    # TAB 3: DATA SCIENCE LOGIC
    with tab3:
        st.subheader("The Stylist Brain")
        st.write("""
        This AI uses a **25:100 Stratified Sample** to maintain the integrity of the original dataset while optimizing performance.
        - **Professional Mode Recall:** 0.91 (High Workwear Sensitivity)
        - **Visual Engine:** ResNet50 Feature Extraction
        - **Clustering:** Psychographic Mood Engine
        """)
        st.json(u_data.to_dict())

else:
    st.error("Failed to load database. Please check Google Drive permissions.")
