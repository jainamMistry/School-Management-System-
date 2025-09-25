from rest_framework import serializers
from django.contrib.auth.models import User
from . import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class TeacherExtraSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = models.TeacherExtra
        fields = ['id', 'user', 'salary', 'joindate', 'mobile', 'status']


class StudentExtraSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = models.StudentExtra
        fields = ['id', 'user', 'roll', 'mobile', 'fee', 'cl', 'status']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subject
        fields = ['id', 'name', 'code', 'description', 'created_at']


class AssignmentSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    teacher = TeacherExtraSerializer(read_only=True)
    
    class Meta:
        model = models.Assignment
        fields = ['id', 'title', 'description', 'subject', 'teacher', 'class_name', 
                'due_date', 'max_marks', 'created_at', 'is_active']


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    assignment = AssignmentSerializer(read_only=True)
    student = StudentExtraSerializer(read_only=True)
    
    class Meta:
        model = models.AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'submission_file', 'submission_text',
                'submitted_at', 'marks_obtained', 'feedback', 'is_graded']


class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = models.Notification
        fields = ['id', 'title', 'message', 'notification_type', 'recipient',
                'is_read', 'created_at', 'expires_at']


class ExamSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    created_by = TeacherExtraSerializer(read_only=True)
    
    class Meta:
        model = models.Exam
        fields = ['id', 'name', 'exam_type', 'subject', 'class_name', 'exam_date',
                'duration_minutes', 'max_marks', 'instructions', 'created_by', 'created_at']


class ExamResultSerializer(serializers.ModelSerializer):
    exam = ExamSerializer(read_only=True)
    student = StudentExtraSerializer(read_only=True)
    
    class Meta:
        model = models.ExamResult
        fields = ['id', 'exam', 'student', 'marks_obtained', 'grade', 'remarks', 'created_at']


class FeePaymentSerializer(serializers.ModelSerializer):
    student = StudentExtraSerializer(read_only=True)
    
    class Meta:
        model = models.FeePayment
        fields = ['id', 'student', 'amount', 'due_date', 'payment_date', 'status',
                'payment_method', 'transaction_id', 'notes', 'created_at']


class LibraryBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LibraryBook
        fields = ['id', 'title', 'author', 'isbn', 'category', 'publisher',
                'publication_year', 'pages', 'status', 'added_date']


class BookBorrowingSerializer(serializers.ModelSerializer):
    book = LibraryBookSerializer(read_only=True)
    borrower = UserSerializer(read_only=True)
    
    class Meta:
        model = models.BookBorrowing
        fields = ['id', 'book', 'borrower', 'borrow_date', 'due_date', 'return_date',
                'fine_amount', 'is_returned']


class SchoolEventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    
    class Meta:
        model = models.SchoolEvent
        fields = ['id', 'title', 'description', 'event_type', 'start_date', 'end_date',
                'location', 'organizer', 'is_public', 'created_at']


class StudentPerformanceSerializer(serializers.ModelSerializer):
    student = StudentExtraSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    
    class Meta:
        model = models.StudentPerformance
        fields = ['id', 'student', 'subject', 'semester', 'attendance_percentage',
                'average_marks', 'grade', 'remarks', 'created_at']


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attendance
        fields = ['id', 'roll', 'date', 'cl', 'present_status']


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notice
        fields = ['id', 'date', 'by', 'message']
