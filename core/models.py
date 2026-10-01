from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('ADMIN', 'Admin/Faculty'),
    )
    TIER_CHOICES = (
        ('FREE', 'Free Tier'),
        ('PRO', 'Pro Tier'),
        ('PREMIUM', 'Premium Tier'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    subscription_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='FREE')
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def is_subscription_active(self):
        if self.subscription_tier == 'FREE':
            return True
        if self.subscription_expires_at and self.subscription_expires_at > timezone.now():
            return True
        return False

    def can_access_premium_pyq(self):
        return self.subscription_tier in ['PRO', 'PREMIUM'] and self.is_subscription_active()

    def __str__(self):
        return f"{self.user.username} ({self.role} - {self.subscription_tier})"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book-open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class PYQFile(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='pyqs')
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    description = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to='pyqs/')
    is_premium = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.year} ({'Premium' if self.is_premium else 'Free'})"


class Test(models.Model):
    DIFFICULTY_CHOICES = (
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    )

    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tests')
    description = models.TextField()
    duration_minutes = models.IntegerField(default=30)
    total_marks = models.IntegerField(default=100)
    pass_percentage = models.FloatField(default=40.0)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Medium')
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def question_count(self):
        return self.questions.count()

    def __str__(self):
        return f"{self.title} - {self.subject.name}"


class Question(models.Model):
    OPTION_CHOICES = (
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    )

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField(blank=True)
    marks = models.IntegerField(default=5)

    def __str__(self):
        return f"Q: {self.question_text[:50]}... (Test: {self.test.title})"


class TestAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(default=0.0)
    total_marks = models.FloatField(default=0.0)
    percentage = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(default=0)
    ai_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.test.title} - Score: {self.score}/{self.total_marks}"


class UserAnswer(models.Model):
    test_attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    marks_obtained = models.FloatField(default=0.0)

    def __str__(self):
        return f"Attempt #{self.test_attempt.id} - Q#{self.question.id} -> {self.selected_option}"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    tier_code = models.CharField(max_length=20, choices=UserProfile.TIER_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    description = models.TextField()
    features = models.TextField(help_text="Comma-separated features")
    is_popular = models.BooleanField(default=False)

    def get_features_list(self):
        return [f.strip() for f in self.features.split(',') if f.strip()]

    def __str__(self):
        return f"{self.name} - ₹{self.price} ({self.duration_days} days)"


class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.user.username} - {self.status} (₹{self.amount})"
