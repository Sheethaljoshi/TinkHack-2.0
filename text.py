from collections import Counter
from datetime import datetime, timedelta
import os
import random
import tempfile
import traceback
from fastapi.staticfiles import StaticFiles
from groq import Groq
import uuid
import PyPDF2
from fastapi import FastAPI, HTTPException, File, Query, UploadFile, Form
from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv
import json
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from pymongo.server_api import ServerApi
import base64
from fastapi.responses import FileResponse, JSONResponse
import requests
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import random

load_dotenv()

print("Loaded API Key:", os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

cluster = MongoClient("mongodb+srv://sh33thal24:devi@cluster0.42dks.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", server_api=ServerApi('1'))
db = cluster["Learners"]
collection = db["Learner"]

MODEL = "gpt-4o-mini"

USER_EMAIL = "sh33thal24@gmail.com"



class ToggleRequest(BaseModel):
    email: str
    medicine: str
    date: str  # Format: YYYY-MM-DD

@app.post("/toggle_medicine_status")
async def toggle_medicine_status(request: ToggleRequest):
    """
    Toggle medicine intake status (True <--> False) for a given user, medicine, and date.
    """
    user = collection.find_one({"email": request.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    medicine_tracker = user.get("medicine_tracker", {})

    if "schedule" not in medicine_tracker or "medicines" not in medicine_tracker:
        raise HTTPException(status_code=400, detail="Medicine tracker data is missing.")

    try:
        med_index = medicine_tracker["medicines"].index(request.medicine)
    except ValueError:
        raise HTTPException(status_code=404, detail="Medicine not found in tracker.")

    # Get the existing status
    if request.date not in medicine_tracker["schedule"][med_index]:
        raise HTTPException(status_code=404, detail="Date not found in schedule.")

    current_status = medicine_tracker["schedule"][med_index][request.date]["taken"]

    # ✅ Toggle the status (True ↔ False)
    new_status = not current_status

    # ✅ Update the timestamp
    medicine_tracker["schedule"][med_index][request.date] = {
        "taken": new_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # ✅ Update in MongoDB
    collection.update_one(
        {"email": request.email},
        {"$set": {"medicine_tracker": medicine_tracker}}
    )
    
    print(f"Medicine '{request.medicine}' for {request.date} updated successfully.")

    return {
        "message": f"Medicine '{request.medicine}' for {request.date} updated successfully.",
        "new_status": new_status
    }

@app.get("/get_medicine_tracker")
async def get_medicine_tracker(email: str = "sh33thal24@gmail.com"):
    user = collection.find_one({"email": email})

    if not user or "medicine_tracker" not in user:
        raise HTTPException(status_code=404, detail="User or medicine tracker data not found")

    # Get today's date and find the start of the current week (Sunday)
    today = datetime.now(timezone.utc)
    start_of_week = today - timedelta(days=today.weekday() + 1)  # Adjust to get the last Sunday
    if today.weekday() == 6:  # If today is Sunday, no adjustment needed
        start_of_week = today

    # Generate date range for Sunday to Saturday
    week_dates = [(start_of_week + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    # Extract relevant data from the user's stored medicine tracker
    medicines = user["medicine_tracker"]["medicines"]
    schedule_data = user["medicine_tracker"]["schedule"]

    # Convert the schedule data into the required format
    formatted_schedule = []
    for med_schedule in schedule_data:
        weekly_taken = [
            med_schedule.get(date, {"taken": False})["taken"]  # Default to False if missing
            for date in week_dates
        ]
        formatted_schedule.append(weekly_taken)

    # Final response matching sampleDB format
    response = {
        "medicines": medicines,
        "schedule": formatted_schedule
    }

    return response

def print_current_datetime():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def detect_sentiment(text):
    sentiments = {
        "happy": "joyful", "sad": "sorrowful", "excited": "enthusiastic", "anxious": "nervous", "relieved": "comforted", "scared": "fearful",
        "angry": "hostile", "frustrated": "agitated", "content": "satisfied", "hopeful": "optimistic", "disappointed": "let down",
        "confused": "uncertain", "indifferent": "apathetic", "neutral": "neutral", "bored": "disinterested", "uncertain": "ambivalent", "reserved": "withdrawn"
    }
    for word in text.split():
        word_lower = word.lower()
        if word_lower in sentiments:
            return sentiments[word_lower]
    return "neutral"

def determine_wellness(sentiment):
    wellness_scores = {
        "joyful": 10, "enthusiastic": 9, "optimistic": 8, "satisfied": 7,
        "comforted": 6, "neutral": 5, "uncertain": 4, "ambivalent": 4,
        "withdrawn": 3, "disinterested": 3, "apathetic": 3,
        "let down": 2, "nervous": 2, "fearful": 2, "agitated": 2,
        "hostile": 1, "sorrowful": 1
    }
    return wellness_scores.get(sentiment, 5)


def export_and_upload_to_vector_store():
    def export_to_json():
        data = list(collection.find())
        for item in data:
            item['_id'] = str(item['_id'])
        json_bytes = json.dumps(data).encode('utf-8')
        return BytesIO(json_bytes)

    def create_file(file_contents):
        client = OpenAI()
        file3 = client.files.create(
            file=("data.json", file_contents, "application/json"),
            purpose="assistants"
        )
        return file3

    def create_and_upload_vector_store_file(file_id):
        client = OpenAI()
        vector_store_files = client.vector_stores.files.list(vector_store_id='vs_67d542ae493881918be2d7418d8d7b57' )
        for vector_store_file in vector_store_files:
            deleted = client.vector_stores.files.delete(
                vector_store_id='vs_67d542ae493881918be2d7418d8d7b57' ,
                file_id=vector_store_file.id
            )
            print("deleted", deleted.id)
        vector_store_file = client.vector_stores.files.create(
            vector_store_id='vs_67d542ae493881918be2d7418d8d7b57' ,
            file_id=file_id
        )

        vector_store_files = client.vector_stores.files.list(
            vector_store_id='vs_67d542ae493881918be2d7418d8d7b57' 
        )
        print(vector_store_files)

        return vector_store_file

    json_file_contents = export_to_json()
    created_file = create_file(json_file_contents)
    vector_store_file = create_and_upload_vector_store_file(created_file.id)

    return vector_store_file

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

# Function to generate key topics and an image
def generate_key_topics_and_image(pdf_text):
    client = OpenAI()
    
    # Generate key topics using GPT-4o
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts key learning points from text."},
            {"role": "user", "content": f"Analyze the following text and extract the key topics to be learned from it.\n\n"
                                             "Present them in a numbered list with each point in the following format:\n\n"
                                             "[Topic Name]: A concise description (max 10 words) of its relevance or importance.\n\n"
                                             "Ensure the topics cover all major aspects of the text and are arranged logically.\n\n"
                                             f"Text:\n{pdf_text}"}
        ]
    )
    key_topics = completion.choices[0].message.content
    
    # Generate an image using DALL·E 3
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=f"An artistic representation of the main themes in the following text: {pdf_text[:1000]}",
        n=1,
        size="1024x1024"
    )
    
    image_url = image_response.data[0].url
    
    return key_topics, image_url

@app.post("/insert/person_with_pdf/")
async def insert_person_with_pdf(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    name: str = Form(...),
    relation: str = Form(...),
    occupation: str = Form(...),
    pdf_file: UploadFile = File(...),
):
    try:
        # Save uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_file.file.read())
            temp_pdf_path = temp_pdf.name
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(temp_pdf_path)
        
        # Generate topics and image
        description, image_url = generate_key_topics_and_image(pdf_text)
        
        # Store data in MongoDB
        person_data = {
            'name': name,
            'relation': relation,
            'occupation': occupation,
            'description': description,
            'image_url': image_url,
        }

        result = collection.update_one(
            {'email': email, 'first_name': first_name, 'last_name': last_name},
            {'$push': {'people_data': person_data}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"status": "Person data inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/delete/person")
async def delete_person(email: str, first_name: str, last_name: str, person_index: int):
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"people_data": 1, "_id": 0}
    )
    if query_result:
        person_data = query_result.get("people_data", [])
        if person_index < len(person_data):
            person_to_delete = person_data[person_index]
            collection.update_one(
                {"email": email, "first_name": first_name, "last_name": last_name},
                {"$pull": {"people_data": person_to_delete}}
            )
            export_and_upload_to_vector_store()
            return {"message": "Person data deleted successfully"}
    raise HTTPException(status_code=404, detail="Person not found")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/generate-mnemonic/")
async def generate_mnemonic(input_text: str = Form(...)):
    try:
        # Step 2: Generate Mnemonic Phrase
        client = Groq()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Generate a mnemonic device to remember the given phrase."},
                {"role": "user", "content": input_text}
            ]
        )
        mnemonic_text = response.choices[0].message.content

        # Step 3: Convert Mnemonic to Speech (TTS)
        openai_client = OpenAI()
        tts_response = openai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            input=mnemonic_text,
            voice="alloy",
            instructions="Explain in a caring engaging way like a teacher."
        )

        # Step 4: Save Audio File in Static Directory
        static_audio_dir = os.path.join("static", "audio")
        os.makedirs(static_audio_dir, exist_ok=True)
        audio_filename = f"{next(tempfile._get_candidate_names())}.mp3"
        audio_filepath = os.path.join(static_audio_dir, audio_filename)
        with open(audio_filepath, "wb") as audio_file:
            audio_file.write(tts_response.read())

        # Step 5: Construct the Audio URL
        audio_url = f"/static/audio/{audio_filename}"

        return JSONResponse(content={"mnemonic": mnemonic_text, "audio_url": audio_url})

    except Exception as e:
        print("ERROR:", str(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get/person")
async def get_person(email: str, first_name: str, last_name: str):
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"people_data": 1, "_id": 0}
    )
    if query_result:
        return query_result.get("people_data", [])
    else:
        return []
    
    





@app.get("/total_wellness")
def get_total_wellness():
    today = datetime.utcnow().date()  # Get today's date
    past_six_days = {today - timedelta(days=i): 0 for i in range(7)}  # Now includes today!

    # Fetch sentiment data
    user_data = collection.find_one({"email": "sh33thal24@gmail.com"})  # Fetch user by email
    if not user_data or "sentiment" not in user_data:
        return {"error": "No sentiment data found"}

    for entry in user_data["sentiment"]:
        try:
            # Convert timestamp to date only
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S").date()

            if entry_date in past_six_days:
                wellness_score = (
                    int(entry["wellness"]["$numberInt"])  # Handle MongoDB number format
                    if isinstance(entry["wellness"], dict) and "$numberInt" in entry["wellness"]
                    else int(entry["wellness"])
                )
                past_six_days[entry_date] += wellness_score
        except Exception as e:
            print(f"Skipping invalid entry: {entry}, Error: {e}")

    # Ensure today's entry exists even if no data is found
    if today not in past_six_days:
        past_six_days[today] = 0  # Default value

    # Format response
    response = [{"date": str(date), "value": score} for date, score in sorted(past_six_days.items(), reverse=True)]
    
    return response


@app.post("/get_answer/")
async def get_answer( question: str):
    final_answer = return_answer(question)

    # Store chat in the database
    collection.update_one(
        {"email": "sh33thal24@gmail.com"},
        {"$push": {"chat": {"user": question, "assistant": final_answer}}},
        upsert=True
    )
    export_and_upload_to_vector_store()
    return {"answer": final_answer}

def return_answer(question):
    # Your OpenAI Assistant logic here
    client = OpenAI()
    response1 = client.chat.completions.create(
        model="gpt-4o",  
        messages=[
            {"role": "system", "content": "You are an expert in advanced sentiment analysis. Given a text input, analyze sentiment at both the word level and the overall sentence structure. Detect emotionally charged words (e.g., 'scared,' 'excited,' 'angry', 'hopeful', 'frustrated', 'confused', 'indifferent', 'bored', 'reserved') and determine their impact on sentiment classification. Consider intensity, implied emotions, and context shifts. Classify the sentiment using a broader range of emotions such as 'joyful', 'sorrowful', 'enthusiastic', 'nervous', 'comforted', 'fearful', 'hostile', 'agitated', 'satisfied', 'optimistic', 'let down', 'uncertain', 'apathetic', 'disinterested', 'ambivalent', 'withdrawn', or 'neutral'. Provide only the sentiment classification as output."},
            {"role": "user", "content": question}
        ]
    )

    # Extract sentiment from OpenAI response
    ai_sentiment = response1.choices[0].message.content.strip().lower() if response1.choices else "Error"

    # Ensure the response contains only valid sentiment values
    valid_sentiments = {"joyful", "sorrowful", "enthusiastic", "nervous", "comforted", "fearful", "hostile", "agitated", "satisfied", "optimistic", "let down", "uncertain", "apathetic", "neutral", "disinterested", "ambivalent", "withdrawn"}
    if ai_sentiment not in valid_sentiments:
        ai_sentiment = "Error"

    # Fallback logic if OpenAI response is not available
    fallback_sentiment = detect_sentiment(question)
    final_sentiment = ai_sentiment if ai_sentiment != "Error" else fallback_sentiment

    # Determine wellness score
    wellness_score = determine_wellness(final_sentiment)

    output = {
        "date": print_current_datetime(),
        "sentiment": final_sentiment,
        "wellness": wellness_score
    }

    # Push to MongoDB
    collection.update_one(
        {"email": "sh33thal24@gmail.com"},
        {"$push": {"sentiment": output}}
    )
    
    assistant = client.beta.assistants.create(
        name="Personal Helper",
        instructions="The person asking questions is Sheethal Joshi",
        model=MODEL,
        tools=[{"type": "file_search"}],
    )

    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": ['vs_67d542ae493881918be2d7418d8d7b57' ]}},
    )

    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "Answer the following questions from the data files provided, keeping in mind that the user is Sheethal Joshi. She talks in first person."
            },
            {
                "role": "user",
                "content": question,
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=question,
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        return messages.data[0].content[0].text.value

    return "Sorry, I couldn't process that request."
    
@app.get("/get_chat_history")
async def get_chat_history(email: str):
    user = collection.find_one({"email": email})
    if not user or "chat" not in user:
        return JSONResponse(content={"chat": []}, status_code=200)

    chat_history = []
    for entry in user["chat"]:
        if "user" in entry:
            chat_history.append({"role": "user", "message": entry["user"]})
        if "assistant" in entry:
            chat_history.append({"role": "assistant", "message": entry["assistant"]})

    return {"chat": chat_history}

@app.get("/top-emotions")
def get_top_emotions():
    # Fetch sentiment data
    document = collection.find_one({"email": "sh33thal24@gmail.com"})  # Query by email
    if not document or "sentiment" not in document:
        return {"error": "No sentiment data found"}
    
    sentiments = [entry["sentiment"] for entry in document["sentiment"]]
    
    # Count occurrences of each sentiment
    sentiment_counts = Counter(sentiments)
    total_sentiments = sum(sentiment_counts.values())
    
    # Get the top 5 most common emotions with their percentages
    top_emotions = sentiment_counts.most_common(5)
    data = [
        {"name": emotion, "value": round((count / total_sentiments) * 100, 2)}
        for emotion, count in top_emotions
    ]
    
    return {"data": data}

@app.get("/wellness-trend")
def get_wellness_trend():
    # Fetch the document by email
    document = collection.find_one({"email": "sh33thal24@gmail.com"})
    if not document or "sentiment" not in document:
        return {"error": "No wellness data found"}

    wellness_data = document["sentiment"]

    # Transform data: Convert date format & apply transformation logic
    transformed_data = []
    for entry in wellness_data:
        if "date" in entry and "wellness" in entry:
            # Convert date format to "DD-MM-YYYY"
            try:
                formatted_date = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
            except ValueError:
                formatted_date = entry["date"]  # Use as-is if conversion fails
            
            # Transformation logic (example: scale values)
            scaled_wellness = entry["wellness"]["$numberInt"]
            transformed_data.append({
                "date": formatted_date,
                "wellness": int(scaled_wellness) * 10  # Adjust height by a factor
            })

    return {"data": transformed_data}


@app.delete("/clear_chat/")
async def clear_chat():
    result = collection.update_one(
        {"email": "sh33thal24@gmail.com"},
        {"$set": {"chat": []}}  
    )

    if result.matched_count == 0:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    
    return {"message": "Chat history cleared successfully"}

# Directory where PDFs are stored
PDF_DIRECTORY = "pdf_files"
AUDIO_DIRECTORY = "audio_files"
os.makedirs(PDF_DIRECTORY, exist_ok=True)
os.makedirs(AUDIO_DIRECTORY, exist_ok=True)

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class SummaryRequest(BaseModel):
    filename: str
    level: str

def extract_text_from_pdf(pdf_filename):
    """Extracts text from a locally stored PDF file."""
    pdf_path = os.path.join(PDF_DIRECTORY, pdf_filename)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file '{pdf_filename}' not found in {PDF_DIRECTORY}.")

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

    return text[:4000]  # Limit text to avoid API token limits

def generate_summary(text, level):
    """Generates a summary at the specified difficulty level using OpenAI."""
    prompts = {
        "beginner": "Narrate this content in simple and engaging terms for a curious learner.",
        "intermediate": "Explain this content with structured guidance for a college student.",
        "advanced": "Deliver an in-depth explanation for an advanced student or professional."
    }
    prompt = prompts.get(level, prompts["beginner"])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Summarize this content: {text}"}
        ]
    )
    return response.choices[0].message.content

def generate_story(text):
    """Generates a fun, story-based explanation of the content."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Convert this educational content into a storytelling format that makes learning fun."},
            {"role": "user", "content": f"Tell a story that teaches this topic: {text}"}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_mnemonic(text):
    """Generates a mnemonic or song to help remember the content."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Create a catchy mnemonic or song to help remember key information."},
            {"role": "user", "content": f"Generate a mnemonic or short song for: {text}"}
        ]
    )
    return response.choices[0].message.content.strip()

def text_to_speech(text, output_audio_path):
    """Converts text to speech and saves it as an audio file."""
    speech_file_path = os.path.join(AUDIO_DIRECTORY, output_audio_path)
    
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text,
        instructions="Narrate this content in a lively and engaging way."
    ) as response:
        response.stream_to_file(speech_file_path)

    return speech_file_path

# **API Endpoints**
@app.get("/summary/{pdf_filename}/{level}")
async def get_summary(pdf_filename: str, level: str = "beginner"):
    """Generates a summary from a locally stored PDF."""
    try:
        text = extract_text_from_pdf(pdf_filename)
        summary = generate_summary(text, level)

        audio_filename = f"{pdf_filename}_summary.mp3"
        audio_path = text_to_speech(summary, audio_filename)

        return {"summary": summary, "audio_path": f"/download_audio/{audio_filename}"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/{pdf_filename}")
async def get_story(pdf_filename: str):
    """Generates an educational story from a PDF."""
    try:
        text = extract_text_from_pdf(pdf_filename)
        story = generate_story(text)

        audio_filename = f"{pdf_filename}_story.mp3"
        audio_path = text_to_speech(story, audio_filename)

        return {"story": story, "audio_path": f"/download_audio/{audio_filename}"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount the audio files directory properly for static file serving
app.mount("/audio_files", StaticFiles(directory=AUDIO_DIRECTORY), name="audio_files")

@app.get("/download_audio/{filename}")
async def download_audio(filename: str):
    """Downloads the generated speech audio file."""
    file_path = os.path.join(AUDIO_DIRECTORY, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Return the direct URL instead of a JSON response
    return {"audio_url": f"/audio_files/{filename}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
