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

# Custom CSS for professional look
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .header-title { font-size: 2.5rem; font-weight: 700; color: #E50019; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1rem; color: #666; margin-bottom: 2rem; }
    .metric-box { background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 10px; }
    .insight-box { background: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #E50019; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING UTILITIES (Fixed with your Google Drive Links)
# ============================================================================
@st.cache_resource
def load_data():
    file_ids = {
        "article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "hm_web_images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    
    for filename, fid in file_ids.items():
        if not os.path.exists(filename):
            url = f'https://drive.google.com/uc?id={fid}'
            gdown.download(url, filename, quiet=False)

    # Extract images if not already done
    if os.path.exists("hm_web_images.zip") and not os.path.exists("images"):
        with zipfile.ZipFile("hm_web_images.zip", 'r') as zip_ref:
            zip_ref.extractall("images")

    try:
        df_articles = pd.read_csv("article_master_web.csv")
        df_customers = pd.read_csv("customer_dna_master.csv")
        df_validation = pd.read_csv("customer_test_validation.csv")
        
        # Data Preprocessing
        df_articles['article_id'] = df_articles['article_id'].astype(str).str.zfill(10)
        df_articles['revenue'] = df_articles['hotness_score'] * df_articles['price'] * 1000
        
        return df_articles, df_customers, df_validation
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None

df_articles, df_customers, df_validation = load_data()

if df_articles is None:
    st.error("Could not initialize data. Please check connection.")
    st.stop()

# ============================================================================
# SIDEBAR FILTERS (Translated to English)
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
    st.markdown("### GLOBAL FILTERS")
    
    # Filter by Section
    sections = ["All"] + sorted(df_articles['section_name'].unique().tolist())
    selected_section = st.selectbox("Select Section", sections)
    
    # Filter by Product Group
    product_groups = ["All"] + sorted(df_articles['product_group_name'].unique().tolist())
    selected_group = st.selectbox("Select Product Group", product_groups)
    
    # Filter by Mood
    moods = ["All"] + sorted(df_articles['mood'].unique().tolist())
    selected_mood = st.selectbox("Select Emotional Mood", moods)

# Apply Filters
filtered_df = df_articles.copy()
if selected_section != "All":
    filtered_df = filtered_df[filtered_df['section_name'] == selected_section]
if selected_group != "All":
    filtered_df = filtered_df[filtered_df['product_group_name'] == selected_group]
if selected_mood != "All":
    filtered_df = filtered_df[filtered_df['mood'] == selected_mood]

# ============================================================================
# PAGE 1: EXECUTIVE DASHBOARD
# ============================================================================
if page == "📊 Executive Dashboard":
    st.markdown('<h1 class="header-title">Executive Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">High-level overview of fashion performance and emotion metrics</p>', unsafe_allow_html=True)
    
    # KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><h3>{len(filtered_df):,}</h3><p>Total Products</p></div>', unsafe_allow_html=True)
    with m2:
        avg_hotness = filtered_df['hotness_score'].mean()
        st.markdown(f'<div class="metric-box"><h3>{avg_hotness:.2f}</h3><p>Avg Hotness Score</p></div>', unsafe_allow_html=True)
    with m3:
        avg_price = filtered_df['price'].mean()
        st.markdown(f'<div class="metric-box"><h3>${avg_price:.4f}</h3><p>Avg Unit Price</p></div>', unsafe_allow_html=True)
    with m4:
        total_rev = filtered_df['revenue'].sum()
        st.markdown(f'<div class="metric-box"><h3>${total_rev:,.0f}</h3><p>Revenue Potential</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Revenue Potential by Category")
        cat_rev = filtered_df.groupby('product_group_name')['revenue'].sum().sort_values(ascending=True).reset_index()
        # FIXED: orientation='h' replaces barh
        fig_rev = px.bar(cat_rev, x='revenue', y='product_group_name', orientation='h',
                         color='revenue', color_continuous_scale='Reds', template="plotly_white")
        st.plotly_chart(fig_rev, use_container_width=True)

    with col2:
        st.subheader("🎭 Emotion-Driven Revenue Distribution")
        mood_rev = filtered_df.groupby('mood')['revenue'].sum().reset_index()
        fig_pie = px.pie(mood_rev, values='revenue', names='mood', hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_pie, use_container_width=True)

# ============================================================================
# PAGE 4: EMOTION ANALYTICS (Fixed Logic)
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<h1 class="header-title">Emotion Analytics</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Mood vs Hotness Correlation")
        mood_hot = filtered_df.groupby('mood')['hotness_score'].mean().sort_values(ascending=False).reset_index()
        fig_mood = px.bar(mood_hot, x='mood', y='hotness_score', color='hotness_score',
                          color_continuous_scale='Reds', template="plotly_white")
        st.plotly_chart(fig_mood, use_container_width=True)
        
    with col2:
        st.subheader("💹 Pricing Strategy by Emotion")
        mood_price = filtered_df.groupby('mood')['price'].mean().sort_values(ascending=False).reset_index()
        fig_price = px.line(mood_price, x='mood', y='price', markers=True, template="plotly_white")
        fig_price.update_traces(line_color='#E50019')
        st.plotly_chart(fig_price, use_container_width=True)

# ============================================================================
# PAGE 5: RECOMMENDATION ENGINE
# ============================================================================
elif page == "🤖 Recommendation Engine":
    st.markdown('<h1 class="header-title">AI Recommendation Engine</h1>', unsafe_allow_html=True)
    
    # Select product for similarity search
    prod_list = filtered_df['prod_name'].unique()
    if len(prod_list) > 0:
        selected_prod = st.selectbox("Search for a product to find similar styles:", prod_list)
        
        target_item = filtered_df[filtered_df['prod_name'] == selected_prod].iloc[0]
        target_mood = target_item['mood']
        
        st.markdown(f'<div class="insight-box">Targeting <b>{target_mood}</b> mood profile for <b>{selected_prod}</b></div>', unsafe_allow_html=True)
        
        # Simple similarity logic based on Mood and Hotness
        recs = df_articles[(df_articles['mood'] == target_mood) & (df_articles['prod_name'] != selected_prod)].head(6)
        
        cols = st.columns(3)
        for idx, (i, row) in enumerate(recs.iterrows()):
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:10px; background:white; text-align:center;">
                    <h5 style="color:#E50019;">{row['prod_name'][:25]}</h5>
                    <p>Price: <b>${row['price']:.4f}</b><br>Hotness: {row['hotness_score']:.2f}</p>
                    <span style="background:#f0f2f6; padding:2px 8px; border-radius:5px; font-size:0.8rem;">{row['mood']}</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No products found with current filter criteria.")

# ============================================================================
# PAGE 6: MODEL PERFORMANCE (Gap Analysis)
# ============================================================================
elif page == "📈 Model Performance":
    st.markdown('<h1 class="header-title">Model Performance & Validation</h1>', unsafe_allow_html=True)
    
    if not df_validation.empty:
        # Comparison logic from original code
        st.subheader("Inventory Supply vs. Actual Market Demand")
        inv_dist = df_articles['mood'].value_counts(normalize=True).reset_index()
        sales_dist = df_validation['actual_purchased_mood'].value_counts(normalize=True).reset_index()
        
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Bar(x=inv_dist['mood'], y=inv_dist['proportion'], name='Inventory Supply (AI Predictions)', marker_color='#E50019'))
        fig_perf.add_trace(go.Bar(x=sales_dist['actual_purchased_mood'], y=sales_dist['proportion'], name='Actual Sales Demand', marker_color='#333333'))
        
        fig_perf.update_layout(barmode='group', template='plotly_white')
        st.plotly_chart(fig_perf, use_container_width=True)
    else:
        st.error("Validation data not available.")

# Other pages (Product & Customer Intelligence)
elif page == "🔍 Product Intelligence":
    st.markdown('<h1 class="header-title">Product Intelligence</h1>', unsafe_allow_html=True)
    st.dataframe(filtered_df, use_container_width=True)

elif page == "👤 Customer Intelligence":
    st.markdown('<h1 class="header-title">Customer Intelligence</h1>', unsafe_allow_html=True)
    if not df_customers.empty:
        st.write("### Customer Segmentation Distribution")
        fig_seg = px.pie(df_customers, names='segment', color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.error("Customer data not found.")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown('<div style="text-align: center; color: #999;">Fashion Emotion BI Dashboard | Master Thesis | © 2026</div>', unsafe_allow_html=True)
