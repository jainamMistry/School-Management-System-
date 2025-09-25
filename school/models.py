from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class TeacherExtra(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    salary = models.PositiveIntegerField(null=False)
    joindate=models.DateField(auto_now_add=True)
    mobile = models.CharField(max_length=40)
    status=models.BooleanField(default=False)
    def __str__(self):
        return self.user.first_name
    @property
    def get_id(self):
        return self.user.id
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name




classes=[('one','one'),('two','two'),('three','three'),
('four','four'),('five','five'),('six','six'),('seven','seven'),('eight','eight'),('nine','nine'),('ten','ten')]
class StudentExtra(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    roll = models.CharField(max_length=10)
    mobile = models.CharField(max_length=40,null=True)
    fee=models.PositiveIntegerField(null=True)
    cl= models.CharField(max_length=10,choices=classes,default='one')
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return self.user.first_name



class Attendance(models.Model):
    roll=models.CharField(max_length=10,null=True)
    date=models.DateField()
    cl=models.CharField(max_length=10)
    present_status = models.CharField(max_length=10)



class Notice(models.Model):
    date=models.DateField(auto_now=True)
    by=models.CharField(max_length=20,null=True,default='school')
    message=models.CharField(max_length=500)


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = self.user.username if self.user else 'anon'
        return f"{self.method} {self.path} [{self.status_code}] by {username}"


# Advanced Features Models

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherExtra, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=10, choices=classes)
    due_date = models.DateTimeField()
    max_marks = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.subject.name}"


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentExtra, on_delete=models.CASCADE)
    submission_file = models.FileField(upload_to='assignments/submissions/')
    submission_text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_graded = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.get_name} - {self.assignment.title}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('assignment', 'Assignment'),
        ('attendance', 'Attendance'),
        ('fee', 'Fee'),
        ('general', 'General'),
        ('exam', 'Exam'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"


class Exam(models.Model):
    EXAM_TYPES = [
        ('midterm', 'Midterm'),
        ('final', 'Final'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]
    
    name = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=10, choices=classes)
    exam_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    max_marks = models.PositiveIntegerField()
    instructions = models.TextField()
    created_by = models.ForeignKey(TeacherExtra, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.subject.name}"


class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentExtra, on_delete=models.CASCADE)
    marks_obtained = models.PositiveIntegerField()
    grade = models.CharField(max_length=2, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Auto-calculate grade based on marks
        percentage = (self.marks_obtained / self.exam.max_marks) * 100
        if percentage >= 90:
            self.grade = 'A+'
        elif percentage >= 80:
            self.grade = 'A'
        elif percentage >= 70:
            self.grade = 'B+'
        elif percentage >= 60:
            self.grade = 'B'
        elif percentage >= 50:
            self.grade = 'C'
        else:
            self.grade = 'F'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.get_name} - {self.exam.name}"


class FeePayment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    student = models.ForeignKey(StudentExtra, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.get_name} - {self.amount}"


class LibraryBook(models.Model):
    BOOK_STATUS = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=50)
    publisher = models.CharField(max_length=100)
    publication_year = models.PositiveIntegerField()
    pages = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=BOOK_STATUS, default='available')
    added_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.author}"


class BookBorrowing(models.Model):
    book = models.ForeignKey(LibraryBook, on_delete=models.CASCADE)
    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_returned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.borrower.username} - {self.book.title}"


class SchoolEvent(models.Model):
    EVENT_TYPES = [
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('social', 'Social'),
        ('holiday', 'Holiday'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.start_date.date()}"


class StudentPerformance(models.Model):
    student = models.ForeignKey(StudentExtra, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    average_marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.get_name} - {self.subject.name}"


class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.key}: {self.value}"
