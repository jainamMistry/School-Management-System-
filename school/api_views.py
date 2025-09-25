from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from . import models, serializers

logger = logging.getLogger('school')


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = models.TeacherExtra.objects.all()
    serializer_class = serializers.TeacherExtraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'salary']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    ordering_fields = ['salary', 'joindate']
    ordering = ['-joindate']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get teacher statistics"""
        total_teachers = self.queryset.count()
        active_teachers = self.queryset.filter(status=True).count()
        pending_teachers = self.queryset.filter(status=False).count()
        avg_salary = self.queryset.filter(status=True).aggregate(avg_salary=Avg('salary'))['avg_salary'] or 0
        
        return Response({
            'total_teachers': total_teachers,
            'active_teachers': active_teachers,
            'pending_teachers': pending_teachers,
            'average_salary': round(avg_salary, 2)
        })


class StudentViewSet(viewsets.ModelViewSet):
    queryset = models.StudentExtra.objects.all()
    serializer_class = serializers.StudentExtraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'cl', 'fee']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'roll']
    ordering_fields = ['roll', 'fee']
    ordering = ['roll']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get student statistics"""
        total_students = self.queryset.count()
        active_students = self.queryset.filter(status=True).count()
        pending_students = self.queryset.filter(status=False).count()
        
        # Class-wise distribution
        class_distribution = self.queryset.filter(status=True).values('cl').annotate(count=Count('id'))
        
        return Response({
            'total_students': total_students,
            'active_students': active_students,
            'pending_students': pending_students,
            'class_distribution': list(class_distribution)
        })


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = models.Subject.objects.all()
    serializer_class = serializers.SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = models.Assignment.objects.all()
    serializer_class = serializers.AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['subject', 'class_name', 'teacher', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get all submissions for an assignment"""
        assignment = self.get_object()
        submissions = models.AssignmentSubmission.objects.filter(assignment=assignment)
        serializer = serializers.AssignmentSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming assignments"""
        upcoming = self.queryset.filter(
            due_date__gte=timezone.now(),
            is_active=True
        ).order_by('due_date')[:10]
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
    queryset = models.AssignmentSubmission.objects.all()
    serializer_class = serializers.AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assignment', 'student', 'is_graded']
    ordering_fields = ['submitted_at', 'marks_obtained']
    ordering = ['-submitted_at']

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """Grade an assignment submission"""
        submission = self.get_object()
        marks = request.data.get('marks_obtained')
        feedback = request.data.get('feedback', '')
        
        if marks is not None:
            submission.marks_obtained = marks
            submission.feedback = feedback
            submission.is_graded = True
            submission.save()
            
            serializer = self.get_serializer(submission)
            return Response(serializer.data)
        
        return Response({'error': 'Marks are required'}, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['notification_type', 'is_read', 'recipient']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter notifications by current user"""
        return self.queryset.filter(recipient=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


class ExamViewSet(viewsets.ModelViewSet):
    queryset = models.Exam.objects.all()
    serializer_class = serializers.ExamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['exam_type', 'subject', 'class_name', 'created_by']
    search_fields = ['name', 'instructions']
    ordering_fields = ['exam_date', 'created_at']
    ordering = ['exam_date']

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming exams"""
        upcoming = self.queryset.filter(
            exam_date__gte=timezone.now()
        ).order_by('exam_date')[:10]
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


class ExamResultViewSet(viewsets.ModelViewSet):
    queryset = models.ExamResult.objects.all()
    serializer_class = serializers.ExamResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['exam', 'student', 'grade']
    ordering_fields = ['marks_obtained', 'created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get performance summary"""
        student_id = request.query_params.get('student_id')
        if student_id:
            results = self.queryset.filter(student_id=student_id)
            avg_marks = results.aggregate(avg_marks=Avg('marks_obtained'))['avg_marks'] or 0
            grade_distribution = results.values('grade').annotate(count=Count('id'))
            
            return Response({
                'average_marks': round(avg_marks, 2),
                'total_exams': results.count(),
                'grade_distribution': list(grade_distribution)
            })
        
        return Response({'error': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)


class FeePaymentViewSet(viewsets.ModelViewSet):
    queryset = models.FeePayment.objects.all()
    serializer_class = serializers.FeePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'status', 'payment_method']
    ordering_fields = ['due_date', 'payment_date', 'amount']
    ordering = ['-due_date']

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue payments"""
        overdue = self.queryset.filter(
            status='pending',
            due_date__lt=timezone.now().date()
        )
        serializer = self.get_serializer(overdue, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get fee payment statistics"""
        total_amount = self.queryset.aggregate(total=Sum('amount'))['total'] or 0
        paid_amount = self.queryset.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
        pending_amount = self.queryset.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount,
            'collection_rate': round((paid_amount / total_amount * 100) if total_amount > 0 else 0, 2)
        })


class LibraryBookViewSet(viewsets.ModelViewSet):
    queryset = models.LibraryBook.objects.all()
    serializer_class = serializers.LibraryBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'added_date']
    ordering = ['title']

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available books"""
        available = self.queryset.filter(status='available')
        serializer = self.get_serializer(available, many=True)
        return Response(serializer.data)


class BookBorrowingViewSet(viewsets.ModelViewSet):
    queryset = models.BookBorrowing.objects.all()
    serializer_class = serializers.BookBorrowingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['book', 'borrower', 'is_returned']
    ordering_fields = ['borrow_date', 'due_date']
    ordering = ['-borrow_date']

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """Return a borrowed book"""
        borrowing = self.get_object()
        borrowing.return_date = timezone.now().date()
        borrowing.is_returned = True
        
        # Calculate fine if overdue
        if borrowing.due_date < borrowing.return_date:
            days_overdue = (borrowing.return_date - borrowing.due_date).days
            borrowing.fine_amount = days_overdue * 5  # $5 per day fine
        
        borrowing.save()
        
        # Update book status
        borrowing.book.status = 'available'
        borrowing.book.save()
        
        serializer = self.get_serializer(borrowing)
        return Response(serializer.data)


class SchoolEventViewSet(viewsets.ModelViewSet):
    queryset = models.SchoolEvent.objects.all()
    serializer_class = serializers.SchoolEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'is_public', 'organizer']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['start_date']

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events"""
        upcoming = self.queryset.filter(
            start_date__gte=timezone.now(),
            is_public=True
        ).order_by('start_date')[:10]
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = models.Attendance.objects.all()
    serializer_class = serializers.AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['cl', 'date', 'present_status']
    ordering_fields = ['date']
    ordering = ['-date']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get attendance statistics"""
        class_name = request.query_params.get('class_name')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.queryset
        if class_name:
            queryset = queryset.filter(cl=class_name)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        total_records = queryset.count()
        present_count = queryset.filter(present_status='Present').count()
        absent_count = queryset.filter(present_status='Absent').count()
        
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        return Response({
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': round(attendance_percentage, 2)
        })


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def admin_stats(self, request):
        """Get admin dashboard statistics"""
        teacher_count = models.TeacherExtra.objects.filter(status=True).count()
        student_count = models.StudentExtra.objects.filter(status=True).count()
        pending_teachers = models.TeacherExtra.objects.filter(status=False).count()
        pending_students = models.StudentExtra.objects.filter(status=False).count()
        
        # Recent activities
        recent_notices = models.Notice.objects.all().order_by('-date')[:5]
        upcoming_events = models.SchoolEvent.objects.filter(
            start_date__gte=timezone.now(),
            is_public=True
        ).order_by('start_date')[:5]
        
        return Response({
            'teacher_count': teacher_count,
            'student_count': student_count,
            'pending_teachers': pending_teachers,
            'pending_students': pending_students,
            'recent_notices': serializers.NoticeSerializer(recent_notices, many=True).data,
            'upcoming_events': serializers.SchoolEventSerializer(upcoming_events, many=True).data
        })

    @action(detail=False, methods=['get'])
    def student_stats(self, request):
        """Get student dashboard statistics"""
        try:
            student = models.StudentExtra.objects.get(user=request.user)
            
            # Attendance statistics
            attendance_records = models.Attendance.objects.filter(
                cl=student.cl,
                roll=student.roll
            )
            total_days = attendance_records.count()
            present_days = attendance_records.filter(present_status='Present').count()
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            # Recent assignments
            recent_assignments = models.Assignment.objects.filter(
                class_name=student.cl,
                is_active=True
            ).order_by('-created_at')[:5]
            
            # Recent notifications
            recent_notifications = models.Notification.objects.filter(
                recipient=request.user
            ).order_by('-created_at')[:5]
            
            return Response({
                'attendance_percentage': round(attendance_percentage, 2),
                'total_days': total_days,
                'present_days': present_days,
                'recent_assignments': serializers.AssignmentSerializer(recent_assignments, many=True).data,
                'recent_notifications': serializers.NotificationSerializer(recent_notifications, many=True).data
            })
        except models.StudentExtra.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def teacher_stats(self, request):
        """Get teacher dashboard statistics"""
        try:
            teacher = models.TeacherExtra.objects.get(user=request.user)
            
            # Classes taught
            classes_taught = models.Assignment.objects.filter(
                teacher=teacher
            ).values('class_name').distinct()
            
            # Recent assignments created
            recent_assignments = models.Assignment.objects.filter(
                teacher=teacher
            ).order_by('-created_at')[:5]
            
            # Recent notifications
            recent_notifications = models.Notification.objects.filter(
                recipient=request.user
            ).order_by('-created_at')[:5]
            
            return Response({
                'classes_taught': list(classes_taught),
                'recent_assignments': serializers.AssignmentSerializer(recent_assignments, many=True).data,
                'recent_notifications': serializers.NotificationSerializer(recent_notifications, many=True).data
            })
        except models.TeacherExtra.DoesNotExist:
            return Response({'error': 'Teacher profile not found'}, status=status.HTTP_404_NOT_FOUND)
