import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gdown
import os
import zipfile
from typing import Optional, Tuple, Dict
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Fashion Emotion BI Dashboard",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look (GIỮ NGUYÊN BẢN GỐC)
st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #E50019;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-box {
        background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }
    .insight-box {
        background: #f0f2f6;
        padding: 15px;
        border-left: 4px solid #E50019;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS (Cập nhật ID từ link Google Drive của bạn)
# ============================================================================

@st.cache_resource
def load_all_data():
    # IDs lấy từ link mới của bạn
    file_ids = {
        "article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "hm_web_images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }

    # Download files
    for filename, fid in file_ids.items():
        if not os.path.exists(filename):
            try:
                url = f'https://drive.google.com/uc?id={fid}'
                gdown.download(url, filename, quiet=False)
            except Exception as e:
                st.error(f"Error downloading {filename}: {e}")

    # Extract images
    if os.path.exists("hm_web_images.zip") and not os.path.exists("images"):
        with zipfile.ZipFile("hm_web_images.zip", 'r') as zip_ref:
            zip_ref.extractall("images")

    try:
        # Load datasets
        df_art = pd.read_csv("article_master_web.csv")
        df_cust = pd.read_csv("customer_dna_master.csv")
        df_val = pd.read_csv("customer_test_validation.csv")
        
        # Preprocessing (giữ nguyên logic gốc)
        df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
        df_art['revenue'] = df_art['hotness_score'] * df_art['price'] * 1000
        
        return df_art, df_cust, df_val
    except Exception as e:
        st.error(f"Data processing error: {e}")
        return None, None, None

df_articles, df_customers, df_validation = load_all_data()

# Check if data is loaded
if df_articles is None:
    st.error("Failed to load data. Please ensure Google Drive links are accessible.")
    st.stop()

# ============================================================================
# SIDEBAR NAVIGATION (Chuyển sang tiếng Anh)
# ============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
    st.markdown("---")
    
    page = st.radio(
        "NAVIGATION",
        ["📊 Executive Dashboard", "🔍 Product Intelligence", "👤 Customer Intelligence", 
         "😊 Emotion Analytics", "🤖 Recommendation Engine", "📈 Model Performance"]
    )
    
    st.markdown("---")
    st.markdown("### FILTERS")
    
    # Section Filter
    sections = ["All"] + sorted(df_articles['section_name'].unique().tolist())
    selected_section = st.selectbox("Gender/Section", sections)
    
    # Category Filter
    product_groups = ["All"] + sorted(df_articles['product_group_name'].unique().tolist())
    selected_group = st.selectbox("Product Category", product_groups)
    
    # Mood Filter
    moods = ["All"] + sorted(df_articles['mood'].unique().tolist())
    selected_mood = st.selectbox("Emotional Mood", moods)

# Data Filtering Logic
filtered_df = df_articles.copy()
if selected_section != "All":
    filtered_df = filtered_df[filtered_df['section_name'] == selected_section]
if selected_group != "All":
    filtered_df = filtered_df[filtered_df['product_group_name'] == selected_group]
if selected_mood != "All":
    filtered_df = filtered_df[filtered_df['mood'] == selected_mood]

# ============================================================================
# 1. EXECUTIVE DASHBOARD (Chuyển sang tiếng Anh)
# ============================================================================
if page == "📊 Executive Dashboard":
    st.markdown('<h1 class="header-title">Executive Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Real-time Fashion Emotion & Performance Overview</p>', unsafe_allow_html=True)
    
    # KPI Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f'<div class="metric-box"><h3>{len(filtered_df):,}</h3><p>Active Articles</p></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="metric-box"><h3>{filtered_df["hotness_score"].mean():.2f}</h3><p>Avg Hotness Score</p></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="metric-box"><h3>${filtered_df["price"].mean():.4f}</h3><p>Avg Price</p></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'<div class="metric-box"><h3>${filtered_df["revenue"].sum():,.0f}</h3><p>Revenue Potential</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Revenue Potential by Category")
        rev_cat = filtered_df.groupby('product_group_name')['revenue'].sum().sort_values(ascending=True).reset_index()
        fig_rev = px.bar(rev_cat, x='revenue', y='product_group_name', orientation='h', 
                         color='revenue', color_continuous_scale='Reds', template='plotly_white')
        st.plotly_chart(fig_rev, use_container_width=True)

    with col2:
        st.subheader("🎭 Emotion Distribution")
        fig_mood = px.pie(filtered_df, names='mood', values='revenue', hole=0.4,
                          color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_mood, use_container_width=True)

# ============================================================================
# 2. PRODUCT INTELLIGENCE (Chuyển sang tiếng Anh)
# ============================================================================
elif page == "🔍 Product Intelligence":
    st.markdown('<h1 class="header-title">Product Intelligence</h1>', unsafe_allow_html=True)
    st.dataframe(filtered_df[['article_id', 'prod_name', 'product_group_name', 'section_name', 'price', 'hotness_score', 'mood', 'revenue']], 
                 use_container_width=True)

# ============================================================================
# 3. CUSTOMER INTELLIGENCE (Chuyển sang tiếng Anh)
# ============================================================================
elif page == "👤 Customer Intelligence":
    st.markdown('<h1 class="header-title">Customer Intelligence</h1>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.subheader("Customer Segments")
        fig_seg = px.pie(df_customers, names='segment', color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig_seg, use_container_width=True)
    with col_b:
        st.subheader("Spending vs Age Analysis")
        fig_scatter = px.scatter(df_customers.sample(min(1000, len(df_customers))), 
                                 x='age', y='avg_spending', color='segment', size='purchase_count',
                                 title="Customer Demographics & Value", template='plotly_white')
        st.plotly_chart(fig_scatter, use_container_width=True)

# ============================================================================
# 4. EMOTION ANALYTICS (Chuyển sang tiếng Anh)
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<h1 class="header-title">Emotion Analytics</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Emotion vs Hotness")
        mood_hot = filtered_df.groupby('mood')['hotness_score'].mean().sort_values().reset_index()
        fig_h = px.bar(mood_hot, x='hotness_score', y='mood', orientation='h', color='hotness_score', color_continuous_scale='Reds')
        st.plotly_chart(fig_h, use_container_width=True)
    with col2:
        st.subheader("Price Strategy by Mood")
        fig_p = px.box(filtered_df, x='mood', y='price', color='mood', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_p, use_container_width=True)

# ============================================================================
# 5. RECOMMENDATION ENGINE (Chuyển sang tiếng Anh)
# ============================================================================
elif page == "🤖 Recommendation Engine":
    st.markdown('<h1 class="header-title">AI Recommendation Engine</h1>', unsafe_allow_html=True)
    
    ref_prod = st.selectbox("Select a reference product:", filtered_df['prod_name'].unique())
    target_mood = filtered_df[filtered_df['prod_name'] == ref_prod]['mood'].values[0]
    
    st.info(f"Finding products matching the **{target_mood}** emotional profile.")
    
    recs = df_articles[df_articles['mood'] == target_mood].head(6)
    cols = st.columns(3)
    for i, (idx, row) in enumerate(recs.iterrows()):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="border:1px solid #eee; padding:10px; border-radius:10px; background:white;">
                <h5 style="color:#E50019;">{row['prod_name'][:25]}</h5>
                <p>Price: ${row['price']:.4f}<br>Hotness: {row['hotness_score']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# 6. MODEL PERFORMANCE (Chuyển sang tiếng Anh)
# ============================================================================
elif page == "📈 Model Performance":
    st.markdown('<h1 class="header-title">Model Performance & Validation</h1>', unsafe_allow_html=True)
    
    # Gap Analysis (Giữ nguyên logic gốc)
    inv_dist = df_articles['mood'].value_counts(normalize=True).reset_index()
    sales_dist = df_validation['actual_purchased_mood'].value_counts(normalize=True).reset_index()
    
    fig_gap = go.Figure()
    fig_gap.add_trace(go.Bar(x=inv_dist['mood'], y=inv_dist['proportion'], name='AI Inventory Prediction', marker_color='#E50019'))
    fig_gap.add_trace(go.Bar(x=sales_dist['actual_purchased_mood'], y=sales_dist['proportion'], name='Actual Market Demand', marker_color='#333333'))
    
    fig_gap.update_layout(title="Inventory Supply vs. Market Demand Gap", barmode='group', template='plotly_white')
    st.plotly_chart(fig_gap, use_container_width=True)

# ============================================================================
# FOOTER (Chuyển sang tiếng Anh)
# ============================================================================
st.divider()
st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p><strong>Fashion Emotion BI Dashboard</strong> | Master Thesis Project</p>
    <p>Advanced Analytics for E-commerce | Based on Emotion & Hotness Score Analysis</p>
    <p>© 2026 Fashion BI Insights</p>
    </div>
""", unsafe_allow_html=True)
