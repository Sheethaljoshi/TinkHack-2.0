from collections import Counter
from datetime import datetime, timedelta
import os
import random
import uuid
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
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

cluster = MongoClient("mongodb+srv://sh33thal24:sh33thal24@cluster0.wfa7cip.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", server_api=ServerApi('1'))
db = cluster["dementia"]
collection = db["fileids"]

MODEL = "gpt-4o-mini"

USER_EMAIL = "sh33thal24@gmail.com"

# Route to fetch user memories
@app.get("/memories/")
async def get_memories():
    user_data = collection.find_one({"email": USER_EMAIL}, {"_id": 0, "mem_data": 1})  # Fetch only mem_data
    if not user_data or "mem_data" not in user_data:
        raise HTTPException(status_code=404, detail="No memories found")
    return user_data["mem_data"]

@app.get("/generate_story")
async def generate_story():
    print("🔹 Received request to generate story")
    client = OpenAI()
    user_data = collection.find_one({"email": USER_EMAIL}, {"_id": 0, "mem_data": 1})
    print(f"🔹 User data found: {user_data}") 
    if not user_data or "mem_data" not in user_data:
        print("❌ No memories found")
        raise HTTPException(status_code=404, detail="No memories found")

    memories = user_data["mem_data"]
    if not memories:
        print("❌ Memory list is empty")
        raise HTTPException(status_code=404, detail="No memories found")

    
    selected_memory = random.choice(memories)
    print(f"🔹 Selected memory: {selected_memory}")
    
    story_prompt = f"Turn this memory into a short, warm, and nostalgic recap for a dementia patient:\n\nDate: {selected_memory['date']}\nMemory: {selected_memory['description']}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Gently remind the user of this past moment in a warm and reassuring tone. Keep it simple, clear, and nostalgic."},
                {"role": "user", "content": story_prompt}
            ]
        )
        story = response.choices[0].message.content
        print(f"✅ Story generated: {story}")

        audio_filename = f"story_{uuid.uuid4()}.mp3"
        print("🔹 Generating audio...")
        audio_response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=story,
            instructions="Whisper the response in a small, light tone."
        )

        with open(audio_filename, "wb") as audio_file:
            audio_file.write(audio_response.content)
        print(f"✅ Audio saved: {audio_filename}")

        dalle_response = client.images.generate(
            prompt=f"A heartwarming image representing this memory: {selected_memory['description']}",
            model="dall-e-3",
            n=1,
            size="1024x1024"
        )
        image_url = dalle_response.data[0].url
        
        print(f"✅ Image generated: {image_url}")

        return {
            "title": "Remember When...",
            "story": story,
             "audio_url": f"http://127.0.0.1:8000/get_audio/{audio_filename}",
            "image_url": image_url
        }
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")  # Log the exact error
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get_audio/{filename}")
async def get_audio(filename: str):
    file_path = f"./{filename}"  # Ensure correct path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")

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

@app.post("/insert/place")
async def insert_place(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    place_name: str = Form(...),
    place_description: str = Form(...),
    image: UploadFile = File(None)
):
    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": os.environ.get("IMGBB_API_KEY"),
        "image": image_base64
    }
    response = requests.post(url, payload)
    result = json.loads(response.text)
    print(result)
    url = result["data"]["url"]
    print(url)
    
    place_data = {
        'place_name': place_name,
        'image_url': url,
        'description': place_description,
    }

    update_result = collection.update_one(
        {'email': email, 'first_name': first_name, 'last_name': last_name},
        {'$push': {'places_mem': place_data}}
    )
    export_and_upload_to_vector_store()
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"status": "Place data inserted successfully"}

@app.post("/insert/person")
async def insert_person(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    name: str = Form(...),
    relation: str = Form(...),
    occupation: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(None)
):
    image_url = None
    if image:
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": os.environ.get("IMGBB_API_KEY"),
            "image": image_base64
        }
        response = requests.post(url, payload)
        result = json.loads(response.text)
        print(result)
        image_url = result["data"]["url"]
        print(image_url)
    
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

    export_and_upload_to_vector_store()
    return {"status": "Person data inserted successfully"}

@app.post("/insert/memory")
async def insert_memory(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    date: str = Form(...),
    description: str = Form(...)
):
    memory_data = {
        'date': date,
        'description': description
    }

    result = collection.update_one(
        {'email': email, 'first_name': first_name, 'last_name': last_name},
        {'$push': {'mem_data': memory_data}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    export_and_upload_to_vector_store()
    return {"status": "Memory data inserted successfully"}


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

@app.post("/delete/place")
async def delete_place(email: str, first_name: str, last_name: str, place_index: int):
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"places_mem": 1, "_id": 0}
    )
    if query_result:
        place_data = query_result.get("places_mem", [])
        if place_index < len(place_data):
            place_to_delete = place_data[place_index]
            collection.update_one(
                {"email": email, "first_name": first_name, "last_name": last_name},
                {"$pull": {"places_mem": place_to_delete}}
            )
            export_and_upload_to_vector_store()
            return {"message": "Place data deleted successfully"}
    raise HTTPException(status_code=404, detail="Place not found")

@app.post("/delete/mem")
async def delete_mem_data(email: str, first_name: str, last_name: str, mem_index: int):
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"mem_data": 1, "_id": 0}
    )
    if query_result:
        mem_data = query_result.get("mem_data", [])
        if mem_index < len(mem_data):
            mem_to_delete = mem_data[mem_index]
            collection.update_one(
                {"email": email, "first_name": first_name, "last_name": last_name},
                {"$pull": {"mem_data": mem_to_delete}}
            )
            export_and_upload_to_vector_store()
            return {"message": "Memory data deleted successfully"}
    raise HTTPException(status_code=404, detail="Memory data not found")

@app.get("/get/mem")
async def get_mem(email: str, first_name: str, last_name: str):
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"mem_data": 1, "_id": 0}
    )
    if query_result:
        return query_result.get("mem_data", [])
    else:
        return []

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

@app.get("/get/place")
async def get_place(email: str, first_name: str, last_name: str):
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"places_mem": 1, "_id": 0}
    )
    if query_result:
        return query_result.get("places_mem", [])
    else:
        return []
    
    

@app.post("/update/person")
async def update_person(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    name: str = Form(...),
    relation: str = Form(...),
    occupation: str = Form(...),
    description: str = Form(...),
    person_index: str = Form(...),
    image: UploadFile = File(None)
):  
    
    if image:
        image_bytes = await image.read()
        if image_bytes:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": os.environ.get("IMGBB_API_KEY"),
                "image": image_base64
            }
            response = requests.post(url, payload)
            result = json.loads(response.text)
            url = result["data"]["url"]
        else:
            url = None
    else:
        url = None
        
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"people_data": 1, "_id": 0}
    )
    
    if query_result:
        people_data = query_result.get("people_data", [])
        person_index = int(person_index)
        if person_index < len(people_data):
            existing_place = people_data[person_index]
            people_data[person_index] = {
                "name": name,
                "relation": relation,
                "occupation": occupation,
                "description": description,
                "image_url": url if url else existing_place.get("image_url"),
            }
            collection.update_one(
                {"email": email, "first_name": first_name, "last_name": last_name},
                {"$set": {"people_data": people_data}}
            )
            export_and_upload_to_vector_store()
            return {"message": "Person data updated successfully"}
    raise HTTPException(status_code=404, detail="Person not found")


@app.post("/update/place")
async def update_person(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    place_name: str = Form(...),
    description: str = Form(...),
    place_index: str = Form(...),  # Received as a string
    image: UploadFile = File(None)
):  
    if image:
        image_bytes = await image.read()
        if image_bytes:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": os.environ.get("IMGBB_API_KEY"),
                "image": image_base64
            }
            response = requests.post(url, payload)
            result = json.loads(response.text)
            url = result["data"]["url"]
        else:
            url = None
    else:
        url = None
    
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"places_mem": 1, "_id": 0}
    )
    if query_result:
        places_mem = query_result.get("places_mem", [])
        place_index = int(place_index)  # Convert to integer
        
        if place_index < len(places_mem):
            existing_place = places_mem[place_index]
            places_mem[place_index] = {
                "place_name": place_name,
                "image_url": url if url else existing_place.get("image_url"),
                "description": description
            }
            collection.update_one(
                {"email": email, "first_name": first_name, "last_name": last_name},
                {"$set": {"places_mem": places_mem}}
            )
            export_and_upload_to_vector_store()
            return {"message": "Place data updated successfully"}
    
    raise HTTPException(status_code=404, detail="Place not found")

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


@app.post("/update/mem")
async def update_person(email: str, first_name: str, last_name: str, mem_index: int, date: str, description: str):
    query_result = collection.find_one(
        {"email": email, "first_name": first_name, "last_name": last_name},
        {"mem_data": 1, "_id": 0}
    )
    if query_result:
        places_mem= query_result.get("mem_data", [])
        if mem_index < len(places_mem):
            places_mem[mem_index] = {
                "date": date,
                "description": description
            }
            collection.update_one(
                {"email": email, "first_name": first_name, "last_name": last_name},
                {"$set": {"mem_data": places_mem}}
            )
            export_and_upload_to_vector_store()
            return {"message": "Place data updated successfully"}
    raise HTTPException(status_code=404, detail="Place not found")

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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
