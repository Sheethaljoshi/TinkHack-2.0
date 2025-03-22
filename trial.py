import json
from openai import OpenAI
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

client  = OpenAI()

# Load JSON Data
with open("dementia_patient_data.json", "r", encoding="utf-8") as file:
    data = json.load(file)


# Extract Personal Info
patient_name = f"{data['first_name']} {data['last_name']}"
email = data["email"]
memories = data.get("mem_data", [])
sentiments = data.get("sentiment", [])
people = data.get("people_data", [])
places = data.get("places_mem", [])
medicine_tracker = data.get("medicine_tracker", {})

# Extract Missed Medicines
missed_meds = []
if "schedule" in medicine_tracker and "medicines" in medicine_tracker:
    medicines = medicine_tracker["medicines"]
    for date, meds_info in medicine_tracker["schedule"][0].items():
        missed_today = [med for med, status in meds_info.items() if status == "missed"]
        if missed_today:
            missed_meds.append({"date": date, "missed": missed_today})

# Generate AI Summary
def generate_ai_summary(memories, sentiments, people, places, missed_meds):
    prompt = f"""
    You are a caring memory assistant for a dementia patient. 
    Create a compassionate, engaging memory report using the following data:
    
    - **Key Memories**: {memories}
    - **Emotional Trends**: {sentiments}
    - **Important People**: {people}
    - **Special Places**: {places}
    - **Missed Medications**: {missed_meds}

    **Report Structure**:
    1️⃣ **Memory Recap** – Use a warm, storytelling tone. Highlight key events.  
    2️⃣ **Emotional Well-being** – Identify trends in emotions.  
    3️⃣ **Familiar Faces & Places** – Remind the patient of loved ones & locations.  
    4️⃣ **Missed Medications** – Show which medicines were missed and recommend consistency.  
    5️⃣ **Encouragement & Tips** – Provide comforting, reassuring advice.  
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a gentle memory coach for a dementia patient."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# AI Summary Generation
ai_summary = generate_ai_summary(memories, sentiments, people, places, missed_meds)

# Generate Sentiment Chart
def plot_sentiment_chart(sentiments):
    sentiment_counts = Counter([s["sentiment"] for s in sentiments])
    labels, values = zip(*sentiment_counts.items())

    plt.figure(figsize=(6, 3))
    plt.bar(labels, values, color=["#4682B4", "#FF6347", "#32CD32", "#FFA500", "#9370DB"])
    plt.xlabel("Sentiments", fontsize=12, fontweight="bold")
    plt.ylabel("Frequency", fontsize=12, fontweight="bold")
    plt.title("Emotional Trends Over Time", fontsize=14, fontweight="bold")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("sentiment_chart.png")
    plt.close()

# Generate PDF Report
def generate_pdf(output_pdf, ai_summary, missed_meds):
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4

    # Title Styling
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.darkblue)
    c.drawString(100, height - 60, f"Memory & Well-being Report")

    # Patient Info
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(100, height - 90, f"Patient: {patient_name}")
    c.drawString(100, height - 110, f"Email: {email}")

    # Section Title: AI-Generated Summary
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.darkred)
    c.drawString(100, height - 150, "📜 Memory Recap & Well-being Summary:")

    # AI-Generated Summary Content
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    y_position = height - 170
    wrapped_summary = simpleSplit(ai_summary, "Helvetica", 12, width - 150)
    for line in wrapped_summary:
        c.drawString(100, y_position, line)
        y_position -= 18

    # Insert Sentiment Chart
    plot_sentiment_chart(sentiments)
    c.drawImage("sentiment_chart.png", 100, y_position - 220, width=400, height=200)

    # Missed Medications Section
    y_position -= 250
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.darkred)
    c.drawString(100, y_position, "❗ Missed Medications:")

    # Table Data for Missed Medicines
    if missed_meds:
        table_data = [["Date", "Missed Medicines"]]
        for entry in missed_meds[:5]:  # Show last 5 records
            table_data.append([entry["date"], ", ".join(entry["missed"])])

        # Draw Table
        y_position -= 30
        table = Table(table_data, colWidths=[100, 350])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        table.wrapOn(c, width, height)
        table.drawOn(c, 100, y_position - 100)
    
    else:
        c.setFont("Helvetica", 12)
        c.drawString(100, y_position - 30, "✅ No missed medications recorded.")

    # Encouragement Section
    y_position -= 160
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.darkorange)
    c.drawString(100, y_position, "💡 Encouragement & Reflection Questions:")

    y_position -= 20
    encouragement_text = [
        "🔹 What was a moment that made you laugh recently?",
        "🔹 Can you describe the happiest day from last week?",
        "🔹 Remember to take small moments to appreciate the present.",
        "🔹 Your memories are valuable, and it's okay to ask for help when needed!"
    ]

    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    for line in encouragement_text:
        c.drawString(100, y_position, line)
        y_position -= 20

    # Save PDF
    c.save()
    print(f"📄 Report successfully created: {output_pdf}")

# Run Report Generation
generate_pdf("dementia_report.pdf", ai_summary, missed_meds)


