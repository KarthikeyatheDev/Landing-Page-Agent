# Hyper-Personalized Landing Page Generator

## Overview
This project is an AI-powered prototype that dynamically generates hyper-personalized landing pages for new or guest users visiting an eCommerce website. It leverages historical user activity and transaction data to recommend content and product modules, even for first-time or anonymous visitors (solving the cold start problem).

**Key Features:**
- Analyzes historical data to infer user interests and segment preferences
- Recommends personalized landing page modules (hero banners, product carousels, CTAs)
- Handles cold start scenarios using fallback strategies based on region, device, source, and general trends
- Modern, interactive frontend UI

---

## Project Structure
```
Landpage Agent/
├── backend/
│   └── app.py           # Flask backend API
├── frontend/
│   └── index.html       # Frontend UI (HTML, CSS, JS)
├── dataset1_final.csv   # User activity data (ignored by git)
├── dataset2_final.csv   # Transaction data (ignored by git)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## How It Works

### Data Engineering & Segmentation
- Merges activity and transaction datasets
- Constructs user sessions and calculates engagement metrics
- Segments users using KMeans clustering on age, session duration, and page views
- Assigns behavioral tags (High Engager, Browser, Quick Looker)

### Cold Start Strategy
- For new/unknown users, recommends products based on available city, device, and source
- If no match, falls back to popular categories or a default demo list

### Personalization Logic
- Hero banner, product carousel, and CTA are dynamically generated based on user segment and behavioral tag
- If user ID is not found, a random segment and tag are assigned for demo purposes

---

## Running the Project

### 1. Install Python Dependencies
```
pip install -r requirements.txt
```

### 2. Start the Backend
```
cd backend
python app.py
```
The API will be available at `http://127.0.0.1:5000/`.

### 3. Start the Frontend
You can open `frontend/index.html` directly in your browser, but for best results (avoiding CORS issues):
```
cd frontend
python -m http.server 8000
```
Then visit [http://localhost:8000](http://localhost:8000) in your browser.

---

## API Endpoint
- `POST /generate-landing`
  - Request JSON: `{ "city": "Mumbai", "device": "mobile", "source": "facebook", "user_id": "user123" }`
  - Response JSON: `{ "hero_banner": ..., "product_carousel": [...], "CTA": ..., "user_segment": ..., "behavioral_tag": ... }`

---

## Customization & Demo
- Try different values for city, device, source, and user ID to see how the recommendations change.
- If user ID is not found, the backend assigns a random segment and tag for demo purposes.
- The UI is fully responsive and visually enhanced for a modern look.

---

## Evaluation Criteria
- **Data Engineering & Strategy:** Robust preprocessing and segmentation
- **Personalization Logic:** Dynamic, relevant recommendations
- **Cold Start Handling:** Effective fallback for new users
- **UI/UX:** Modern, clear, and interactive
- **Technical Execution:** Clean, modular code
- **Documentation:** Clear logic and usage instructions

---

## License
This project is for educational and demonstration purposes.
