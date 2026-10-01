from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Knowledge database for question generation
SAMPLE_QUESTION_BANK = {
    "Computer Science": [
        {
            "question_text": "What is the worst-case time complexity of QuickSort algorithm?",
            "option_a": "O(N)",
            "option_b": "O(N log N)",
            "option_c": "O(N^2)",
            "option_d": "O(log N)",
            "correct_option": "C",
            "explanation": "QuickSort degrades to O(N^2) worst case when the pivot chosen is consistently the smallest or largest element (e.g. already sorted array).",
            "marks": 5
        },
        {
            "question_text": "Which ACID property ensures that transactions are committed permanently even in case of system crashes?",
            "option_a": "Atomicity",
            "option_b": "Consistency",
            "option_c": "Isolation",
            "option_d": "Durability",
            "correct_option": "D",
            "explanation": "Durability guarantees that once a transaction has committed, it will remain committed even in the event of a power loss or system failure.",
            "marks": 5
        },
        {
            "question_text": "In TCP/IP protocol stack, which layer is responsible for end-to-end reliable transmission?",
            "option_a": "Application Layer",
            "option_b": "Transport Layer",
            "option_c": "Network Layer",
            "option_d": "Data Link Layer",
            "correct_option": "B",
            "explanation": "The Transport Layer (TCP) provides transparent, reliable end-to-end data transfer services to upper layers.",
            "marks": 5
        }
    ],
    "Data Structures": [
        {
            "question_text": "Which data structure follows the LIFO (Last In First Out) principle?",
            "option_a": "Queue",
            "option_b": "Stack",
            "option_c": "Array",
            "option_d": "Linked List",
            "correct_option": "B",
            "explanation": "Stack inserts (push) and removes (pop) elements from the top end, operating on LIFO principle.",
            "marks": 5
        },
        {
            "question_text": "What is the height of a balanced Binary Search Tree (AVL Tree) with N nodes?",
            "option_a": "O(N)",
            "option_b": "O(log N)",
            "option_c": "O(N log N)",
            "option_d": "O(1)",
            "correct_option": "B",
            "explanation": "Self-balancing binary search trees maintain a maximum height strictly bounded by O(log N).",
            "marks": 5
        }
    ]
}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "running", "service": "ExamVault AI Engine", "version": "1.0"})

@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    data = request.json or {}
    subject = data.get('subject', 'Computer Science')
    count = data.get('count', 3)
    difficulty = data.get('difficulty', 'Medium')
    
    available = SAMPLE_QUESTION_BANK.get(subject, SAMPLE_QUESTION_BANK["Computer Science"])
    
    # Generate variations or return sampled
    selected = random.choices(available, k=min(count, len(available)))
    return jsonify({
        "status": "success",
        "subject": subject,
        "difficulty": difficulty,
        "questions": selected
    })

@app.route('/api/explain-solution', methods=['POST'])
def explain_solution():
    data = request.json or {}
    question = data.get('question', '')
    correct = data.get('correct_option', 'A')
    user_ans = data.get('student_option', '')
    
    if correct == user_ans:
        explanation = f"✨ Correct! Option ({correct}) is the right answer. Your understanding of this prompt is accurate."
    else:
        explanation = (
            f"❌ Incorrect. You selected ({user_ans or 'Skipped'}), but the correct answer is ({correct}). "
            f"Detailed Analysis: Option ({correct}) satisfies all logical constraints defined in the question."
        )
    
    return jsonify({
        "status": "success",
        "explanation": explanation
    })

@app.route('/api/analyze-performance', methods=['POST'])
def analyze_performance():
    data = request.json or {}
    percentage = data.get('percentage', 0.0)
    score = data.get('score', 0)
    total = data.get('total_marks', 100)
    subject = data.get('subject', 'General')
    
    if percentage >= 85:
        analysis = f"🏆 Master Level! Excellent mastery in {subject} with {percentage}% score. Recommendation: Try speed challenges and teach peer students."
    elif percentage >= 60:
        analysis = f"👍 Good Performance! You scored {score}/{total} ({percentage}%). Recommendation: Review missed questions and solve 2 PYQ papers this week."
    elif percentage >= 40:
        analysis = f"⚡ Passing Level. Score: {percentage}%. Focus area: Strengthen baseline concepts in {subject} before attempting full mock tests."
    else:
        analysis = f"⚠️ Needs Revision. Score: {percentage}%. Key action: Go through PYQ solution guides step-by-step and re-attempt chapter quizzes."

    return jsonify({
        "status": "success",
        "analysis": analysis,
        "score_insights": {
            "retention_rate": f"{percentage}%",
            "strength": "High accuracy in standard questions" if percentage > 50 else "Requires concept reinforcement"
        }
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
