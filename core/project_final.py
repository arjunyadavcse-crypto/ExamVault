from django.contrib import admin
from .models import UserProfile, Subject, PYQFile, Test, Question, TestAttempt, UserAnswer, SubscriptionPlan, Payment

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'subscription_tier', 'subscription_expires_at')
    list_filter = ('role', 'subscription_tier')
    search_fields = ('user__username', 'user__email')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

@admin.register(PYQFile)
class PYQFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'year', 'is_premium', 'download_count', 'uploaded_at')
    list_filter = ('subject', 'year', 'is_premium')
    search_fields = ('title', 'description')

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 2

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'duration_minutes', 'total_marks', 'difficulty', 'is_active', 'is_premium')
    list_filter = ('subject', 'difficulty', 'is_active', 'is_premium')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'test', 'correct_option', 'marks')
    list_filter = ('test__subject', 'correct_option')
    search_fields = ('question_text', 'explanation')

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'score', 'total_marks', 'percentage', 'passed', 'completed_at')
    list_filter = ('passed', 'completed_at', 'test__subject')
    search_fields = ('student__username', 'test__title')

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('test_attempt', 'question', 'selected_option', 'is_correct', 'marks_obtained')
    list_filter = ('is_correct',)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier_code', 'price', 'duration_days', 'is_popular')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount', 'status', 'razorpay_order_id', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'razorpay_order_id', 'razorpay_payment_id')
