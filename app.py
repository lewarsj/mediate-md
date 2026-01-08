import os
import json
import time
import requests
import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MedMate MD",
    page_icon="🩺",
    layout="centered",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}


# ============================================================
# GLOBAL UI STYLING
# ============================================================

st.markdown("""
<style>

html, body, [class*="css"]  {
    margin: 0;
    padding: 0;
}

#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

.stApp {
    background: #f7f7f7;
    font-family: 'Helvetica Neue', sans-serif;
    padding-bottom: 120px; /* space above sticky footer */
}

/* HEADER AREA */
.med-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin-top: 10px;
}

.med-logo {
    width: 42px;
    height: 42px;
}

.med-title-text {
    font-size: 2.4rem;
    font-weight: 800;
    color: #303030;
    margin: 0;
}

.med-subtitle {
    text-align: center;
    color: #666;
    font-size: 1rem;
    margin-top: -6px;
}

/* MAIN CARD */
.med-card {
    background: white;
    border-radius: 16px;
    padding: 1.7rem;
    border: 1px solid #e1e1e1;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    margin-top: 20px;
}

/* BUTTONS */
.stButton button {
    background-color: #b00000 !important;
    color: white !important;
    padding: 0.55rem 1.1rem;
    border-radius: 8px;
    font-weight: 600;
    border: none;
    font-size: 0.95rem;
}
.stButton button:hover {
    background-color: #8a0000 !important;
}

/* STICKY FOOTER */
.med-footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background: white;
    border-top: 1px solid #ddd;
    padding: 12px 0;
    text-align: center;
    color: #777;
    font-size: 0.9rem;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOGO + HEADER
# ============================================================

# --------- LOGO + TITLE (Emoji Logo Version) ---------
st.markdown(
    """
<div style='text-align: center; margin-top: 5px;'>
    <div style="
        font-size: 3rem;
        line-height: 1;
        margin-bottom: -5px;
    ">
        🩺
    </div>
    <h1 style="
        font-size: 2.4rem;
        font-weight: 800;
        color: #303030;
        margin: 0;
        padding: 0;
    ">
        MedMate MD
    </h1>
    <div style="
        color: #666;
        font-size: 1rem;
        margin-top: -4px;
    ">
        Your conversational clinical tutor — educational use only.
    </div>
</div>
""",
    unsafe_allow_html=True,
)



# ============================================================
# SYSTEM PROMPTS
# ============================================================

PROMPTS = {
    "Case Tutor": """
You are an attending physician teaching a 3rd-year medical student.

Speak conversationally and professionally.
Ask ONE question at a time.

Workflow:
1. React to the case naturally.
2. Ask a single focused follow-up question.
3. Build reasoning step-by-step.
4. After 6 total exchanges OR if the student says "conclude",
   provide a clean teaching summary including:

- Final Impression
- Most Likely Diagnosis (educational only)
- Clinical Reasoning
- Other Considerations (2–3)
- Recommended Next Step (educational only)
- Teaching Pearls (2–3)

Tone should be warm, calm, attending-like, and human.
"""
}


# ============================================================
# OPENAI CALL
# ============================================================

def call_openai(messages):
    body = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.25
    }

    r = requests.post(URL, headers=HEADERS, json=body)

    try:
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "⚠️ Unexpected API response."


# ============================================================
# SESSION STATE
# ============================================================

if "case_started" not in st.session_state:
    st.session_state.case_started = False

if "case_history" not in st.session_state:
    st.session_state.case_history = []

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0


# ============================================================
# MAIN APP CARD
# ============================================================

st.markdown("<div class='med-card'>", unsafe_allow_html=True)

mode = st.radio("Choose a mode:", ["Case Tutor"])


# ============================================================
# CASE TUTOR MODE
# ============================================================

if mode == "Case Tutor":

    vignette = st.text_area("Paste your case vignette here:", height=140)

    if st.button("Start / Reset Case"):
        if vignette.strip():

            st.session_state.case_started = True
            st.session_state.turn_count = 0

            st.session_state.case_history = [
                {"role": "system", "content": PROMPTS["Case Tutor"]},
                {
                    "role": "user",
                    "content": f"Here is the clinical case. Begin with your natural reaction and your first question: {vignette}"
                }
            ]

            # First AI response
            ai_reply = call_openai(st.session_state.case_history)
            st.session_state.case_history.append({"role": "assistant", "content": ai_reply})


    st.markdown("---")

    if st.session_state.case_started:

        # DISPLAY CHAT
        st.markdown("### Conversation")

        for msg in st.session_state.case_history:
            if msg["role"] == "assistant":
                st.markdown(f"**AI (Attending):** {msg['content']}")
            elif msg["role"] == "user" and "Here is the clinical case" not in msg["content"]:
                st.markdown(f"**You:** {msg['content']}")


        # ------------------------------------------------------------
        # INPUT BOX (single line, auto-clears using form)
        # ------------------------------------------------------------
        with st.form("response_form", clear_on_submit=True):
            user_answer = st.text_input("Your response:")
            submitted = st.form_submit_button("Send")

        if submitted:

            answer = user_answer.strip()

            if answer:
                st.session_state.case_history.append({
                    "role": "user",
                    "content": answer
                })

                st.session_state.turn_count += 1

                # Trigger final summary
                if st.session_state.turn_count >= 6 or "conclude" in answer.lower():
                    st.session_state.case_history.append({
                        "role": "user",
                        "content": "Please conclude with the final clinical impression and teaching summary."
                    })

                # AI Reply
                ai_reply = call_openai(st.session_state.case_history)
                st.session_state.case_history.append({"role": "assistant", "content": ai_reply})

            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# STICKY FOOTER
# ============================================================

st.markdown(
    """
<div class="med-footer">
    MedMate MD © 2026 — Built for medical education. Not for clinical decision-making.
</div>
""",
    unsafe_allow_html=True,
)
