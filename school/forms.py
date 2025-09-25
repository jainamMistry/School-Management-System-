from django import forms
from django.contrib.auth.models import User
from . import models

# Import classes from models
classes = models.classes

#for admin
class AdminSigupForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']


#for student related form
class StudentUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
class StudentExtraForm(forms.ModelForm):
    class Meta:
        model=models.StudentExtra
        fields=['roll','cl','mobile','fee','status']



#for teacher related form
class TeacherUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
class TeacherExtraForm(forms.ModelForm):
    class Meta:
        model=models.TeacherExtra
        fields=['salary','mobile','status']




#for Attendance related form
presence_choices=(('Present','Present'),('Absent','Absent'))
class AttendanceForm(forms.Form):
    present_status=forms.ChoiceField( choices=presence_choices)
    date=forms.DateField()

class AskDateForm(forms.Form):
    date=forms.DateField()




#for notice related form
class NoticeForm(forms.ModelForm):
    class Meta:
        model=models.Notice
        fields='__all__'



#for contact us page
class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))


# Advanced Forms for New Features

class SubjectForm(forms.ModelForm):
    class Meta:
        model = models.Subject
        fields = ['name', 'code', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'cols': 30}),
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = models.Assignment
        fields = ['title', 'description', 'subject', 'class_name', 'due_date', 'max_marks']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 30}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = models.AssignmentSubmission
        fields = ['submission_file', 'submission_text']
        widgets = {
            'submission_text': forms.Textarea(attrs={'rows': 5, 'cols': 30}),
        }


class ExamForm(forms.ModelForm):
    class Meta:
        model = models.Exam
        fields = ['name', 'exam_type', 'subject', 'class_name', 'exam_date', 'duration_minutes', 'max_marks', 'instructions']
        widgets = {
            'exam_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'instructions': forms.Textarea(attrs={'rows': 4, 'cols': 30}),
        }


class ExamResultForm(forms.ModelForm):
    class Meta:
        model = models.ExamResult
        fields = ['marks_obtained', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3, 'cols': 30}),
        }


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = models.FeePayment
        fields = ['amount', 'due_date', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'cols': 30}),
        }


class LibraryBookForm(forms.ModelForm):
    class Meta:
        model = models.LibraryBook
        fields = ['title', 'author', 'isbn', 'category', 'publisher', 'publication_year', 'pages']


class BookBorrowingForm(forms.ModelForm):
    class Meta:
        model = models.BookBorrowing
        fields = ['book', 'borrower', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class SchoolEventForm(forms.ModelForm):
    class Meta:
        model = models.SchoolEvent
        fields = ['title', 'description', 'event_type', 'start_date', 'end_date', 'location', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 30}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class StudentPerformanceForm(forms.ModelForm):
    class Meta:
        model = models.StudentPerformance
        fields = ['student', 'subject', 'semester', 'attendance_percentage', 'average_marks', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3, 'cols': 30}),
        }


class NotificationForm(forms.ModelForm):
    class Meta:
        model = models.Notification
        fields = ['title', 'message', 'notification_type', 'recipient', 'expires_at']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'cols': 30}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class AdvancedSearchForm(forms.Form):
    SEARCH_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
        ('book', 'Library Book'),
        ('event', 'Event'),
    ]
    
    search_type = forms.ChoiceField(choices=SEARCH_CHOICES)
    query = forms.CharField(max_length=200, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    class_name = forms.ChoiceField(choices=classes, required=False)
    status = forms.ChoiceField(choices=[('', 'All'), ('active', 'Active'), ('inactive', 'Inactive')], required=False)


class BulkUploadForm(forms.Form):
    file = forms.FileField(help_text="Upload CSV or Excel file")
    upload_type = forms.ChoiceField(choices=[
        ('students', 'Students'),
        ('teachers', 'Teachers'),
        ('subjects', 'Subjects'),
        ('books', 'Library Books'),
    ])


class ReportForm(forms.Form):
    REPORT_TYPES = [
        ('attendance', 'Attendance Report'),
        ('performance', 'Performance Report'),
        ('fee', 'Fee Report'),
        ('library', 'Library Report'),
        ('exam', 'Exam Report'),
    ]
    
    report_type = forms.ChoiceField(choices=REPORT_TYPES)
    class_name = forms.ChoiceField(choices=classes, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    format = forms.ChoiceField(choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV')], initial='pdf')
