import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gdown
import os
import zipfile
from typing import Optional, Dict, Tuple, List
import warnings
import urllib.request

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="H & M Fashion BI - Executive Dashboard",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .header-title { font-size: 3.5rem; font-weight: 900; background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; letter-spacing: -1px; }
    .subtitle { font-size: 1.2rem; color: #666; margin-bottom: 2rem; font-weight: 500; }
    
    .tier-premium { background: linear-gradient(135deg, #1e5631 0%, #40916c 100%); color: white; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-premium:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(30, 86, 49, 0.3); }
    
    .tier-trend { background: linear-gradient(135deg, #52b788 0%, #74c69d 100%); color: white; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-trend:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(82, 183, 136, 0.3); }
    
    .tier-stability { background: linear-gradient(135deg, #ffd60a 0%, #ffc300 100%); color: #333; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-stability:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(255, 214, 10, 0.3); }
    
    .tier-liquidation { background: linear-gradient(135deg, #ffb4a2 0%, #ff8b7b 100%); color: white; padding: 20px; border-radius: 12px; cursor: pointer; transition: all 0.3s; border: none; }
    .tier-liquidation:hover { transform: scale(1.05); box-shadow: 0 8px 16px rgba(255, 139, 123, 0.3); }
    
    .product-card { border: 2px solid #e0e0e0; border-radius: 12px; padding: 12px; text-align: center; transition: all 0.3s ease; background: white; }
    .product-card:hover { border-color: #E50019; box-shadow: 0 8px 20px rgba(229, 0, 25, 0.2); transform: translateY(-4px); }
    
    .detail-panel { background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border-left: 4px solid #E50019; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .insight-box { background: #f0f2f6; padding: 15px; border-left: 4px solid #E50019; border-radius: 5px; margin: 10px 0; }
    .metric-badge { background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); color: white; padding: 10px 15px; border-radius: 8px; font-weight: bold; display: inline-block; margin: 5px 5px 5px 0; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'selected_tier' not in st.session_state:
    st.session_state.selected_tier = None
if 'show_detail_modal' not in st.session_state:
    st.session_state.show_detail_modal = False
if 'detail_product_id' not in st.session_state:
    st.session_state.detail_product_id = None

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def ensure_data_dir():
    os.makedirs('data', exist_ok=True)

def download_from_drive(file_id: str, file_path: str) -> bool:
    """Download file from Google Drive with multiple fallback methods"""
    try:
        if os.path.exists(file_path):
            return True
        
        url = f"https://drive.google.com/uc?id={file_id}"
        
        try:
            gdown.download(url, file_path, quiet=False)
        except:
            try:
                urllib.request.urlretrieve(url, file_path)
            except:
                import requests
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
        
        return os.path.exists(file_path)
    except:
        return False

def load_csv_safe(file_path: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(file_path)
    except:
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
        if download_from_drive(DRIVE_FILES[key], file_path):
            df = load_csv_safe(file_path)
            if df is not None:
                data[key] = df
        progress_bar.progress((idx + 1) / (len(csv_files) + 1))
    
    # Load images
    images_zip_path = 'data/hm_web_images.zip'
    images_dir = 'data/hm_web_images'
    
    if not os.path.exists(images_dir):
        if not os.path.exists(images_zip_path):
            st.info("📥 Downloading images (this may take a few minutes)...")
            download_from_drive(DRIVE_FILES['hm_web_images'], images_zip_path)
        
        if os.path.exists(images_zip_path):
            try:
                st.info("📦 Extracting images...")
                os.makedirs(images_dir, exist_ok=True)
                with zipfile.ZipFile(images_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(images_dir)
                st.success("✅ Images extracted!")
            except Exception as e:
                st.warning(f"⚠️ Image extraction issue: {str(e)}")
    
    data['images_dir'] = images_dir if os.path.exists(images_dir) else None
    st.success("✅ Data loaded successfully!")
    progress_bar.progress(1.0)
    
    return data

def get_image_path(article_id: str, images_dir: Optional[str]) -> Optional[str]:
    """Get image path - images stored directly in folder as 10-digit ID + .jpg"""
    if images_dir is None:
        return None
    try:
        article_id_str = str(article_id).zfill(10)
        image_path = os.path.join(images_dir, f"{article_id_str}.jpg")
        
        if os.path.exists(image_path):
            return image_path
        
        # Fallback: try other extensions
        for ext in ['.JPG', '.jpeg', '.JPEG', '.png', '.PNG']:
            alt_path = os.path.join(images_dir, f"{article_id_str}{ext}")
            if os.path.exists(alt_path):
                return alt_path
        
        return None
    except:
        return None

def get_tier_info(hotness: float) -> Tuple[str, str, str]:
    """Return (tier_name, color_class, strategy)"""
    if hotness > 0.8:
        return ("💎 Premium Tier (>0.8)", "tier-premium", "Maximize Profit - Premium Branding")
    elif hotness > 0.5:
        return ("🔥 Trend Tier (0.5-0.8)", "tier-trend", "Push Marketing - Boost Visibility")
    elif hotness > 0.3:
        return ("⚖️ Stability Tier (0.3-0.5)", "tier-stability", "Gentle Discount 10-15%")
    else:
        return ("📉 Liquidation Tier (<0.3)", "tier-liquidation", "Clearance 20-30%")

def get_smart_recommendations(selected_product: pd.Series, df_articles: pd.DataFrame, 
                             n_recommendations: int = 10) -> pd.DataFrame:
    """Hybrid recommendation engine"""
    candidates = df_articles[
        (df_articles['article_id'] != selected_product['article_id']) &
        (df_articles['mood'] == selected_product['mood'])
    ].copy()
    
    if len(candidates) == 0:
        return pd.DataFrame()
    
    candidates['match_score'] = 0.0
    candidates['match_score'] += 0.4
    candidates['match_score'] += (candidates['section_name'] == selected_product['section_name']) * 0.2
    
    price_diff = abs(candidates['price'] - selected_product['price'])
    max_price = max(candidates['price'].max(), selected_product['price'])
    if max_price > 0:
        price_sim = 1 - (price_diff / (max_price * 0.5)).clip(0, 1)
        candidates['match_score'] += price_sim * 0.2
    
    hotness_diff = abs(candidates['hotness_score'] - selected_product['hotness_score'])
    hotness_sim = 1 - hotness_diff.clip(0, 1)
    candidates['match_score'] += hotness_sim * 0.2
    
    candidates = candidates[candidates['match_score'] >= 0.60]
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
st.sidebar.markdown("## 🎯 H & M Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["📊 Executive Pulse", "🔍 Inventory & Pricing", "😊 Emotion Analytics", 
     "👥 Customer DNA", "🤖 AI Recommendation", "📈 Performance & Financial"]
)

# ============================================================================
# PAGE 1: EXECUTIVE PULSE
# ============================================================================
if page == "📊 Executive Pulse":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Executive Pulse - Strategic Overview</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        df_customers = data.get('customer_dna_master')
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📦 Total SKUs", f"{len(df_articles):,}", "↑ 2.3%")
        with col2:
            st.metric("💰 Avg Price", f"${df_articles['price'].mean():.2f}", "↑ 1.2%")
        with col3:
            st.metric("🔥 Avg Hotness", f"{df_articles['hotness_score'].mean():.2f}", "↑ 0.8%")
        with col4:
            st.metric("👥 Customers", f"{len(df_customers):,}" if df_customers is not None else "N/A", "↑ 5.1%")
        with col5:
            df_articles['revenue_potential'] = df_articles['price'] * df_articles['hotness_score']
            st.metric("💵 Revenue Potential", f"${df_articles['revenue_potential'].sum():,.0f}", "↑ 3.4%")
        
        st.divider()
        
        st.subheader("😊 Emotion Matrix (Price vs Hotness vs Revenue)")
        
        emotion_stats = df_articles.groupby('mood').agg({
            'price': 'mean',
            'hotness_score': 'mean',
            'revenue_potential': 'sum',
            'article_id': 'count'
        }).reset_index()
        emotion_stats.columns = ['Emotion', 'Avg_Price', 'Avg_Hotness', 'Total_Revenue', 'Product_Count']
        
        fig_bubble = px.scatter(
            emotion_stats,
            x='Avg_Price',
            y='Avg_Hotness',
            size='Total_Revenue',
            color='Emotion',
            hover_data=['Product_Count', 'Total_Revenue'],
            title="Emotion Performance Matrix",
            labels={'Avg_Price': 'Average Price ($)', 'Avg_Hotness': 'Average Hotness Score'},
            color_discrete_sequence=px.colors.qualitative.Set2,
            size_max=60
        )
        fig_bubble.update_layout(height=500, showlegend=True)
        st.plotly_chart(fig_bubble, use_container_width=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Emotion Distribution**")
            emotion_counts = df_articles['mood'].value_counts()
            fig_dist = px.pie(
                values=emotion_counts.values,
                names=emotion_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            st.markdown("**Revenue by Emotion**")
            revenue_by_emotion = df_articles.groupby('mood')['revenue_potential'].sum().sort_values(ascending=False)
            fig_revenue = px.bar(
                x=revenue_by_emotion.index,
                y=revenue_by_emotion.values,
                color=revenue_by_emotion.values,
                color_continuous_scale='Reds',
                labels={'x': 'Emotion', 'y': 'Revenue Potential ($)'}
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 2: INVENTORY & PRICING INTELLIGENCE
# ============================================================================
elif page == "🔍 Inventory & Pricing":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Inventory & Pricing Intelligence - 4-Tier Strategy</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        images_dir = data.get('images_dir')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_emotion = st.selectbox(
                "Select Emotion",
                ["All"] + sorted(df_articles['mood'].unique().tolist()),
                key="inv_emotion"
            )
        
        with col2:
            selected_category = st.selectbox(
                "Category",
                ["All"] + sorted(df_articles['section_name'].unique().tolist())
            )
        
        with col3:
            selected_group = st.selectbox(
                "Product Group",
                ["All"] + sorted(df_articles['product_group_name'].unique().tolist())
            )
        
        # Filter data
        filtered_df = df_articles.copy()
        
        if selected_emotion != "All":
            filtered_df = filtered_df[filtered_df['mood'] == selected_emotion]
        
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df['section_name'] == selected_category]
        
        if selected_group != "All":
            filtered_df = filtered_df[filtered_df['product_group_name'] == selected_group]
        
        st.info(f"📊 Analyzing {len(filtered_df)} products")
        
        st.divider()
        
        # 4-Tier Strategy Buttons
        st.subheader("💰 4-Tier Pricing Strategy - Click to View Products")
        
        tier_data = {
            'premium': (0.8, 1.0, 'tier-premium', '💎 Premium Tier (>0.8)'),
            'trend': (0.5, 0.8, 'tier-trend', '🔥 Trend Tier (0.5-0.8)'),
            'stability': (0.3, 0.5, 'tier-stability', '⚖️ Stability Tier (0.3-0.5)'),
            'liquidation': (0.0, 0.3, 'tier-liquidation', '📉 Liquidation Tier (<0.3)')
        }
        
        cols = st.columns(4)
        
        for idx, (tier_key, (min_h, max_h, color_class, tier_label)) in enumerate(tier_data.items()):
            tier_products = filtered_df[
                (filtered_df['hotness_score'] >= min_h) &
                (filtered_df['hotness_score'] < max_h)
            ]
            
            avg_price = tier_products['price'].mean() if len(tier_products) > 0 else 0
            avg_hotness = tier_products['hotness_score'].mean() if len(tier_products) > 0 else 0
            
            with cols[idx]:
                if st.button(f"""
{tier_label}
📦 {len(tier_products)} products
💰 ${avg_price:.2f} avg
🔥 {avg_hotness:.2f} hotness
                """, key=f"tier_{tier_key}", use_container_width=True):
                    st.session_state.selected_tier = tier_key
        
        st.divider()
        
        # Display products for selected tier
        if st.session_state.selected_tier:
            tier_key = st.session_state.selected_tier
            min_h, max_h, color_class, tier_label = tier_data[tier_key]
            
            tier_products = filtered_df[
                (filtered_df['hotness_score'] >= min_h) &
                (filtered_df['hotness_score'] < max_h)
            ].sort_values('hotness_score', ascending=False)
            
            st.markdown(f"### {tier_label} - Top Products")
            
            if len(tier_products) > 0:
                cols = st.columns(5)
                
                for idx, (_, product) in enumerate(tier_products.head(20).iterrows()):
                    col_idx = idx % 5
                    
                    with cols[col_idx]:
                        with st.container(border=True):
                            image_path = get_image_path(product['article_id'], images_dir)
                            if image_path:
                                st.image(image_path, use_column_width=True)
                            else:
                                st.info("📷 No image")
                            
                            st.markdown(f"**{product['prod_name'][:25]}...**")
                            st.write(f"💰 ${product['price']:.2f}")
                            st.write(f"🔥 {product['hotness_score']:.2f}")
                            st.write(f"😊 {product['mood']}")
            else:
                st.warning("No products in this tier")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 3: DEEP EMOTION ANALYTICS
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Deep Emotion Analytics</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        
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
        
        st.subheader("📊 Emotion Statistics")
        
        emotion_stats = df_articles.groupby('mood')['price'].agg([
            ('Mean', 'mean'),
            ('Median', 'median'),
            ('Std Dev', 'std'),
            ('Min', 'min'),
            ('Max', 'max'),
            ('Count', 'count')
        ]).round(2)
        
        st.dataframe(emotion_stats, use_container_width=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Category Affinity by Emotion**")
            category_affinity = emotion_df['section_name'].value_counts().head(10)
            fig_cat = px.bar(
                x=category_affinity.values,
                y=category_affinity.index,
                orientation='h',
                color=category_affinity.values,
                color_continuous_scale='Reds'
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
        
        st.subheader("⭐ Top 10 Emotion Heroes")
        
        top_products = emotion_df.nlargest(10, 'hotness_score')[[
            'prod_name', 'section_name', 'price', 'hotness_score', 'mood'
        ]].reset_index(drop=True)
        
        top_products.index = top_products.index + 1
        st.dataframe(top_products, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 4: CUSTOMER DNA & BEHAVIOR
# ============================================================================
elif page == "👥 Customer DNA":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Customer DNA & Behavior</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        df_customers = data.get('customer_dna_master')
        df_transactions = data.get('customer_test_validation')
        
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
                    ["All"] + sorted(df_customers['segment'].unique().tolist()) if 'segment' in df_customers.columns else ["All"],
                    key="cust_segment"
                )
            
            # Filter customers based on segment
            filtered_customers = df_customers.copy()
            if selected_segment != "All":
                filtered_customers = filtered_customers[filtered_customers['segment'] == selected_segment]
            
            # Filter transactions by emotion if available
            filtered_transactions = df_transactions.copy() if df_transactions is not None else None
            if selected_emotion != "All" and filtered_transactions is not None:
                # Filter transactions by emotion (actual_purchased_mood)
                filtered_transactions = filtered_transactions[filtered_transactions['actual_purchased_mood'].str.contains(selected_emotion, case=False, na=False)]
                # Get customers who bought from this emotion
                emotion_customers = filtered_transactions['customer_id'].unique()
                filtered_customers = filtered_customers[filtered_customers['customer_id'].isin(emotion_customers)]
            
            st.divider()
            
            # Dynamic KPIs based on filters
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Customers", f"{len(filtered_customers):,}")
            with col2:
                avg_age = filtered_customers['age'].mean() if 'age' in filtered_customers.columns and len(filtered_customers) > 0 else 0
                st.metric("📅 Avg Age", f"{avg_age:.1f}")
            with col3:
                avg_spending = filtered_customers['avg_spending'].mean() if 'avg_spending' in filtered_customers.columns and len(filtered_customers) > 0 else 0
                st.metric("💰 Avg Spending", f"${avg_spending:.2f}")
            with col4:
                avg_purchases = filtered_customers['purchase_count'].mean() if 'purchase_count' in filtered_customers.columns and len(filtered_customers) > 0 else 0
                st.metric("🛍️ Avg Purchases", f"{avg_purchases:.1f}")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Spending vs Age**")
                if len(filtered_customers) > 0:
                    fig_scatter = px.scatter(
                        filtered_customers,
                        x='age',
                        y='avg_spending',
                        color='segment' if 'segment' in filtered_customers.columns else None,
                        hover_data=['purchase_count'],
                        color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.info("No data available for selected filters")
            
            with col2:
                st.markdown("**Segment Distribution**")
                if 'segment' in filtered_customers.columns and len(filtered_customers) > 0:
                    segment_counts = filtered_customers['segment'].value_counts()
                    fig_segment = px.pie(
                        values=segment_counts.values,
                        names=segment_counts.index,
                        color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
                    )
                    st.plotly_chart(fig_segment, use_container_width=True)
                else:
                    st.info("No segment data available")
            
            st.divider()
            
            st.subheader("⭐ Top Loyalists")
            
            if len(filtered_customers) > 0:
                top_customers = filtered_customers.nlargest(15, 'purchase_count')[[
                    'customer_id', 'age', 'segment', 'avg_spending', 'purchase_count'
                ]].reset_index(drop=True)
                
                # Add emotion column if transactions available
                if df_transactions is not None and len(df_transactions) > 0:
                    top_customers['emotion'] = top_customers['customer_id'].apply(
                        lambda cid: df_transactions[df_transactions['customer_id'] == cid]['actual_purchased_mood'].mode()[0] if len(df_transactions[df_transactions['customer_id'] == cid]) > 0 else 'N/A'
                    )
                    top_customers = top_customers[['customer_id', 'age', 'segment', 'emotion', 'avg_spending', 'purchase_count']]
                
                top_customers.index = top_customers.index + 1
                st.dataframe(top_customers, use_container_width=True)
            else:
                st.info("No customers found for selected filters")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 5: AI RECOMMENDATION ENGINE
# ============================================================================
elif page == "🤖 AI Recommendation":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI Recommendation Engine - Smart Discovery</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        images_dir = data.get('images_dir')
        
        st.subheader("🔍 Product Selection")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_emotion = st.selectbox(
                "Emotion",
                sorted(df_articles['mood'].unique().tolist()),
                key="rec_emotion"
            )
        
        with col2:
            selected_category = st.selectbox(
                "Category",
                ["All"] + sorted(df_articles['section_name'].unique().tolist()),
                key="rec_cat"
            )
        
        with col3:
            selected_group = st.selectbox(
                "Product Group",
                ["All"] + sorted(df_articles['product_group_name'].unique().tolist()),
                key="rec_group"
            )
        
        with col4:
            price_range = st.slider(
                "Price Range",
                float(df_articles['price'].min()),
                float(df_articles['price'].max()),
                (float(df_articles['price'].min()), float(df_articles['price'].max())),
                key="rec_price"
            )
        
        # Filter products
        filtered_products = df_articles[df_articles['mood'] == selected_emotion].copy()
        
        if selected_category != "All":
            filtered_products = filtered_products[filtered_products['section_name'] == selected_category]
        
        if selected_group != "All":
            filtered_products = filtered_products[filtered_products['product_group_name'] == selected_group]
        
        filtered_products = filtered_products[
            (filtered_products['price'] >= price_range[0]) &
            (filtered_products['price'] <= price_range[1])
        ]
        
        # Dynamic KPIs based on filters
        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📦 Products", f"{len(filtered_products):,}")
        with col2:
            avg_price = filtered_products['price'].mean() if len(filtered_products) > 0 else 0
            st.metric("💰 Avg Price", f"${avg_price:.2f}")
        with col3:
            avg_hotness = filtered_products['hotness_score'].mean() if len(filtered_products) > 0 else 0
            st.metric("🔥 Avg Hotness", f"{avg_hotness:.2f}")
        with col4:
            high_perf = len(filtered_products[filtered_products['hotness_score'] > 0.7])
            st.metric("⭐ High Performers", high_perf)
        with col5:
            filtered_products['revenue'] = filtered_products['price'] * filtered_products['hotness_score']
            total_revenue = filtered_products['revenue'].sum() if len(filtered_products) > 0 else 0
            st.metric("💵 Revenue Potential", f"${total_revenue:,.0f}")
        
        st.divider()
        
        if len(filtered_products) == 0:
            st.warning("No products found with selected filters")
        else:
            selected_product_name = st.selectbox(
                "Choose Product",
                filtered_products['prod_name'].tolist(),
                key="product_select"
            )
            
            selected_product = df_articles[df_articles['prod_name'] == selected_product_name].iloc[0]
            
            st.divider()
            
            st.subheader("📦 Main Product Spotlight")
            
            col_img, col_info = st.columns([1.2, 2])
            
            with col_img:
                image_path = get_image_path(selected_product['article_id'], images_dir)
                if image_path:
                    st.image(image_path, use_column_width=True)
                else:
                    st.info("📷 Image not available")
            
            with col_info:
                st.markdown(f"""
                ### {selected_product['prod_name']}
                
                **Category:** {selected_product['section_name']}  
                **Group:** {selected_product['product_group_name']}  
                **Emotion:** {selected_product['mood']}  
                """)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown(f"<div class='metric-badge'>💰 ${selected_product['price']:.2f}</div>", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"<div class='metric-badge'>🔥 {selected_product['hotness_score']:.2f}</div>", unsafe_allow_html=True)
                with col_c:
                    tier_name, _, _ = get_tier_info(selected_product['hotness_score'])
                    st.markdown(f"<div class='metric-badge'>{tier_name}</div>", unsafe_allow_html=True)
                
                with st.expander("📝 Full Description"):
                    st.write(selected_product.get('detail_desc', 'No description available'))
            
            st.divider()
            
            st.subheader("🎯 Smart Match Engine - Top 10 Similar Products")
            
            recommendations = get_smart_recommendations(selected_product, df_articles, n_recommendations=10)
            
            if len(recommendations) == 0:
                st.warning("No similar products found")
            else:
                cols = st.columns(5)
                
                for idx, (_, product) in enumerate(recommendations.iterrows()):
                    col_idx = idx % 5
                    
                    with cols[col_idx]:
                        with st.container(border=True):
                            image_path = get_image_path(product['article_id'], images_dir)
                            if image_path:
                                st.image(image_path, use_column_width=True)
                            else:
                                st.info("📷")
                            
                            st.markdown(f"**{product['prod_name'][:18]}...**")
                            st.write(f"💰 ${product['price']:.2f}")
                            st.write(f"🔥 {product['hotness_score']:.2f}")
                            
                            match_pct = product['match_score'] * 100
                            st.markdown(
                                f"<div style='background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); color: white; padding: 8px; border-radius: 10px; text-align: center; font-weight: bold; margin-top: 8px;'>✅ {match_pct:.0f}% Match</div>",
                                unsafe_allow_html=True
                            )
                            
                            if st.button("View", key=f"view_{product['article_id']}", use_container_width=True):
                                st.session_state.show_detail_modal = True
                                st.session_state.detail_product_id = product['article_id']
                                st.rerun()
            
            # Detail Modal for Recommended Products
            if st.session_state.show_detail_modal and st.session_state.detail_product_id:
                detail_product = df_articles[df_articles['article_id'] == st.session_state.detail_product_id]
                
                if len(detail_product) > 0:
                    detail_product = detail_product.iloc[0]
                    
                    st.divider()
                    st.subheader(f"🔍 Detailed View - {detail_product['prod_name']}")
                    
                    col_img, col_info = st.columns([1, 2])
                    
                    with col_img:
                        image_path = get_image_path(detail_product['article_id'], images_dir)
                        if image_path:
                            st.image(image_path, use_column_width=True)
                        else:
                            st.info("📷 Image not available")
                    
                    with col_info:
                        st.markdown(f"""
                        ### {detail_product['prod_name']}
                        
                        **Category:** {detail_product['section_name']}  
                        **Group:** {detail_product['product_group_name']}  
                        **Emotion:** {detail_product['mood']}  
                        **Article ID:** {detail_product['article_id']}  
                        
                        **Pricing & Performance:**
                        - Price: ${detail_product['price']:.2f}
                        - Hotness Score: {detail_product['hotness_score']:.2f}
                        - Tier: {get_tier_info(detail_product['hotness_score'])[0]}
                        """)
                    
                    st.markdown("**📝 Full Description:**")
                    st.write(detail_product.get('detail_desc', 'No description available'))
                    
                    if st.button("Close Details", key="close_detail"):
                        st.session_state.show_detail_modal = False
                        st.session_state.detail_product_id = None
                        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 6: PERFORMANCE & FINANCIAL OUTLOOK
# ============================================================================
elif page == "📈 Performance & Financial":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Performance & Financial Outlook</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        
        selected_emotion = st.selectbox(
            "Select Emotion",
            ["All"] + sorted(df_articles['mood'].unique().tolist()),
            key="perf_emotion"
        )
        
        if selected_emotion == "All":
            analysis_df = df_articles
        else:
            analysis_df = df_articles[df_articles['mood'] == selected_emotion]
        
        analysis_df['revenue_potential'] = analysis_df['price'] * analysis_df['hotness_score']
        analysis_df['estimated_margin'] = analysis_df['price'] * 0.4
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Revenue Potential", f"${analysis_df['revenue_potential'].sum():,.0f}")
        with col2:
            st.metric("📊 Avg Margin", f"${analysis_df['estimated_margin'].mean():.2f}")
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
                x=revenue_by_cat.values,
                y=revenue_by_cat.index,
                orientation='h',
                color=revenue_by_cat.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        with col2:
            st.markdown("**Hotness Performance**")
            hotness_bins = pd.cut(analysis_df['hotness_score'],
                                 bins=[0, 0.3, 0.5, 0.7, 1.0],
                                 labels=['Low', 'Medium', 'High', 'Very High'])
            hotness_dist = hotness_bins.value_counts()
            fig_hotness = px.pie(
                values=hotness_dist.values,
                names=hotness_dist.index,
                color_discrete_sequence=['#FF6B6B', '#FFA500', '#FFD700', '#E50019']
            )
            st.plotly_chart(fig_hotness, use_container_width=True)
        
        st.divider()
        
        st.subheader("📦 Inventory Health & Optimization")
        
        analysis_df['performance_tier'] = pd.cut(
            analysis_df['hotness_score'],
            bins=[0, 0.3, 0.5, 0.7, 1.0],
            labels=['Low', 'Medium', 'High', 'Very High']
        )
        
        inventory_rec = analysis_df.groupby('performance_tier').agg({
            'article_id': 'count',
            'price': 'mean',
            'hotness_score': 'mean',
            'revenue_potential': 'sum'
        }).round(2)
        
        inventory_rec.columns = ['Product Count', 'Avg Price', 'Avg Hotness', 'Total Revenue']
        st.dataframe(inventory_rec, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
        <strong>📋 Inventory Recommendations:</strong>
        <ul>
        <li><strong>Very High:</strong> Increase stock 30-50%</li>
        <li><strong>High:</strong> Maintain levels</li>
        <li><strong>Medium:</strong> Reduce stock 20%</li>
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
    <p><strong>H & M Fashion BI Dashboard</strong></p>
    <p>Deep Learning-Driven Business Intelligence For Personalized Fashion Retail</p>
    <p>Integrating Emotion Analytics And Recommendation System</p>
    </div>
""", unsafe_allow_html=True)
