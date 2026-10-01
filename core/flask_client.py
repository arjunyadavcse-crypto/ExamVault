import requests
import logging

logger = logging.getLogger(__name__)

FLASK_SERVICE_URL = "http://127.0.0.1:5001"

def generate_ai_questions(subject_name, count=3, difficulty="Medium"):
    """
    Call Flask Microservice to generate questions.
    """
    try:
        response = requests.post(
            f"{FLASK_SERVICE_URL}/api/generate-questions",
            json={"subject": subject_name, "count": count, "difficulty": difficulty},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("questions", [])
    except Exception as e:
        logger.warning(f"Flask service unreachable ({e}), using fallback question generator.")
    
    # Fallback smart generator
    return [
        {
            "question_text": f"What is a fundamental concept in {subject_name} regarding system architecture and efficiency?",
            "option_a": "Modular decomposition and encapsulation",
            "option_b": "Unbounded recursive loops",
            "option_c": "Static file allocation table fragmentation",
            "option_d": "Linear queue overflow without buffer limit",
            "correct_option": "A",
            "explanation": f"Modular decomposition allows complex {subject_name} systems to be divided into manageable, reusable components.",
            "marks": 5
        },
        {
            "question_text": f"In {subject_name}, which data structure or algorithm provides optimal average time complexity?",
            "option_a": "O(N^2) bubble sort algorithm",
            "option_b": "O(1) Hash Map lookup",
            "option_c": "O(N^3) Floyd-Warshall matrix multiplication",
            "option_d": "O(2^N) exponential backtracking",
            "correct_option": "B",
            "explanation": "Hash tables offer direct index mapping giving average O(1) constant time complexity for search and insertion.",
            "marks": 5
        }
    ]

def get_ai_solution_explanation(question_text, correct_option, student_option):
    """
    Call Flask Microservice to get AI-powered step-by-step explanation.
    """
    try:
        response = requests.post(
            f"{FLASK_SERVICE_URL}/api/explain-solution",
            json={"question": question_text, "correct_option": correct_option, "student_option": student_option},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("explanation", "")
    except Exception as e:
        logger.warning(f"Flask service unreachable ({e}), using fallback explanation.")
    
    if correct_option == student_option:
        return f"Great job! Option ({correct_option}) is correct. You demonstrated strong comprehension of the core concept."
    else:
        return f"Option ({correct_option}) is the correct answer. Your choice ({student_option}) missed key constraints specified in the prompt."

def get_ai_performance_analysis(attempt_data):
    """
    Call Flask Microservice for personalized student recommendations.
    """
    try:
        response = requests.post(
            f"{FLASK_SERVICE_URL}/api/analyze-performance",
            json=attempt_data,
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("analysis", "")
    except Exception as e:
        logger.warning(f"Flask service unreachable ({e}), using fallback analysis.")

    percentage = attempt_data.get('percentage', 0)
    subject = attempt_data.get('subject', 'General')
    
    if percentage >= 80:
        return f"Outstanding performance in {subject}! Your accuracy is {percentage}%. Recommendation: Attempt advanced mock exams and focus on timed speed drills."
    elif percentage >= 50:
        return f"Good effort in {subject} ({percentage}%). Recommendation: Review incorrect answers in detail and re-read foundational concepts."
    else:
        return f"Needs Improvement in {subject} ({percentage}%). Recommendation: Revise Previous Year Question (PYQ) papers and attempt subject topic-wise quizzes."
