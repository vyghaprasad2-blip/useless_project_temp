from flask import Flask, render_template, request, session
from groq import Groq
from dotenv import load_dotenv
import os
import json

# =====================================================
# SETUP
# =====================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = "delul-hackathon-secret-key"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY is missing from .env")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# =====================================================
# PERSONALITY QUESTIONS
# =====================================================

questions = [

    {
        "question": "Your friend hasn't replied for 2 hours. What do you think?",
        "options": [
            ("They're probably busy 😌", "chill"),
            ("Maybe they didn't see it.", "normal"),
            ("Did I say something wrong? 🕵️", "detective"),
            ("Something definitely happened. 🔮", "scenario")
        ]
    },

    {
        "question": "Someone replies 'K'. What's your first thought?",
        "options": [
            ("Okay, whatever.", "chill"),
            ("That's slightly dry.", "normal"),
            ("Why did they say K specifically?", "message"),
            ("This could mean something terrible.", "scenario")
        ]
    },

    {
        "question": "You notice a typo after sending a message.",
        "options": [
            ("Nobody cares.", "chill"),
            ("I'll correct it.", "normal"),
            ("Why didn't I notice it before sending?", "message"),
            ("They probably think I'm weird now.", "scenario")
        ]
    },

    {
        "question": "Someone says: 'We need to talk.'",
        "options": [
            ("Okay.", "chill"),
            ("I'll ask what about.", "normal"),
            ("Why did they phrase it like that?", "detective"),
            ("Let's prepare for every possible outcome.", "scenario")
        ]
    },

    {
        "question": "Someone leaves you on seen.",
        "options": [
            ("They're busy.", "chill"),
            ("I'll wait.", "normal"),
            ("Why did they read it but not reply?", "message"),
            ("Something must be wrong.", "scenario")
        ]
    },

    {
        "question": "Someone replies after exactly 5 minutes.",
        "options": [
            ("Normal.", "chill"),
            ("Didn't notice.", "normal"),
            ("Why exactly 5 minutes?", "detective"),
            ("Were they deciding what to say?", "scenario")
        ]
    }
]


# =====================================================
# DELUL PERSONALITIES
# =====================================================

DELUL_PERSONALITIES = {

    "chill": {
        "name": "THE CHILL ONE 😌",

        "description":
            "You somehow manage to not overthink everything.",

        "style":
            "Be extremely relaxed and reasonable."
    },

    "normal": {
        "name": "THE CASUAL THINKER 🤔",

        "description":
            "You think about things, but usually know when to stop.",

        "style":
            "Give a few realistic possibilities while staying playful."
    },

    "detective": {
        "name": "THE DELUL DETECTIVE 🕵️",

        "description":
            "You see clues where normal people see absolutely nothing.",

        "style":
            """
Act like an absurd detective.

Analyze:
- wording
- punctuation
- timing
- emojis
- tiny details

Use phrases such as:
'Evidence #1'
'Suspicious...'
'Something isn't adding up.'

Everything must be obviously fictional and humorous.
"""
    },

    "message": {
        "name": "THE MESSAGE ANALYST 💬",

        "description":
            "You believe punctuation contains information.",

        "style":
            """
Obsess over:
- punctuation
- emojis
- typing style
- response time
- word choice
- message length

Make the analysis ridiculously detailed but harmless.
"""
    },

    "scenario": {
        "name": "THE SCENARIO BUILDER 🔮",

        "description":
            "One tiny event can create an entire cinematic universe.",

        "style":
            """
Create increasingly ridiculous hypothetical scenarios.

Use:
'What if...'
'But then...'
'Imagine if...'
'Theoretically...'

Everything is fictional and comedic.
"""
    }
}


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# QUESTIONS
# =====================================================

@app.route("/questions")
def show_questions():
    return render_template(
        "questions.html",
        questions=questions
    )


# =====================================================
# PERSONALITY CALCULATION
# =====================================================

@app.route("/personality", methods=["POST"])
def calculate_personality():

    scores = {
        "chill": 0,
        "normal": 0,
        "detective": 0,
        "message": 0,
        "scenario": 0
    }

    for i in range(len(questions)):

        answer = request.form.get(f"q{i}")

        if answer in scores:
            scores[answer] += 1

    personality = max(
        scores,
        key=scores.get
    )

    session["personality"] = personality
    session["scores"] = scores

    profile = DELUL_PERSONALITIES[personality]

    return render_template(
        "result.html",
        personality=profile["name"],
        description=profile["description"],
        scores=scores,
        personality_only=True
    )


# =====================================================
# GROQ AI
# =====================================================

def generate_delul(decision, personality, level):

    if not client:

        return {
            "title": "DELUL API IS SLEEPING 😭",

            "delul_score": 50,

            "analysis":
                "Groq isn't connected yet.",

            "spiral": [
                "Did we add the API key?",
                "Is the .env file correct?",
                "Did Python load the .env file?",
                "Is Groq judging our project?",
                "Maybe we're overthinking the API."
            ],

            "verdict":
                "CHECK YOUR GROQ API KEY 💀"
        }

    profile = DELUL_PERSONALITIES[personality]

    system_prompt = f"""
You are DELUL.

You are NOT a normal assistant.

You are a comedy AI that takes a harmless everyday
decision and dramatically overthinks it.

USER PERSONALITY:
{profile["name"]}

PERSONALITY DESCRIPTION:
{profile["description"]}

PERSONALITY STYLE:
{profile["style"]}

OVERTHINKING LEVEL:
{level}/5

LEVEL RULES:

1 = mild overthinking
2 = noticeable overthinking
3 = ridiculous overthinking
4 = extreme thought spiral
5 = completely unnecessary cinematic overthinking

IMPORTANT:

This is comedy.

Never claim that your speculation about another
person is actually true.

Never diagnose anyone.

Never encourage harmful behavior.

Make everything playful and obviously hypothetical.

Return ONLY JSON.

The JSON must contain:

{{
    "title": "funny short title",

    "delul_score": 0,

    "analysis": "personalized analysis",

    "spiral": [
        "thought 1",
        "thought 2",
        "thought 3",
        "thought 4",
        "thought 5"
    ],

    "verdict": "funny final verdict"
}}

delul_score must be between 0 and 100.
"""


    user_prompt = f"""
The user's decision is:

"{decision}"

Overthink this according to their personality.

Make it increasingly ridiculous according to
level {level}.
"""


    try:

        response = client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],

            temperature=1,

            max_tokens=1000,

            response_format={
                "type": "json_object"
            }
        )

        text = response.choices[0].message.content

        result = json.loads(text)

        return result

    except Exception as e:

        print("\n========== GROQ ERROR ==========")
        print(e)
        print("================================\n")

        return {

            "title":
                "THE AI STARTED OVERTHINKING ITSELF 💀",

            "delul_score": 99,

            "analysis":
                "Groq encountered a plot twist.",

            "spiral": [
                "Was the API key correct?",
                "Was the model available?",
                "Did the request reach Groq?",
                "Why is the AI thinking about its own thoughts?",
                "Maybe this IS the DELUL experience."
            ],

            "verdict":
                "EVEN GROQ IS DELUL 💀"
        }


# =====================================================
# ANALYZE
# =====================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    decision = request.form.get(
        "decision",
        ""
    ).strip()

    if not decision:

        decision = "Why did I submit nothing?"

    personality = session.get(
        "personality",
        "normal"
    )

    level = 1

    result = generate_delul(
        decision,
        personality,
        level
    )

    session["decision"] = decision
    session["level"] = level

    profile = DELUL_PERSONALITIES[personality]

    return render_template(
        "result.html",
        personality=profile["name"],
        description=profile["description"],
        decision=decision,
        result=result,
        personality_only=False,
        level=level
    )


# =====================================================
# MAKE IT WORSE
# =====================================================

@app.route("/worse", methods=["POST"])
def make_it_worse():

    decision = session.get(
        "decision",
        "Something happened."
    )

    personality = session.get(
        "personality",
        "normal"
    )

    old_level = session.get(
        "level",
        1
    )

    level = min(
        old_level + 1,
        5
    )

    session["level"] = level

    result = generate_delul(
        decision,
        personality,
        level
    )

    profile = DELUL_PERSONALITIES[personality]

    return render_template(
        "result.html",
        personality=profile["name"],
        description=profile["description"],
        decision=decision,
        result=result,
        personality_only=False,
        level=level
    )


# =====================================================
# START SERVER
# =====================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )