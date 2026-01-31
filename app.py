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

# Custom CSS for professional look (GIỮ NGUYÊN BỐ CỤC GỐC)
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
# DATA LOADING (FIXED WITH YOUR DRIVE LINKS)
# ============================================================================
@st.cache_resource
def load_all_data():
    file_ids = {
        "article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "hm_web_images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }

    for filename, fid in file_ids.items():
        if not os.path.exists(filename):
            try:
                url = f'https://drive.google.com/uc?id={fid}'
                gdown.download(url, filename, quiet=False)
            except: pass

    if os.path.exists("hm_web_images.zip") and not os.path.exists("images"):
        with zipfile.ZipFile("hm_web_images.zip", 'r') as zip_ref:
            zip_ref.extractall("images")

    try:
        df_art = pd.read_csv("article_master_web.csv")
        df_cust = pd.read_csv("customer_dna_master.csv")
        df_val = pd.read_csv("customer_test_validation.csv")
        
        df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
        df_art['revenue'] = df_art['hotness_score'] * df_art['price'] * 1000
        
        return df_art, df_cust, df_val
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None

df_articles, df_customers, df_validation = load_all_data()

# ============================================================================
# SIDEBAR NAVIGATION & FILTERS (FIXED: ADDED SECTION FILTER)
# ============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
    st.markdown("---")
    
    page = st.radio(
        "NAVIGATION",
        ["📊 Executive Dashboard", "🔍 Product Intelligence", "👤 Customer Intelligence", 
         "😊 Emotion Analytics", "🤖 Recommendation Engine", "📈 Pricing & Strategy"]
    )
    
    st.markdown("---")
    st.markdown("### FILTERS")
    
    # Filter 1: Section (Gender) - FIXED: ADDED THIS FILTER
    section_options = ["All"] + sorted(df_articles['section_name'].unique().tolist())
    selected_section = st.selectbox("Department / Section", section_options)
    
    # Filter 2: Category
    group_options = ["All"] + sorted(df_articles['product_group_name'].unique().tolist())
    selected_group = st.selectbox("Product Category", group_options)
    
    # Filter 3: Mood
    mood_options = ["All"] + sorted(df_articles['mood'].unique().tolist())
    selected_mood = st.selectbox("Emotional Mood", mood_options)

# Filter Logic
filtered_df = df_articles.copy()
if selected_section != "All":
    filtered_df = filtered_df[filtered_df['section_name'] == selected_section]
if selected_group != "All":
    filtered_df = filtered_df[filtered_df['product_group_name'] == selected_group]
if selected_mood != "All":
    filtered_df = filtered_df[filtered_df['mood'] == selected_mood]

# ============================================================================
# 1. EXECUTIVE DASHBOARD
# ============================================================================
if page == "📊 Executive Dashboard":
    st.markdown('<h1 class="header-title">Executive Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Driven Fashion Insights & Market Performance</p>', unsafe_allow_html=True)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f'<div class="metric-box"><h3>{len(filtered_df):,}</h3><p>Active Articles</p></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="metric-box"><h3>{filtered_df["hotness_score"].mean():.2f}</h3><p>Avg Hotness</p></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="metric-box"><h3>${filtered_df["price"].mean():.2f}</h3><p>Avg Price</p></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'<div class="metric-box"><h3>${filtered_df["revenue"].sum():,.0f}</h3><p>Est. Revenue</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Revenue by Category")
        rev_data = filtered_df.groupby('product_group_name')['revenue'].sum().sort_values(ascending=True).reset_index()
        # FIXED: barh error fix
        fig_rev = px.bar(rev_data, x='revenue', y='product_group_name', orientation='h', 
                         color='revenue', color_continuous_scale='Reds', template='plotly_white')
        st.plotly_chart(fig_rev, use_container_width=True)

    with col2:
        st.subheader("🎭 Market Mood Distribution")
        fig_mood = px.pie(filtered_df, names='mood', values='revenue', hole=0.4,
                          color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_mood, use_container_width=True)

# ============================================================================
# 2. PRODUCT INTELLIGENCE
# ============================================================================
elif page == "🔍 Product Intelligence":
    st.markdown('<h1 class="header-title">Product Intelligence</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(filtered_df[['article_id', 'prod_name', 'product_group_name', 'section_name', 'price', 'hotness_score', 'mood']], 
                     use_container_width=True, height=500)
    with col2:
        st.markdown('<div class="insight-box"><h3>Analysis</h3><p>Filter products by department and mood to identify top-performing fashion articles.</p></div>', unsafe_allow_html=True)
        # Category distribution
        cat_dist = filtered_df['product_group_name'].value_counts().reset_index()
        fig_cat = px.bar(cat_dist, x='count', y='product_group_name', orientation='h', title="Inventory Count by Category")
        st.plotly_chart(fig_cat, use_container_width=True)

# ============================================================================
# 3. CUSTOMER INTELLIGENCE
# ============================================================================
elif page == "👤 Customer Intelligence":
    st.markdown('<h1 class="header-title">Customer Intelligence</h1>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Customer Segments")
        fig_seg = px.pie(df_customers, names='segment', color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig_seg, use_container_width=True)
    with c2:
        st.subheader("Value Analysis")
        # FIXED: Scatter display with proper indexes
        fig_scat = px.scatter(df_customers.head(1000), x='age', y='avg_spending', color='segment', 
                              size='purchase_count', template='plotly_white')
        st.plotly_chart(fig_scat, use_container_width=True)
    
    st.subheader("Detailed DNA Database")
    st.dataframe(df_customers.head(100), use_container_width=True)

# ============================================================================
# 4. EMOTION ANALYTICS
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<h1 class="header-title">Emotion Analytics</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Mood Performance (Hotness)")
        mood_perf = filtered_df.groupby('mood')['hotness_score'].mean().sort_values().reset_index()
        fig_p = px.bar(mood_perf, x='hotness_score', y='mood', orientation='h', color='hotness_score', color_continuous_scale='Reds')
        st.plotly_chart(fig_p, use_container_width=True)
    with col2:
        st.subheader("Mood-based Pricing Strategy")
        fig_b = px.box(filtered_df, x='mood', y='price', color='mood')
        st.plotly_chart(fig_b, use_container_width=True)

# ============================================================================
# 5. RECOMMENDATION ENGINE (FIXED LOGIC)
# ============================================================================
elif page == "🤖 Recommendation Engine":
    st.markdown('<h1 class="header-title">AI Recommendation Engine</h1>', unsafe_allow_html=True)
    
    # Use available products from filtered list
    current_products = filtered_df['prod_name'].unique()
    if len(current_products) > 0:
        target_prod = st.selectbox("Select a reference product:", current_products)
        
        # Get mood of selected product
        prod_mood = df_articles[df_articles['prod_name'] == target_prod]['mood'].values[0]
        st.info(f"Target Mood detected: **{prod_mood}**. Finding similar items...")
        
        # FIXED: Logic to get different recommendations based on selection
        recs = df_articles[(df_articles['mood'] == prod_mood) & (df_articles['prod_name'] != target_prod)].head(6)
        
        cols = st.columns(3)
        for i, (idx, row) in enumerate(recs.iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:10px; background:white;">
                    <h5 style="color:#E50019; margin:0;">{row['prod_name'][:30]}</h5>
                    <p style="font-size:0.8rem; margin:5px 0;">ID: {row['article_id']}</p>
                    <p style="font-weight:bold;">${row['price']:.2f}</p>
                    <span style="background:#FFE5E5; color:#E50019; padding:2px 8px; border-radius:5px; font-size:0.7rem;">{row['mood']}</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No products found for the selected filters.")

# ============================================================================
# 6. PRICING & STRATEGY (FIXED: PAGE 6 RESTORED)
# ============================================================================
elif page == "📈 Pricing & Strategy":
    st.markdown('<h1 class="header-title">Pricing & Marketing Strategy</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("""
        <div class="insight-box">
        <h3>Pricing Insights</h3>
        <ul>
            <li><b>High Hotness (>0.7):</b> Maintain premium pricing.</li>
            <li><b>Moderate (0.4-0.7):</b> Seasonal promotions.</li>
            <li><b>Low (<0.4):</b> Inventory clearance recommended.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Scatter correlation
        fig_strat = px.scatter(filtered_df, x='price', y='hotness_score', color='mood',
                               hover_data=['prod_name'], title="Price vs. Hotness Correlation")
        st.plotly_chart(fig_strat, use_container_width=True)

    st.subheader("Model Validation (Inventory vs Demand)")
    # Logic from your original file
    inv_dist = df_articles['mood'].value_counts(normalize=True).reset_index()
    sales_dist = df_validation['actual_purchased_mood'].value_counts(normalize=True).reset_index()
    
    fig_val = go.Figure()
    fig_val.add_trace(go.Bar(x=inv_dist['mood'], y=inv_dist['proportion'], name='AI Predicted Inventory', marker_color='#E50019'))
    fig_val.add_trace(go.Bar(x=sales_dist['actual_purchased_mood'], y=sales_dist['proportion'], name='Actual Sales Demand', marker_color='#333333'))
    fig_val.update_layout(barmode='group', template='plotly_white')
    st.plotly_chart(fig_val, use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9rem;">
    <p><strong>Fashion Emotion BI Dashboard</strong> | Master Thesis Project</p>
    <p>© 2026 AI-Driven Business Intelligence Platform</p>
    </div>
""", unsafe_allow_html=True)
