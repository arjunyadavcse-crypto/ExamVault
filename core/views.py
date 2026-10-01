from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
import json
import uuid
import datetime

from .models import (
    UserProfile, Subject, PYQFile, Test, Question, 
    TestAttempt, UserAnswer, SubscriptionPlan, Payment
)
from .forms import RegisterForm, SubjectForm, PYQUploadForm, TestForm, QuestionForm
from .flask_client import generate_ai_questions, get_ai_solution_explanation, get_ai_performance_analysis

def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile

def home_view(request):
    subjects = Subject.objects.annotate(
        pyq_count=Count('pyqs', distinct=True),
        test_count=Count('tests', distinct=True)
    )[:6]
    tests = Test.objects.filter(is_active=True)[:6]
    pyqs = PYQFile.objects.select_related('subject').order_by('-uploaded_at')[:6]
    plans = SubscriptionPlan.objects.all().order_by('price')
    
    stats = {
        'total_students': UserProfile.objects.filter(role='STUDENT').count() or 1250,
        'total_pyqs': PYQFile.objects.count() or 450,
        'total_tests': Test.objects.count() or 120,
        'total_attempts': TestAttempt.objects.count() or 3400
    }
    
    return render(request, 'core/home.html', {
        'subjects': subjects,
        'tests': tests,
        'pyqs': pyqs,
        'plans': plans,
        'stats': stats
    })

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            role = form.cleaned_data.get('role', 'STUDENT')
            UserProfile.objects.create(
                user=user,
                role=role,
                subscription_tier='FREE'
            )
            login(request, user)
            messages.success(request, f"Welcome to ExamVault, {user.username}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = RegisterForm()
        
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')

@login_required
def dashboard(request):
    profile = get_or_create_profile(request.user)
    
    if profile.role == 'ADMIN':
        return redirect('admin_dashboard')
        
    attempts = TestAttempt.objects.filter(student=request.user).order_by('-completed_at')
    total_attempts = attempts.count()
    passed_attempts = attempts.filter(passed=True).count()
    
    avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0
    
    recent_pyqs = PYQFile.objects.select_related('subject').order_by('-uploaded_at')[:5]
    available_tests = Test.objects.filter(is_active=True).exclude(attempts__student=request.user)[:5]
    
    # Calculate AI recommendation stats
    latest_attempt = attempts.first()
    ai_recommendation = ""
    if latest_attempt:
        ai_recommendation = latest_attempt.ai_feedback or get_ai_performance_analysis({
            'percentage': latest_attempt.percentage,
            'score': latest_attempt.score,
            'total_marks': latest_attempt.total_marks,
            'subject': latest_attempt.test.subject.name
        })

    return render(request, 'core/dashboard.html', {
        'profile': profile,
        'attempts': attempts[:5],
        'total_attempts': total_attempts,
        'passed_attempts': passed_attempts,
        'avg_score': round(avg_score, 1),
        'recent_pyqs': recent_pyqs,
        'available_tests': available_tests,
        'ai_recommendation': ai_recommendation
    })

def subjects_list(request):
    query = request.GET.get('q', '')
    subjects = Subject.objects.annotate(
        pyq_count=Count('pyqs', distinct=True),
        test_count=Count('tests', distinct=True)
    )
    if query:
        subjects = subjects.filter(Q(name__icontains=query) | Q(code__icontains=query) | Q(description__icontains=query))
        
    return render(request, 'core/subjects.html', {'subjects': subjects, 'query': query})

def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    pyqs = subject.pyqs.all().order_by('-year')
    tests = subject.tests.filter(is_active=True)
    
    return render(request, 'core/subject_detail.html', {
        'subject': subject,
        'pyqs': pyqs,
        'tests': tests
    })

def pyqs_list(request):
    subject_id = request.GET.get('subject')
    query = request.GET.get('q', '')
    
    pyqs = PYQFile.objects.select_related('subject').order_by('-uploaded_at')
    
    if subject_id:
        pyqs = pyqs.filter(subject_id=subject_id)
    if query:
        pyqs = pyqs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(year__icontains=query))
        
    subjects = Subject.objects.all()
    
    return render(request, 'core/pyqs.html', {
        'pyqs': pyqs,
        'subjects': subjects,
        'selected_subject': subject_id,
        'query': query
    })

@login_required
def download_pyq(request, pyq_id):
    pyq = get_object_or_404(PYQFile, id=pyq_id)
    profile = get_or_create_profile(request.user)
    
    if pyq.is_premium and not profile.can_access_premium_pyq():
        messages.warning(request, "This PYQ resource requires a Pro or Premium subscription. Please upgrade to download.")
        return redirect('subscriptions')
        
    pyq.download_count += 1
    pyq.save()
    
    if pyq.pdf_file and hasattr(pyq.pdf_file, 'path'):
        return FileResponse(open(pyq.pdf_file.path, 'rb'), content_type='application/pdf', as_attachment=True, filename=pyq.pdf_file.name.split('/')[-1])
    else:
        messages.error(request, "PDF file not found on disk.")
        return redirect('pyqs')

def tests_list(request):
    subject_id = request.GET.get('subject')
    difficulty = request.GET.get('difficulty')
    
    tests = Test.objects.filter(is_active=True).select_related('subject')
    
    if subject_id:
        tests = tests.filter(subject_id=subject_id)
    if difficulty:
        tests = tests.filter(difficulty=difficulty)
        
    subjects = Subject.objects.all()
    
    # Check attempts for logged in user
    user_attempts = {}
    if request.user.is_authenticated:
        attempts = TestAttempt.objects.filter(student=request.user)
        for a in attempts:
            user_attempts[a.test_id] = a
            
    return render(request, 'core/tests.html', {
        'tests': tests,
        'subjects': subjects,
        'selected_subject': subject_id,
        'selected_difficulty': difficulty,
        'user_attempts': user_attempts
    })

@login_required
def test_detail(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    profile = get_or_create_profile(request.user)
    
    if test.is_premium and not profile.can_access_premium_pyq():
        messages.warning(request, "This Test Series requires a Pro or Premium subscription.")
        return redirect('subscriptions')
        
    previous_attempt = TestAttempt.objects.filter(student=request.user, test=test).order_by('-completed_at').first()
    
    return render(request, 'core/test_detail.html', {
        'test': test,
        'previous_attempt': previous_attempt
    })

@login_required
def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all().order_by('id')
    
    if not questions.exists():
        messages.warning(request, "This test does not have questions added yet.")
        return redirect('test_detail', test_id=test.id)
        
    return render(request, 'core/test_take.html', {
        'test': test,
        'questions': questions,
        'total_questions': questions.count()
    })

@login_required
def submit_test(request, test_id):
    if request.method != 'POST':
        return redirect('test_detail', test_id=test_id)
        
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all()
    
    time_taken = int(request.POST.get('time_taken', 0))
    
    score = 0.0
    total_marks = sum(q.marks for q in questions) or test.total_marks
    
    attempt = TestAttempt.objects.create(
        student=request.user,
        test=test,
        started_at=timezone.now(),
        completed_at=timezone.now(),
        time_taken_seconds=time_taken,
        total_marks=total_marks
    )
    
    for q in questions:
        selected_option = request.POST.get(f'question_{q.id}', '').upper()
        is_correct = (selected_option == q.correct_option)
        marks_obtained = q.marks if is_correct else 0.0
        if is_correct:
            score += marks_obtained
            
        UserAnswer.objects.create(
            test_attempt=attempt,
            question=q,
            selected_option=selected_option,
            is_correct=is_correct,
            marks_obtained=marks_obtained
        )
        
    percentage = (score / total_marks * 100.0) if total_marks > 0 else 0.0
    passed = percentage >= test.pass_percentage
    
    attempt.score = score
    attempt.percentage = round(percentage, 1)
    attempt.passed = passed
    
    # Get Flask AI insights
    attempt_data = {
        'percentage': attempt.percentage,
        'score': attempt.score,
        'total_marks': attempt.total_marks,
        'subject': test.subject.name
    }
    attempt.ai_feedback = get_ai_performance_analysis(attempt_data)
    attempt.save()
    
    messages.success(request, f"Test submitted successfully! Your score: {attempt.score}/{attempt.total_marks} ({attempt.percentage}%)")
    return redirect('test_result', attempt_id=attempt.id)

@login_required
def test_result(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    
    # Allow student or admin to view
    if attempt.student != request.user and not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    answers = attempt.answers.select_related('question').all()
    correct_count = answers.filter(is_correct=True).count()
    wrong_count = answers.filter(is_correct=False).exclude(selected_option='').exclude(selected_option=None).count()
    skipped_count = answers.filter(Q(selected_option='') | Q(selected_option=None)).count()
    
    return render(request, 'core/test_result.html', {
        'attempt': attempt,
        'answers': answers,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'skipped_count': skipped_count
    })

def subscriptions_view(request):
    plans = SubscriptionPlan.objects.all().order_by('price')
    profile = get_or_create_profile(request.user) if request.user.is_authenticated else None
    
    return render(request, 'core/subscriptions.html', {
        'plans': plans,
        'profile': profile
    })

@login_required
def initiate_payment(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    order_id = f"order_rzp_{uuid.uuid4().hex[:12]}"
    
    payment = Payment.objects.create(
        user=request.user,
        plan=plan,
        razorpay_order_id=order_id,
        amount=plan.price,
        status='PENDING'
    )
    
    return render(request, 'core/payment_checkout.html', {
        'plan': plan,
        'payment': payment,
        'order_id': order_id,
        'razorpay_key': 'rzp_test_ExamVaultKey123'
    })

@login_required
def verify_payment(request):
    if request.method == 'POST':
        order_id = request.POST.get('razorpay_order_id')
        payment_id = request.POST.get('razorpay_payment_id', f"pay_{uuid.uuid4().hex[:10]}")
        signature = request.POST.get('razorpay_signature', f"sig_{uuid.uuid4().hex[:14]}")
        
        payment = get_object_or_404(Payment, razorpay_order_id=order_id, user=request.user)
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.status = 'SUCCESS'
        payment.save()
        
        # Upgrade User Subscription
        profile = get_or_create_profile(request.user)
        profile.subscription_tier = payment.plan.tier_code
        profile.subscription_expires_at = timezone.now() + datetime.timedelta(days=payment.plan.duration_days)
        profile.save()
        
        messages.success(request, f"🎉 Payment Successful! Your account has been upgraded to {payment.plan.name}.")
        return redirect('dashboard')
        
    return redirect('subscriptions')

@login_required
def admin_dashboard(request):
    profile = get_or_create_profile(request.user)
    
    if profile.role != 'ADMIN' and not request.user.is_staff:
        messages.error(request, "Access restricted to Staff/Faculty only.")
        return redirect('dashboard')
        
    subjects = Subject.objects.annotate(
        pyq_count=Count('pyqs', distinct=True),
        test_count=Count('tests', distinct=True)
    )
    tests = Test.objects.all().order_by('-created_at')
    pyqs = PYQFile.objects.all().order_by('-uploaded_at')
    attempts = TestAttempt.objects.select_related('student', 'test').order_by('-completed_at')[:10]
    payments = Payment.objects.select_related('user', 'plan').order_by('-created_at')[:10]
    
    subject_form = SubjectForm()
    pyq_form = PYQUploadForm()
    test_form = TestForm()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_subject':
            form = SubjectForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Subject created successfully!")
                return redirect('admin_dashboard')
        elif action == 'upload_pyq':
            form = PYQUploadForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "PYQ PDF uploaded successfully!")
                return redirect('admin_dashboard')
        elif action == 'add_test':
            form = TestForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Test created successfully!")
                return redirect('admin_dashboard')
        elif action == 'generate_ai_test':
            subj_id = request.POST.get('subject')
            count = int(request.POST.get('question_count', 3))
            subject = get_object_or_404(Subject, id=subj_id)
            
            ai_qs = generate_ai_questions(subject.name, count=count)
            test_obj = Test.objects.create(
                title=f"AI Generated Test: {subject.name}",
                subject=subject,
                description=f"Automated AI question set created for {subject.name}",
                duration_minutes=15,
                total_marks=len(ai_qs)*5,
                difficulty='Medium'
            )
            for q in ai_qs:
                Question.objects.create(
                    test=test_obj,
                    question_text=q['question_text'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_option=q['correct_option'],
                    explanation=q.get('explanation', ''),
                    marks=q.get('marks', 5)
                )
            messages.success(request, f"Generated AI Test '{test_obj.title}' with {len(ai_qs)} questions!")
            return redirect('admin_dashboard')

    return render(request, 'core/admin_dashboard.html', {
        'subjects': subjects,
        'tests': tests,
        'pyqs': pyqs,
        'attempts': attempts,
        'payments': payments,
        'subject_form': subject_form,
        'pyq_form': pyq_form,
        'test_form': test_form
    })

@login_required
def ai_assistant_view(request):
    ai_questions = []
    explanation_result = ""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'generate_questions':
            subject_name = request.POST.get('subject_name', 'Computer Science')
            ai_questions = generate_ai_questions(subject_name, count=3)
        elif action == 'explain_solution':
            q_text = request.POST.get('question_text')
            correct_opt = request.POST.get('correct_option')
            user_opt = request.POST.get('student_option')
            explanation_result = get_ai_solution_explanation(q_text, correct_opt, user_opt)
            
    subjects = Subject.objects.all()
    return render(request, 'core/ai_assistant.html', {
        'subjects': subjects,
        'ai_questions': ai_questions,
        'explanation_result': explanation_result
    })
