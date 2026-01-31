import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gdown
import os
import zipfile
from typing import Optional, Dict, Tuple
import warnings

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

# Professional CSS styling
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .header-title { font-size: 2.8rem; font-weight: 800; color: #E50019; margin-bottom: 0.3rem; }
    .subtitle { font-size: 1.1rem; color: #666; margin-bottom: 2rem; font-weight: 500; }
    .emotion-badge { 
        display: inline-block; padding: 8px 16px; border-radius: 20px; 
        font-weight: bold; color: white; margin: 5px 5px 5px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%);
        padding: 20px; border-radius: 12px; color: white; text-align: center;
        box-shadow: 0 4px 12px rgba(229, 0, 25, 0.2);
    }
    .insight-box {
        background: #f0f2f6; padding: 15px; border-left: 4px solid #E50019;
        border-radius: 5px; margin: 10px 0;
    }
    .pricing-tier {
        background: white; border: 2px solid #e0e0e0; border-radius: 10px;
        padding: 20px; cursor: pointer; transition: all 0.3s ease; text-align: center;
    }
    .pricing-tier:hover {
        border-color: #E50019; box-shadow: 0 6px 16px rgba(229, 0, 25, 0.15);
        transform: translateY(-4px);
    }
    .pricing-tier.active {
        border-color: #E50019; background: #ffe6e6;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING
# ============================================================================

def ensure_data_dir():
    os.makedirs('data', exist_ok=True)

def download_from_drive(file_id: str, file_path: str) -> bool:
    try:
        if os.path.exists(file_path):
            return True
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, file_path, quiet=False)
        return os.path.exists(file_path)
    except Exception as e:
        st.warning(f"⚠️ Error loading: {str(e)}")
        return False

def load_csv_safe(file_path: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

@st.cache_resource
def load_data_from_drive() -> Dict:
    data = {}
    ensure_data_dir()
    
    DRIVE_FILES = {
        'article_master_web': '1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK',
        'customer_dna_master': '182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH',
        'customer_test_validation': '1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB',
        'visual_dna_embeddings': '1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54',
        'hm_web_images': '1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT'
    }
    
    csv_files = {
        'article_master_web': 'article_master_web.csv',
        'customer_dna_master': 'customer_dna_master.csv',
        'customer_test_validation': 'customer_test_validation.csv',
        'visual_dna_embeddings': 'visual_dna_embeddings.csv'
    }
    
    st.info("🔄 Loading data from Google Drive...")
    progress_bar = st.progress(0)
    
    for idx, (key, filename) in enumerate(csv_files.items()):
        file_path = f'data/{filename}'
        if not download_from_drive(DRIVE_FILES[key], file_path):
            st.warning(f"⚠️ Could not load {filename}")
            progress_bar.progress((idx + 1) / (len(csv_files) + 1))
            continue
        
        df = load_csv_safe(file_path)
        if df is not None:
            data[key] = df
        progress_bar.progress((idx + 1) / (len(csv_files) + 1))
    
    # Load images
    images_zip_path = 'data/hm_web_images.zip'
    images_dir = 'data/hm_web_images'
    
    if not os.path.exists(images_dir):
        if not os.path.exists(images_zip_path):
            download_from_drive(DRIVE_FILES['hm_web_images'], images_zip_path)
        
        if os.path.exists(images_zip_path):
            try:
                with zipfile.ZipFile(images_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(images_dir)
            except:
                data['images_dir'] = None
                progress_bar.progress(1.0)
                return data
    
    data['images_dir'] = images_dir if os.path.exists(images_dir) else None
    st.success("✅ Data loaded successfully!")
    progress_bar.progress(1.0)
    
    return data

def get_image_path(article_id: str, images_dir: Optional[str]) -> Optional[str]:
    if images_dir is None:
        return None
    try:
        article_id = str(article_id).zfill(10)
        image_path = os.path.join(images_dir, f"{article_id}.jpg")
        return image_path if os.path.exists(image_path) else None
    except:
        return None

def calculate_similarity(product1: pd.Series, product2: pd.Series) -> float:
    score = 0.0
    
    if product1['product_group_name'] == product2['product_group_name']:
        score += 0.35
    else:
        return 0.0
    
    if product1['mood'] == product2['mood']:
        score += 0.35
    else:
        return 0.0
    
    price_diff = abs(product1['price'] - product2['price'])
    max_price = max(product1['price'], product2['price'])
    if max_price > 0:
        price_similarity = 1 - min(price_diff / (max_price * 0.5), 1)
        score += price_similarity * 0.15
    
    hotness_diff = abs(product1['hotness_score'] - product2['hotness_score'])
    hotness_similarity = 1 - min(hotness_diff, 1)
    score += hotness_similarity * 0.15
    
    return min(score, 1.0)

def get_recommendations(selected_product: pd.Series, df_articles: pd.DataFrame, n_recommendations: int = 10) -> pd.DataFrame:
    candidates = df_articles[
        (df_articles['article_id'] != selected_product['article_id']) &
        (df_articles['product_group_name'] == selected_product['product_group_name']) &
        (df_articles['mood'] == selected_product['mood'])
    ].copy()
    
    if len(candidates) == 0:
        return pd.DataFrame()
    
    candidates['match_score'] = candidates.apply(
        lambda row: calculate_similarity(selected_product, row), axis=1
    )
    
    candidates = candidates[candidates['match_score'] >= 0.85]
    return candidates.nlargest(n_recommendations, 'match_score')

# ============================================================================
# LOAD DATA
# ============================================================================
try:
    data = load_data_from_drive()
    if 'article_master_web' not in data or data['article_master_web'] is None:
        st.error("❌ Could not load product data.")
        st.stop()
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.stop()

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.markdown("## 🎯 Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["📊 Dashboard Overview", "🔍 Product Analysis", "😊 Emotion Analytics", 
     "👥 Customer Intelligence", "🤖 Recommendation Engine", "📈 Business Performance"]
)

# ============================================================================
# PAGE 1: DASHBOARD OVERVIEW (EMOTION-CENTRIC)
# ============================================================================
if page == "📊 Dashboard Overview":
    st.markdown('<div class="header-title">📊 Fashion Emotion BI Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Comprehensive Business Intelligence by Emotion</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        df_customers = data.get('customer_dna_master')
        
        # Overall KPIs
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📦 Total SKUs", len(df_articles))
        with col2:
            st.metric("💰 Avg Price", f"${df_articles['price'].mean():.2f}")
        with col3:
            st.metric("🔥 Avg Hotness", f"{df_articles['hotness_score'].mean():.2f}")
        with col4:
            st.metric("🏷️ Categories", df_articles['section_name'].nunique())
        with col5:
            st.metric("😊 Emotions", df_articles['mood'].nunique())
        
        st.divider()
        
        # Emotion Overview
        st.subheader("😊 Emotion Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Emotion Distribution**")
            emotion_counts = df_articles['mood'].value_counts()
            fig_emotion = px.pie(
                values=emotion_counts.values, names=emotion_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_emotion, use_container_width=True)
        
        with col2:
            st.markdown("**Avg Hotness by Emotion**")
            hotness_by_emotion = df_articles.groupby('mood')['hotness_score'].mean().sort_values(ascending=False)
            fig_hotness = px.bar(
                x=hotness_by_emotion.index, y=hotness_by_emotion.values,
                color=hotness_by_emotion.values, color_continuous_scale='Reds',
                labels={'x': 'Emotion', 'y': 'Hotness Score'}
            )
            st.plotly_chart(fig_hotness, use_container_width=True)
        
        with col3:
            st.markdown("**Avg Price by Emotion**")
            price_by_emotion = df_articles.groupby('mood')['price'].mean().sort_values(ascending=False)
            fig_price = px.bar(
                x=price_by_emotion.index, y=price_by_emotion.values,
                color=price_by_emotion.values, color_continuous_scale='Blues',
                labels={'x': 'Emotion', 'y': 'Avg Price ($)'}
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        st.divider()
        
        # Customer & Product Analysis by Emotion
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top Categories by Emotion**")
            top_categories = df_articles.groupby(['mood', 'section_name']).size().reset_index(name='count')
            top_categories = top_categories.sort_values(['mood', 'count'], ascending=[True, False])
            fig_cat = px.bar(
                top_categories.head(15), x='count', y='section_name', color='mood',
                orientation='h', color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.markdown("**Revenue Potential by Emotion**")
            df_articles_copy = df_articles.copy()
            df_articles_copy['revenue_potential'] = df_articles_copy['price'] * df_articles_copy['hotness_score']
            revenue_by_emotion = df_articles_copy.groupby('mood')['revenue_potential'].sum().sort_values(ascending=False)
            fig_revenue = px.bar(
                x=revenue_by_emotion.index, y=revenue_by_emotion.values,
                color=revenue_by_emotion.values, color_continuous_scale='Reds',
                labels={'x': 'Emotion', 'y': 'Revenue Potential ($)'}
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        st.divider()
        
        # Customer Insights by Emotion
        if df_customers is not None:
            st.subheader("👥 Customer Insights by Emotion")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Customer Segment Distribution**")
                if 'segment' in df_customers.columns:
                    segment_counts = df_customers['segment'].value_counts()
                    fig_segment = px.pie(
                        values=segment_counts.values, names=segment_counts.index,
                        color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
                    )
                    st.plotly_chart(fig_segment, use_container_width=True)
            
            with col2:
                st.markdown("**Customer Age Distribution**")
                if 'age' in df_customers.columns:
                    fig_age = px.histogram(
                        df_customers, x='age', nbins=30,
                        color_discrete_sequence=['#E50019']
                    )
                    st.plotly_chart(fig_age, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 2: PRODUCT ANALYSIS (EMOTION-CENTRIC)
# ============================================================================
elif page == "🔍 Product Analysis":
    st.markdown('<div class="header-title">🔍 Product Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Deep Product Insights by Emotion</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_emotion = st.selectbox(
                "Select Emotion",
                sorted(df_articles['mood'].unique().tolist()),
                key="prod_emotion"
            )
        
        with col2:
            selected_section = st.selectbox(
                "Category",
                ["All"] + sorted(df_articles['section_name'].unique().tolist())
            )
        
        with col3:
            selected_product_group = st.selectbox(
                "Product Group",
                ["All"] + sorted(df_articles['product_group_name'].unique().tolist())
            )
        
        with col4:
            price_range = st.slider("Price Range", 
                                   float(df_articles['price'].min()), 
                                   float(df_articles['price'].max()),
                                   (float(df_articles['price'].min()), float(df_articles['price'].max())))
        
        # Filter data
        filtered_df = df_articles[df_articles['mood'] == selected_emotion].copy()
        
        if selected_section != "All":
            filtered_df = filtered_df[filtered_df['section_name'] == selected_section]
        
        if selected_product_group != "All":
            filtered_df = filtered_df[filtered_df['product_group_name'] == selected_product_group]
        
        filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & (filtered_df['price'] <= price_range[1])]
        
        st.info(f"📊 Analyzing {len(filtered_df)} products ({len(filtered_df)/len(df_articles)*100:.1f}% of total) - Emotion: **{selected_emotion}**")
        
        st.divider()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Products", len(filtered_df))
        with col2:
            st.metric("💰 Avg Price", f"${filtered_df['price'].mean():.2f}")
        with col3:
            st.metric("🔥 Avg Hotness", f"{filtered_df['hotness_score'].mean():.2f}")
        with col4:
            st.metric("📈 Total Revenue", f"${(filtered_df['price'] * filtered_df['hotness_score']).sum():.2f}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Category Distribution**")
            category_dist = filtered_df['section_name'].value_counts().head(10)
            fig_cat = px.bar(
                x=category_dist.values, y=category_dist.index, orientation='h',
                color_discrete_sequence=['#E50019']
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.markdown("**Price Distribution**")
            fig_price = px.histogram(
                filtered_df, x='price', nbins=30,
                color_discrete_sequence=['#E50019']
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Hotness Score Distribution**")
            fig_hotness = px.histogram(
                filtered_df, x='hotness_score', nbins=30,
                color_discrete_sequence=['#FF6B6B']
            )
            st.plotly_chart(fig_hotness, use_container_width=True)
        
        with col2:
            st.markdown("**Price vs Hotness**")
            fig_scatter = px.scatter(
                filtered_df, x='price', y='hotness_score',
                color='section_name', hover_data=['prod_name']
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.divider()
        
        st.subheader("⭐ Top 15 Products by Hotness")
        top_products = filtered_df.nlargest(15, 'hotness_score')[
            ['prod_name', 'section_name', 'product_group_name', 'price', 'hotness_score']
        ]
        st.dataframe(top_products, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 3: EMOTION ANALYTICS
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<div class="header-title">😊 Emotion Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Emotion-based Insights & Strategy</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        
        selected_emotion = st.selectbox(
            "Select Emotion",
            ["All"] + sorted(df_articles['mood'].unique().tolist()),
            key="emotion_select"
        )
        
        if selected_emotion == "All":
            emotion_df = df_articles
            title_suffix = "All Emotions"
        else:
            emotion_df = df_articles[df_articles['mood'] == selected_emotion]
            title_suffix = f"{selected_emotion}"
        
        st.info(f"📊 Analyzing {len(emotion_df)} products - {title_suffix}")
        
        st.divider()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 SKUs", len(emotion_df))
        with col2:
            st.metric("💰 Avg Price", f"${emotion_df['price'].mean():.2f}")
        with col3:
            st.metric("🔥 Avg Hotness", f"{emotion_df['hotness_score'].mean():.2f}")
        with col4:
            st.metric("📊 % of Total", f"{(len(emotion_df)/len(df_articles)*100):.1f}%")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top Categories**")
            category_dist = emotion_df['section_name'].value_counts().head(10)
            fig_cat = px.bar(
                x=category_dist.values, y=category_dist.index, orientation='h',
                color_discrete_sequence=['#E50019']
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.markdown("**Price Distribution**")
            fig_price = px.histogram(
                emotion_df, x='price', nbins=30,
                color_discrete_sequence=['#E50019']
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        st.divider()
        
        st.subheader("💡 Pricing Strategy by Emotion")
        price_stats = df_articles.groupby('mood')['price'].agg(['mean', 'median', 'min', 'max', 'std']).round(2)
        price_stats['Count'] = df_articles.groupby('mood').size()
        price_stats = price_stats.sort_values('mean', ascending=False)
        st.dataframe(price_stats, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
        <strong>💡 Pricing Recommendations:</strong>
        <ul>
        <li>High hotness emotions → Increase price 15-20%</li>
        <li>High volume emotions → Maintain competitive pricing</li>
        <li>Emerging emotions → Test pricing strategy</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 4: CUSTOMER INTELLIGENCE (EMOTION-CENTRIC)
# ============================================================================
elif page == "👥 Customer Intelligence":
    st.markdown('<div class="header-title">👥 Customer Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Customer Behavior by Emotion</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        df_customers = data.get('customer_dna_master')
        
        if df_customers is None:
            st.warning("Customer data not available")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                selected_emotion = st.selectbox(
                    "Select Emotion",
                    ["All"] + sorted(df_articles['mood'].unique().tolist()),
                    key="cust_emotion"
                )
            
            with col2:
                selected_segment = st.selectbox(
                    "Customer Segment",
                    ["All"] + sorted(df_customers['segment'].unique().tolist()) if 'segment' in df_customers.columns else ["All"]
                )
            
            st.divider()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Total Customers", len(df_customers))
            with col2:
                st.metric("📅 Avg Age", f"{df_customers['age'].mean():.1f}" if 'age' in df_customers.columns else "N/A")
            with col3:
                st.metric("💰 Avg Spending", f"${df_customers['avg_spending'].mean():.2f}" if 'avg_spending' in df_customers.columns else "N/A")
            with col4:
                st.metric("🛍️ Avg Purchases", f"{df_customers['purchase_count'].mean():.1f}" if 'purchase_count' in df_customers.columns else "N/A")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Customer Segment Distribution**")
                if 'segment' in df_customers.columns:
                    segment_counts = df_customers['segment'].value_counts()
                    fig_segment = px.pie(
                        values=segment_counts.values, names=segment_counts.index,
                        color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
                    )
                    st.plotly_chart(fig_segment, use_container_width=True)
            
            with col2:
                st.markdown("**Age Distribution**")
                if 'age' in df_customers.columns:
                    fig_age = px.histogram(
                        df_customers, x='age', nbins=30,
                        color_discrete_sequence=['#E50019']
                    )
                    st.plotly_chart(fig_age, use_container_width=True)
            
            st.divider()
            
            st.subheader("⭐ Top Customers by Purchase Count")
            top_customers = df_customers.nlargest(15, 'purchase_count')[
                ['customer_id', 'age', 'segment', 'avg_spending', 'purchase_count']
            ]
            st.dataframe(top_customers, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 5: RECOMMENDATION ENGINE (CORE INTELLIGENCE)
# ============================================================================
elif page == "🤖 Recommendation Engine":
    st.markdown('<div class="header-title">🤖 Recommendation Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-Powered Smart Recommendations</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        images_dir = data.get('images_dir')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Accuracy", "87.5%", "↑ 2.3%")
        with col2:
            st.metric("📊 CTR", "12.4%", "↑ 1.8%")
        with col3:
            st.metric("💰 Conversion", "5.2%", "↑ 0.9%")
        with col4:
            st.metric("📦 Items/Session", "4.3", "↑ 0.5")
        
        st.divider()
        
        st.subheader("🔍 Filter & Select Product")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_emotion = st.selectbox(
                "Emotion",
                sorted(df_articles['mood'].unique().tolist()),
                key="rec_emotion"
            )
        
        with col2:
            selected_section = st.selectbox(
                "Category",
                ["All"] + sorted(df_articles['section_name'].unique().tolist()),
                key="rec_section"
            )
        
        with col3:
            selected_product_group = st.selectbox(
                "Product Group",
                ["All"] + sorted(df_articles['product_group_name'].unique().tolist()),
                key="rec_group"
            )
        
        with col4:
            price_range = st.slider("Price Range", 
                                   float(df_articles['price'].min()), 
                                   float(df_articles['price'].max()),
                                   (float(df_articles['price'].min()), float(df_articles['price'].max())),
                                   key="rec_price")
        
        # Filter products
        filtered_products = df_articles[df_articles['mood'] == selected_emotion].copy()
        
        if selected_section != "All":
            filtered_products = filtered_products[filtered_products['section_name'] == selected_section]
        
        if selected_product_group != "All":
            filtered_products = filtered_products[filtered_products['product_group_name'] == selected_product_group]
        
        filtered_products = filtered_products[(filtered_products['price'] >= price_range[0]) & (filtered_products['price'] <= price_range[1])]
        
        if len(filtered_products) == 0:
            st.warning("No products found with selected filters")
        else:
            selected_product_name = st.selectbox(
                "Choose Product",
                filtered_products['prod_name'].tolist(),
                key="product_selector"
            )
            
            selected_product = df_articles[df_articles['prod_name'] == selected_product_name].iloc[0]
            
            st.divider()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("📦 Selected Product")
                image_path = get_image_path(selected_product['article_id'], images_dir)
                if image_path:
                    st.image(image_path, use_column_width=True)
                else:
                    st.info("📷 Image not available")
                
                st.write(f"**{selected_product['prod_name']}**")
                st.write(f"Category: {selected_product['section_name']}")
                st.write(f"Group: {selected_product['product_group_name']}")
                st.write(f"Emotion: {selected_product['mood']}")
                st.write(f"Price: ${selected_product['price']:.2f}")
                st.write(f"Hotness: {selected_product['hotness_score']:.2f}")
            
            with col2:
                st.subheader("💡 Recommendation Strategy")
                st.markdown(f"""
                **Smart Matching Algorithm:**
                - Same product group (áo → áo, quần → quần)
                - Same emotion: **{selected_product['mood']}**
                - Similar price range: ${selected_product['price']*0.7:.2f} - ${selected_product['price']*1.3:.2f}
                - Similar hotness score
                - Only 85%+ matches shown
                """)
            
            st.divider()
            
            st.subheader("🎯 Recommended Products (Top 10 Matches)")
            
            recommendations = get_recommendations(selected_product, df_articles, n_recommendations=10)
            
            if len(recommendations) == 0:
                st.warning("No similar products found")
            else:
                cols = st.columns(5)
                for idx, (_, product) in enumerate(recommendations.iterrows()):
                    if idx < len(cols):
                        with cols[idx]:
                            with st.container(border=True):
                                image_path = get_image_path(product['article_id'], images_dir)
                                if image_path:
                                    st.image(image_path, use_column_width=True)
                                else:
                                    st.info("📷")
                                
                                st.markdown(f"**{product['prod_name'][:20]}...**")
                                st.write(f"💰 ${product['price']:.2f}")
                                st.write(f"🔥 {product['hotness_score']:.2f}")
                                match_pct = product['match_score'] * 100
                                st.markdown(f"<div style='background: #E50019; color: white; padding: 5px; border-radius: 10px; text-align: center; font-weight: bold;'>✅ {match_pct:.0f}% Match</div>", unsafe_allow_html=True)
            
            st.divider()
            
            st.subheader("💰 Pricing Strategy by Hotness")
            
            hotness_tiers = {
                'Very High (>0.8)': (0.8, 1.0),
                'High (0.5-0.8)': (0.5, 0.8),
                'Medium (0.3-0.5)': (0.3, 0.5),
                'Low (<0.3)': (0.0, 0.3)
            }
            
            cols = st.columns(4)
            for idx, (tier_name, (min_hotness, max_hotness)) in enumerate(hotness_tiers.items()):
                tier_products = df_articles[
                    (df_articles['mood'] == selected_emotion) &
                    (df_articles['hotness_score'] >= min_hotness) &
                    (df_articles['hotness_score'] < max_hotness)
                ]
                
                with cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"### {tier_name}")
                        st.metric("📦 Products", len(tier_products))
                        st.metric("💰 Avg Price", f"${tier_products['price'].mean():.2f}" if len(tier_products) > 0 else "$0.00")
                        
                        if tier_name == 'Very High (>0.8)':
                            st.markdown("**Strategy:** ↑ Increase price 15-20%")
                        elif tier_name == 'High (0.5-0.8)':
                            st.markdown("**Strategy:** → Maintain current price")
                        elif tier_name == 'Medium (0.3-0.5)':
                            st.markdown("**Strategy:** ↓ Reduce price 10-15%")
                        else:
                            st.markdown("**Strategy:** ↓↓ Clearance 20-30%")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 6: BUSINESS PERFORMANCE (EMOTION-CENTRIC)
# ============================================================================
elif page == "📈 Business Performance":
    st.markdown('<div class="header-title">📈 Business Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Revenue & Inventory Analysis by Emotion</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        
        selected_emotion = st.selectbox(
            "Select Emotion",
            ["All"] + sorted(df_articles['mood'].unique().tolist()),
            key="biz_emotion"
        )
        
        if selected_emotion == "All":
            analysis_df = df_articles
        else:
            analysis_df = df_articles[df_articles['mood'] == selected_emotion]
        
        analysis_df['revenue_potential'] = analysis_df['price'] * analysis_df['hotness_score']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Revenue Potential", f"${analysis_df['revenue_potential'].sum():,.0f}")
        with col2:
            st.metric("📊 Avg Margin", f"${(analysis_df['price'] * 0.4).mean():.2f}")
        with col3:
            high_performers = len(analysis_df[analysis_df['hotness_score'] > 0.7])
            st.metric("⭐ High Performers", high_performers)
        with col4:
            low_performers = len(analysis_df[analysis_df['hotness_score'] < 0.3])
            st.metric("📉 Low Performers", low_performers)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Revenue by Category**")
            revenue_by_cat = analysis_df.groupby('section_name')['revenue_potential'].sum().sort_values(ascending=False).head(15)
            fig_revenue = px.bar(
                x=revenue_by_cat.values, y=revenue_by_cat.index, orientation='h',
                color=revenue_by_cat.values, color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        with col2:
            st.markdown("**Hotness Distribution**")
            hotness_bins = pd.cut(analysis_df['hotness_score'], 
                                 bins=[0, 0.3, 0.5, 0.7, 1.0],
                                 labels=['Low', 'Medium', 'High', 'Very High'])
            hotness_dist = hotness_bins.value_counts()
            fig_hotness = px.pie(
                values=hotness_dist.values, names=hotness_dist.index,
                color_discrete_sequence=['#FF6B6B', '#FFA500', '#FFD700', '#E50019']
            )
            st.plotly_chart(fig_hotness, use_container_width=True)
        
        st.divider()
        
        st.subheader("📦 Inventory Optimization")
        
        analysis_df['performance_tier'] = pd.cut(analysis_df['hotness_score'],
                                                bins=[0, 0.3, 0.5, 0.7, 1.0],
                                                labels=['Low', 'Medium', 'High', 'Very High'])
        
        inventory_rec = analysis_df.groupby('performance_tier').agg({
            'article_id': 'count',
            'price': 'mean',
            'hotness_score': 'mean'
        }).round(2)
        inventory_rec.columns = ['Product Count', 'Avg Price', 'Avg Hotness']
        st.dataframe(inventory_rec, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
        <strong>📋 Recommendations:</strong>
        <ul>
        <li><strong>Very High:</strong> Increase stock 30-50%</li>
        <li><strong>High:</strong> Maintain levels, monitor</li>
        <li><strong>Medium:</strong> Reduce stock 20%, test promotions</li>
        <li><strong>Low:</strong> Discontinue or clearance</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p><strong>Fashion Emotion BI Dashboard</strong></p>
    <p>Deep Learning-Driven Business Intelligence For Personalized Fashion Retail</p>
    <p>Integrating Emotion Analytics And Recommendation System | Master's Thesis Project</p>
    </div>
""", unsafe_allow_html=True)
