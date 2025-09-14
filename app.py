import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
from pathlib import Path
import speech_recognition as sr
import webbrowser
# ------------------------------
# App Settings / Config
# ------------------------------
st.set_page_config(
    page_title="HealthHub • Drug Tools & Appointments",
    page_icon="💊",
    layout="wide"
)
EMERGENCY_NUMBER = "+918660965291"  # Replace with desired number

# ====== THEME TWEAKS (accessible & medical colors) ======
css = """
<style>
.stApp {
    background: radial-gradient( black 100%);
}

/* Updated Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #1a1a2e !important; /* A deep, dark blue */
}

/* Set all text inside the sidebar to white */
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Style for the radio buttons in the sidebar */
.stRadio > label {
    color: #ffffff !important;
}

.stRadio > label:hover {
    background-color: #2e2e4f !important; /* A slightly lighter dark blue on hover */
    border-radius: 8px;
    padding: 8px;
    color: #92e0ff !important; /* A light, vibrant blue on hover */
}

.stRadio > label > div > span {
    color: #ffffff !important;
}

/* Style for the sidebar title */
[data-testid="stSidebar"] h1 {
    color: #92e0ff !important;
    font-weight: bold;
}

/* Style for the sidebar caption */
[data-testid="stSidebar"] .st-cn {
    color: #a0a0c0 !important; /* A soft grey for less prominence */
}

.metric-card {
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 2px 16px rgba(0,0,0,.06);
    border: 1px solid #d6e4f0;
    background: gray;
}
.section {
    border-radius: 16px;
    padding: 18px 18px 4px 18px;
    box-shadow: 0 2px 16px rgba(0,0,0,.06);
    border: 1px solid #c9def1;
    background: #f5faff;
}
.pill {
    display:inline-block;
    padding: 4px 10px;
    border-radius:999px;
    background:#1f77d0;
    color:black !important;
    font-weight:600;
    font-size:12px;
}
.muted {
    color:black !important;
}

/* Force main content text color to black for readability on white background */
.stApp > header, .stApp > div {
    color: black !important;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)
red_button_css = """
<style>
div[data-testid="stButton"] > button.emergency-btn {
    background-color: red !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-size: 18px !important;
    box-shadow: 0px 4px 10px rgba(255,0,0,0.5) !important;
}
div[data-testid="stButton"] > button.emergency-btn:hover {
    background-color: darkred !important;
}
</style>
"""
st.markdown(red_button_css, unsafe_allow_html=True)

# Point to your FastAPI (from main.py). Change if your backend runs elsewhere.
BASE_URL = "http://127.0.0.1:8000"

# Where to store local appointments CSV
APPTS_CSV = "appointments.csv"

# ------------------------------
# Language Support
# ------------------------------

# Dictionary for translations
translations = {
    "English": {
        "title": "HealthHub",
        "caption": "Drug tools • Appointments • NLP",
        "navigate": "Navigate",
        "home": "🏠 Home",
        "drug_interaction": "💊 Drug Interaction",
        "dosage_by_age": "📏 Dosage by Age",
        "alternatives": "🔁 Alternatives",
        "nlp_extract": "🧠 NLP Extract",
        "image_to_text": "🖼️ Image to Text",
        "doctor_appointment": "📅 Doctor's Appointment",
        "appointments_admin": "📋 Appointments Admin",
        "welcome": "Welcome to **HealthHub**",
        "home_intro": "A clean, user-friendly portal for quick drug checks and booking doctor appointments.",
        "interactions_header": "💊 Drug Interaction Detection",
        "interactions_caption": "Enter a comma-separated list of drugs to check for harmful interactions.",
        "interactions_placeholder": "ibuprofen, warfarin, omeprazole",
        "interactions_button": "Check Interactions",
        "interactions_warning_input": "Please enter at least two drugs, separated by commas.",
        "interactions_warning_count": "Please enter at least two drugs.",
        "interactions_error": "Harmful interactions detected!",
        "interactions_success": "No harmful interactions detected.",
        "dosage_header": "📏 Age-Specific Dosage Recommendation",
        "drug_name": "Drug name",
        "age_label": "Patient age",
        "get_recommendation": "Get Recommendation",
        "alternatives_header": "🔁 Alternative Medication Suggestions",
        "alternatives_input": "Drug to find alternatives for",
        "suggest_alternatives": "Suggest Alternatives",
        "alternatives_success": "Alternatives for **{}**:",
        "alternatives_none": "No alternatives found.",
        "nlp_header": "🧠 NLP-Based Drug Information Extraction",
        "nlp_text_area": "Enter a medical text",
        "nlp_placeholder": "The patient was prescribed 200mg of ibuprofen to be taken twice a day.",
        "extract_info": "Extract Info",
        "nlp_warning_input": "Enter some text.",
        "nlp_success": "Extracted Information:",
        "nlp_no_info": "No drug information was extracted from the text.",
        "image_to_text_header": "🖼️ Image to Text (IBM Granite Vision)",
        "input_method": "Choose Input Method",
        "upload_image": "Upload Image",
        "capture_webcam": "Capture from Webcam",
        "image_uploader": "Upload an image",
        "image_camera": "Take a picture",
        "generate_description": "Generate Description",
        "description_success": "Generated Description",
        "booking_header": "📅 Book a Doctor's Appointment",
        "booking_caption": "Choose a doctor, pick a date and time, and leave your details. We'll hold your slot immediately.",
        "doctor": "Doctor",
        "mode": "Mode",
        "date": "Date",
        "time": "Time",
        "no_slots": "No slots available",
        "patient_details": "Patient Details",
        "full_name": "Full name",
        "email": "Email (optional)",
        "phone": "Phone",
        "age_patient": "Age",
        "gender": "Gender",
        "notes": "Describe your concern (optional)",
        "confirm_booking": "Confirm Booking",
        "required_fields_warning": "Name and phone are required.",
        "slot_taken_error": "Sorry, that slot was just taken. Please choose another time.",
        "booking_success": "✅ Appointment booked! Your reference ID is **{}**.",
        "view_details": "View booking details",
        "admin_header": "📋 Appointments Admin",
        "admin_caption": "View, filter, update status, and export all bookings.",
        "no_appointments": "No appointments yet.",
        "all": "All",
        "status": "Status",
        "from": "From",
        "to": "To",
        "download_csv": "⬇️ Download CSV",
        "update_status": "Update Status",
        "booking_id": "Booking ID",
        "new_status": "New status",
        "update_button": "Update",
        "status_updated": "Status updated.",
        "booking_id_not_found": "Booking ID not found."
    },
    "Kannada": {
        "title": "ಹೆಲ್ತ್ ಹಬ್",
        "caption": "ಔಷಧ ಪರಿಕರಗಳು • ನೇಮಕಾತಿಗಳು • ಎನ್‌ಎಲ್‌ಪಿ",
        "navigate": "ನ್ಯಾವಿಗೇಟ್ ಮಾಡಿ",
        "home": "🏠 ಮುಖಪುಟ",
        "drug_interaction": "💊 ಔಷಧ ಸಂವಹನ",
        "dosage_by_age": "📏 ವಯಸ್ಸಿನ ಪ್ರಕಾರ ಡೋಸೇಜ್",
        "alternatives": "🔁 ಪರ್ಯಾಯಗಳು",
        "nlp_extract": "🧠 ಎನ್‌ಎಲ್‌ಪಿ ಹೊರತೆಗೆಯುವಿಕೆ",
        "image_to_text": "🖼️ ಚಿತ್ರದಿಂದ ಪಠ್ಯ",
        "doctor_appointment": "📅 ವೈದ್ಯರ ನೇಮಕಾತಿ",
        "appointments_admin": "📋 ನೇಮಕಾತಿಗಳ ನಿರ್ವಾಹಕ",
        "welcome": "**ಹೆಲ್ತ್ ಹಬ್** ಗೆ ಸುಸ್ವಾಗತ",
        "home_intro": "ತ್ವರಿತ ಔಷಧ ಪರಿಶೀಲನೆ ಮತ್ತು ವೈದ್ಯರ ನೇಮಕಾತಿಗಾಗಿ ಒಂದು ಸ್ವಚ್ಛ, ಬಳಕೆದಾರ ಸ್ನೇಹಿ ಪೋರ್ಟಲ್.",
        "interactions_header": "💊 ಔಷಧ ಸಂವಹನ ಪತ್ತೆ",
        "interactions_caption": "ಹಾನಿಕಾರಕ ಸಂವಹನಗಳನ್ನು ಪರಿಶೀಲಿಸಲು ಕಾಮಾ-ವಿಭಜಿತ ಔಷಧಿಗಳ ಪಟ್ಟಿಯನ್ನು ನಮೂದಿಸಿ.",
        "interactions_placeholder": "ಐಬುಪ್ರೊಫೆನ್, ವಾರ್ಫರಿನ್, ಒಮೆಪ್ರಜೋಲ್",
        "interactions_button": "ಸಂವಹನಗಳನ್ನು ಪರಿಶೀಲಿಸಿ",
        "interactions_warning_input": "ದಯವಿಟ್ಟು ಕನಿಷ್ಠ ಎರಡು ಔಷಧಿಗಳನ್ನು ಕಾಮಾದಿಂದ ಬೇರ್ಪಡಿಸಿ ನಮೂದಿಸಿ.",
        "interactions_warning_count": "ದಯವಿಟ್ಟು ಕನಿಷ್ಠ ಎರಡು ಔಷಧಿಗಳನ್ನು ನಮೂದಿಸಿ.",
        "interactions_error": "ಹಾನಿಕಾರಕ ಸಂವಹನಗಳು ಪತ್ತೆಯಾಗಿವೆ!",
        "interactions_success": "ಯಾವುದೇ ಹಾನಿಕಾರಕ ಸಂವಹನಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ.",
        "dosage_header": "📏 ವಯಸ್ಸು-ನಿರ್ದಿಷ್ಟ ಡೋಸೇಜ್ ಶಿಫಾರಸು",
        "drug_name": "ಔಷಧದ ಹೆಸರು",
        "age_label": "ರೋಗಿಯ ವಯಸ್ಸು",
        "get_recommendation": "ಶಿಫಾರಸು ಪಡೆಯಿರಿ",
        "alternatives_header": "🔁 ಪರ್ಯಾಯ ಔಷಧಿಗಳ ಸಲಹೆಗಳು",
        "alternatives_input": "ಪರ್ಯಾಯಗಳನ್ನು ಹುಡುಕಲು ಔಷಧ",
        "suggest_alternatives": "ಪರ್ಯಾಯಗಳನ್ನು ಸೂಚಿಸಿ",
        "alternatives_success": "**{}** ಗಾಗಿ ಪರ್ಯಾಯಗಳು:",
        "alternatives_none": "ಯಾವುದೇ ಪರ್ಯಾಯಗಳು ಕಂಡುಬಂದಿಲ್ಲ.",
        "nlp_header": "🧠 ಎನ್‌ಎಲ್‌ಪಿ ಆಧಾರಿತ ಔಷಧ ಮಾಹಿತಿ ಹೊರತೆಗೆಯುವಿಕೆ",
        "nlp_text_area": "ವೈದ್ಯಕೀಯ ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ",
        "nlp_placeholder": "ರೋಗಿಗೆ ದಿನಕ್ಕೆ ಎರಡು ಬಾರಿ 200mg ಐಬುಪ್ರೊಫೆನ್ ತೆಗೆದುಕೊಳ್ಳಲು ಸೂಚಿಸಲಾಗಿತ್ತು.",
        "extract_info": "ಮಾಹಿತಿಯನ್ನು ಹೊರತೆಗೆಯಿರಿ",
        "nlp_warning_input": "ಕೆಲವು ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ.",
        "nlp_success": "ಹೊರತೆಗೆದ ಮಾಹಿತಿ:",
        "nlp_no_info": "ಪಠ್ಯದಿಂದ ಯಾವುದೇ ಔಷಧ ಮಾಹಿತಿಯನ್ನು ಹೊರತೆಗೆಯಲಾಗಿಲ್ಲ.",
        "image_to_text_header": "🖼️ ಚಿತ್ರದಿಂದ ಪಠ್ಯ (ಐಬಿಎಂ ಗ್ರಾನೈಟ್ ವಿಷನ್)",
        "input_method": "ಇನ್ಪುಟ್ ವಿಧಾನವನ್ನು ಆರಿಸಿ",
        "upload_image": "ಚಿತ್ರವನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಿ",
        "capture_webcam": "ವೆಬ್‌ಕ್ಯಾಮ್‌ನಿಂದ ಸೆರೆಹಿಡಿಯಿರಿ",
        "image_uploader": "ಚಿತ್ರವನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಿ",
        "image_camera": "ಚಿತ್ರವನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ",
        "generate_description": "ವಿವರಣೆಯನ್ನು ರಚಿಸಿ",
        "description_success": "ರಚಿತವಾದ ವಿವರಣೆ",
        "booking_header": "📅 ವೈದ್ಯರ ನೇಮಕಾತಿಯನ್ನು ಕಾಯ್ದಿರಿಸಿ",
        "booking_caption": "ವೈದ್ಯರನ್ನು ಆಯ್ಕೆಮಾಡಿ, ದಿನಾಂಕ ಮತ್ತು ಸಮಯವನ್ನು ಆರಿಸಿ ಮತ್ತು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ನೀಡಿ. ನಾವು ನಿಮ್ಮ ಸ್ಲಾಟ್ ಅನ್ನು ತಕ್ಷಣವೇ ಕಾಯ್ದಿರಿಸುತ್ತೇವೆ.",
        "doctor": "ವೈದ್ಯರು",
        "mode": "ಮೋಡ್",
        "date": "ದಿನಾಂಕ",
        "time": "ಸಮಯ",
        "no_slots": "ಯಾವುದೇ ಸ್ಲಾಟ್‌ಗಳು ಲಭ್ಯವಿಲ್ಲ",
        "patient_details": "ರೋಗಿಯ ವಿವರಗಳು",
        "full_name": "ಪೂರ್ಣ ಹೆಸರು",
        "email": "ಇಮೇಲ್ (ಐಚ್ಛಿಕ)",
        "phone": "ಫೋನ್",
        "age_patient": "ವಯಸ್ಸು",
        "gender": "ಲಿಂಗ",
        "notes": "ನಿಮ್ಮ ಸಮಸ್ಯೆಯನ್ನು ವಿವರಿಸಿ (ಐಚ್ಛಿಕ)",
        "confirm_booking": "ಬುಕಿಂಗ್ ದೃಢೀಕರಿಸಿ",
        "required_fields_warning": "ಹೆಸರು ಮತ್ತು ಫೋನ್ ಅಗತ್ಯವಿದೆ.",
        "slot_taken_error": "ಕ್ಷಮಿಸಿ, ಆ ಸ್ಲಾಟ್ ಅನ್ನು ಈಗಷ್ಟೇ ತೆಗೆದುಕೊಳ್ಳಲಾಗಿದೆ. ದಯವಿಟ್ಟು ಬೇರೆ ಸಮಯವನ್ನು ಆರಿಸಿ.",
        "booking_success": "✅ ನೇಮಕಾತಿಯನ್ನು ಕಾಯ್ದಿರಿಸಲಾಗಿದೆ! ನಿಮ್ಮ ಉಲ್ಲೇಖ ಐಡಿ **{}** ಆಗಿದೆ.",
        "view_details": "ಬುಕಿಂಗ್ ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
        "admin_header": "📋 ನೇಮಕಾತಿಗಳ ನಿರ್ವಾಹಕ",
        "admin_caption": "ಎಲ್ಲಾ ಬುಕಿಂಗ್‌ಗಳನ್ನು ವೀಕ್ಷಿಸಿ, ಫಿಲ್ಟರ್ ಮಾಡಿ, ಸ್ಥಿತಿಯನ್ನು ನವೀಕರಿಸಿ ಮತ್ತು ರಫ್ತು ಮಾಡಿ.",
        "no_appointments": "ಇನ್ನೂ ಯಾವುದೇ ನೇಮಕಾತಿಗಳಿಲ್ಲ.",
        "all": "ಎಲ್ಲಾ",
        "status": "ಸ್ಥಿತಿ",
        "from": "ಇಂದ",
        "to": "ಗೆ",
        "download_csv": "⬇️ ಸಿಎಸ್‌ವಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
        "update_status": "ಸ್ಥಿತಿಯನ್ನು ನವೀಕರಿಸಿ",
        "booking_id": "ಬುಕಿಂಗ್ ಐಡಿ",
        "new_status": "ಹೊಸ ಸ್ಥಿತಿ",
        "update_button": "ನವೀಕರಿಸಿ",
        "status_updated": "ಸ್ಥಿತಿಯನ್ನು ನವೀಕರಿಸಲಾಗಿದೆ.",
        "booking_id_not_found": "ಬುಕಿಂಗ್ ಐಡಿ ಕಂಡುಬಂದಿಲ್ಲ."
    },
    "Hindi": {
        "title": "हेल्थ हब",
        "caption": "ड्रग टूल्स • अपॉइंटमेंट • एनएलपी",
        "navigate": "नेविगेट करें",
        "home": "🏠 होम",
        "drug_interaction": "💊 ड्रग इंटरेक्शन",
        "dosage_by_age": "📏 उम्र के अनुसार खुराक",
        "alternatives": "🔁 विकल्प",
        "nlp_extract": "🧠 एनएलपी एक्सट्रैक्ट",
        "image_to_text": "🖼️ इमेज से टेक्स्ट",
        "doctor_appointment": "📅 डॉक्टर का अपॉइंटमेंट",
        "appointments_admin": "📋 अपॉइंटमेंट एडमिन",
        "welcome": "**हेल्थ हब** में आपका स्वागत है",
        "home_intro": "त्वरित दवा जांच और डॉक्टर अपॉइंटमेंट बुक करने के लिए एक स्वच्छ, उपयोगकर्ता-अनुकूल पोर्टल।",
        "interactions_header": "💊 ड्रग इंटरेक्शन डिटेक्शन",
        "interactions_caption": "हानिकारक इंटरैक्शन की जांच करने के लिए दवाओं की अल्पविराम-पृथक सूची दर्ज करें।",
        "interactions_placeholder": "इबुप्रोफेन, वारफेरिन, ओमेप्राजोल",
        "interactions_button": "इंटरैक्शन जांचें",
        "interactions_warning_input": "कृपया अल्पविराम से अलग की गई कम से कम दो दवाएं दर्ज करें।",
        "interactions_warning_count": "कृपया कम से कम दो दवाएं दर्ज करें।",
        "interactions_error": "हानिकारक इंटरैक्शन का पता चला!",
        "interactions_success": "कोई हानिकारक इंटरैक्शन का पता नहीं चला।",
        "dosage_header": "📏 आयु-विशिष्ट खुराक सिफारिश",
        "drug_name": "दवा का नाम",
        "age_label": "रोगी की उम्र",
        "get_recommendation": "सिफारिश प्राप्त करें",
        "alternatives_header": "🔁 वैकल्पिक दवा सुझाव",
        "alternatives_input": "विकल्प खोजने के लिए दवा",
        "suggest_alternatives": "विकल्प सुझाएं",
        "alternatives_success": "**{}** के लिए विकल्प:",
        "alternatives_none": "कोई विकल्प नहीं मिला।",
        "nlp_header": "🧠 एनएलपी-आधारित दवा जानकारी निष्कर्षण",
        "nlp_text_area": "एक मेडिकल टेक्स्ट दर्ज करें",
        "nlp_placeholder": "रोगी को दिन में दो बार 200mg इबुप्रोफेन लेने की सलाह दी गई थी।",
        "extract_info": "जानकारी निकालें",
        "nlp_warning_input": "कुछ टेक्स्ट दर्ज करें।",
        "nlp_success": "निकाली गई जानकारी:",
        "nlp_no_info": "टेक्स्ट से कोई दवा जानकारी नहीं निकाली गई।",
        "image_to_text_header": "🖼️ इमेज से टेक्स्ट (आईबीएम ग्रेनाइट विजन)",
        "input_method": "इनपुट विधि चुनें",
        "upload_image": "इमेज अपलोड करें",
        "capture_webcam": "वेबकैम से कैप्चर करें",
        "image_uploader": "एक इमेज अपलोड करें",
        "image_camera": "एक तस्वीर लें",
        "generate_description": "विवरण उत्पन्न करें",
        "description_success": "उत्पन्न विवरण",
        "booking_header": "📅 डॉक्टर का अपॉइंटमेंट बुक करें",
        "booking_caption": "एक डॉक्टर चुनें, एक तारीख और समय चुनें, और अपने विवरण छोड़ दें। हम तुरंत आपकी स्लॉट आरक्षित कर देंगे।",
        "doctor": "डॉक्टर",
        "mode": "मोड",
        "date": "दिनांक",
        "time": "समय",
        "no_slots": "कोई स्लॉट उपलब्ध नहीं",
        "patient_details": "रोगी का विवरण",
        "full_name": "पूरा नाम",
        "email": "ईमेल (वैकल्पिक)",
        "phone": "फ़ोन",
        "age_patient": "उम्र",
        "gender": "लिंग",
        "notes": "अपनी चिंता का वर्णन करें (वैकल्पिक)",
        "confirm_booking": "बुकिंग की पुष्टि करें",
        "required_fields_warning": "नाम और फ़ोन आवश्यक हैं।",
        "slot_taken_error": "क्षमा करें, वह स्लॉट अभी लिया गया है। कृपया कोई और समय चुनें।",
        "booking_success": "✅ अपॉइंटमेंट बुक हो गया! आपका संदर्भ आईडी **{}** है।",
        "view_details": "बुकिंग विवरण देखें",
        "admin_header": "📋 अपॉइंटमेंट एडमिन",
        "admin_caption": "सभी बुकिंग देखें, फ़िल्टर करें, स्थिति अपडेट करें और निर्यात करें।",
        "no_appointments": "अभी तक कोई अपॉइंटमेंट नहीं है।",
        "all": "सभी",
        "status": "स्थिति",
        "from": "से",
        "to": "तक",
        "download_csv": "⬇️ सीएसवी डाउनलोड करें",
        "update_status": "स्थिति अपडेट करें",
        "booking_id": "बुकिंग आईडी",
        "new_status": "नई स्थिति",
        "update_button": "अपडेट करें",
        "status_updated": "स्थिति अपडेट की गई।",
        "booking_id_not_found": "बुकिंग आईडी नहीं मिली।"
    },
    "Telugu": {
        "title": "హెల్త్ హబ్",
        "caption": "మందుల సాధనాలు • అపాయింట్‌మెంట్‌లు • NLP",
        "navigate": "నావిగేట్ చేయండి",
        "home": "🏠 హోమ్",
        "drug_interaction": "💊 మందుల పరస్పర చర్య",
        "dosage_by_age": "📏 వయస్సు ప్రకారం మోతాదు",
        "alternatives": "🔁 ప్రత్యామ్నాయాలు",
        "nlp_extract": "🧠 NLP సంగ్రహణ",
        "image_to_text": "🖼️ చిత్రం నుండి వచనం",
        "doctor_appointment": "📅 డాక్టర్ అపాయింట్‌మెంట్",
        "appointments_admin": "📋 అపాయింట్‌మెంట్‌ల అడ్మిన్",
        "welcome": "**హెల్త్ హబ్** కు స్వాగతం",
        "home_intro": "త్వరిత మందుల తనిఖీలు మరియు డాక్టర్ అపాయింట్‌మెంట్‌లు బుక్ చేయడానికి ఒక శుభ్రమైన, వినియోగదారు-స్నేహపూర్వక పోర్టల్.",
        "interactions_header": "💊 మందుల పరస్పర చర్య గుర్తింపు",
        "interactions_caption": "హానికరమైన పరస్పర చర్యలను తనిఖీ చేయడానికి కామా-విభజిత మందుల జాబితాను నమోదు చేయండి.",
        "interactions_placeholder": "ఐబుప్రోఫెన్, వార్ఫరిన్, ఒమెప్రజోల్",
        "interactions_button": "పరస్పర చర్యలను తనిఖీ చేయండి",
        "interactions_warning_input": "దయచేసి కనీసం రెండు మందులను, కామాలతో వేరు చేసి నమోదు చేయండి.",
        "interactions_warning_count": "దయచేసి కనీసం రెండు మందులను నమోదు చేయండి.",
        "interactions_error": "హానికరమైన పరస్పర చర్యలు గుర్తించబడ్డాయి!",
        "interactions_success": "హానికరమైన పరస్పర చర్యలు గుర్తించబడలేదు.",
        "dosage_header": "📏 వయస్సు-నిర్దిష్ట మోతాదు సిఫార్సు",
        "drug_name": "మందు పేరు",
        "age_label": "రోగి వయస్సు",
        "get_recommendation": "సిఫార్సు పొందండి",
        "alternatives_header": "🔁 ప్రత్యామ్నాయ మందుల సూచనలు",
        "alternatives_input": "ప్రత్యామ్నాయాల కోసం మందు",
        "suggest_alternatives": "ప్రత్యామ్నాయాలను సూచించండి",
        "alternatives_success": "**{}** కోసం ప్రత్యామ్నాయాలు:",
        "alternatives_none": "ప్రత్యామ్నాయాలు కనుగొనబడలేదు.",
        "nlp_header": "🧠 NLP-ఆధారిత మందుల సమాచారం సంగ్రహణ",
        "nlp_text_area": "వైద్య వచనాన్ని నమోదు చేయండి",
        "nlp_placeholder": "రోగికి రోజుకు రెండుసార్లు 200mg ఐబుప్రోఫెన్ తీసుకోవాలని సూచించబడింది.",
        "extract_info": "సమాచారాన్ని సంగ్రహించండి",
        "nlp_warning_input": "కొంత వచనాన్ని నమోదు చేయండి.",
        "nlp_success": "సంగ్రహించబడిన సమాచారం:",
        "nlp_no_info": "వచనం నుండి మందుల సమాచారం సంగ్రహించబడలేదు.",
        "image_to_text_header": "🖼️ చిత్రం నుండి వచనం (IBM గ్రానైట్ విజన్)",
        "input_method": "ఇన్‌పుట్ పద్ధతిని ఎంచుకోండి",
        "upload_image": "చిత్రాన్ని అప్‌లోడ్ చేయండి",
        "capture_webcam": "వెబ్‌క్యామ్ నుండి సంగ్రహించండి",
        "image_uploader": "ఒక చిత్రాన్ని అప్‌లోడ్ చేయండి",
        "image_camera": "ఒక చిత్రం తీయండి",
        "generate_description": "వివరణను రూపొందించండి",
        "description_success": "రూపొందించబడిన వివరణ",
        "booking_header": "📅 డాక్టర్ అపాయింట్‌మెంట్‌ను బుక్ చేయండి",
        "booking_caption": "ఒక డాక్టర్‌ను ఎంచుకోండి, ఒక తేదీ మరియు సమయాన్ని ఎంచుకోండి మరియు మీ వివరాలను ఇవ్వండి. మేము మీ స్లాట్‌ను వెంటనే రిజర్వ్ చేస్తాము.",
        "doctor": "డాక్టర్",
        "mode": "మోడ్",
        "date": "తేదీ",
        "time": "సమయం",
        "no_slots": "ఏ స్లాట్‌లు అందుబాటులో లేవు",
        "patient_details": "రోగి వివరాలు",
        "full_name": "పూర్తి పేరు",
        "email": "ఇమెయిల్ (ఐచ్ఛికం)",
        "phone": "ఫోన్",
        "age_patient": "వయస్సు",
        "gender": "లింగం",
        "notes": "మీ సమస్యను వివరించండి (ఐచ్ఛికం)",
        "confirm_booking": "బుకింగ్ నిర్ధారించండి",
        "required_fields_warning": "పేరు మరియు ఫోన్ అవసరం.",
        "slot_taken_error": "క్షమించండి, ఆ స్లాట్ ఇప్పుడే తీసుకోబడింది. దయచేసి మరొక సమయాన్ని ఎంచుకోండి.",
        "booking_success": "✅ అపాయింట్‌మెంట్ బుక్ చేయబడింది! మీ రిఫరెన్స్ ID **{}**.",
        "view_details": "బుకింగ్ వివరాలను చూడండి",
        "admin_header": "📋 అపాయింట్‌మెంట్‌ల అడ్మిన్",
        "admin_caption": "అన్ని బుకింగ్‌లను వీక్షించండి, ఫిల్టర్ చేయండి, స్థితిని నవీకరించండి మరియు ఎగుమతి చేయండి.",
        "no_appointments": "ఇంకా అపాయింట్‌మెంట్‌లు లేవు.",
        "all": "అన్ని",
        "status": "స్థితి",
        "from": "నుండి",
        "to": "వరకు",
        "download_csv": "⬇️ CSVని డౌన్‌లోడ్ చేయండి",
        "update_status": "స్థితిని నవీకరించండి",
        "booking_id": "బుకింగ్ ID",
        "new_status": "కొత్త స్థితి",
        "update_button": "నవీకరించండి",
        "status_updated": "స్థితి నవీకరించబడింది.",
        "booking_id_not_found": "బుకింగ్ ID కనుగొనబడలేదు."
    },
    "Tamil": {
        "title": "ஹெல்த் ஹப்",
        "caption": "மருந்து கருவிகள் • சந்திப்புகள் • NLP",
        "navigate": "செல்லவும்",
        "home": "🏠 முகப்பு",
        "drug_interaction": "💊 மருந்து இடைவினை",
        "dosage_by_age": "📏 வயது வாரியாக மருந்தளவு",
        "alternatives": "🔁 மாற்று மருந்துகள்",
        "nlp_extract": "🧠 NLP பிரித்தெடுத்தல்",
        "image_to_text": "🖼️ படத்திலிருந்து உரை",
        "doctor_appointment": "📅 மருத்துவர் சந்திப்பு",
        "appointments_admin": "📋 சந்திப்புகள் நிர்வாகம்",
        "welcome": "**ஹெல்த் ஹப்** க்கு வருக",
        "home_intro": "விரைவான மருந்து சோதனைகள் மற்றும் மருத்துவர் சந்திப்புகளை முன்பதிவு செய்வதற்கான ஒரு சுத்தமான, பயனர் நட்பு போர்டல்.",
        "interactions_header": "💊 மருந்து இடைவினை கண்டறிதல்",
        "interactions_caption": "தீங்கு விளைவிக்கும் இடைவினைகளைச் சரிபார்க்க, காற்புள்ளியால் பிரிக்கப்பட்ட மருந்துகளின் பட்டியலை உள்ளிடவும்.",
        "interactions_placeholder": "இபுப்ரோஃபென், வார்ஃபரின், ஒமெப்ரசொல்",
        "interactions_button": "இடைவினைகளைச் சரிபார்க்கவும்",
        "interactions_warning_input": "தயவுசெய்து குறைந்தது இரண்டு மருந்துகளை, காற்புள்ளிகளால் பிரித்து உள்ளிடவும்.",
        "interactions_warning_count": "தயவுசெய்து குறைந்தது இரண்டு மருந்துகளை உள்ளிடவும்.",
        "interactions_error": "தீங்கு விளைவிக்கும் இடைவினைகள் கண்டறியப்பட்டன!",
        "interactions_success": "தீங்கு விளைவிக்கும் இடைவினைகள் எதுவும் கண்டறியப்படவில்லை.",
        "dosage_header": "📏 வயது-குறிப்பிட்ட மருந்தளவு பரிந்துரை",
        "drug_name": "மருந்தின் பெயர்",
        "age_label": "நோயாளி வயது",
        "get_recommendation": "பரிந்துரையைப் பெறவும்",
        "alternatives_header": "🔁 மாற்று மருந்து ஆலோசனைகள்",
        "alternatives_input": "மாற்று மருந்துகளைக் கண்டறிய மருந்து",
        "suggest_alternatives": "மாற்று மருந்துகளைப் பரிந்துரைக்கவும்",
        "alternatives_success": "**{}** க்கான மாற்று மருந்துகள்:",
        "alternatives_none": "மாற்று மருந்துகள் எதுவும் கண்டறியப்படவில்லை.",
        "nlp_header": "🧠 NLP-அடிப்படையிலான மருந்து தகவல் பிரித்தெடுத்தல்",
        "nlp_text_area": "ஒரு மருத்துவ உரையை உள்ளிடவும்",
        "nlp_placeholder": "நோயாளிக்கு தினமும் இரண்டு முறை 200mg இபுப்ரோஃபென் எடுக்கப் பரிந்துரைக்கப்பட்டது.",
        "extract_info": "தகவலைப் பிரித்தெடுக்கவும்",
        "nlp_warning_input": "சில உரையை உள்ளிடவும்.",
        "nlp_success": "பிரித்தெடுக்கப்பட்ட தகவல்:",
        "nlp_no_info": "உரையில் இருந்து மருந்து தகவல் எதுவும் பிரித்தெடுக்கப்படவில்லை.",
        "image_to_text_header": "🖼️ படத்திலிருந்து உரை (IBM Granite Vision)",
        "input_method": "உள்ளீட்டு முறையைத் தேர்ந்தெடுக்கவும்",
        "upload_image": "படத்தைப் பதிவேற்றவும்",
        "capture_webcam": "வெப்கேமிலிருந்து கைப்பற்றவும்",
        "image_uploader": "ஒரு படத்தைப் பதிவேற்றவும்",
        "image_camera": "ஒரு படம் எடுக்கவும்",
        "generate_description": "விவரணையை உருவாக்கவும்",
        "description_success": "உருவாக்கப்பட்ட விவரணை",
        "booking_header": "📅 மருத்துவர் சந்திப்பை முன்பதிவு செய்யவும்",
        "booking_caption": "ஒரு மருத்துவரைத் தேர்ந்தெடுத்து, ஒரு தேதி மற்றும் நேரத்தைத் தேர்ந்தெடுத்து, உங்கள் விவரங்களை உள்ளிடவும். நாங்கள் உடனடியாக உங்கள் நேரத்தை முன்பதிவு செய்வோம்.",
        "doctor": "மருத்துவர்",
        "mode": "முறை",
        "date": "தேதி",
        "time": "நேரம்",
        "no_slots": "நேரங்கள் எதுவும் இல்லை",
        "patient_details": "நோயாளி விவரங்கள்",
        "full_name": "முழுப் பெயர்",
        "email": "மின்னஞ்சல் (விரும்பினால்)",
        "phone": "தொலைபேசி",
        "age_patient": "வயது",
        "gender": "பாலினம்",
        "notes": "உங்கள் கவலையை விவரிக்கவும் (விரும்பினால்)",
        "confirm_booking": "முன்பதிவை உறுதிப்படுத்தவும்",
        "required_fields_warning": "பெயர் மற்றும் தொலைபேசி தேவை.",
        "slot_taken_error": "மன்னிக்கவும், அந்த நேரம் இப்போது எடுக்கப்பட்டது. தயவுசெய்து வேறு நேரத்தைத் தேர்ந்தெடுக்கவும்.",
        "booking_success": "✅ சந்திப்பு முன்பதிவு செய்யப்பட்டது! உங்கள் குறிப்பு ஐடி **{}**.",
        "view_details": "முன்பதிவு விவரங்களைப் பார்க்கவும்",
        "admin_header": "📋 சந்திப்புகள் நிர்வாகம்",
        "admin_caption": "அனைத்து முன்பதிவுகளையும் பார்க்கவும், வடிகட்டவும், நிலையை புதுப்பிக்கவும் மற்றும் ஏற்றுமதி செய்யவும்.",
        "no_appointments": "சந்திப்புகள் எதுவும் இல்லை.",
        "all": "அனைத்தும்",
        "status": "நிலை",
        "from": "இருந்து",
        "to": "வரை",
        "download_csv": "⬇️ CSV பதிவிறக்க",
        "update_status": "நிலையை புதுப்பிக்கவும்",
        "booking_id": "முன்பதிவு ஐடி",
        "new_status": "புதிய நிலை",
        "update_button": "புதுப்பிக்கவும்",
        "status_updated": "நிலை புதுப்பிக்கப்பட்டது.",
        "booking_id_not_found": "முன்பதிவு ஐடி கண்டறியப்படவில்லை."
    }
}

# Function to get the current language and its translations
def get_language():
    if 'language' not in st.session_state:
        st.session_state.language = "English"
    return st.session_state.language, translations[st.session_state.language]
def listen_for_emergency():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Say 'healthhub emergency' loudly!")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            text = r.recognize_google(audio).lower()
            if "healthhub emergency" in text:
                st.error("🚨 Emergency Detected! Calling now...")
                # Open phone dialer (works on mobile/web)
                webbrowser.open(f"tel:{EMERGENCY_NUMBER}")
            else:
                st.warning("🚨 Emergency Detected! Calling now...")
        except Exception as e:
            st.warning(f"Listening failed: {e}")
# ------------------------------
# Helpers
# ------------------------------
def post_json(path: str, payload: dict):
    try:
        with st.spinner("Contacting server..."):
            r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=15)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, {"error": f"HTTP {r.status_code}: {r.text}"}
    except requests.exceptions.ConnectionError as e:
        return False, {"error": "Connection error. Is the FastAPI server running?", "detail": str(e)}
    except requests.exceptions.Timeout as e:
        return False, {"error": "Request timed out.", "detail": str(e)}
    except Exception as e:
        return False, {"error": "Unknown error", "detail": str(e)}

def init_csv():
    p = Path(APPTS_CSV)
    if not p.exists():
        df = pd.DataFrame(columns=[
            "booking_id","patient_name","phone","email","age","gender",
            "doctor","speciality","mode","date","time","notes","created_at","status"
        ])
        df.to_csv(APPTS_CSV, index=False)
    return p

def read_appts():
    init_csv()
    return pd.read_csv(APPTS_CSV)

def write_appt(row: dict):
    df = read_appts()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(APPTS_CSV, index=False)

def is_slot_taken(df: pd.DataFrame, doctor: str, appt_date: str, appt_time: str):
    if df.empty:
        return False
    clash = df[        (df["doctor"] == doctor) &        (df["date"] == appt_date) &        (df["time"] == appt_time) &        (df["status"].isin(["Booked","Confirmed"]))    ]
    return not clash.empty

def gen_slots(start="09:00", end="17:00", step_minutes=30):
    from datetime import datetime as _dt
    start_t = _dt.combine(date.today(), _dt.strptime(start, "%H:%M").time())
    end_t = _dt.combine(date.today(), _dt.strptime(end, "%H:%M").time())
    slots = []
    cur = start_t
    while cur <= end_t:
        slots.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=step_minutes)
    return slots

DOCTORS = [
    {"name":"Dr. A. Rao","speciality":"General Physician"},
    {"name":"Dr. S. Mehta","speciality":"Cardiologist"},
    {"name":"Dr. P. Kulkarni","speciality":"Pediatrician"},
    {"name":"Dr. R. Nair","speciality":"Dermatologist"},
]

# ------------------------------
# Sidebar Navigation
# ------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=64)
    st.title("HealthHub")
    st.caption("Drug tools • Appointments • NLP")

    # Language selection
    lang_options = list(translations.keys())
    st.session_state.language = st.selectbox("Choose Language", lang_options, index=lang_options.index(st.session_state.language) if 'language' in st.session_state else 0)
    
    current_lang, t = get_language()

    page = st.radio(t["navigate"], [
        t["home"],
        t["drug_interaction"],
        t["dosage_by_age"],
        t["alternatives"],
        t["nlp_extract"],
        t["image_to_text"],
        t["doctor_appointment"],
        t["appointments_admin"]
    ])
    st.markdown("---")
    st.markdown("**Backend:** " + BASE_URL)


# ------------------------------
# Pages
# ------------------------------
def page_home():
    current_lang, t = get_language()
    st.markdown(f"### {t['welcome']}")
    st.write(t["home_intro"])
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="metric-card"><div class="pill">Tool</div><h3>Drug Interactions</h3><p class="muted">Check for harmful combinations</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="metric-card"><div class="pill">Tool</div><h3>Dosage by Age</h3><p class="muted">Age-appropriate recommendations</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="metric-card"><div class="pill">New</div><h3>Doctor Appointments</h3><p class="muted">Book a visit or video consult</p></div>', unsafe_allow_html=True)
    if st.button("🚨 Activate Voice Emergency"):
        listen_for_emergency()

def page_interactions():
    current_lang, t = get_language()
    st.header(t["interactions_header"])
    st.caption(t["interactions_caption"])
    drugs_input = st.text_area(t["drug_interaction"], placeholder=t["interactions_placeholder"])
    if st.button(t["interactions_button"], type="primary"):
        if not drugs_input.strip():
            st.warning(t["interactions_warning_input"])
            return
        drugs_list = [d.strip() for d in drugs_input.split(",") if d.strip()]
        if len(drugs_list) < 2:
            st.warning(t["interactions_warning_count"])
            return
        ok, data = post_json("/check_interactions", {"drugs": drugs_list})
        if ok:
            if data.get("status") == "warning":
                st.error(t["interactions_error"])
                for it in data.get("interactions", []):
                    st.write(f"- {it}")
            else:
                st.success(t["interactions_success"])
        else:
            st.error(data.get("error","Error"))
            if "detail" in data: st.caption(data["detail"])

def page_dosage():
    current_lang, t = get_language()
    st.header(t["dosage_header"])
    c1, c2 = st.columns([2,1])
    with c1:
        drug = st.text_input(t["drug_name"], placeholder="ibuprofen")
    with c2:
        age = st.number_input(t["age_label"], min_value=0, max_value=120, value=30)
    if st.button(t["get_recommendation"], type="primary"):
        if not drug.strip():
            st.warning(t["drug_name"])
            return
        ok, data = post_json("/recommend_dosage", {"drug": drug, "age": int(age)})
        if ok:
            st.info(f"**Recommendation for {data.get('drug', drug)} (Age {age}):** {data.get('recommendation','—')}")
        else:
            st.error(data.get("error","Error")); st.caption(data.get("detail",""))

def page_alternatives():
    current_lang, t = get_language()
    st.header(t["alternatives_header"])
    drug = st.text_input(t["alternatives_input"], placeholder="warfarin")
    if st.button(t["suggest_alternatives"], type="primary"):
        if not drug.strip():
            st.warning(t["alternatives_input"])
            return
        ok, data = post_json("/suggest_alternatives", {"drug": drug})
        if ok:
            alts = data.get("alternatives", [])
            if alts:
                st.success(f"{t['alternatives_success'].format(data.get('drug',drug))} " + ', '.join(alts))
            else:
                st.warning(t["alternatives_none"])
        else:
            st.error(data.get("error","Error")); st.caption(data.get("detail",""))

def page_nlp():
    current_lang, t = get_language()
    st.header(t["nlp_header"])
    txt = st.text_area(t["nlp_text_area"], height=160, placeholder=t["nlp_placeholder"])
    if st.button(t["extract_info"], type="primary"):
        if not txt.strip():
            st.warning(t["nlp_warning_input"])
            return
        ok, data = post_json("/extract_info", {"text": txt})
        if ok:
            if data.get("status") == "success" and data.get("matches"):
                st.success(t["nlp_success"])
                st.json(data.get("matches"))   # ✅ fixed
            elif data.get("status") == "no_match":
                st.warning(t["nlp_no_info"])
            else:
                st.error(data.get("message","Unknown error."))
        else:
            st.error(data.get("error","Error"))
            st.caption(data.get("detail",""))

def page_image_to_text():
    current_lang, t = get_language()
    st.header(t["image_to_text_header"])
    method = st.radio(t["input_method"], [t["upload_image"], t["capture_webcam"]], horizontal=True)

    uploaded = None
    if method == t["upload_image"]:
        uploaded = st.file_uploader(t["image_uploader"], type=["jpg", "jpeg", "png"])
    else:
        uploaded = st.camera_input(t["image_camera"])

    if uploaded:
        st.image(uploaded, caption="Selected image", use_container_width=True)  # ✅ replaced deprecated param

    if uploaded and st.button(t["generate_description"], type="primary"):
        try:
            files = {"file": ("image.png", uploaded.getvalue(), "image/png")}
            with st.spinner("Talking to Granite Vision..."):
                r = requests.post(f"{BASE_URL}/image_to_text", files=files, timeout=60)

            if r.status_code == 200:
                data = r.json()

                # Always show raw OCR details
                st.subheader("🔎 OCR Debug Info")
                st.json({
                    "OCR Raw": data.get("caption_raw"),
                    "OCR Joined": data.get("caption_joined"),
                    "Normalized": data.get("caption_normalized"),
                    "Similarities": data.get("similarities"),
                })

                if data.get("status") == "success" and data.get("matches"):
                    st.success(t["description_success"])
                    st.write("**Caption:**", data.get("caption", "—"))

                    st.subheader("✅ Related Dataset Entries")
                    st.json(data["matches"])
                else:
                    st.warning("⚠ No matching entries found in dataset.")

            else:
                st.error(f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")


def page_booking():
    current_lang, t = get_language()
    st.header(t["booking_header"])
    st.caption(t["booking_caption"])

    df = read_appts()
    cols = st.columns(2)
    with cols[0]:
        doc_names = [f"{d['name']} — {d['speciality']}" for d in DOCTORS]
        doc_display = st.selectbox(t["doctor"], doc_names, index=0)
        sel = DOCTORS[doc_names.index(doc_display)]
        speciality = sel["speciality"]
    with cols[1]:
        mode = st.selectbox(t["mode"], ["In-clinic", "Video Call"])

    c2 = st.columns(3)
    with c2[0]:
        appt_date = st.date_input(t["date"], min_value=date.today())
    with c2[1]:
        slots = gen_slots("09:00","17:00",30)
        taken = set(df[(df["doctor"]==sel["name"]) & (df["date"]==appt_date.strftime("%Y-%m-%d"))]["time"].tolist())
        free_slots = [s for s in slots if s not in taken]
        appt_time = st.selectbox(t["time"], free_slots if free_slots else [t["no_slots"]])
    with c2[2]:
        pass

    st.markdown("---")
    st.subheader(t["patient_details"])
    p1, p2, p3 = st.columns([2,1,1])
    with p1:
        patient_name = st.text_input(t["full_name"])
        email = st.text_input(t["email"])
    with p2:
        phone = st.text_input(t["phone"])
    with p3:
        age = st.number_input(t["age_patient"], min_value=0, max_value=120, value=30)
    gender = st.selectbox(t["gender"], ["Female","Male","Other","Prefer not to say"], index=0)
    notes = st.text_area(t["notes"], height=100)

    if st.button(t["confirm_booking"], type="primary", use_container_width=True, disabled=(appt_time==t["no_slots"])):
        if not patient_name.strip() or not phone.strip():
            st.warning(t["required_fields_warning"])
            return
        appt_date_str = appt_date.strftime("%Y-%m-%d")
        if is_slot_taken(df, sel["name"], appt_date_str, appt_time):
            st.error(t["slot_taken_error"])
            st.stop()
        booking = {
            "booking_id": str(uuid.uuid4())[:8].upper(),
            "patient_name": patient_name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "age": int(age),
            "gender": gender,
            "doctor": sel["name"],
            "speciality": speciality,
            "mode": mode,
            "date": appt_date_str,
            "time": appt_time,
            "notes": notes.strip(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Booked"
        }
        write_appt(booking)
        st.success(f"✅ {t['booking_success'].format(booking['booking_id'])}")
        with st.expander(t["view_details"]):
            st.json(booking)

def page_admin():
    current_lang, t = get_language()
    st.header(t["admin_header"])
    st.caption(t["admin_caption"])
    init_csv()
    df = read_appts()
    if df.empty:
        st.info(t["no_appointments"])
        return
    c = st.columns(4)
    with c[0]:
        doctor_f = st.selectbox(t["doctor"], [t["all"]] + [d["name"] for d in DOCTORS])
    with c[1]:
        status_f = st.selectbox(t["status"], [t["all"],"Booked","Confirmed","Cancelled","Completed"], index=0)
    with c[2]:
        start_d = st.date_input(t["from"], value=date.today()-timedelta(days=7))
    with c[3]:
        end_d = st.date_input(t["to"], value=date.today()+timedelta(days=30))

    mask = (
        (pd.to_datetime(df["date"]) >= pd.to_datetime(start_d)) &
        (pd.to_datetime(df["date"]) <= pd.to_datetime(end_d))
    )
    if doctor_f != t["all"]:
        mask &= (df["doctor"] == doctor_f)
    if status_f != t["all"]:
        mask &= (df["status"] == status_f)
    view = df[mask].copy()
    st.dataframe(view, use_container_width=True)

    st.download_button(f"⬇️ {t['download_csv']}", data=view.to_csv(index=False), file_name="appointments_filtered.csv", mime="text/csv")

    st.markdown("---")
    st.subheader(t["update_status"])
    if not df.empty:
        bid = st.text_input(t["booking_id"])
        new_status = st.selectbox(t["new_status"], ["Confirmed","Cancelled","Completed"])
        if st.button(t["update_button"]):
            idx = df.index[df["booking_id"]==bid].tolist()
            if idx:
                df.loc[idx[0], "status"] = new_status
                df.to_csv(APPTS_CSV, index=False)
                st.success(t["status_updated"])
            else:
                st.error(t["booking_id_not_found"])


current_lang, t = get_language()
if page == t["home"]:
    page_home()
elif page == t["drug_interaction"]:
    page_interactions()
elif page == t["dosage_by_age"]:
    page_dosage()
elif page == t["alternatives"]:
    page_alternatives()
elif page == t["nlp_extract"]:
    page_nlp()
elif page == t["image_to_text"]:
    page_image_to_text()
elif page == t["doctor_appointment"]:
    page_booking()
elif page == t["appointments_admin"]:
    page_admin()