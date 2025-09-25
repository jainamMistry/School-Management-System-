"""

"""
from django.contrib import admin
from django.urls import path, include
from school import views
from django.contrib.auth.views import LoginView,LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home_view,name=''),

    path('adminclick', views.adminclick_view),
    path('teacherclick', views.teacherclick_view),
    path('studentclick', views.studentclick_view),


    path('adminsignup', views.admin_signup_view),
    path('studentsignup', views.student_signup_view,name='studentsignup'),
    path('teachersignup', views.teacher_signup_view),
    path('adminlogin', LoginView.as_view(template_name='school/adminlogin.html', redirect_authenticated_user=True)),
    path('studentlogin', LoginView.as_view(template_name='school/studentlogin.html', redirect_authenticated_user=True)),
    path('teacherlogin', LoginView.as_view(template_name='school/teacherlogin.html', redirect_authenticated_user=True)),


    path('afterlogin', views.afterlogin_view,name='afterlogin'),
    path('logout', views.logout_view, name='logout'),


    path('admin-dashboard', views.admin_dashboard_view,name='admin-dashboard'),



    path('admin-teacher', views.admin_teacher_view,name='admin-teacher'),
    path('admin-add-teacher', views.admin_add_teacher_view,name='admin-add-teacher'),
    path('admin-view-teacher', views.admin_view_teacher_view,name='admin-view-teacher'),
    path('admin-approve-teacher', views.admin_approve_teacher_view,name='admin-approve-teacher'),
    path('approve-teacher/<int:pk>', views.approve_teacher_view,name='approve-teacher'),
    path('delete-teacher/<int:pk>', views.delete_teacher_view,name='delete-teacher'),
    path('delete-teacher-from-school/<int:pk>', views.delete_teacher_from_school_view,name='delete-teacher-from-school'),
    path('update-teacher/<int:pk>', views.update_teacher_view,name='update-teacher'),
    path('admin-view-teacher-salary', views.admin_view_teacher_salary_view,name='admin-view-teacher-salary'),


    path('admin-student', views.admin_student_view,name='admin-student'),
    path('admin-add-student', views.admin_add_student_view,name='admin-add-student'),
    path('admin-view-student', views.admin_view_student_view,name='admin-view-student'),
    path('delete-student-from-school/<int:pk>', views.delete_student_from_school_view,name='delete-student-from-school'),
    path('delete-student/<int:pk>', views.delete_student_view,name='delete-student'),
    path('update-student/<int:pk>', views.update_student_view,name='update-student'),
    path('admin-approve-student', views.admin_approve_student_view,name='admin-approve-student'),
    path('approve-student/<int:pk>', views.approve_student_view,name='approve-student'),
    path('admin-view-student-fee', views.admin_view_student_fee_view,name='admin-view-student-fee'),


    path('admin-attendance', views.admin_attendance_view,name='admin-attendance'),
    path('admin-take-attendance/<str:cl>', views.admin_take_attendance_view,name='admin-take-attendance'),
    path('admin-view-attendance/<str:cl>', views.admin_view_attendance_view,name='admin-view-attendance'),
    path('admin-export-attendance/<str:cl>', views.admin_export_attendance_csv, name='admin-export-attendance'),


    path('admin-fee', views.admin_fee_view,name='admin-fee'),
    path('admin-view-fee/<str:cl>', views.admin_view_fee_view,name='admin-view-fee'),

    path('admin-notice', views.admin_notice_view,name='admin-notice'),



    path('teacher-dashboard', views.teacher_dashboard_view,name='teacher-dashboard'),
    path('teacher-attendance', views.teacher_attendance_view,name='teacher-attendance'),
    path('teacher-take-attendance/<str:cl>', views.teacher_take_attendance_view,name='teacher-take-attendance'),
    path('teacher-view-attendance/<str:cl>', views.teacher_view_attendance_view,name='teacher-view-attendance'),
    path('teacher-export-attendance/<str:cl>', views.teacher_export_attendance_csv, name='teacher-export-attendance'),
    path('teacher-notice', views.teacher_notice_view,name='teacher-notice'),

    path('student-dashboard', views.student_dashboard_view,name='student-dashboard'),
    path('student-attendance', views.student_attendance_view,name='student-attendance'),




    path('aboutus', views.aboutus_view),
    path('contactus', views.contactus_view),
    
    # Advanced Features URLs
    path('advanced-analytics', views.advanced_analytics_view, name='advanced-analytics'),
    
    # Assignment Management
    path('teacher-assignments', views.teacher_assignments_view, name='teacher-assignments'),
    path('create-assignment', views.create_assignment_view, name='create-assignment'),
    path('student-assignments', views.student_assignments_view, name='student-assignments'),
    path('submit-assignment/<int:assignment_id>', views.submit_assignment_view, name='submit-assignment'),
    
    # Library Management
    path('library-management', views.library_management_view, name='library-management'),
    path('add-book', views.add_book_view, name='add-book'),
    path('borrow-book', views.borrow_book_view, name='borrow-book'),
    
    # Event Management
    path('event-management', views.event_management_view, name='event-management'),
    path('create-event', views.create_event_view, name='create-event'),
    
    # Advanced Search
    path('advanced-search', views.advanced_search_view, name='advanced-search'),
    
    # Bulk Upload
    path('bulk-upload', views.bulk_upload_view, name='bulk-upload'),
    
    # Report Generation
    path('generate-report', views.generate_report_view, name='generate-report'),
    
    # Notifications
    path('notifications', views.notifications_view, name='notifications'),
    path('mark-notification-read/<int:notification_id>', views.mark_notification_read, name='mark-notification-read'),
    
    # QR Codes
    path('student-qr-codes', views.student_qr_codes_view, name='student-qr-codes'),
    
    # Performance Analytics
    path('performance-analytics', views.performance_analytics_view, name='performance-analytics'),
    
    # System Settings
    path('system-settings', views.system_settings_view, name='system-settings'),
    
    # API Endpoints
    path('api/dashboard-stats', views.api_dashboard_stats, name='api-dashboard-stats'),
    path('api/send-notification', views.api_send_notification, name='api-send-notification'),
    
    # REST API (commented out for migration creation)
    # path('', include('school.api_urls')),
]
