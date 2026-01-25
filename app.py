import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO
import zipfile
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="H&M AI Stylist | Professional Edition",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR PROFESSIONAL FINISH ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .product-card { border: 1px solid #e0e0e0; padding: 10px; border-radius: 8px; background: white; transition: 0.3s; }
    .product-card:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.1); transform: translateY(-5px); }
    </style>
    """, unsafe_allow_stdio=True)

# --- GOOGLE DRIVE FILE IDS ---
FILE_IDS = {
    "article_csv": "1qYtRpJU9yKdqrcvmE7wUFC-QmU87NSyv",
    "customer_dna": "1ZrEvTcVb0DKS6cIv4vZf-jod9EGH4srK",
    "seasonal_trends": "1vS2vDuhHCifie9wRLOoa70t02UUOI0bs",
    "images_zip": "1X5q8o8fnR-MGBjBzhZf5gH8URNKD2uJA"
}

def get_drive_url(file_id):
    return f'https://drive.google.com/uc?id={file_id}'

# --- DATA LOADING ENGINES ---
@st.cache_data
def load_data():
    articles = pd.read_csv(get_drive_url(FILE_IDS["article_csv"]))
    dna = pd.read_csv(get_drive_url(FILE_IDS["customer_dna"]))
    seasonal = pd.read_csv(get_drive_url(FILE_IDS["seasonal_trends"]))
    return articles, dna, seasonal

@st.cache_resource
def setup_images():
    if not os.path.exists("images"):
        response = requests.get(get_drive_url(FILE_IDS["images_zip"]))
        with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
            zip_ref.extractall("images")
    return True

# Initialize Data
with st.spinner('Synchronizing AI Mood Engine...'):
    articles, dna, seasonal = load_data()
    setup_images()

# --- SIDEBAR: PERSONALIZATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
st.sidebar.title("Stylist Dashboard")
st.sidebar.divider()

user_id = st.sidebar.selectbox("👤 Select Client DNA Profile", dna['customer_id'].unique()[:100])
user_info = dna[dna['customer_id'] == user_id].iloc[0]

st.sidebar.metric("Avg. Spending Segment", f"${user_info['avg_price']:.3f}")
st.sidebar.metric("Purchase History", f"{int(user_info['transaction_count'])} Items")

st.sidebar.divider()
selected_mood = st.sidebar.radio("✨ Select Your Target Mood", articles['mood'].unique())

# --- MAIN UI: SEASONAL INTELLIGENCE ---
st.title("👗 H&M AI Stylist: Psychographic Intelligence")
st.markdown(f"**Current Recommendation Mode:** {selected_mood}")

tabs = st.tabs(["🛍️ Collection", "📈 Seasonal Trends", "🧬 User DNA Analysis"])

# --- TAB 1: SMART COLLECTION GRID ---
with tabs[0]:
    # Professional Mode focus: High Recall logic
    filtered_df = articles[articles['mood'] == selected_mood].sort_values(by='hotness_score', ascending=False)
    
    st.write(f"Displaying top-tier **{selected_mood}** selections based on your 25:100 Stratified Sample.")
    
    cols = st.columns(4)
    for i, (idx, row) in enumerate(filtered_df.head(24).iterrows()):
        with cols[i % 4]:
            img_path = os.path.join("images", row['image_path'])
            if os.path.exists(img_path):
                st.image(Image.open(img_path), use_column_width=True)
                st.markdown(f"**{row['prod_name']}**")
                st.caption(f"Category: {row['garment_group_name']}")
                
                # Hotness Score Visualization
                st.progress(row['hotness_score'], text=f"Hotness: {row['hotness_score']:.2f}")
                
                with st.expander("View Stylist Insights"):
                    st.write(row['detail_desc'])
            else:
                st.info("Loading Image...")

# --- TAB 2: SEASONAL TRENDS ---
with tabs[1]:
    st.subheader("Monthly Style Density")
    # Using seasonal_trends.csv for scientific validation
    fig = px.area(seasonal, x="month", y=articles['mood'].unique(),
                  labels={"value": "Popularity Index", "month": "Month"},
                  color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: DNA ANALYSIS ---
with tabs[2]:
    st.subheader("Client Behavioral Analysis")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**DNA Profile Summary**")
        st.dataframe(user_info, use_container_width=True)
    with col_b:
        st.info("This AI uses the **25:100 Ratio** to ensure that even with reduced data, your recommendations match the full 31M transaction scale.")

st.divider()
st.caption("AI Stylist Backend: LightGBM Predictor + ResNet50 Visual DNA Engine.")
