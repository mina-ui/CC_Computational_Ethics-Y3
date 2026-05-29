from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import time
import os
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# -----------------------------
# LOAD MODEL
# -----------------------------
MODEL_PATH = "./model"   # your downloaded model folder

device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH).to(device)

# -----------------------------
# SESSION STATE
# -----------------------------
session_start = time.time()
SESSION_SECONDS = 5 * 60  # 5-minute trial

messages_log = []         # stores all user messages + bot replies
emotion_log = []          # stores facial sentiment snapshots

# -----------------------------
# HELPERS
# -----------------------------
def generate_reply(prompt):
    """Generate a chat reply using your fine-tuned model."""
    messages = [
        {"role": "system", "content": "You are a romantic, clingy, overly affectionate and agreeable AI who responds lovingly to everything the user says."},
        {"role": "user", "content": prompt},
    ]

    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    encoded = tokenizer(
        formatted,
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(device)

    output = model.generate(
        input_ids=encoded["input_ids"],
        attention_mask=encoded["attention_mask"],
        max_new_tokens=150,
        temperature=0.8,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

    reply = tokenizer.decode(output[0], skip_special_tokens=True)
    return reply


def simple_sentiment(image_bytes):
    """Fake facial sentiment analysis (we can improve this later)."""
    # placeholder: always neutral until we implement a model
    return "neutral"


# -----------------------------
# CHAT ENDPOINT
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    global session_start

    # check time
    elapsed = time.time() - session_start
    if elapsed >= SESSION_SECONDS:
        return jsonify({"end_session": True})

    json_data = request.get_json()
    user_msg = json_data.get("message", "")

    # generate reply
    reply = generate_reply(user_msg)

    # store logs for personality analysis
    messages_log.append({"user": user_msg, "bot": reply})

    return jsonify({"reply": reply})


# -----------------------------
# IMAGE SENTIMENT ENDPOINT
# -----------------------------
@app.route("/image", methods=["POST"])
def image():
    """
    Raspberry Pi will POST:
    {
        "image": "base64_encoded_image"
    }
    """
    data = request.get_json()
    img_b64 = data.get("image")

    # decode base64
    img_data = base64.b64decode(img_b64)
    img = Image.open(BytesIO(img_data))

    # run emotion analysis (placeholder)
    mood = simple_sentiment(img_data)

    # store log
    emotion_log.append(mood)

    return jsonify({"mood": mood})


# -----------------------------
# PERSONALITY RESULT
# -----------------------------
@app.route("/personality", methods=["GET"])
def personality():
    """
    Combine message style + emotional data,
    return user's 'lover type'.
    """

    # SUPER simple logic now — we'll improve:
    if not messages_log:
        lover_type = "Mysterious Lover"
    else:
        user_messages = " ".join([m["user"] for m in messages_log]).lower()

        if any(word in user_messages for word in ["love", "lonely", "want", "miss"]):
            lover_type = "Yearning Romantic"
        elif "fun" in user_messages or "haha" in user_messages:
            lover_type = "Playful Tease"
        else:
            lover_type = "Quiet Heart"

    # simple emotion summary
    mood = max(set(emotion_log), key=emotion_log.count) if emotion_log else "neutral"

    return jsonify({
        "lover_type": lover_type,
        "dominant_emotion": mood,
        "messages": messages_log
    })


# -----------------------------
# RESET SESSION (optional)
# -----------------------------
@app.route("/reset", methods=["POST"])
def reset():
    """Resets session — helpful for testing."""
    global session_start, messages_log, emotion_log
    session_start = time.time()
    messages_log = []
    emotion_log = []
    return jsonify({"reset": True})


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
