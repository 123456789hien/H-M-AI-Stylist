import streamlit as st
import pandas as pd
import numpy as np
import os
import zipfile
import gdown
from typing import Optional, Tuple, Dict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Updated Google Drive file IDs from user
DRIVE_FILES = {
    'article_master_web': '1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK',
    'customer_dna_master': '182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH',
    'customer_test_validation': '1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB',
    'visual_dna_embeddings': '1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54',
    'hm_web_images': '1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT'
}

def ensure_data_dir():
    """Ensure data directory exists."""
    os.makedirs('data', exist_ok=True)

def download_from_drive(file_id: str, file_path: str, file_name: str) -> bool:
    """
    Download file from Google Drive with error handling.
    
    Args:
        file_id: Google Drive file ID
        file_path: Local file path to save
        file_name: Display name for logging
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_name} already exists locally")
            return True
        
        logger.info(f"📥 Downloading {file_name}...")
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, file_path, quiet=False)
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            logger.info(f"✅ Downloaded {file_name} ({file_size:.2f} MB)")
            return True
        else:
            logger.error(f"❌ Failed to download {file_name}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error downloading {file_name}: {str(e)}")
        return False

def load_csv_safe(file_path: str, file_name: str) -> Optional[pd.DataFrame]:
    """
    Safely load CSV file with error handling.
    
    Args:
        file_path: Path to CSV file
        file_name: Display name for logging
    
    Returns:
        DataFrame if successful, None otherwise
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"✅ Loaded {file_name}: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"❌ Error loading {file_name}: {str(e)}")
        return None

@st.cache_resource
def load_data_from_drive() -> Dict:
    """
    Load all datasets from Google Drive with comprehensive error handling.
    Returns a dictionary with all dataframes and image paths.
    """
    data = {}
    ensure_data_dir()
    
    # Load CSV files
    csv_files = {
        'article_master_web': 'article_master_web.csv',
        'customer_dna_master': 'customer_dna_master.csv',
        'customer_test_validation': 'customer_test_validation.csv',
        'visual_dna_embeddings': 'visual_dna_embeddings.csv'
    }
    
    st.info("🔄 Loading data from Google Drive...")
    progress_bar = st.progress(0)
    total_files = len(csv_files) + 1  # +1 for images
    current = 0
    
    for key, filename in csv_files.items():
        current += 1
        file_path = f'data/{filename}'
        
        # Download if not exists
        if not download_from_drive(DRIVE_FILES[key], file_path, filename):
            st.warning(f"⚠️ Could not download {filename}")
            progress_bar.progress(current / total_files)
            continue
        
        # Load CSV
        df = load_csv_safe(file_path, filename)
        if df is not None:
            data[key] = df
        
        progress_bar.progress(current / total_files)
    
    # Load and extract images
    images_zip_path = 'data/hm_web_images.zip'
    images_dir = 'data/hm_web_images'
    
    if not os.path.exists(images_dir):
        if not os.path.exists(images_zip_path):
            if not download_from_drive(DRIVE_FILES['hm_web_images'], images_zip_path, 'hm_web_images.zip'):
                st.warning("⚠️ Could not download product images")
                data['images_dir'] = None
                progress_bar.progress(1.0)
                return data
        
        # Extract zip
        if os.path.exists(images_zip_path):
            try:
                st.info("📦 Extracting product images...")
                with zipfile.ZipFile(images_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(images_dir)
                logger.info(f"✅ Extracted images to {images_dir}")
            except Exception as e:
                logger.error(f"❌ Error extracting images: {str(e)}")
                st.warning(f"⚠️ Could not extract images: {str(e)}")
                data['images_dir'] = None
                progress_bar.progress(1.0)
                return data
    
    current += 1
    progress_bar.progress(current / total_files)
    
    data['images_dir'] = images_dir if os.path.exists(images_dir) else None
    st.success("✅ All data loaded successfully!")
    
    return data

def get_image_path(article_id: str, images_dir: Optional[str]) -> Optional[str]:
    """
    Get the image path for a given article ID.
    
    Args:
        article_id: Product article ID
        images_dir: Directory containing images
    
    Returns:
        Image path if exists, None otherwise
    """
    if images_dir is None:
        return None
    
    try:
        article_id = str(article_id).zfill(10)
        image_path = os.path.join(images_dir, f"{article_id}.jpg")
        
        if os.path.exists(image_path):
            return image_path
    except Exception as e:
        logger.error(f"Error getting image path: {str(e)}")
    
    return None

def filter_products(df: pd.DataFrame, 
                   mood: Optional[str] = None,
                   price_range: Optional[Tuple[float, float]] = None,
                   color: Optional[str] = None,
                   hotness_min: Optional[float] = None) -> pd.DataFrame:
    """
    Filter products based on multiple criteria.
    
    Args:
        df: Products dataframe
        mood: Mood category to filter
        price_range: Tuple of (min_price, max_price)
        color: Color to filter
        hotness_min: Minimum hotness score
    
    Returns:
        Filtered dataframe
    """
    try:
        result = df.copy()
        
        if mood and mood != "All Moods":
            result = result[result['mood'] == mood]
        
        if price_range:
            result = result[(result['price'] >= price_range[0]) & (result['price'] <= price_range[1])]
        
        if color and color != "All Colors":
            result = result[result['perceived_colour_master_name'] == color]
        
        if hotness_min:
            result = result[result['hotness_score'] >= hotness_min]
        
        return result
    except Exception as e:
        logger.error(f"Error filtering products: {str(e)}")
        return df

def get_mood_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate statistics by mood category.
    
    Args:
        df: Products dataframe
    
    Returns:
        Statistics dataframe
    """
    try:
        stats = df.groupby('mood').agg({
            'price': ['mean', 'min', 'max', 'std'],
            'hotness_score': ['mean', 'max', 'min'],
            'article_id': 'count'
        }).round(2)
        
        stats.columns = ['Avg Price', 'Min Price', 'Max Price', 'Std Dev', 
                        'Avg Hotness', 'Max Hotness', 'Min Hotness', 'Count']
        
        return stats.reset_index()
    except Exception as e:
        logger.error(f"Error calculating mood stats: {str(e)}")
        return pd.DataFrame()

def validate_data(data: Dict) -> bool:
    """
    Validate loaded data for completeness and quality.
    
    Args:
        data: Dictionary of loaded dataframes
    
    Returns:
        True if data is valid, False otherwise
    """
    try:
        required_keys = ['article_master_web', 'customer_dna_master', 'customer_test_validation']
        
        for key in required_keys:
            if key not in data:
                logger.warning(f"Missing {key}")
                return False
            
            df = data[key]
            if df is None or len(df) == 0:
                logger.warning(f"{key} is empty")
                return False
        
        logger.info("✅ Data validation passed")
        return True
    except Exception as e:
        logger.error(f"Error validating data: {str(e)}")
        return False
