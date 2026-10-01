import os
import django
import sys
import datetime
from pathlib import Path

# Setup Django Environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examvault.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from core.models import (
    UserProfile, Subject, PYQFile, Test, Question, 
    TestAttempt, UserAnswer, SubscriptionPlan, Payment
)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_pdf(file_path, title, subject_code):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 750, f"ExamVault Official Paper: {title}")
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, f"Subject Code: {subject_code} | Academic Year Solved Paper")
    c.line(100, 720, 500, 720)
    
    c.drawString(100, 680, "SECTION A - Multiple Choice Questions")
    c.setFont("Helvetica", 10)
    c.drawString(100, 660, "Q1. What is the average time complexity of searching in a Hash Table?")
    c.drawString(120, 645, "a) O(N)   b) O(1) [Correct]   c) O(log N)   d) O(N^2)")
    
    c.drawString(100, 620, "Q2. Which architectural layer in Django handles business logic?")
    c.drawString(120, 605, "a) Template   b) View [Correct]   c) URL Routing   d) Migration Engine")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 560, "SECTION B - Descriptive Solutions")
    c.setFont("Helvetica", 10)
    c.drawString(100, 540, "1. Explain Modular Microservices architecture with Django + Flask.")
    c.drawString(100, 525, "Solution: Flask provides low-overhead REST microservice capabilities while Django handles")
    c.drawString(100, 510, "authentication, administrative backend, and SQLite ORM persistence.")
    
    c.showPage()
    c.save()

def run_seed():
    print("Seeding ExamVault database with sample data...")

    # 1. Create Subscription Plans
    p_free, _ = SubscriptionPlan.objects.get_or_create(
        tier_code='FREE',
        defaults={
            'name': 'Free Tier',
            'price': 0.00,
            'duration_days': 365,
            'description': 'Basic access to public PYQ papers and standard quizzes.',
            'features': 'Access free PYQ PDFs, Standard MCQ practice tests, Basic result summary',
            'is_popular': False
        }
    )

    p_pro, _ = SubscriptionPlan.objects.get_or_create(
        tier_code='PRO',
        defaults={
            'name': 'Pro Student Plan',
            'price': 299.00,
            'duration_days': 90,
            'description': 'Complete access to all verified PYQ PDF downloads and AI analytics.',
            'features': 'Unlimited PYQ PDF Downloads, Full Mock Test Series, Step-by-Step AI Explanations, Priority Study Recommendations',
            'is_popular': True
        }
    )

    p_prem, _ = SubscriptionPlan.objects.get_or_create(
        tier_code='PREMIUM',
        defaults={
            'name': 'Faculty & Premium Plan',
            'price': 599.00,
            'duration_days': 365,
            'description': 'Full platform access including AI Question Generator and Staff Portal.',
            'features': 'All Pro Plan Features, Unlimited AI Question Generator, Custom Test Builder, Faculty Admin Panel Access, 1-on-1 Analytics',
            'is_popular': False
        }
    )

    # 2. Create Users
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@examvault.edu', 'first_name': 'System', 'last_name': 'Administrator', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        UserProfile.objects.create(user=admin_user, role='ADMIN', subscription_tier='PREMIUM')

    student_user, created = User.objects.get_or_create(
        username='student',
        defaults={'email': 'student@examvault.edu', 'first_name': 'Arjun', 'last_name': 'Kumar'}
    )
    if created:
        student_user.set_password('student123')
        student_user.save()
        UserProfile.objects.create(user=student_user, role='STUDENT', subscription_tier='PRO', subscription_expires_at=timezone.now() + datetime.timedelta(days=90))

    # 3. Create Subjects
    sub_cs, _ = Subject.objects.get_or_create(
        code='CS101',
        defaults={'name': 'Computer Science & Engineering', 'description': 'Fundamentals of computing, software engineering, OS & computer organization.', 'icon': 'code'}
    )

    sub_dsa, _ = Subject.objects.get_or_create(
        code='DSA201',
        defaults={'name': 'Data Structures & Algorithms', 'description': 'Arrays, Linked Lists, Stacks, Queues, Trees, Graphs, Sorting & Dynamic Programming.', 'icon': 'cpu'}
    )

    sub_dbms, _ = Subject.objects.get_or_create(
        code='DBMS301',
        defaults={'name': 'Database Management Systems', 'description': 'Relational databases, SQL queries, Normalization, ACID transactions & Indexing.', 'icon': 'database'}
    )

    sub_web, _ = Subject.objects.get_or_create(
        code='WEB401',
        defaults={'name': 'Web Architecture & Cloud', 'description': 'Fullstack web development, REST APIs, Microservices, Django & Flask frameworks.', 'icon': 'globe'}
    )

    # 4. Generate PYQ PDF files and database records
    media_dir = BASE_DIR / 'media' / 'pyqs'
    os.makedirs(media_dir, exist_ok=True)

    pdf1_path = media_dir / 'cs101_midterm_2025.pdf'
    pdf2_path = media_dir / 'dsa201_final_2024.pdf'
    pdf3_path = media_dir / 'dbms301_pyq_2023.pdf'
    pdf4_path = media_dir / 'web401_pyq_2025.pdf'

    create_sample_pdf(str(pdf1_path), "CS101 Mid-Term Examination", "CS101")
    create_sample_pdf(str(pdf2_path), "DSA201 End-Sem Question Paper", "DSA201")
    create_sample_pdf(str(pdf3_path), "DBMS301 University PYQ", "DBMS301")
    create_sample_pdf(str(pdf4_path), "WEB401 Cloud & Web Solved Paper", "WEB401")

    PYQFile.objects.get_or_create(
        title="Computer Science Mid-Term Solved PYQ 2025",
        defaults={
            'subject': sub_cs,
            'year': 2025,
            'description': 'Official mid-semester examination paper with step-by-step verified solutions.',
            'pdf_file': 'pyqs/cs101_midterm_2025.pdf',
            'is_premium': False,
            'download_count': 142
        }
    )

    PYQFile.objects.get_or_create(
        title="Data Structures Advanced End-Sem PYQ 2024",
        defaults={
            'subject': sub_dsa,
            'year': 2024,
            'description': 'Complete solved paper covering Trees, Graphs, AVL Tree balancing and Dynamic Programming.',
            'pdf_file': 'pyqs/dsa201_final_2024.pdf',
            'is_premium': True,
            'download_count': 289
        }
    )

    PYQFile.objects.get_or_create(
        title="DBMS Relational Algebra & SQL Solved PYQ 2023",
        defaults={
            'subject': sub_dbms,
            'year': 2023,
            'description': 'Includes 25+ SQL query solutions and ER diagram design breakdowns.',
            'pdf_file': 'pyqs/dbms301_pyq_2023.pdf',
            'is_premium': False,
            'download_count': 95
        }
    )

    PYQFile.objects.get_or_create(
        title="Web Architecture & Fullstack Django PYQ 2025",
        defaults={
            'subject': sub_web,
            'year': 2025,
            'description': 'Comprehensive question paper covering HTTP protocol, Django ORM, REST APIs & Flask microservices.',
            'pdf_file': 'pyqs/web401_pyq_2025.pdf',
            'is_premium': True,
            'download_count': 310
        }
    )

    # 5. Create Tests & Questions
    test1, _ = Test.objects.get_or_create(
        title="Computer Science Core Fundamentals Mock Test",
        defaults={
            'subject': sub_cs,
            'description': 'Test your core understanding of OS, computer organization and software architecture.',
            'duration_minutes': 15,
            'total_marks': 20,
            'pass_percentage': 50.0,
            'difficulty': 'Easy'
        }
    )

    if not test1.questions.exists():
        Question.objects.create(
            test=test1,
            question_text="Which component of the CPU is responsible for performing arithmetic and logical calculations?",
            option_a="Control Unit (CU)",
            option_b="Arithmetic Logic Unit (ALU)",
            option_c="Memory Management Unit (MMU)",
            option_d="Register File",
            correct_option="B",
            explanation="The ALU (Arithmetic Logic Unit) executes integer arithmetic operations (addition, subtraction) and logical comparisons.",
            marks=5
        )
        Question.objects.create(
            test=test1,
            question_text="Which operating system scheduling algorithm can cause the convoy effect?",
            option_a="First-Come First-Served (FCFS)",
            option_b="Round Robin (RR)",
            option_c="Shortest Job First (SJF)",
            option_d="Priority Scheduling",
            correct_option="A",
            explanation="FCFS scheduling causes smaller processes to wait behind long CPU-bound processes, known as the convoy effect.",
            marks=5
        )
        Question.objects.create(
            test=test1,
            question_text="What is the main role of the HTTP protocol in Web Applications?",
            option_a="Encrypt database tables at rest",
            option_b="Transfer hypermedia documents between client and server",
            option_c="Compile Python code into machine instructions",
            option_d="Allocate physical RAM blocks in memory",
            correct_option="B",
            explanation="HTTP (Hypertext Transfer Protocol) is an application layer protocol designed to transfer documents and API data between Web Clients and Servers.",
            marks=5
        )
        Question.objects.create(
            test=test1,
            question_text="In Object-Oriented Programming, what is Encapsulation?",
            option_a="Inheriting features from multiple parent classes",
            option_b="Bundling data and methods into a single unit and restricting direct access",
            option_c="Converting high-level code to bytecode",
            option_d="Writing recursive functions without base cases",
            correct_option="B",
            explanation="Encapsulation binds data attributes with methods operating on them, hiding internal state details from outside code.",
            marks=5
        )

    test2, _ = Test.objects.get_or_create(
        title="Data Structures Master Challenge (DSA)",
        defaults={
            'subject': sub_dsa,
            'description': 'Advanced test series covering algorithm complexities, linked lists, trees and stacks.',
            'duration_minutes': 20,
            'total_marks': 20,
            'pass_percentage': 60.0,
            'difficulty': 'Medium'
        }
    )

    if not test2.questions.exists():
        Question.objects.create(
            test=test2,
            question_text="What is the worst-case time complexity of searching an element in a balanced Binary Search Tree (AVL Tree)?",
            option_a="O(N)",
            option_b="O(log N)",
            option_c="O(N^2)",
            option_d="O(1)",
            correct_option="B",
            explanation="AVL trees maintain height balance within 1, ensuring maximum search depth is strictly O(log N).",
            marks=5
        )
        Question.objects.create(
            test=test2,
            question_text="Which data structure is primarily used for depth-first traversal (DFS) of a graph?",
            option_a="Queue",
            option_b="Stack",
            option_c="Heap",
            option_d="Hash Map",
            correct_option="B",
            explanation="DFS uses a Stack (either explicit stack or implicit function call stack) to explore as deep as possible along each branch.",
            marks=5
        )
        Question.objects.create(
            test=test2,
            question_text="What data structure is optimal for implementing a LIFO (Last-In-First-Out) cache?",
            option_a="Queue",
            option_b="Stack",
            option_c="Binary Tree",
            option_d="Array",
            correct_option="B",
            explanation="Stack operates on LIFO principle, where elements added last are popped first.",
            marks=5
        )
        Question.objects.create(
            test=test2,
            question_text="What is the average time complexity of inserting an element into a Hash Map with low load factor?",
            option_a="O(N)",
            option_b="O(log N)",
            option_c="O(1)",
            option_d="O(N log N)",
            correct_option="C",
            explanation="Hash tables perform direct index computation using hash functions, giving average O(1) constant time insertion.",
            marks=5
        )

    # 6. Create sample test attempt for student
    if not TestAttempt.objects.filter(student=student_user).exists():
        att = TestAttempt.objects.create(
            student=student_user,
            test=test1,
            score=15.0,
            total_marks=20.0,
            percentage=75.0,
            passed=True,
            started_at=timezone.now() - datetime.timedelta(hours=2),
            completed_at=timezone.now() - datetime.timedelta(hours=1),
            time_taken_seconds=420,
            ai_feedback="👍 Good performance! You scored 15.0/20.0 (75.0%). Recommendation: Review missed questions and solve 2 PYQ papers this week."
        )
        for q in test1.questions.all():
            UserAnswer.objects.create(
                test_attempt=att,
                question=q,
                selected_option=q.correct_option if q.id % 2 == 1 else 'A',
                is_correct=(q.correct_option if q.id % 2 == 1 else 'A') == q.correct_option,
                marks_obtained=5.0 if (q.correct_option if q.id % 2 == 1 else 'A') == q.correct_option else 0.0
            )

    print("[SUCCESS] Seed completed successfully!")

if __name__ == '__main__':
    run_seed()
