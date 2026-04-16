# 🎯 AI Interview Coach

An advanced AI-powered interview preparation platform that simulates real-world technical interviews, evaluates responses, and provides intelligent feedback to help candidates improve performance.

---

## 🚀 Overview

AI Interview Coach is a full-stack intelligent application designed to replicate real interview environments using AI. It dynamically generates role-based questions, evaluates answers with detailed feedback, and provides performance analytics.

The platform integrates **Groq LLaMA models** for question generation and evaluation, along with **voice-based interaction** and **resume-based personalization**.

---

## ✨ Key Features

### 🎤 Smart Interview Simulation

* AI-generated interview questions based on:

  * Role (Software Engineer, Data Scientist, etc.)
  * Domain (DSA, System Design, AI, etc.)
  * Difficulty & Experience Level
* Company-specific interview modes (FAANG, etc.)

---

### 🧠 AI Answer Evaluation

* Score (0–10) with detailed verdict
* Strengths & weaknesses breakdown
* Model answers for comparison
* Personalized improvement suggestions

---

### 🎙️ Voice + Text Input

* Speak your answers using microphone
* Automatic speech-to-text transcription (Groq Whisper)
* Editable transcripts before submission

---

### 📄 Resume-Based Personalization

* Upload resume (PDF/DOCX/TXT)
* Extracts skills and experience
* Tailors questions based on candidate profile

---

### 📊 Performance Analytics

* Session-wise performance tracking
* Score trends over time
* Domain-wise performance insights
* Best score and average score metrics

---

### 🔐 Authentication System

* Secure login/signup using hashed passwords (`bcrypt`)
* User-specific sessions and history

---



## 🛠️ Tech Stack

| Layer         | Technology              |
| ------------- | ----------------------- |
| Frontend      | Streamlit               |
| Backend       | Python                  |
| AI Engine     | Groq (LLaMA 3, Whisper) |
| Database      | SQLite                  |
| Auth          | bcrypt                  |
| Visualization | Plotly                  |
| Env Config    | python-dotenv           |

---

## 📂 Project Structure

```bash
AI-INTERVIEW-PREPARATION-PLATFORM/
│
├── app.py                  # Main Streamlit application :contentReference[oaicite:5]{index=5}
├── interview_bot.py        # AI logic (question generation, evaluation)
├── auth.py                 # Authentication system
├── database.py             # Database operations (SQLite)
├── resume_parser.py        # Resume parsing logic
├── requirements.txt        # Dependencies
├── .gitignore              # Ignored files
└── .env                    # API keys (not pushed)
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/SATISHDASA/AI-INTERVIEW-PREPARATION-PLATFORM.git
cd AI-INTERVIEW-PREPARATION-PLATFORM
```

---

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Add Groq API Key

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_api_key_here
```

---

### 4️⃣ Run the Application

```bash
streamlit run app.py
```

---

## 🧪 How It Works

1. User logs in or signs up
2. Configures interview settings (role, domain, difficulty)
3. AI generates interview questions
4. User answers via text or voice
5. AI evaluates response and provides feedback
6. Follow-up questions improve weak areas
7. Final analytics and performance summary displayed

---

## 📌 Highlights

* 🔥 Real-time AI evaluation using LLMs
* 🎙️ Voice-enabled interview interaction
* 📊 Advanced analytics dashboard
* 🎯 Personalized interview experience
* 💡 Industry-level interview simulation

---

## 🚀 Future Enhancements

* Live mock interview (real-time conversation AI)
* Code editor with execution support
* Multi-language interview support
* Cloud deployment (AWS / Streamlit Cloud)
* Interview report PDF generation

---

## 👨‍💻 Author

**D. Satish**
Enrollment No: 23STUCHH010519
ICFAI Foundation for Higher Education, Hyderabad

---

## 📜 License

This project is developed for academic and educational purposes.

---

## ⭐ Show Your Support

If you found this project useful, consider giving it a ⭐ on GitHub!
