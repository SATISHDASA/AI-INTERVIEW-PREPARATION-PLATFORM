import os
import json
import re
import time
import logging
from groq import Groq, APIConnectionError, APIStatusError, RateLimitError
from dotenv import load_dotenv

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Models ───────────────────────────────────────────────────────────────────
PRIMARY_MODEL  = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"
WHISPER_MODEL  = "whisper-large-v3-turbo"

# ─── Data ─────────────────────────────────────────────────────────────────────
ROLES = {
    "Software Engineering": [
        "Software Engineer","Backend Engineer","Frontend Engineer",
        "Full Stack Developer","DevOps Engineer","Site Reliability Engineer",
        "Mobile Developer (Android)","Mobile Developer (iOS)","Embedded Systems Engineer",
    ],
    "Data & AI": [
        "Data Scientist","Machine Learning Engineer","AI/ML Engineer",
        "Data Engineer","Data Analyst","NLP Engineer",
        "Computer Vision Engineer","MLOps Engineer","Research Scientist",
    ],
    "Cloud & Infrastructure": [
        "Cloud Architect","AWS Solutions Architect","GCP Engineer",
        "Azure Engineer","Kubernetes Engineer","Infrastructure Engineer",
        "Security Engineer","Network Engineer",
    ],
    "Product & Design": [
        "Product Manager","Technical Product Manager","UI/UX Designer",
        "Business Analyst","Scrum Master","Project Manager",
    ],
    "Management": [
        "Engineering Manager","Tech Lead","CTO","VP Engineering","Director of Engineering",
    ],
    "Other Tech": [
        "QA Engineer","Test Automation Engineer","Blockchain Developer",
        "Game Developer","AR/VR Developer","Cybersecurity Analyst",
    ],
}

DOMAINS = {
    "Core CS": [
        "Data Structures & Algorithms","System Design","Operating Systems",
        "Computer Networks","Database Management","Compiler Design",
    ],
    "Programming Languages": [
        "Python","Java","JavaScript / TypeScript","C / C++","Go (Golang)","Rust","Kotlin","Swift",
    ],
    "Web Development": [
        "React.js","Node.js / Express","Django / Flask","FastAPI",
        "Next.js","GraphQL","REST API Design","Microservices",
    ],
    "Data Science & AI": [
        "Machine Learning","Deep Learning","Natural Language Processing",
        "Computer Vision","Statistics & Probability","Big Data / Spark","MLOps & Model Deployment",
    ],
    "Cloud & DevOps": [
        "AWS","Google Cloud Platform","Microsoft Azure","Docker & Kubernetes",
        "CI/CD & DevOps","Terraform & IaC","Linux & Shell Scripting",
    ],
    "Databases": [
        "SQL & Relational Databases","MongoDB / NoSQL","Redis & Caching",
        "Elasticsearch","PostgreSQL Advanced","Database Optimization",
    ],
    "Behavioral / HR": [
        "Leadership & Teamwork","Conflict Resolution","Communication Skills",
        "Problem Solving","Time Management","Situational Judgment",
    ],
}

TOP_COMPANIES = {
    "FAANG+": ["Amazon","Google","Meta (Facebook)","Apple","Netflix","Microsoft"],
    "Unicorns": ["Uber","Airbnb","Stripe","Spotify","LinkedIn","Twitter / X",
                 "Salesforce","Adobe","Oracle","IBM"],
    "Indian Tech": ["TCS","Infosys","Wipro","HCL","Cognizant","Accenture",
                    "Flipkart","Zomato","Swiggy","Paytm","BYJU'S","Ola"],
    "Finance Tech": ["Goldman Sachs","JPMorgan Chase","Morgan Stanley","Citi",
                     "Visa","Mastercard","PayPal"],
    "Other": ["General (No Company Focus)"],
}

DIFFICULTY_LEVELS = ["Easy","Medium","Hard","Expert"]

EXPERIENCE_LEVELS = [
    "Fresher (0 years)",
    "Junior (1-2 years)",
    "Mid-level (3-5 years)",
    "Senior (6-9 years)",
    "Lead / Principal (10+ years)",
]

# Per-company interview guidance
COMPANY_GUIDANCE = {
    "Amazon": (
        "Focus heavily on Amazon Leadership Principles (Customer Obsession, Ownership, "
        "Invent and Simplify, Bias for Action, Deliver Results, Dive Deep, etc.). "
        "Ask STAR-method behavioral questions that map to specific LPs. "
        "Also include coding problems on arrays, trees, graphs, and dynamic programming "
        "typical of Amazon SDE OA rounds."
    ),
    "Google": (
        "Focus on algorithmic problem-solving, Big-O complexity analysis, clean scalable code, "
        "and large-scale system design (billions of users). Include graph, tree, DP coding problems. "
        "Behavioral questions focus on Googleyness and impact."
    ),
    "Meta (Facebook)": (
        "Focus on product sense, large-scale system design (News Feed, WhatsApp, Instagram), "
        "and coding problems on arrays, strings, graphs, DP. "
        "Behavioral questions emphasize impact, collaboration, and moving fast."
    ),
    "Microsoft": (
        "Mix of OOP design, practical coding (medium LeetCode), system design, and behavioral "
        "questions around growth mindset, collaboration, and Microsoft values."
    ),
    "Apple": (
        "Emphasis on attention to detail, low-level systems, performance optimization, "
        "and design sensibility. Swift/Objective-C for iOS roles. "
        "Behavioral questions focus on craftsmanship and cross-functional collaboration."
    ),
    "Netflix": (
        "Senior-level ownership mindset, distributed streaming systems, fault tolerance, "
        "and the Netflix culture of freedom & responsibility. Open-ended scenario questions."
    ),
    "Goldman Sachs": (
        "Strong CS fundamentals (DSA + system design), financial domain awareness, "
        "behavioral questions on integrity, risk management, and client focus."
    ),
    "JPMorgan Chase": (
        "Core CS fundamentals, secure engineering, behavioral questions on integrity "
        "and client service, financial products knowledge for relevant roles."
    ),
    "TCS": (
        "CS fundamentals (DBMS, OS, networking), simple coding in C/Java/Python, "
        "verbal/aptitude, HR questions on teamwork, relocation, and career goals. Fresher-focused."
    ),
    "Infosys": (
        "Aptitude, verbal, basic OOP, DBMS SQL queries, and HR questions on adaptability. "
        "Beginner-friendly difficulty."
    ),
    "Wipro": (
        "NLTH pattern: aptitude, essay writing, basic coding, technical fundamentals, "
        "and HR soft-skills questions. Entry-level focused."
    ),
    "Flipkart": (
        "Product thinking, medium-hard DSA (trees, graphs, DP), LLD, and system design "
        "for e-commerce at scale (search, catalog, recommendations, inventory)."
    ),
    "Zomato": (
        "Medium DSA, food-delivery system design (order routing, real-time tracking), "
        "product sense, ownership, and user empathy behavioral questions."
    ),
    "Uber": (
        "Real-time systems, geospatial algorithms, high-concurrency backend design, "
        "coding problems with optimal complexity, ride-matching system design."
    ),
    "Airbnb": (
        "Product thinking, trust-and-safety system design, frontend (React) for UI roles, "
        "data pipelines for data roles, behavioral questions on belonging and empathy."
    ),
    "Stripe": (
        "Distributed payments systems, API design for reliability, correctness-focused coding, "
        "and clear technical communication."
    ),
    "Spotify": (
        "Recommendation systems, real-time audio streaming architecture, backend scalability, "
        "behavioral questions around data-driven decisions and experimentation."
    ),
}

# ─── Groq Client ──────────────────────────────────────────────────────────────

def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add  GROQ_API_KEY=gsk_...  to your .env file."
        )
    return Groq(api_key=api_key)


def _clean_json(raw: str) -> str:
    raw = raw.strip().lstrip("\ufeff")
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    m = re.search(r"\{[\s\S]*\}", raw)
    return m.group(0).strip() if m else raw.strip()


def call_groq(messages: list, temperature: float = 0.7,
              max_tokens: int = 2048, retries: int = 3) -> str:
    client = get_client()
    model  = PRIMARY_MODEL

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Groq | model={model} | attempt={attempt}")
            resp    = client.chat.completions.create(
                model=model, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content
            if content and content.strip():
                return content.strip()
            raise ValueError("Empty response from Groq.")

        except RateLimitError:
            wait = 2 ** attempt
            logger.warning(f"Rate limited — waiting {wait}s")
            time.sleep(wait)

        except APIConnectionError as e:
            logger.error(f"Connection error attempt {attempt}: {e}")
            if attempt == retries:
                raise ConnectionError("Cannot reach Groq API. Check your internet.") from e
            time.sleep(2)

        except APIStatusError as e:
            if e.status_code == 401:
                raise PermissionError("Invalid GROQ_API_KEY. Check https://console.groq.com/keys") from e
            if e.status_code in (503, 529) and model == PRIMARY_MODEL:
                logger.warning("Primary model overloaded — switching to fallback.")
                model = FALLBACK_MODEL
                continue
            if attempt == retries:
                raise RuntimeError(f"Groq API error {e.status_code}: {e.message}") from e
            time.sleep(2)

        except Exception as e:
            logger.error(f"Unexpected error attempt {attempt}: {e}")
            if attempt == retries:
                raise
            time.sleep(1)

    raise RuntimeError("All Groq API retry attempts exhausted.")


def _parse_json(raw: str, fallback: dict) -> dict:
    try:
        data = json.loads(_clean_json(raw))
        return data if isinstance(data, dict) else fallback
    except Exception as e:
        logger.error(f"JSON parse failed: {e} | raw[:300]={raw[:300]}")
        return fallback


def validate_api_key(api_key: str):
    try:
        client = Groq(api_key=api_key.strip())
        client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
        )
        return True, "API key is valid ✅"
    except Exception as e:
        return False, str(e)


# ─── Voice Transcription ──────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes using Groq Whisper.
    Returns the transcript string, or raises on error.
    """
    import io as _io
    client     = get_client()
    audio_file = _io.BytesIO(audio_bytes)
    audio_file.name = "recording.wav"
    try:
        response = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file,
            response_format="text",
            language="en",
        )
        return str(response).strip()
    except APIStatusError as e:
        if e.status_code == 401:
            raise PermissionError("Invalid API key for transcription.") from e
        raise RuntimeError(f"Transcription API error {e.status_code}: {e.message}") from e
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e


# ─── Question Generation ──────────────────────────────────────────────────────

def generate_question(role: str, domain: str, difficulty: str, experience: str,
                       company: str = "General", question_num: int = 1,
                       previous_questions: list = None,
                       resume_context: str = "") -> dict:

    prev_block = ""
    if previous_questions:
        prev_block = "Previously asked — do NOT repeat:\n" + \
                     "\n".join(f"  - {q}" for q in previous_questions[-6:])

    company_block = ""
    if company and company not in ("General", "General (No Company Focus)"):
        guidance = COMPANY_GUIDANCE.get(company, f"Ask realistic questions for {company}.")
        company_block = f"\nCompany: {company}\n{guidance}\n"

    resume_block = ""
    if resume_context:
        resume_block = f"\nCandidate background (personalise question):\n{resume_context[:600]}\n"

    system_msg = (
        "You are a senior technical interviewer with 15+ years at top tech companies. "
        "You generate precise, realistic, non-trivial interview questions. "
        "Respond with VALID JSON ONLY — no prose, no markdown fences."
    )

    user_msg = f"""Generate ONE interview question for this context:

Role:             {role}
Domain:           {domain}
Difficulty:       {difficulty}
Experience Level: {experience}
Question #:       {question_num}
{company_block}{resume_block}{prev_block}

Return JSON with EXACTLY these keys:
{{
  "question": "<Full, specific, realistic question — no markdown>",
  "type": "<technical | behavioral | system_design | coding | situational>",
  "hint": "<One subtle hint sentence for a stuck candidate>",
  "expected_topics": ["<topic1>", "<topic2>", "<topic3>"]
}}

Rules:
- coding: include problem statement, constraints, example I/O
- system_design: specify scale (e.g. 10M users/day)
- behavioral: reference a realistic workplace scenario
- difficulty MUST match {difficulty} for a {experience} candidate
- Return ONLY the JSON object. Nothing before or after it."""

    fallback = {
        "question": f"Describe the most technically challenging problem you solved in {domain} and your step-by-step approach.",
        "type": "behavioral",
        "hint": "Use the STAR method: Situation → Task → Action → Result.",
        "expected_topics": [domain, "problem-solving", "technical depth"],
    }

    try:
        raw  = call_groq(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.75, max_tokens=512,
        )
        data = _parse_json(raw, fallback)
        if not isinstance(data.get("question"), str) or len(data["question"].strip()) < 15:
            return fallback
        if not isinstance(data.get("expected_topics"), list):
            data["expected_topics"] = fallback["expected_topics"]
        data.setdefault("type",  "technical")
        data.setdefault("hint",  "Think about edge cases and complexity.")
        return data
    except (EnvironmentError, PermissionError, ConnectionError):
        raise
    except Exception as e:
        logger.error(f"generate_question error: {e}")
        return fallback


# ─── Answer Evaluation ────────────────────────────────────────────────────────

def evaluate_answer(question: str, user_answer: str, role: str, domain: str,
                     difficulty: str, question_type: str,
                     expected_topics: list = None) -> dict:

    # Empty answer fast path
    if not user_answer or len(user_answer.strip()) < 5:
        return {
            "score": 0, "percentage": 0, "verdict": "No Answer",
            "strengths": [],
            "weaknesses": ["No answer was provided."],
            "feedback": "You did not attempt this question. Always try — partial answers earn partial credit.",
            "model_answer": _placeholder_model_answer(domain, question_type),
            "correct_answer": "A structured, complete response addressing all parts of the question.",
            "improvements": [
                "Always attempt every question — even partial answers earn partial credit.",
                "If unsure, explain your thought process and what you do know.",
                "Practice answering under time constraints to build confidence.",
            ],
            "key_concepts_covered": [],
            "key_concepts_missed": expected_topics or [],
        }

    topics_line = f"Key topics a strong answer must cover: {', '.join(expected_topics)}." if expected_topics else ""

    system_msg = (
        "You are a strict but fair senior technical interviewer evaluating a candidate's answer. "
        "You give specific, actionable feedback and always provide a technically correct model answer. "
        "Respond with VALID JSON ONLY — no markdown, no prose outside the JSON object."
    )

    user_msg = f"""Evaluate the candidate's answer below.

=== CONTEXT ===
Role:           {role}
Domain:         {domain}
Difficulty:     {difficulty}
Question Type:  {question_type}
{topics_line}

=== QUESTION ===
{question}

=== CANDIDATE'S ANSWER ===
{user_answer}

=== REQUIRED JSON OUTPUT ===
{{
  "score": <integer 0-10>,
  "percentage": <integer 0-100, always score * 10>,
  "verdict": "<Excellent | Good | Average | Below Average | Poor>",
  "strengths": ["<exact concept/skill the candidate demonstrated well>", ...],
  "weaknesses": ["<exact concept/topic the candidate missed or got wrong>", ...],
  "feedback": "<2-3 sentence honest assessment: what was good and what was missing>",
  "model_answer": "<Ideal 4-6 sentence answer a top candidate would give — technically precise, complete, with examples>",
  "correct_answer": "<The single most important key insight they should have mentioned — 1-2 sentences>",
  "improvements": [
    "<Specific actionable tip 1, e.g. 'Always mention O(n log n) time complexity when discussing merge sort'>",
    "<Specific actionable tip 2>",
    "<Specific actionable tip 3>"
  ],
  "key_concepts_covered": ["<concept candidate addressed correctly>", ...],
  "key_concepts_missed":  ["<concept candidate missed or got wrong>", ...]
}}

=== SCORING RUBRIC ===
10    Perfect — all concepts, correct terminology, concrete examples, nothing missing
8-9   Excellent — thorough, minor omissions only
6-7   Good — solid understanding, some gaps or imprecise language
4-5   Average — basics covered, important details missing or vague
2-3   Below Average — significant gaps, partially incorrect
1     Poor — mostly wrong or irrelevant
0     No answer or completely off-topic

STRICT RULES:
- Name EXACT missing concepts — never say just "more detail needed"
- model_answer must be detailed enough that it would score 10/10
- correct_answer must be a concise KEY INSIGHT, not a repeat of model_answer
- strengths and weaknesses must have at least 1 item each, always
- Return ONLY the JSON object. No text before or after."""

    fallback = {
        "score": 5, "percentage": 50, "verdict": "Average",
        "strengths":  ["Attempted the question"],
        "weaknesses": ["Could not fully evaluate — API error occurred"],
        "feedback": "Evaluation failed due to an API error. Please retry.",
        "model_answer": _placeholder_model_answer(domain, question_type),
        "correct_answer": "Please retry for a complete model answer.",
        "improvements": [
            "Ensure GROQ_API_KEY is set correctly in your .env file.",
            "Restart the app after updating .env.",
        ],
        "key_concepts_covered": [],
        "key_concepts_missed":  expected_topics or [],
    }

    try:
        raw  = call_groq(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.15,   # very low → consistent, precise scoring
            max_tokens=1800,
        )
        data = _parse_json(raw, fallback)

        # Sanitise score
        try:
            data["score"] = max(0, min(10, int(data.get("score", 5))))
        except (TypeError, ValueError):
            data["score"] = 5

        # Percentage always derived
        data["percentage"] = data["score"] * 10

        # Verdict
        valid_verdicts = {"Excellent","Good","Average","Below Average","Poor"}
        if data.get("verdict") not in valid_verdicts:
            data["verdict"] = _score_to_verdict(data["score"])

        # List fields
        for key in ("strengths","weaknesses","improvements",
                    "key_concepts_covered","key_concepts_missed"):
            if not isinstance(data.get(key), list):
                data[key] = []

        if not data["strengths"]:
            data["strengths"] = ["Attempted the question"]
        if not data["weaknesses"]:
            data["weaknesses"] = ["No major weaknesses identified"]

        # String fields
        for key in ("feedback","model_answer","correct_answer"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                data[key] = fallback[key]

        return data

    except (EnvironmentError, PermissionError, ConnectionError, RuntimeError):
        raise
    except Exception as e:
        error_detail = f"{type(e).__name__}: {e}"
        logger.error(f"evaluate_answer unexpected error: {error_detail}")
        fallback["feedback"] = f"Evaluation error: {error_detail}. Run python test_groq.py to diagnose."
        fallback["weaknesses"] = [f"Error: {error_detail}"]
        return fallback


# ─── Session Summary ──────────────────────────────────────────────────────────

def generate_session_summary(answers: list, role: str, domain: str, company: str) -> str:
    if not answers:
        return "No answers recorded in this session."

    scores = [a.get("score", 0) for a in answers if isinstance(a.get("score"), (int, float))]
    avg    = sum(scores) / len(scores) if scores else 0

    missed    = []
    strengths = []
    for a in answers:
        if isinstance(a.get("key_concepts_missed"), list):
            missed.extend(a["key_concepts_missed"])
        if isinstance(a.get("strengths"), list):
            strengths.extend(a["strengths"])

    breakdown = ", ".join(f"Q{i+1}:{s}" for i, s in enumerate(scores))

    prompt = (
        f"Write a professional interview performance summary.\n\n"
        f"Role: {role} | Domain: {domain} | Company: {company}\n"
        f"Questions: {len(answers)} | Average: {avg:.1f}/10\n"
        f"Score breakdown: {breakdown}\n"
        f"Key strengths: {', '.join(strengths[:5]) or 'N/A'}\n"
        f"Concepts missed: {', '.join(missed[:6]) or 'None'}\n\n"
        f"Write 4-5 sentences covering:\n"
        f"1. Overall performance verdict\n"
        f"2. Two key strengths demonstrated\n"
        f"3. Two main areas needing improvement\n"
        f"4. Final recommendation: 'Ready to Interview', 'Nearly Ready', or 'Needs More Preparation'\n\n"
        f"Be specific, honest, and constructive. Plain text only — no markdown."
    )
    try:
        return call_groq(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4, max_tokens=350,
        )
    except Exception as e:
        logger.error(f"generate_session_summary error: {e}")
        return (
            f"Session complete: {len(answers)} questions answered, "
            f"average score {avg:.1f}/10. "
            f"Review individual feedback for detailed improvements."
        )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _score_to_verdict(score: int) -> str:
    if score >= 9: return "Excellent"
    if score >= 7: return "Good"
    if score >= 5: return "Average"
    if score >= 3: return "Below Average"
    return "Poor"

def _placeholder_model_answer(domain: str, question_type: str) -> str:
    if question_type == "behavioral":
        return (
            f"A strong answer uses the STAR method with a specific example from {domain}. "
            "It includes concrete metrics or outcomes, demonstrates clear ownership, "
            "explains what was learned, and shows how the experience applies to future situations."
        )
    if question_type == "system_design":
        return (
            "A strong system design answer: (1) clarifies functional and non-functional requirements, "
            "(2) estimates scale and capacity, (3) proposes a high-level architecture with components, "
            "(4) defines data model and API design, (5) addresses scalability via caching, "
            "load balancing, and sharding, and (6) discusses trade-offs and failure handling."
        )
    if question_type == "coding":
        return (
            "A strong coding answer: (1) clarifies constraints and edge cases, "
            "(2) explains brute-force approach and its O(n²) complexity, "
            "(3) derives an optimized O(n log n) or O(n) solution, "
            "(4) traces through an example to verify correctness, "
            "(5) discusses space complexity and any trade-offs."
        )
    return (
        f"A strong answer demonstrates deep knowledge of {domain}, uses precise technical "
        "terminology, provides concrete code examples or diagrams where appropriate, "
        "clearly explains the reasoning behind design choices, and acknowledges trade-offs."
    )
