import streamlit as st
from openai import OpenAI
import base64
import re

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="MedMate MD",
    page_icon="🩺",
    layout="wide"
)

client = OpenAI()

ROYAL_INDIGO = "#3949AB"
LIGHT_GREY = "#F7F7F7"
TEXT_GREY = "#4F4F4F"

# -----------------------------------------------------
# CUSTOM CSS (UI3 UPGRADE)
# -----------------------------------------------------
st.markdown(
    f"""
    <style>
        body {{
            background-color: white;
        }}

        .main-header {{
            text-align: center;
            margin-bottom: 5px;
        }}

        .app-title {{
            font-size: 40px;
            font-weight: 800;
            color: {ROYAL_INDIGO};
        }}

        .tagline {{
            font-size: 18px;
            margin-top: -10px;
            color: {TEXT_GREY};
        }}

        .chat-container {{
            background: {LIGHT_GREY};
            padding: 20px;
            border-radius: 12px;
            height: 600px;
            overflow-y: auto;
            border: 1px solid #E0E0E0;
        }}

        .ai-bubble {{
            background: #E8EAF6;
            padding: 14px;
            border-radius: 10px;
            margin-bottom: 12px;
            color: black;
            border-left: 5px solid {ROYAL_INDIGO};
        }}

        .user-bubble {{
            background: white;
            padding: 14px;
            border-radius: 10px;
            margin-bottom: 12px;
            border: 1px solid #D3D3D3;
            color: black;
        }}

        .diagram-block {{
            background: white;
            border: 1px solid #D3D3D3;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            margin-bottom: 15px;
        }}

        .footer {{
            text-align: center;
            margin-top: 25px;
            color: {TEXT_GREY};
            font-size: 13px;
            padding-bottom: 20px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------
# SYSTEM PROMPT (ATTENDING TEACHER)
# -----------------------------------------------------
SYSTEM_PROMPT = """
You are an attending physician teaching a 3rd-year medical student.
Your tone is warm, conversational, and supportive — but always clinically correct.

DURING THE CASE:
1. Ask ONE focused question at a time.
2. Build reasoning step-by-step.
3. Insert visual cues when appropriate, such as:
   - "Here is a simple diagram to clarify..."
   - "Let me illustrate this..."
   - "Visually, this looks like..."
4. NEVER output actual image data in text — the app will handle that.
5. Your visuals should be simple, clean medical diagrams.

WHEN STUDENT IS READY FOR SUMMARY:
Provide:
- Final Impression
- Most Likely Diagnosis
- 3–5 Item Differential
- Clinical Reasoning Breakdown
- Recommended Diagnostic Next Steps
- Educational Initial Management
- Red Flags
- 1 Sentence Visual Description
- 3 Teaching Pearls

DO NOT give real medical advice. Educational only.
"""

# -----------------------------------------------------
# INITIALIZE SESSION STATE
# -----------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False


# -----------------------------------------------------
# IMAGE GENERATOR (GPT-4o)
# -----------------------------------------------------
def generate_medical_diagram(description: str):
    """Generate a soft medical-style diagram from GPT-4o."""
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=f"Create a clean, labeled medical diagram in soft colors. {description}. Style: simple, clinical, minimal shading.",
            size="1024x1024"
        )

        img_base64 = response.data[0].b64_json
        return base64.b64decode(img_base64)

    except Exception as e:
        print("Image generation error:", e)
        return None


# -----------------------------------------------------
# TEXT RESPONSE HANDLER (GPT-4o)
# -----------------------------------------------------
def generate_ai_response(user_input):
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "system",
                "content": "You are an experienced medical attending teaching a student through clinical cases. Be conversational, clear, and always end with a concrete recommendation."
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    return response.output_text


# -----------------------------------------------------
# VISUAL TRIGGER DETECTION
# -----------------------------------------------------
def detect_visual_trigger(text: str):
    triggers = [
        "diagram",
        "visual",
        "illustrate",
        "map",
        "let me show",
        "here is a simple"
    ]
    return any(t in text.lower() for t in triggers)


# -----------------------------------------------------
# UI HEADER
# -----------------------------------------------------
st.markdown(
    f"""
    <div class="main-header">
        <div class="app-title">🩺 MedMate MD</div>
        <div class="tagline">Your AI Attending for Smarter Clinical Learning.</div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------
# CHAT DISPLAY CONTAINER
# -----------------------------------------------------
chat_col, input_col = st.columns([3, 2])

with chat_col:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

            if "diagram_image" in msg:
                st.markdown('<div class="diagram-block">', unsafe_allow_html=True)
                st.image(msg["diagram_image"], use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------
# USER INPUT AREA
# -----------------------------------------------------
with input_col:
    st.subheader("Enter Your Case")
    user_input = st.text_area("",
        placeholder="Present your case or answer the attending’s question...",
        height=180
    )

    if st.button("Submit"):
        if user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input})

            ai_text = generate_ai_response(user_input)

            ai_message = {"role": "assistant", "content": ai_text}

            if detect_visual_trigger(ai_text):
                diagram = generate_medical_diagram(ai_text)
                if diagram:
                    ai_message["diagram_image"] = diagram

            st.session_state.messages.append(ai_message)

            

# -----------------------------------------------------
# FOOTER
# -----------------------------------------------------
st.markdown(
    f"""
    <div class="footer">
        MedMate MD © 2026 — AI Clinical Teaching Assistant.
    </div>
    """,
    unsafe_allow_html=True
)
