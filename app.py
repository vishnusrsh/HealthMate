from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

# Load environment variables and configure API key
print("Current working directory:", os.getcwd())
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key first 4 chars: {api_key[:4] if api_key else 'None'}")

# Fallback API key if environment variable is not set
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables.")
    print("Please set your Gemini API key in the .env file or environment variables.")
    print("You can get an API key from: https://ai.google.dev/")
    api_key = "AIzaSyBoR5S4Ezp23UoxrMg_8HAf1JjzXZo2WdE"  # Your API key

# Configure Gemini AI API
try:
    genai.configure(api_key=api_key)
    print("Successfully configured Gemini API")
except Exception as e:
    print(f"Error configuring Gemini API: {str(e)}")

# Initialize Flask application and configure SQLite database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthmate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy database
db = SQLAlchemy(app)

# Define PillReminder database model for storing medication reminders
class PillReminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pill_name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(5), nullable=False)  # Store time as HH:MM
    frequency = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize Gemini AI model
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Function to interact with Gemini AI for health-related queries
def ask_gemini(prompt):
    try:
        instruction = (
            "You are an AI Health Assistant. Only answer health-related questions. "
            "If the question is not about health, disease, symptoms, or wellness, reply with: "
            "'I'm sorry, I can only assist with health-related queries.'"
        )
        full_prompt = f"{instruction}\n\nUser: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        if "API_KEY" in str(e):
            return "The AI service is currently unavailable. Please check your API key configuration in the .env file."
        elif "quota" in str(e).lower():
            return "The AI service has reached its usage limit. Please try again later."
        else:
            return "I'm having trouble connecting to the AI service. Please check your internet connection and try again."

# Function to get health tips based on category
def get_tip(category="general"):
    try:
        return ask_gemini(f"Give a health tip about {category}.")
    except Exception as e:
        print(f"Error getting tip: {str(e)}")
        return "Unable to fetch health tips at the moment. Please try again later."

# Function to get information about specific diseases
def get_disease_info(disease_name):
    try:
        return ask_gemini(f"Give a detailed summary about the disease: {disease_name}. Include symptoms, causes, and treatments.")
    except Exception as e:
        print(f"Error getting disease info: {str(e)}")
        return "Unable to fetch disease information at the moment. Please try again later."

# Function for mental health support chat
def mental_health_chat(user_input):
    try:
        return ask_gemini(f"You are a friendly mental wellness coach. The user says: {user_input}")
    except Exception as e:
        print(f"Error in mental health chat: {str(e)}")
        return "I'm unable to respond to your message right now. Please try again later."

# Function to check symptoms and get possible conditions
def check_symptoms(symptoms):
    try:
        return ask_gemini(f"A patient reports: {symptoms}. What possible conditions could this indicate?")
    except Exception as e:
        print(f"Error checking symptoms: {str(e)}")
        return "Unable to analyze symptoms at the moment. Please try again later."

# Function to calculate ideal weight based on height, age, and gender
def calculate_ideal_weight(height, age, gender):
    if gender.lower() == "male":
        return 50 + 0.9 * (height - 152)
    else:
        return 45.5 + 0.9 * (height - 152)

# Route for home page and general health queries
@app.route("/", methods=["GET", "POST"])
def home():
    response = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        response = ask_gemini(user_input)
    return render_template("index.html", response=response)

# Route for symptom checker page
@app.route('/symptom')
def symptom():
    return render_template('symptom.html')

# Route to handle symptom checking requests
@app.route('/check_symptoms', methods=['POST'])
def check_symptoms():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No data provided",
                "details": "Please provide symptoms, duration, and severity"
            }), 400

        symptoms = data.get('symptoms', '')
        duration = data.get('duration', '')
        severity = data.get('severity', '')

        if not all([symptoms, duration, severity]):
            return jsonify({
                "error": "Missing required fields",
                "details": "Please provide all required fields: symptoms, duration, and severity"
            }), 400

        # Create a prompt for symptom analysis
        prompt = f"""
        Analyze these symptoms and provide medical insights:
        Symptoms: {symptoms}
        Duration: {duration}
        Severity: {severity}

        Please provide:
        1. Possible conditions (list 2-3 most likely)
        2. Recommendations for next steps
        3. Whether immediate medical attention is needed

        Format the response as JSON with these keys:
        - conditions: array of possible conditions
        - recommendations: array of recommendations
        - urgent: boolean indicating if immediate medical attention is needed
        """

        # Get response from Gemini
        response = model.generate_content(prompt)
        response_text = response.text

        # Parse the response to extract JSON
        try:
            # Find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                # If no JSON found, create a structured response
                result = {
                    "conditions": ["Unable to determine specific conditions"],
                    "recommendations": ["Please consult with a healthcare professional for proper diagnosis"],
                    "urgent": False
                }
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            # If JSON parsing fails, create a structured response
            result = {
                "conditions": ["Unable to determine specific conditions"],
                "recommendations": ["Please consult with a healthcare professional for proper diagnosis"],
                "urgent": False
            }

        return jsonify(result)

    except Exception as e:
        print(f"Error in check_symptoms: {str(e)}")
        error_message = "Unable to process symptoms at this time. Please try again later."
        if "API_KEY" in str(e):
            error_message = "The AI service is currently unavailable. Please check your API key configuration."
        elif "quota" in str(e).lower():
            error_message = "The AI service has reached its usage limit. Please try again later."
        
        return jsonify({
            "error": error_message,
            "details": str(e)
        }), 500

# Route for daily health tips
@app.route("/tip", methods=["GET", "POST"])
def daily_tip():
    response = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        response = get_tip(user_input if user_input else "general")
    return render_template("daily_tip.html", response=response)

# Route for mental health support
@app.route("/mental", methods=["GET", "POST"])
def mental_support():
    response = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        response = mental_health_chat(user_input)
    return render_template("mental_support.html", response=response)

# Route for disease information
@app.route("/disease", methods=["GET", "POST"])
def disease_info():
    response = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        response = get_disease_info(user_input)
    return render_template("disease_info.html", response=response)

# Route for BMI calculator
@app.route("/bmi", methods=["GET", "POST"])
def bmi_calculator():
    result = None
    advice = ""
    if request.method == "POST":
        age = int(request.form["age"])
        gender = request.form["gender"]
        height = float(request.form["height"])  # in cm
        weight = float(request.form["weight"])  # in kg

        bmi = weight / ((height / 100) ** 2)
        ideal_weight = calculate_ideal_weight(height, age, gender)
        advice = ask_gemini(
            f"My age is {age}, gender is {gender}, height is {height} cm, weight is {weight} kg, and my BMI is {bmi:.2f}. "
            f" Give me a detailed diet plan and health instructions to become the healthiest version of myself."
            f"What is my ideal weight?"
        )
        result = {
            "bmi": round(bmi, 2),
            "ideal_weight": round(ideal_weight, 2),
            "advice": advice
        }
    return render_template("bmi.html", result=result)

# Route for pill reminder functionality
@app.route("/pill-reminder", methods=["GET", "POST"])
def pill_reminder():
    if request.method == "POST":
        pill_name = request.form.get("pillName")
        reminder_time = request.form.get("reminderTime")
        frequency = request.form.get("frequency")
        
        new_reminder = PillReminder(
            pill_name=pill_name,
            time=reminder_time,
            frequency=frequency
        )
        db.session.add(new_reminder)
        db.session.commit()
        
    reminders = PillReminder.query.order_by(PillReminder.time).all()
    return render_template("pill_reminder.html", reminders=reminders)

# Route to delete pill reminders
@app.route("/delete_reminder/<int:id>", methods=["DELETE"])
def delete_reminder(id):
    reminder = PillReminder.query.get_or_404(id)
    db.session.delete(reminder)
    db.session.commit()
    return jsonify({"success": True})

# Route to check current pill reminders
@app.route("/check_reminders")
def check_reminders():
    current_time = datetime.now().strftime("%H:%M")
    reminders = PillReminder.query.filter_by(time=current_time).all()
    return jsonify({
        "reminders": [{
            "pill_name": reminder.pill_name,
            "time": reminder.time,
            "frequency": reminder.frequency
        } for reminder in reminders]
    })

# Route for depression support page
@app.route('/depression-support')
def depression_support():
    return render_template('depression_support.html')

# Main entry point of the application
if __name__ == "__main__":
    # Create database tables
    with app.app_context():
        db.drop_all()  # Drop existing tables
        db.create_all()  # Create new tables
    app.run(debug=True)
