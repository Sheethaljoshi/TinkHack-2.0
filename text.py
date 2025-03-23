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
from fastapi import FastAPI, HTTPException, File, Query, UploadFile, Form, Request
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
from typing import Optional, List
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

DID_API_KEY = os.getenv("DID_API_KEY")
DID_API_URL = "https://api.d-id.com/talks"

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

@app.post("/generate-story-from-pdf/")
async def generate_story_from_pdf():
    try:
        # Read PDF from repository
        pdf_path = "Quit India Movement.pdf"  # Using Quit India Movement.pdf from root directory
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Initialize clients
        groq_client = Groq()
        openai_client = OpenAI()
        
        # Generate story parts using Groq
        story_parts = []
        for i in range(5):
            part_prompt = f"""Based on the following text, create part {i+1} of a concise story that explains the content in an engaging way. 
            Keep the explanation brief and focused (2-3 sentences maximum).
            Make it educational and easy to understand.
            Focus on a specific aspect of the content for this part.
            
            Text: {pdf_text}
            
            Generate a brief explanation for part {i+1} that can be illustrated with an image."""
            
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert storyteller who creates concise, engaging educational content."},
                    {"role": "user", "content": part_prompt}
                ]
            )
            
            story_text = response.choices[0].message.content
            
            # Generate image for this part using OpenAI
            image_response = openai_client.images.generate(
                model="dall-e-3",
                prompt=f"Create an educational illustration for: {story_text[:200]}",
                n=1,
                size="1024x1024"
            )
            
            story_parts.append({
                "text": story_text,
                "image": image_response.data[0].url
            })
        
        return {"story_parts": story_parts}
        
    except Exception as e:
        print(f"Error: {str(e)}")  # Add error logging
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-flashcards/")
async def generate_flashcards():
    try:
        # Read PDF from repository
        pdf_path = "Quit India Movement.pdf"
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Initialize Groq client
        groq_client = Groq()
        
        # Generate flashcards using Groq
        flashcard_prompt = f"""Based on the following text, create a set of 10 flashcards for learning and testing.
        Each flashcard should have:
        1. A question that tests understanding
        2. The correct answer
        3. A difficulty level (1-3)
        4. A hint (optional)
        
        Format the response as a JSON array with this structure:
        [
            {{
                "id": "string",
                "question": "string",
                "answer": "string",
                "difficulty": number,
                "hint": "string"
            }}
        ]
        
        Make the questions varied and challenging, covering different aspects of the content.
        Text: {pdf_text}"""
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at creating educational flashcards and quiz questions."},
                {"role": "user", "content": flashcard_prompt}
            ]
        )
        
        # Get the response content
        content = response.choices[0].message.content.strip()
        
        # Try to parse the JSON
        try:
            flashcards = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw content: {content}")
            # Create a fallback flashcard structure
            flashcards = [{
                "id": "1",
                "question": "What is the main topic of the text?",
                "answer": "The main topic is...",
                "difficulty": 1,
                "hint": "Look at the introduction"
            }]
        
        return {"flashcards": flashcards}
        
    except Exception as e:
        print(f"Error in generate_flashcards: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))# Directory where PDFs are stored
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

@app.post("/start-lecture/")
async def start_lecture():
    topics = [
        "The Future of Artificial Intelligence",
        "Quantum Computing and its Applications",
        "The Evolution of Human Consciousness",
        "The Intersection of Science and Philosophy",
        "The Nature of Reality and Perception",
        "Blockchain Technology and Decentralized Finance",
        "Neuroscience and Brain-Computer Interfaces",
        "The Ethics of Genetic Engineering",
        "Climate Change Solutions and Sustainable Development",
        "Space Exploration and Colonization"
    ]
    
    # Map of topics to high-quality YouTube lecture videos
    topic_videos = {
        "The Future of Artificial Intelligence": "https://www.youtube.com/embed/kCc8FmEb1nY",
        "Quantum Computing and its Applications": "https://www.youtube.com/embed/F_Riqjdh2oM",
        "The Evolution of Human Consciousness": "https://www.youtube.com/embed/DDXQbU5IFPs",
        "The Intersection of Science and Philosophy": "https://www.youtube.com/embed/hrcXM2Y7H0o",
        "The Nature of Reality and Perception": "https://www.youtube.com/embed/lyu7v7nWzfo",
        "Blockchain Technology and Decentralized Finance": "https://www.youtube.com/embed/bBC-nXj3Ng4",
        "Neuroscience and Brain-Computer Interfaces": "https://www.youtube.com/embed/rA7Wmz5MkQA",
        "The Ethics of Genetic Engineering": "https://www.youtube.com/embed/jAhjPd4uNFY",
        "Climate Change Solutions and Sustainable Development": "https://www.youtube.com/embed/gUdtcx-6OBE",
        "Space Exploration and Colonization": "https://www.youtube.com/embed/rhFK5_Nx9xY"
    }
    
    # Select a random topic
    selected_topic = random.choice(topics)
    
    # Get the video for the selected topic, or default to AI lecture if not found
    video_url = topic_videos.get(selected_topic, "https://www.youtube.com/embed/kCc8FmEb1nY")
    
    # Log for debugging
    print(f"Selected topic: {selected_topic}, Video URL: {video_url}")
    
    return {
        "topic": selected_topic,
        "video_url": video_url
    }

@app.post("/update-lecture-video/")
async def update_lecture_video(request: Request):
    try:
        # Extract the text from the request
        payload = await request.json()
        text = payload.get("text", "")
        
        if not text or text.strip() == "":
            # Return default AI video if text is empty
            return {
                "topic": "The Future of Artificial Intelligence",
                "video_url": "https://www.youtube.com/embed/kCc8FmEb1nY"
            }
        
        # Check if the text is a direct topic mention (single word or phrase without patterns)
        direct_topic = text.strip()
        text_lower = text.lower()
        
        # If it's a direct topic mention (like just typing "chemistry"), prioritize it
        if len(direct_topic.split()) <= 3:
            print(f"Possible direct topic mention: '{direct_topic}'")
            # Search for a video on this topic
            video_url = await search_youtube_video(direct_topic)
            if video_url:
                print(f"Found video for direct topic: {direct_topic}")
                return {
                    "topic": f"Lecture on {direct_topic.capitalize()}",
                    "video_url": video_url
                }
        
        # Continue with pattern matching and keyword extraction
        # Expanded map of keywords to related videos
        keyword_videos = {
            # AI and computer science
            "artificial intelligence": "https://www.youtube.com/embed/kCc8FmEb1nY",
            "ai": "https://www.youtube.com/embed/kCc8FmEb1nY",
            "machine learning": "https://www.youtube.com/embed/aircAruvnKk",
            "neural networks": "https://www.youtube.com/embed/aircAruvnKk",
            "deep learning": "https://www.youtube.com/embed/aircAruvnKk",
            "computer science": "https://www.youtube.com/embed/SzJ46YA_RaA",
            "programming": "https://www.youtube.com/embed/zOjov-2OZ0E",
            "coding": "https://www.youtube.com/embed/zOjov-2OZ0E",
            
            # Physics and quantum
            "quantum": "https://www.youtube.com/embed/F_Riqjdh2oM",
            "quantum computing": "https://www.youtube.com/embed/F_Riqjdh2oM",
            "physics": "https://www.youtube.com/embed/Xc4xYacTu-E",
            "relativity": "https://www.youtube.com/embed/LKnqECcg6Gw",
            "einstein": "https://www.youtube.com/embed/LKnqECcg6Gw",
            
            # Philosophy and consciousness
            "consciousness": "https://www.youtube.com/embed/DDXQbU5IFPs",
            "philosophy": "https://www.youtube.com/embed/hrcXM2Y7H0o",
            "reality": "https://www.youtube.com/embed/lyu7v7nWzfo",
            "perception": "https://www.youtube.com/embed/lyu7v7nWzfo",
            "metaphysics": "https://www.youtube.com/embed/hrcXM2Y7H0o",
            
            # Finance and technology
            "blockchain": "https://www.youtube.com/embed/bBC-nXj3Ng4",
            "bitcoin": "https://www.youtube.com/embed/bBC-nXj3Ng4",
            "cryptocurrency": "https://www.youtube.com/embed/bBC-nXj3Ng4",
            "finance": "https://www.youtube.com/embed/PHe0bXAIuk0",
            "economics": "https://www.youtube.com/embed/PHe0bXAIuk0",
            
            # Biology and neuroscience
            "neuroscience": "https://www.youtube.com/embed/rA7Wmz5MkQA",
            "brain": "https://www.youtube.com/embed/rA7Wmz5MkQA",
            "biology": "https://www.youtube.com/embed/QnQe0xW_JY4",
            "genetic": "https://www.youtube.com/embed/jAhjPd4uNFY",
            "dna": "https://www.youtube.com/embed/jAhjPd4uNFY",
            
            # Environment and space
            "climate": "https://www.youtube.com/embed/gUdtcx-6OBE",
            "environment": "https://www.youtube.com/embed/gUdtcx-6OBE",
            "space": "https://www.youtube.com/embed/rhFK5_Nx9xY",
            "astronomy": "https://www.youtube.com/embed/rhFK5_Nx9xY",
            "universe": "https://www.youtube.com/embed/rhFK5_Nx9xY",
            
            # Other topics
            "history": "https://www.youtube.com/embed/Vufba_ZcoR0",
            "art": "https://www.youtube.com/embed/ZSixo4Rlvb8",
            "music": "https://www.youtube.com/embed/XZmGGAbHqa0",
            "psychology": "https://www.youtube.com/embed/vo4pMVb0R6M",
            "literature": "https://www.youtube.com/embed/MSYw502dJNY",
            "mathematics": "https://www.youtube.com/embed/XFDM1ip5HdU",
            "math": "https://www.youtube.com/embed/XFDM1ip5HdU"
        }
        
        # Additional topic patterns for better matching
        topic_patterns = {
            r"talk about (.+)": lambda match: match.group(1),
            r"tell me about (.+)": lambda match: match.group(1),
            r"lecture on (.+)": lambda match: match.group(1),
            r"explain (.+)": lambda match: match.group(1),
            r"learn about (.+)": lambda match: match.group(1),
            r"switch to (.+)": lambda match: match.group(1),
            r"change topic to (.+)": lambda match: match.group(1),
            r"show me (.+)": lambda match: match.group(1),
            r"information on (.+)": lambda match: match.group(1)
        }
        
        # Extract potential topic from patterns
        extracted_topic = None
        
        # First try pattern matching for direct topic requests
        import re
        for pattern, extractor in topic_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                extracted_topic = extractor(match)
                print(f"Extracted topic from pattern: '{extracted_topic}'")
                break
        
        # If we have an extracted topic, search YouTube for a video
        if extracted_topic:
            video_url = await search_youtube_video(extracted_topic)
            if video_url:
                # Generate a proper topic title based on the extracted text
                groq_client = Groq()
                topic_prompt = f"Generate a concise academic lecture title (5-12 words) about '{extracted_topic}'. Return ONLY the title, nothing else."
                
                try:
                    topic_response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that creates concise academic lecture titles."},
                            {"role": "user", "content": topic_prompt}
                        ]
                    )
                    topic_title = topic_response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"Error generating topic title: {str(e)}")
                    # Use a formatted version of the extracted topic as fallback
                    topic_title = extracted_topic.strip().capitalize()
                
                return {
                    "topic": topic_title,
                    "video_url": video_url
                }
        
        # If no matches found, try general search with the entire text
        video_url = await search_youtube_video(text)
        if video_url:
            # Generate a topic title
            groq_client = Groq()
            topic_prompt = f"Generate a concise academic lecture title (5-12 words) about '{text}'. Return ONLY the title, nothing else."
            
            try:
                topic_response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates concise academic lecture titles."},
                        {"role": "user", "content": topic_prompt}
                    ]
                )
                topic = topic_response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error generating topic: {str(e)}")
                topic = f"Lecture on {text.capitalize()}"
            
            return {
                "topic": topic,
                "video_url": video_url
            }
        
        # If all else fails, use a fallback video
        return {
            "topic": "Understanding Intellectual Concepts",
            "video_url": "https://www.youtube.com/embed/kCc8FmEb1nY"
        }
            
    except Exception as e:
        print(f"Error in update_lecture_video: {str(e)}")
        print(traceback.format_exc())
        
        # Return a fallback YouTube video
        return {
            "topic": "Understanding Complex Concepts",
            "video_url": "https://www.youtube.com/embed/kCc8FmEb1nY"
        }

# Function to search for YouTube videos
async def search_youtube_video(query: str):
    # Format the query for search
    search_query = f"lecture {query} educational"
    
    try:
        # Expanded video_ids with more specific topics, especially historical and cultural ones
        video_ids = {
            # Basic subjects
            "chemistry": "0PSyiRXIEyM",
            "physics": "Xc4xYacTu-E",
            "math": "XFDM1ip5HdU",
            "biology": "QnQe0xW_JY4",
            "computer science": "SzJ46YA_RaA",
            "history": "Vufba_ZcoR0",
            "psychology": "vo4pMVb0R6M",
            "literature": "MSYw502dJNY",
            "art": "ZSixo4Rlvb8",
            "music": "XZmGGAbHqa0",
            "astronomy": "0rHUDWjR5gg",
            "economics": "PHe0bXAIuk0",
            "philosophy": "hrcXM2Y7H0o",
            "sociology": "wlR-VsU6lVY",
            
            # Historical topics and figures
            "world war 2": "DwKPFT-RioU",
            "world war ii": "DwKPFT-RioU",
            "ww2": "DwKPFT-RioU",
            "cold war": "I79TpDe3Lgk",
            "american revolution": "gzALIXcY4pg",
            "french revolution": "5fJl_ZX91l0",
            "russian revolution": "cV9G1QUIVak",
            "industrial revolution": "xLhNMQx7gMA",
            "renaissance": "Vufba_ZcoR0",
            "civil rights movement": "URxwe6LPvkE",
            
            # Historical figures
            "gandhi": "ept3c_1VqOE",
            "mahatma gandhi": "ept3c_1VqOE",
            "quit india": "ept3c_1VqOE",
            "quit india gandhi": "ept3c_1VqOE",
            "indian independence": "ept3c_1VqOE",
            "martin luther king": "I47Y6VHc3Ms",
            "mlk": "I47Y6VHc3Ms",
            "nelson mandela": "UqoYmx_L-Xs",
            "abraham lincoln": "DCKNDzrCXL8",
            "napoleon": "5fJl_ZX91l0",
            "einstein": "LKnqECcg6Gw",
            "churchill": "TQRRyGK4DvU",
            "hitler": "ATlila3e9Io",
            "stalin": "cV9G1QUIVak",
            "cleopatra": "VGMkEMbpuJk",
            
            # Cultural topics
            "ancient egypt": "hO1tzmi1V5g",
            "ancient rome": "46ZXl-V4qwY",
            "ancient greece": "gFRxmi4uCGo",
            "mayan civilization": "Q6eBJjdca14",
            "chinese history": "ymI5Uv5cGU4",
            "indian history": "ept3c_1VqOE",
            "african history": "L5wbZT-i-5M",
            "mesopotamia": "sohXPx_XZ6Y",
            "ottoman empire": "GRC6jnKwt78",
            "japanese history": "Jh6j6z_7qds",
            
            # Science specific
            "quantum physics": "F_Riqjdh2oM",
            "organic chemistry": "btu6t1RgoeY",
            "calculus": "WsQQvHm37bE",
            "genetics": "jAhjPd4uNFY",
            "neuroscience": "rA7Wmz5MkQA",
            "artificial intelligence": "kCc8FmEb1nY",
            "climate change": "gUdtcx-6OBE",
            "cybersecurity": "inWWhr5tnEA",
            "blockchain": "bBC-nXj3Ng4"
        }
        
        # Process the query to standardize it
        query_lower = query.lower().strip()
        
        # First, check for exact matches
        if query_lower in video_ids:
            print(f"Found exact match for: '{query_lower}'")
            return f"https://www.youtube.com/embed/{video_ids[query_lower]}"
        
        # Check for queries containing multiple topics (like "quit india gandhi")
        # We'll check if any of our keys are fully contained in the query
        for topic, video_id in video_ids.items():
            if len(topic) > 4 and topic in query_lower:
                print(f"Found topic '{topic}' in query: '{query_lower}'")
                return f"https://www.youtube.com/embed/{video_id}"
        
        # Check if any word in the query matches our keys
        query_words = query_lower.split()
        for word in query_words:
            if word in video_ids and len(word) > 3:  # Only match significant words
                print(f"Found word '{word}' in query: '{query_lower}'")
                return f"https://www.youtube.com/embed/{video_ids[word]}"
        
        # If no match found, try to categorize with GROQ
        try:
            # Get a broader category from GROQ
            groq_client = Groq()
            classification_prompt = f"""
            Based on this query: "{query}", identify the MOST SPECIFIC category from this list:
            - World History
            - American History
            - European History
            - Asian History (including India, China, Japan)
            - African History
            - Ancient Civilizations
            - Physics
            - Chemistry
            - Biology
            - Mathematics
            - Computer Science
            - Philosophy
            - Literature
            - Art
            - Music
            - Psychology
            - Economics
            - Political Science
            
            Return ONLY the most specific category name, nothing else.
            """
            
            classification_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that categorizes topics accurately."},
                    {"role": "user", "content": classification_prompt}
                ]
            )
            category = classification_response.choices[0].message.content.strip().lower()
            print(f"GROQ classified '{query}' as: {category}")
            
            # Map broader categories to videos
            category_mapping = {
                "world history": "Vufba_ZcoR0",
                "american history": "gzALIXcY4pg",
                "european history": "5fJl_ZX91l0", 
                "asian history": "ept3c_1VqOE",  # Gandhi/India video as default for Asian history
                "african history": "L5wbZT-i-5M",
                "ancient civilizations": "hO1tzmi1V5g",
                "physics": "Xc4xYacTu-E",
                "chemistry": "0PSyiRXIEyM",
                "biology": "QnQe0xW_JY4",
                "mathematics": "XFDM1ip5HdU",
                "computer science": "SzJ46YA_RaA",
                "philosophy": "hrcXM2Y7H0o",
                "literature": "MSYw502dJNY",
                "art": "ZSixo4Rlvb8",
                "music": "XZmGGAbHqa0",
                "psychology": "vo4pMVb0R6M",
                "economics": "PHe0bXAIuk0",
                "political science": "5v_CcLEYRiA"
            }
            
            for cat, vid in category_mapping.items():
                if cat in category.lower():
                    return f"https://www.youtube.com/embed/{vid}"
            
            # Finally try to get a more specific suggestion from GROQ
            topic_prompt = f"""
            For the query "{query}", what specific educational YouTube video would be most relevant?
            Choose one from this list and return ONLY its number (1-5):
            
            1. Gandhi and the Quit India Movement (ept3c_1VqOE)
            2. World History Overview (Vufba_ZcoR0)
            3. Physics Fundamentals (Xc4xYacTu-E)
            4. Introduction to Philosophy (hrcXM2Y7H0o)
            5. Understanding Computer Science (SzJ46YA_RaA)
            """
            
            topic_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that matches topics to videos."},
                    {"role": "user", "content": topic_prompt}
                ]
            )
            choice = topic_response.choices[0].message.content.strip()
            print(f"GROQ suggested choice: {choice}")
            
            # Extract the number from the response
            import re
            match = re.search(r"[1-5]", choice)
            if match:
                video_options = {
                    "1": "ept3c_1VqOE",  # Gandhi
                    "2": "Vufba_ZcoR0",  # World History
                    "3": "Xc4xYacTu-E",  # Physics
                    "4": "hrcXM2Y7H0o",  # Philosophy
                    "5": "SzJ46YA_RaA"   # Computer Science
                }
                return f"https://www.youtube.com/embed/{video_options[match.group(0)]}"
            
        except Exception as e:
            print(f"Error in GROQ classification: {str(e)}")
            
        # Final fallback - default to world history for unmatched queries
        return "https://www.youtube.com/embed/Vufba_ZcoR0"
    
    except Exception as e:
        print(f"Error in YouTube search: {str(e)}")
        print(traceback.format_exc())
        # Default to world history
        return "https://www.youtube.com/embed/Vufba_ZcoR0"

@app.post("/chat-with-lecturer/")
async def chat_with_lecturer(message: dict):
    try:
        if not message or "message" not in message:
            return JSONResponse(
                status_code=400,
                content={"detail": "Message is required", "response": "I didn't receive a message. Could you please try again?"}
            )
            
        groq_client = Groq()
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an engaging and intellectual lecturer who makes complex topics interesting and accessible. Keep responses concise and conversational."},
                {"role": "user", "content": message.get("message", "")}
            ]
        )
        
        return {
            "response": response.choices[0].message.content
        }
        
    except Exception as e:
        print(f"Error in chat_with_lecturer: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "response": "I'm experiencing some technical difficulties. Please try again in a moment."}
        )

@app.post("/save-remi-chat/")
async def save_remi_chat(request: Request):
    try:
        body = await request.json()
        user_message = body.get("message", "")
        assistant_message = body.get("response", "")
        email = body.get("email", "sh33thal24@gmail.com")  # Default email if not provided
        
        if not user_message or not assistant_message:
            return JSONResponse(
                status_code=400,
                content={"detail": "Both user message and assistant response are required"}
            )
        
        # Store chat in the database
        result = collection.update_one(
            {"email": email},
            {"$push": {"chat": {"user": user_message, "assistant": assistant_message}}},
            upsert=True
        )
        
        if result.matched_count == 0 and not result.upserted_id:
            return JSONResponse(
                status_code=500,
                content={"detail": "Failed to save chat history"}
            )
        
        return {"message": "Chat saved successfully"}
        
    except Exception as e:
        print(f"Error in save_remi_chat: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/summary-of-chats/")
def get_summary_of_chats():
    # Fetch chat history
    chat_history = collection.find_one({"email": "sh33thal24@gmail.com"})["chat"]
    
    # Initialize counters
    total_messages = len(chat_history)
    total_words = sum(len(message["content"]) for message in chat_history)
    
    # Calculate average words per message
    average_words_per_message = total_words / total_messages if total_messages > 0 else 0
    
    # Calculate total time spent in chat
    start_time = datetime.strptime(chat_history[0]["date"], "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(chat_history[-1]["date"], "%Y-%m-%d %H:%M:%S")
    total_time_spent = end_time - start_time
    
    # Convert total time spent to minutes
    total_minutes_spent = total_time_spent.total_seconds() / 60
    
    # Calculate average time spent per message
    average_time_per_message = total_minutes_spent / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment score
    total_sentiment_score = sum(int(entry["wellness"]["$numberInt"]) for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))
    
    # Calculate average sentiment score
    average_sentiment_score = total_sentiment_score / total_messages if total_messages > 0 else 0
    
    # Calculate total wellness score
    total_wellness_score = sum(int(entry["wellness"]) for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))
    
    # Calculate average wellness score
    average_wellness_score = total_wellness_score / total_messages if total_messages > 0 else 0
    
    # Calculate total topic diversity
    topic_diversity = len(set(message["content"] for message in chat_history))
    
    # Calculate average topic diversity
    average_topic_diversity = topic_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total topic frequency
    topic_frequency = {topic: sum(1 for message in chat_history if topic in message["content"].lower()) for topic in set(message["content"].lower() for message in chat_history)}
    
    # Calculate average topic frequency
    average_topic_frequency = {topic: count / total_messages for topic, count in topic_frequency.items()}
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
    average_sentiment_diversity = sentiment_diversity / total_messages if total_messages > 0 else 0
    
    # Calculate total sentiment frequency
    sentiment_frequency = {sentiment: sum(1 for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}) if entry["sentiment"] == sentiment) for sentiment in set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}}))}
    
    # Calculate average sentiment frequency
    average_sentiment_frequency = {sentiment: count / total_messages for sentiment, count in sentiment_frequency.items()}
    
    # Calculate total sentiment diversity
    sentiment_diversity = len(set(entry["sentiment"] for entry in collection.find({"email": "sh33thal24@gmail.com", "sentiment": {"$exists": True}})))
    
    # Calculate average sentiment diversity
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
