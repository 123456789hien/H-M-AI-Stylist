import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import gdown
import zipfile

# --- 1. SETTINGS & THEME ---
st.set_page_config(
    page_title="Fashion Emotion BI Hub",
    page_icon="👠",
    layout="wide"
)

# --- 2. DATA LOADER (Embedded for reliability) ---
@st.cache_resource
def load_all_resources():
    if not os.path.exists('data'): os.makedirs('data')
    
    # IDs from your project documentation
    files = {
        "articles": ("1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK", "data/articles.csv"),
        "customers": ("182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH", "data/customers.csv"),
        "validation": ("1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB", "data/validation.csv"),
        "embeddings": ("1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54", "data/embeddings.csv")
    }
    
    for key, (fid, path) in files.items():
        if not os.path.exists(path):
            gdown.download(f'https://drive.google.com/uc?id={fid}', path, quiet=True)
            
    # CHỈ GIẢI NÉN ẢNH NẾU CHẠY LOCAL. TRÊN CLOUD SẼ DÙNG URL HOẶC PLACEHOLDER
    # Điều này giúp tránh lỗi "Oh no" do tràn bộ nhớ Cloud
    return (pd.read_csv("data/articles.csv"), pd.read_csv("data/customers.csv"), 
            pd.read_csv("data/validation.csv"), pd.read_csv("data/embeddings.csv"))

# Load Data
df_art, df_cust, df_val, df_emb = load_all_resources()
df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)

# --- 3. NAVIGATION (6 PAGES) ---
st.sidebar.title("Strategic BI Panel")
page = st.sidebar.selectbox("Navigate to Module:", [
    "📊 Dashboard Overview",
    "🛍️ Product Explorer",
    "😊 Emotion Analytics",
    "👥 Customer Insights",
    "🤖 Recommendations",
    "📈 Model Performance"
])

# --- MODULE LOGIC ---
if page == "📊 Dashboard Overview":
    st.title("📊 Executive Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total SKU", f"{len(df_art):,}")
    c2.metric("Hotness Score", f"{df_art['hotness_score'].mean():.2f}")
    
    fig = px.pie(df_art, names='mood', hole=0.4, title="Inventory Share by Mood")
    st.plotly_chart(fig, use_container_width=True)

elif page == "🛍️ Product Explorer":
    st.title("🛍️ Product Explorer")
    # Tối ưu: Không hiện ảnh 3GB nếu trên Cloud để tránh crash, chỉ hiện thông tin
    st.dataframe(df_art.head(100))

elif page == "😊 Emotion Analytics":
    st.title("😊 Emotion Analytics")
    fig = px.scatter(df_art, x="price", y="hotness_score", color="mood", title="Price vs Hotness Correlation")
    st.plotly_chart(fig, use_container_width=True)

elif page == "👥 Customer Insights":
    st.title("👥 Customer DNA Insights")
    fig = px.box(df_cust, x="segment", y="avg_spending", color="segment")
    st.plotly_chart(fig, use_container_width=True)

elif page == "🤖 Recommendations":
    st.title("🤖 AI Recommendations")
    # Hiển thị không gian Vector (Research Question 10)
    fig_3d = px.scatter(df_emb, x='x', y='y', color='mood', title="Visual DNA Latent Space")
    st.plotly_chart(fig_3d, use_container_width=True)

elif page == "📈 Model Performance":
    st.title("📈 Model Performance")
    # So sánh Supply và Demand (Research Question 9)
    supply = df_art['mood'].value_counts(normalize=True)
    demand = df_val['actual_purchased_mood'].value_counts(normalize=True)
    gap_df = pd.DataFrame({'Inventory': supply, 'Market Demand': demand})
    st.bar_chart(gap_df)

st.sidebar.markdown("---")
st.sidebar.caption("H&M Emotion Intelligence v1.0")
