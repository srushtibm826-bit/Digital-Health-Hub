# Digital-Health-Hub
HealthHub: Drug Tools & Appointments
HealthHub is a powerful Streamlit application designed to assist users with drug information, including interactions and dosages, as well as a local appointment management system. The application is composed of a Streamlit frontend (app.py) and a FastAPI backend (main.py) that handles image analysis and drug data processing.

Features
Drug Information Lookup: Get comprehensive details on various drugs, including alternatives, interactions, and recommended dosages for different age groups.

Appointment Management: A simple system to book, view, and update the status of appointments (e.g., Confirmed, Cancelled, Completed).

Image-based Drug Identification: Upload an image of a medication label to extract text and automatically find matching drug information from the database.

Voice-Activated Commands: Use your voice to navigate the app, make a call to an emergency number, or manage appointments.

Multi-language Support: The app is available in both English and Hindi.

Tech Stack
Frontend: Streamlit, Pandas, SpeechRecognition, requests

Backend: FastAPI, pytesseract (for OCR), Pillow, difflib

Data: CSV files for appointment data and a Python dictionary for drug information.

Getting Started
Prerequisites
Python 3.8 or higher

tesseract-ocr installed on your system.

Windows: Download from Tesseract at GitHub.

macOS: brew install tesseract

Linux (Debian/Ubuntu): sudo apt-get install tesseract-ocr

A virtual environment is highly recommended.

Installation
Clone this repository to your local machine:

git clone [https://github.com/your-repo/healthhub.git](https://github.com/your-repo/healthhub.git)
cd healthhub

Install the required Python packages:

pip install -r requirements.txt

Note: You may need to create a requirements.txt file from the imports in app.py and main.py.

Set the path to the Tesseract executable in main.py according to your installation.

# For Windows:
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# For macOS/Linux:
# pytesseract.pytesseract.tesseract_cmd = 'tesseract'

Usage
Start the FastAPI backend server:

uvicorn main:app --reload

This will run the backend on http://127.0.0.1:8000.

In a new terminal, run the Streamlit frontend app:

streamlit run app.py

The Streamlit app will open in your default web browser.

Use the application to navigate between different tools (Drug Info, Appointments, etc.) and explore the features.

Project Structure
app.py: The main Streamlit application script.

main.py: The FastAPI backend server with API endpoints for OCR and drug data.

appointments.csv: (Optional) A CSV file to store appointment data. The app will create one if it doesn't exist.

requirements.txt: (Optional) Lists all the necessary Python packages.
