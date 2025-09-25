import logging
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.http import HttpResponse
import openpyxl
from openpyxl.styles import Font, Alignment

from . import models

logger = logging.getLogger('school')
channel_layer = get_channel_layer()


@shared_task
def send_notification_email(user_id, title, message, notification_type):
    """Send email notification to user"""
    try:
        user = models.User.objects.get(id=user_id)
        
        # Create notification in database
        notification = models.Notification.objects.create(
            title=title,
            message=message,
            notification_type=notification_type,
            recipient=user
        )
        
        # Send real-time notification via WebSocket
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                'type': 'notification_message',
                'title': title,
                'message': message,
                'notification_type': notification_type,
                'created_at': notification.created_at.isoformat()
            }
        )
        
        # Send email if user has email
        if user.email:
            send_mail(
                subject=f"School Management System - {title}",
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=True,
            )
        
        logger.info(f"Notification sent to user {user.username}")
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")


@shared_task
def send_attendance_reminder():
    """Send attendance reminder to teachers"""
    try:
        teachers = models.TeacherExtra.objects.filter(status=True)
        for teacher in teachers:
            send_notification_email.delay(
                teacher.user.id,
                "Attendance Reminder",
                "Please mark attendance for your classes today.",
                "attendance"
            )
        logger.info("Attendance reminders sent to all teachers")
    except Exception as e:
        logger.error(f"Error sending attendance reminders: {str(e)}")


@shared_task
def send_assignment_reminder():
    """Send assignment due date reminders"""
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        assignments = models.Assignment.objects.filter(
            due_date__date=tomorrow.date(),
            is_active=True
        )
        
        for assignment in assignments:
            students = models.StudentExtra.objects.filter(
                cl=assignment.class_name,
                status=True
            )
            
            for student in students:
                send_notification_email.delay(
                    student.user.id,
                    f"Assignment Due Tomorrow: {assignment.title}",
                    f"Assignment '{assignment.title}' is due tomorrow. Please submit it on time.",
                    "assignment"
                )
        
        logger.info(f"Assignment reminders sent for {assignments.count()} assignments")
    except Exception as e:
        logger.error(f"Error sending assignment reminders: {str(e)}")


@shared_task
def send_fee_reminder():
    """Send fee payment reminders"""
    try:
        overdue_payments = models.FeePayment.objects.filter(
            status='pending',
            due_date__lt=timezone.now().date()
        )
        
        for payment in overdue_payments:
            send_notification_email.delay(
                payment.student.user.id,
                "Fee Payment Overdue",
                f"Your fee payment of ${payment.amount} is overdue. Please make the payment as soon as possible.",
                "fee"
            )
        
        logger.info(f"Fee reminders sent for {overdue_payments.count()} overdue payments")
    except Exception as e:
        logger.error(f"Error sending fee reminders: {str(e)}")


def generate_attendance_report(class_name, date_from, date_to, format='pdf'):
    """Generate attendance report"""
    try:
        attendance_data = models.Attendance.objects.filter(
            cl=class_name,
            date__range=[date_from, date_to]
        ).order_by('date', 'roll')
        
        if format == 'pdf':
            return generate_pdf_attendance_report(attendance_data, class_name, date_from, date_to)
        elif format == 'excel':
            return generate_excel_attendance_report(attendance_data, class_name, date_from, date_to)
        elif format == 'csv':
            return generate_csv_attendance_report(attendance_data, class_name, date_from, date_to)
    except Exception as e:
        logger.error(f"Error generating attendance report: {str(e)}")
        return None


def generate_pdf_attendance_report(attendance_data, class_name, date_from, date_to):
    """Generate PDF attendance report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph(f"Attendance Report - Class {class_name}", title_style))
    story.append(Paragraph(f"Period: {date_from} to {date_to}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Calculate statistics
    total_records = attendance_data.count()
    present_count = attendance_data.filter(present_status='Present').count()
    absent_count = attendance_data.filter(present_status='Absent').count()
    attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
    
    # Statistics table
    stats_data = [
        ['Total Records', str(total_records)],
        ['Present', str(present_count)],
        ['Absent', str(absent_count)],
        ['Attendance %', f"{attendance_percentage:.2f}%"]
    ]
    
    stats_table = Table(stats_data, colWidths=[200, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Detailed attendance table
    if attendance_data.exists():
        # Get unique dates and rolls
        dates = sorted(attendance_data.values_list('date', flat=True).distinct())
        rolls = sorted(attendance_data.values_list('roll', flat=True).distinct())
        
        # Create table headers
        table_data = [['Roll'] + [str(date) for date in dates]]
        
        # Create table rows
        for roll in rolls:
            row = [str(roll)]
            for date in dates:
                try:
                    record = attendance_data.get(roll=roll, date=date)
                    row.append('P' if record.present_status == 'Present' else 'A')
                except models.Attendance.DoesNotExist:
                    row.append('-')
            table_data.append(row)
        
        # Create table
        attendance_table = Table(table_data, colWidths=[60] + [40] * len(dates))
        attendance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8)
        ]))
        
        story.append(attendance_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_excel_attendance_report(attendance_data, class_name, date_from, date_to):
    """Generate Excel attendance report"""
    buffer = BytesIO()
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = f"Attendance Report - Class {class_name}"
    
    # Title
    worksheet['A1'] = f"Attendance Report - Class {class_name}"
    worksheet['A2'] = f"Period: {date_from} to {date_to}"
    
    # Statistics
    total_records = attendance_data.count()
    present_count = attendance_data.filter(present_status='Present').count()
    absent_count = attendance_data.filter(present_status='Absent').count()
    attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
    
    worksheet['A4'] = 'Total Records'
    worksheet['B4'] = total_records
    worksheet['A5'] = 'Present'
    worksheet['B5'] = present_count
    worksheet['A6'] = 'Absent'
    worksheet['B6'] = absent_count
    worksheet['A7'] = 'Attendance %'
    worksheet['B7'] = f"{attendance_percentage:.2f}%"
    
    # Detailed data
    if attendance_data.exists():
        dates = sorted(attendance_data.values_list('date', flat=True).distinct())
        rolls = sorted(attendance_data.values_list('roll', flat=True).distinct())
        
        # Headers
        row = 9
        worksheet[f'A{row}'] = 'Roll'
        for i, date in enumerate(dates):
            worksheet[f'{chr(66+i)}{row}'] = str(date)
        
        # Data rows
        for roll in rolls:
            row += 1
            worksheet[f'A{row}'] = str(roll)
            for i, date in enumerate(dates):
                try:
                    record = attendance_data.get(roll=roll, date=date)
                    worksheet[f'{chr(66+i)}{row}'] = 'P' if record.present_status == 'Present' else 'A'
                except models.Attendance.DoesNotExist:
                    worksheet[f'{chr(66+i)}{row}'] = '-'
    
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def generate_csv_attendance_report(attendance_data, class_name, date_from, date_to):
    """Generate CSV attendance report"""
    buffer = BytesIO()
    
    # Create DataFrame
    data = []
    for record in attendance_data:
        data.append({
            'Roll': record.roll,
            'Date': record.date,
            'Class': record.cl,
            'Status': record.present_status
        })
    
    df = pd.DataFrame(data)
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer


def bulk_import_students(file_path):
    """Bulk import students from Excel/CSV file"""
    try:
        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Create user
                user = models.User.objects.create_user(
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    email=row.get('email', ''),
                    password=row['password']
                )
                
                # Create student extra
                student_extra = models.StudentExtra.objects.create(
                    user=user,
                    roll=row['roll'],
                    mobile=row.get('mobile', ''),
                    fee=row.get('fee', 0),
                    cl=row.get('class', 'one'),
                    status=True
                )
                
                # Add to student group
                from django.contrib.auth.models import Group
                student_group = Group.objects.get_or_create(name='STUDENT')[0]
                student_group.user_set.add(user)
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'imported_count': imported_count,
            'errors': errors,
            'success': True
        }
        
    except Exception as e:
        return {
            'imported_count': 0,
            'errors': [str(e)],
            'success': False
        }


def calculate_student_performance(student_id, semester):
    """Calculate student performance metrics"""
    try:
        student = models.StudentExtra.objects.get(id=student_id)
        
        # Get attendance data
        attendance_records = models.Attendance.objects.filter(
            cl=student.cl,
            roll=student.roll
        )
        total_days = attendance_records.count()
        present_days = attendance_records.filter(present_status='Present').count()
        attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Get exam results
        exam_results = models.ExamResult.objects.filter(student=student)
        if exam_results.exists():
            average_marks = exam_results.aggregate(avg_marks=models.Avg('marks_obtained'))['avg_marks']
            
            # Calculate grade
            if average_marks >= 90:
                grade = 'A+'
            elif average_marks >= 80:
                grade = 'A'
            elif average_marks >= 70:
                grade = 'B+'
            elif average_marks >= 60:
                grade = 'B'
            elif average_marks >= 50:
                grade = 'C'
            else:
                grade = 'F'
        else:
            average_marks = 0
            grade = 'N/A'
        
        # Create or update performance record
        performance, created = models.StudentPerformance.objects.get_or_create(
            student=student,
            semester=semester,
            defaults={
                'attendance_percentage': attendance_percentage,
                'average_marks': average_marks,
                'grade': grade
            }
        )
        
        if not created:
            performance.attendance_percentage = attendance_percentage
            performance.average_marks = average_marks
            performance.grade = grade
            performance.save()
        
        return performance
        
    except Exception as e:
        logger.error(f"Error calculating student performance: {str(e)}")
        return None


def send_real_time_attendance_update(class_name, date, total_students, present_count, absent_count):
    """Send real-time attendance update via WebSocket"""
    try:
        async_to_sync(channel_layer.group_send)(
            "attendance_updates",
            {
                'type': 'attendance_update',
                'class_name': class_name,
                'date': date.isoformat(),
                'total_students': total_students,
                'present_count': present_count,
                'absent_count': absent_count
            }
        )
    except Exception as e:
        logger.error(f"Error sending real-time attendance update: {str(e)}")


def generate_qr_code_for_student(student_id):
    """Generate QR code for student ID"""
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        student = models.StudentExtra.objects.get(id=student_id)
        qr_data = f"Student ID: {student.id}\nName: {student.get_name}\nRoll: {student.roll}\nClass: {student.cl}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Convert to base64 for embedding in HTML
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        return qr_base64
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None
