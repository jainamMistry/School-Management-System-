from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'teachers', api_views.TeacherViewSet)
router.register(r'students', api_views.StudentViewSet)
router.register(r'subjects', api_views.SubjectViewSet)
router.register(r'assignments', api_views.AssignmentViewSet)
router.register(r'assignment-submissions', api_views.AssignmentSubmissionViewSet)
router.register(r'notifications', api_views.NotificationViewSet)
router.register(r'exams', api_views.ExamViewSet)
router.register(r'exam-results', api_views.ExamResultViewSet)
router.register(r'fee-payments', api_views.FeePaymentViewSet)
router.register(r'library-books', api_views.LibraryBookViewSet)
router.register(r'book-borrowings', api_views.BookBorrowingViewSet)
router.register(r'events', api_views.SchoolEventViewSet)
router.register(r'attendance', api_views.AttendanceViewSet)
router.register(r'dashboard', api_views.DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
