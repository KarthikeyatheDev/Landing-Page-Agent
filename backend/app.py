from flask import Flask, request, jsonify
from flasgger import Swagger
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
from flask_cors import CORS # Import CORS

# Suppress all warnings
warnings.filterwarnings("ignore")


app = Flask(__name__)
CORS(app) # Enable CORS for all origins and all routes
swagger = Swagger(app)

### 🔗 Load and Prepare Data

activity_log = pd.read_csv('dataset1_final.csv', low_memory=False)
transaction = pd.read_csv('dataset2_final.csv', low_memory=False)

# Standardize columns
activity_log.columns = activity_log.columns.str.lower()
transaction.columns = transaction.columns.str.lower()

# Merge datasets
merged_data = pd.concat([activity_log, transaction], ignore_index=True)

# Handle missing columns
for col in ['eventtimestamp', 'eventdate', 'gender', 'income_group', 'age', 'user_pseudo_id', 'event_name']:
    if col not in merged_data.columns:
        merged_data[col] = np.nan

# Date conversions
merged_data['eventtimestamp'] = pd.to_datetime(merged_data['eventtimestamp'], errors='coerce')
merged_data['eventdate'] = pd.to_datetime(merged_data['eventdate'], errors='coerce')

# Fill demographic missing values
merged_data['gender'].fillna('unknown', inplace=True)
merged_data['income_group'].fillna('unknown', inplace=True)


# Parse age
def parse_age(val):
    if pd.isnull(val):
        return np.nan
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        if '-' in val:
            parts = val.split('-')
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except:
                return np.nan
        if 'above' in val:
            return 70
        if val.isdigit():
            return float(val)
    return np.nan


merged_data['age'] = merged_data['age'].apply(parse_age)
merged_data['age'].fillna(merged_data['age'].median(), inplace=True)

# Session duration
session_df = merged_data.dropna(subset=['user_pseudo_id', 'eventtimestamp'])
if not session_df.empty:
    session_times = session_df.groupby('user_pseudo_id')['eventtimestamp'].agg(['min', 'max'])
    session_times['session_duration_sec'] = (session_times['max'] - session_times['min']).dt.total_seconds()
    merged_data = merged_data.merge(session_times['session_duration_sec'], on='user_pseudo_id', how='left')
else:
    merged_data['session_duration_sec'] = np.nan

# Page views
pageview_df = merged_data.dropna(subset=['user_pseudo_id', 'event_name'])
if not pageview_df.empty:
    page_views = pageview_df[pageview_df['event_name'] == 'page_view'].groupby('user_pseudo_id').size().reset_index(
        name='page_views')
    merged_data = merged_data.merge(page_views, on='user_pseudo_id', how='left')
    merged_data['page_views'].fillna(0, inplace=True)
else:
    merged_data['page_views'] = 0

# --- New: Segmentation with KMeans ---
# Prepare data for clustering
# Fill NaN values for clustering columns before scaling
merged_data['session_duration_sec'].fillna(0, inplace=True)
merged_data['page_views'].fillna(0, inplace=True)

# Select features for clustering
features_for_clustering = merged_data[['age', 'session_duration_sec', 'page_views']].copy()

# Scale the features
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features_for_clustering)

# Apply KMeans clustering
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10) # n_init added to suppress warning
merged_data['user_segment'] = kmeans.fit_predict(scaled_features)

# --- New: Behavioral Tags ---
def get_behavioral_tag(row):
    if row['session_duration_sec'] > 300 and row['page_views'] > 10:
        return "High Engager"
    elif row['session_duration_sec'] > 60 and row['page_views'] > 3:
        return "Browser"
    else:
        return "Quick Looker"

merged_data['behavioral_tag'] = merged_data.apply(get_behavioral_tag, axis=1)


### 🔥 Cold Start Recommendation Function

def cold_start_recommendation(city, device, source):
    filter_data = merged_data.copy()

    if city in filter_data['city'].dropna().unique():
        filter_data = filter_data[filter_data['city'] == city]

    if device in filter_data['category'].dropna().unique():
        filter_data = filter_data[filter_data['category'] == device]

    if source in filter_data['source'].dropna().unique():
        filter_data = filter_data[filter_data['source'] == source]

    if 'itemcategory' in filter_data.columns:
        grouped = filter_data.groupby('itemcategory').size().reset_index(name='count')
        top_items = grouped.sort_values('count', ascending=False).head(5)
        return top_items['itemcategory'].tolist()

    if 'itemcategory' not in filter_data.columns and 'item_category' in filter_data.columns:
        grouped = filter_data.groupby('item_category').size().reset_index(name='count')
        top_items = grouped.sort_values('count', ascending=False).head(5)
        return top_items['item_category'].tolist()

    return ["Accessories", "Apparel", "Footwear"]


### 🚀 API Routes


@app.route('/')
def home():
    return "✅ Landing Page Generator API is running! Go to /apidocs for Swagger UI."


@app.route('/generate-landing', methods=['POST'])
def generate_landing():
    """
    Generate Landing Page
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            city:
              type: string
              example: Mumbai
            device:
              type: string
              example: mobile
            source:
              type: string
              example: facebook
            user_id:
              type: string
              example: user123 # Added for segmentation lookup
    responses:
      200:
        description: Landing Page
        schema:
          type: object
          properties:
            hero_banner:
              type: string
            product_carousel:
              type: array
              items:
                type: string
            CTA:
              type: string
            user_segment:
              type: integer
            behavioral_tag:
              type: string
    """
    data = request.get_json()

    city = data.get('city', 'Unknown')
    device = data.get('device', 'mobile')
    source = data.get('source', 'organic')
    user_id = data.get('user_id', None) # Get user_id from request

    products = cold_start_recommendation(city, device, source)

    if products:
        hero_banner = f"Top picks in {products[0]}"
    else:
        hero_banner = "Top picks for you"

    # --- New: Dynamic CTA Text and Behavioral Tags based on user segment ---
    user_segment = None
    behavioral_tag = "Unknown"
    cta_text = "Shop Now" # Default CTA

    if user_id and user_id in merged_data['user_pseudo_id'].values:
        user_row = merged_data[merged_data['user_pseudo_id'] == user_id].iloc[0]
        user_segment = int(user_row['user_segment']) # Ensure it's an integer
        behavioral_tag = user_row['behavioral_tag']

        if user_segment == 0:
            cta_text = "Explore Now"
        elif user_segment == 1:
            cta_text = "See What’s Trending"
        elif user_segment == 2:
            cta_text = "Buy Now"
    else:
        # If user_id is not provided or not found, use a default segment/CTA
        # For demonstration, we can assign a default segment or pick one randomly
        # For now, we'll keep the default "Shop Now" and "Unknown" tag
        pass


    landing_page = {
        "hero_banner": hero_banner,
        "product_carousel": products,
        "CTA": cta_text,
        "user_segment": user_segment,
        "behavioral_tag": behavioral_tag
    }

    return jsonify(landing_page)


if __name__ == '__main__':
    app.run(debug=True)
