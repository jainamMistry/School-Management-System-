from django.shortcuts import render,redirect,reverse, get_object_or_404
from . import forms,models
# from . import services  # Commented out for migration creation
from django.db.models import Sum, Avg, Count, Q
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout as auth_logout
from django.utils.deprecation import MiddlewareMixin
from django.http import StreamingHttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import logging
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync

logger = logging.getLogger('school')
# channel_layer = get_channel_layer()

@never_cache
def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'school/index.html')



#for showing signup/login button for teacher
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'school/adminclick.html')


#for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'school/teacherclick.html')


#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'school/studentclick.html')





def admin_signup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()


            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)

            return HttpResponseRedirect('adminlogin')
    return render(request,'school/adminsignup.html',{'form':form})




def student_signup_view(request):
    form1=forms.StudentUserForm()
    form2=forms.StudentExtraForm()
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.StudentUserForm(request.POST)
        form2=forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            f2.user=user
            f2.status=True
            user2=f2.save()

            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)

            return HttpResponseRedirect('studentlogin')
        else:
            mydict={'form1':form1,'form2':form2}
            return render(request,'school/studentsignup.html',context=mydict)
    return render(request,'school/studentsignup.html',context=mydict)


def teacher_signup_view(request):
    form1=forms.TeacherUserForm()
    form2=forms.TeacherExtraForm()
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.TeacherUserForm(request.POST)
        form2=forms.TeacherExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            f2.user=user
            f2.status=True
            user2=f2.save()

            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)

            return HttpResponseRedirect('teacherlogin')
        else:
            mydict={'form1':form1,'form2':form2}
            return render(request,'school/teachersignup.html',context=mydict)
    return render(request,'school/teachersignup.html',context=mydict)






#for checking user is techer , student or admin
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_teacher(user):
    if user.groups.filter(name='TEACHER').exists():
        return True
    try:
        return models.TeacherExtra.objects.filter(user_id=user.id).exists()
    except Exception:
        return False
def is_student(user):
    if user.groups.filter(name='STUDENT').exists():
        return True
    try:
        return models.StudentExtra.objects.filter(user_id=user.id).exists()
    except Exception:
        return False


@never_cache
def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_teacher(request.user):
        return redirect('teacher-dashboard')
    elif is_student(request.user):
        return redirect('student-dashboard')
    else:
        return HttpResponseRedirect('/')


@never_cache
def logout_view(request):
    auth_logout(request)
    return redirect('/')


# Simple audit logging middleware implementation colocated for brevity
class AuditLoggingMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            from .models import AuditLog
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            AuditLog.objects.create(
                user=user,
                path=request.path[:255],
                method=getattr(request, 'method', 'GET')[:10],
                status_code=getattr(response, 'status_code', 0),
            )
        except Exception:
            pass
        return response



#for dashboard of adminnnnnnnnnnnnnnnnnnnn

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_dashboard_view(request):
    teachercount=models.TeacherExtra.objects.all().filter(status=True).count()
    pendingteachercount=models.TeacherExtra.objects.all().filter(status=False).count()

    studentcount=models.StudentExtra.objects.all().filter(status=True).count()
    pendingstudentcount=models.StudentExtra.objects.all().filter(status=False).count()

    teachersalary=models.TeacherExtra.objects.filter(status=True).aggregate(Sum('salary'))
    pendingteachersalary=models.TeacherExtra.objects.filter(status=False).aggregate(Sum('salary'))

    studentfee=models.StudentExtra.objects.filter(status=True).aggregate(Sum('fee',default=0))
    pendingstudentfee=models.StudentExtra.objects.filter(status=False).aggregate(Sum('fee'))

    notice=models.Notice.objects.all()

    #aggregate function return dictionary so fetch data from dictionay
    mydict={
        'teachercount':teachercount,
        'pendingteachercount':pendingteachercount,

        'studentcount':studentcount,
        'pendingstudentcount':pendingstudentcount,

        'teachersalary':teachersalary['salary__sum'],
        'pendingteachersalary':pendingteachersalary['salary__sum'],

        'studentfee':studentfee['fee__sum'],
        'pendingstudentfee':pendingstudentfee['fee__sum'],

        'notice':notice

    }

    return render(request,'school/admin_dashboard.html',context=mydict)







#for teacher sectionnnnnnnn by adminnnnnnnnnnnnnnnnnnnnnnnn

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_teacher_view(request):
    return render(request,'school/admin_teacher.html')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_add_teacher_view(request):
    form1=forms.TeacherUserForm()
    form2=forms.TeacherExtraForm()
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.TeacherUserForm(request.POST)
        form2=forms.TeacherExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()

            f2=form2.save(commit=False)
            f2.user=user
            f2.status=True
            f2.save()

            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-teacher')
    return render(request,'school/admin_add_teacher.html',context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_view_teacher_view(request):
    from django.core.paginator import Paginator
    teacher_qs=models.TeacherExtra.objects.all().filter(status=True).order_by('user__first_name')
    paginator = Paginator(teacher_qs, 10)
    page_number = request.GET.get('page')
    teachers = paginator.get_page(page_number)
    return render(request,'school/admin_view_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_approve_teacher_view(request):
    teachers=models.TeacherExtra.objects.all().filter(status=False)
    return render(request,'school/admin_approve_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def approve_teacher_view(request,pk):
    teacher=models.TeacherExtra.objects.get(id=pk)
    teacher.status=True
    teacher.save()
    return redirect(reverse('admin-approve-teacher'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def delete_teacher_view(request,pk):
    teacher=models.TeacherExtra.objects.get(id=pk)
    user=models.User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return redirect('admin-approve-teacher')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def delete_teacher_from_school_view(request,pk):
    teacher=models.TeacherExtra.objects.get(id=pk)
    user=models.User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return redirect('admin-view-teacher')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def update_teacher_view(request,pk):
    teacher=models.TeacherExtra.objects.get(id=pk)
    user=models.User.objects.get(id=teacher.user_id)

    form1=forms.TeacherUserForm(instance=user)
    form2=forms.TeacherExtraForm(instance=teacher)
    mydict={'form1':form1,'form2':form2}

    if request.method=='POST':
        form1=forms.TeacherUserForm(request.POST,instance=user)
        form2=forms.TeacherExtraForm(request.POST,instance=teacher)
        print(form1)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            f2.status=True
            f2.save()
            return redirect('admin-view-teacher')
    return render(request,'school/admin_update_teacher.html',context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_view_teacher_salary_view(request):
    teachers=models.TeacherExtra.objects.all()
    return render(request,'school/admin_view_teacher_salary.html',{'teachers':teachers})






#for student by adminnnnnnnnnnnnnnnnnnnnnnnnnnn

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_student_view(request):
    return render(request,'school/admin_student.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_add_student_view(request):
    form1=forms.StudentUserForm()
    form2=forms.StudentExtraForm()
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.StudentUserForm(request.POST)
        form2=forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            print("form is valid")
            user=form1.save()
            user.set_password(user.password)
            user.save()

            f2=form2.save(commit=False)
            f2.user=user
            f2.status=True
            f2.save()

            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
        else:
            print("form is invalid")
        return HttpResponseRedirect('admin-student')
    return render(request,'school/admin_add_student.html',context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_view_student_view(request):
    from django.core.paginator import Paginator
    student_qs=models.StudentExtra.objects.all().filter(status=True).order_by('user__first_name')
    paginator = Paginator(student_qs, 10)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    return render(request,'school/admin_view_student.html',{'students':students})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def delete_student_from_school_view(request,pk):
    student=models.StudentExtra.objects.get(id=pk)
    user=models.User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return redirect('admin-view-student')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def delete_student_view(request,pk):
    student=models.StudentExtra.objects.get(id=pk)
    user=models.User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return redirect('admin-approve-student')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def update_student_view(request,pk):
    student=models.StudentExtra.objects.get(id=pk)
    user=models.User.objects.get(id=student.user_id)
    form1=forms.StudentUserForm(instance=user)
    form2=forms.StudentExtraForm(instance=student)
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.StudentUserForm(request.POST,instance=user)
        form2=forms.StudentExtraForm(request.POST,instance=student)
        print(form1)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            f2.status=True
            f2.save()
            return redirect('admin-view-student')
    return render(request,'school/admin_update_student.html',context=mydict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_approve_student_view(request):
    students=models.StudentExtra.objects.all().filter(status=False)
    return render(request,'school/admin_approve_student.html',{'students':students})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def approve_student_view(request,pk):
    students=models.StudentExtra.objects.get(id=pk)
    students.status=True
    students.save()
    return redirect(reverse('admin-approve-student'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_view_student_fee_view(request):
    students=models.StudentExtra.objects.all()
    return render(request,'school/admin_view_student_fee.html',{'students':students})






#attendance related viewwwwwwwwwwwwwwwwwwwwwwwww
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_attendance_view(request):
    return render(request,'school/admin_attendance.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_take_attendance_view(request,cl):
    students=models.StudentExtra.objects.all().filter(cl=cl).order_by('roll')
    print(students)
    aform=forms.AttendanceForm()
    if request.method=='POST':
        form=forms.AttendanceForm(request.POST)
        if form.is_valid():
            Attendances=request.POST.getlist('present_status')
            date=form.cleaned_data['date']
            # Overwrite existing attendance for this class and date
            models.Attendance.objects.filter(date=date, cl=cl).delete()
            for i in range(len(Attendances)):
                AttendanceModel=models.Attendance()
                AttendanceModel.cl=cl
                AttendanceModel.date=date
                AttendanceModel.present_status=Attendances[i]
                AttendanceModel.roll=students[i].roll
                AttendanceModel.save()
            return redirect('admin-attendance')
        else:
            print('form invalid')
    return render(request,'school/admin_take_attendance.html',{'students':students,'aform':aform})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_view_attendance_view(request,cl):
    form=forms.AskDateForm()
    if request.method=='POST':
        form=forms.AskDateForm(request.POST)
        if form.is_valid():
            date=form.cleaned_data['date']
            attendancedata=models.Attendance.objects.all().filter(date=date,cl=cl)
            studentdata=models.StudentExtra.objects.all().filter(cl=cl)
            mylist=zip(attendancedata,studentdata)
            return render(request,'school/admin_view_attendance_page.html',{'cl':cl,'mylist':mylist,'date':date})
        else:
            print('form invalid')
    return render(request,'school/admin_view_attendance_ask_date.html',{'cl':cl,'form':form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_export_attendance_csv(request, cl):
    from datetime import datetime
    date_str = request.GET.get('date')
    if not date_str:
        return redirect('admin-view-attendance', cl=cl)
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return redirect('admin-view-attendance', cl=cl)

    rows = models.Attendance.objects.filter(cl=cl, date=date).order_by('roll')

    def row_iter():
        yield 'roll,class,date,status\n'
        for r in rows:
            yield f"{r.roll},{r.cl},{r.date},{r.present_status}\n"

    response = StreamingHttpResponse(row_iter(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{cl}_{date}.csv"'
    return response









#fee related view by adminnnnnnnnnnnnnnnnnnn
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_fee_view(request):
    return render(request,'school/admin_fee.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_view_fee_view(request,cl):
    feedetails=models.StudentExtra.objects.all().filter(cl=cl)
    return render(request,'school/admin_view_fee.html',{'feedetails':feedetails,'cl':cl})








#notice related viewsssssssssssssssssssss
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def admin_notice_view(request):
    form=forms.NoticeForm()
    if request.method=='POST':
        form=forms.NoticeForm(request.POST)
        if form.is_valid():
            form=form.save(commit=False)
            form.by=request.user.first_name
            form.save()
            return redirect('admin-dashboard')
    return render(request,'school/admin_notice.html',{'form':form})








#for TEACHER  LOGIN    SECTIONNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def teacher_dashboard_view(request):
    teacherdata=models.TeacherExtra.objects.all().filter(user_id=request.user.id)
    notice=models.Notice.objects.all()
    mydict={
        'salary':teacherdata[0].salary,
        'mobile':teacherdata[0].mobile,
        'date':teacherdata[0].joindate,
        'notice':notice
    }
    return render(request,'school/teacher_dashboard.html',context=mydict)



@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def teacher_attendance_view(request):
    return render(request,'school/teacher_attendance.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def teacher_take_attendance_view(request,cl):
    students=models.StudentExtra.objects.all().filter(cl=cl).order_by('roll')
    aform=forms.AttendanceForm()
    if request.method=='POST':
        form=forms.AttendanceForm(request.POST)
        if form.is_valid():
            Attendances=request.POST.getlist('present_status')
            date=form.cleaned_data['date']
            # Overwrite existing attendance for this class and date
            models.Attendance.objects.filter(date=date, cl=cl).delete()
            for i in range(len(Attendances)):
                AttendanceModel=models.Attendance()
                AttendanceModel.cl=cl
                AttendanceModel.date=date
                AttendanceModel.present_status=Attendances[i]
                AttendanceModel.roll=students[i].roll
                AttendanceModel.save()
            return redirect('teacher-attendance')
        else:
            print('form invalid')
    return render(request,'school/teacher_take_attendance.html',{'students':students,'aform':aform})



@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def teacher_view_attendance_view(request,cl):
    form=forms.AskDateForm()
    if request.method=='POST':
        form=forms.AskDateForm(request.POST)
        if form.is_valid():
            date=form.cleaned_data['date']
            attendancedata=models.Attendance.objects.all().filter(date=date,cl=cl)
            studentdata=models.StudentExtra.objects.all().filter(cl=cl)
            mylist=zip(attendancedata,studentdata)
            return render(request,'school/teacher_view_attendance_page.html',{'cl':cl,'mylist':mylist,'date':date})
        else:
            print('form invalid')
    return render(request,'school/teacher_view_attendance_ask_date.html',{'cl':cl,'form':form})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def teacher_export_attendance_csv(request, cl):
    from datetime import datetime
    date_str = request.GET.get('date')
    if not date_str:
        return redirect('teacher-view-attendance', cl=cl)
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return redirect('teacher-view-attendance', cl=cl)

    rows = models.Attendance.objects.filter(cl=cl, date=date).order_by('roll')

    def row_iter():
        yield 'roll,class,date,status\n'
        for r in rows:
            yield f"{r.roll},{r.cl},{r.date},{r.present_status}\n"

    response = StreamingHttpResponse(row_iter(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{cl}_{date}.csv"'
    return response



@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def teacher_notice_view(request):
    form=forms.NoticeForm()
    if request.method=='POST':
        form=forms.NoticeForm(request.POST)
        if form.is_valid():
            form=form.save(commit=False)
            form.by=request.user.first_name
            form.save()
            return redirect('teacher-dashboard')
        else:
            print('form invalid')
    return render(request,'school/teacher_notice.html',{'form':form})







#FOR STUDENT AFTER THEIR Loginnnnnnnnnnnnnnnnnnnnn
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
@never_cache
def student_dashboard_view(request):
    studentdata=models.StudentExtra.objects.all().filter(user_id=request.user.id)
    if not studentdata:
        return redirect('studentsignup')
    notice=models.Notice.objects.all()
    mydict={
        'roll':studentdata[0].roll,
        'mobile':studentdata[0].mobile,
        'fee':studentdata[0].fee,
        'notice':notice
    }
    return render(request,'school/student_dashboard.html',context=mydict)



@login_required(login_url='studentlogin')
@user_passes_test(is_student)
@never_cache
def student_attendance_view(request):
    form=forms.AskDateForm()
    if request.method=='POST':
        form=forms.AskDateForm(request.POST)
        if form.is_valid():
            date=form.cleaned_data['date']
            studentdata=models.StudentExtra.objects.all().filter(user_id=request.user.id)
            if not studentdata:
                return redirect('studentsignup')
            attendancedata=models.Attendance.objects.all().filter(date=date,cl=studentdata[0].cl,roll=studentdata[0].roll)
            mylist=zip(attendancedata,studentdata)
            return render(request,'school/student_view_attendance_page.html',{'mylist':mylist,'date':date})
        else:
            print('form invalid')
    return render(request,'school/student_view_attendance_ask_date.html',{'form':form})









# for aboutus and contact ussssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss
def aboutus_view(request):
    return render(request,'school/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'school/contactussuccess.html')
    return render(request, 'school/contactus.html', {'form':sub})


# ==================== ADVANCED FEATURES VIEWS ====================

# Advanced Analytics Dashboard
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def advanced_analytics_view(request):
    """Advanced analytics dashboard with charts and insights"""
    
    # Student Statistics
    total_students = models.StudentExtra.objects.filter(status=True).count()
    class_distribution = models.StudentExtra.objects.filter(status=True).values('cl').annotate(count=Count('id')).order_by('cl')
    
    # Teacher Statistics
    total_teachers = models.TeacherExtra.objects.filter(status=True).count()
    avg_salary = models.TeacherExtra.objects.filter(status=True).aggregate(avg_salary=Avg('salary'))['avg_salary'] or 0
    
    # Attendance Statistics
    attendance_stats = models.Attendance.objects.values('cl').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(present_status='Present')),
        absent=Count('id', filter=Q(present_status='Absent'))
    ).order_by('cl')
    
    # Fee Collection Statistics
    fee_stats = models.FeePayment.objects.aggregate(
        total_amount=Sum('amount'),
        paid_amount=Sum('amount', filter=Q(status='paid')),
        pending_amount=Sum('amount', filter=Q(status='pending'))
    )
    
    # Recent Activities
    recent_notices = models.Notice.objects.all().order_by('-date')[:5]
    upcoming_events = models.SchoolEvent.objects.filter(
        start_date__gte=timezone.now(),
        is_public=True
    ).order_by('start_date')[:5]
    
    # Performance Trends
    performance_data = models.StudentPerformance.objects.values('semester').annotate(
        avg_marks=Avg('average_marks'),
        avg_attendance=Avg('attendance_percentage')
    ).order_by('semester')
    
    context = {
        'total_students': total_students,
        'class_distribution': list(class_distribution),
        'total_teachers': total_teachers,
        'avg_salary': round(avg_salary, 2),
        'attendance_stats': list(attendance_stats),
        'fee_stats': fee_stats,
        'recent_notices': recent_notices,
        'upcoming_events': upcoming_events,
        'performance_data': list(performance_data),
    }
    
    return render(request, 'school/advanced_analytics.html', context)


# Assignment Management
@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def teacher_assignments_view(request):
    """Teacher assignment management"""
    teacher = models.TeacherExtra.objects.get(user=request.user)
    assignments = models.Assignment.objects.filter(teacher=teacher).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    assignments_page = paginator.get_page(page_number)
    
    return render(request, 'school/teacher_assignments.html', {'assignments': assignments_page})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
@never_cache
def create_assignment_view(request):
    """Create new assignment"""
    if request.method == 'POST':
        form = forms.AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = models.TeacherExtra.objects.get(user=request.user)
            assignment.save()
            
            # Send notifications to students
            students = models.StudentExtra.objects.filter(cl=assignment.class_name, status=True)
            for student in students:
                services.send_notification_email.delay(
                    student.user.id,
                    f"New Assignment: {assignment.title}",
                    f"A new assignment '{assignment.title}' has been assigned. Due date: {assignment.due_date}",
                    "assignment"
                )
            
            messages.success(request, 'Assignment created successfully!')
            return redirect('teacher-assignments')
    else:
        form = forms.AssignmentForm()
    
    return render(request, 'school/create_assignment.html', {'form': form})


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
@never_cache
def student_assignments_view(request):
    """Student assignment view"""
    student = models.StudentExtra.objects.get(user=request.user)
    assignments = models.Assignment.objects.filter(
        class_name=student.cl,
        is_active=True
    ).order_by('-created_at')
    
    # Check submission status
    assignments_with_status = []
    for assignment in assignments:
        try:
            submission = models.AssignmentSubmission.objects.get(
                assignment=assignment,
                student=student
            )
            assignments_with_status.append({
                'assignment': assignment,
                'submitted': True,
                'submission': submission
            })
        except models.AssignmentSubmission.DoesNotExist:
            assignments_with_status.append({
                'assignment': assignment,
                'submitted': False,
                'submission': None
            })
    
    return render(request, 'school/student_assignments.html', {'assignments': assignments_with_status})


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
@never_cache
def submit_assignment_view(request, assignment_id):
    """Submit assignment"""
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    student = models.StudentExtra.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = forms.AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = student
            submission.save()
            
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('student-assignments')
    else:
        form = forms.AssignmentSubmissionForm()
    
    return render(request, 'school/submit_assignment.html', {'form': form, 'assignment': assignment})


# Library Management
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def library_management_view(request):
    """Library management dashboard"""
    books = models.LibraryBook.objects.all().order_by('title')
    borrowed_books = models.BookBorrowing.objects.filter(is_returned=False).order_by('-borrow_date')
    
    # Statistics
    total_books = books.count()
    available_books = books.filter(status='available').count()
    borrowed_count = books.filter(status='borrowed').count()
    
    context = {
        'books': books,
        'borrowed_books': borrowed_books,
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_count': borrowed_count,
    }
    
    return render(request, 'school/library_management.html', context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def add_book_view(request):
    """Add new book to library"""
    if request.method == 'POST':
        form = forms.LibraryBookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added successfully!')
            return redirect('library-management')
    else:
        form = forms.LibraryBookForm()
    
    return render(request, 'school/add_book.html', {'form': form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def borrow_book_view(request):
    """Borrow book"""
    if request.method == 'POST':
        form = forms.BookBorrowingForm(request.POST)
        if form.is_valid():
            borrowing = form.save(commit=False)
            borrowing.borrower = request.user
            borrowing.save()
            
            # Update book status
            borrowing.book.status = 'borrowed'
            borrowing.book.save()
            
            messages.success(request, 'Book borrowed successfully!')
            return redirect('library-management')
    else:
        form = forms.BookBorrowingForm()
    
    return render(request, 'school/borrow_book.html', {'form': form})


# Event Management
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def event_management_view(request):
    """Event management dashboard"""
    events = models.SchoolEvent.objects.all().order_by('-start_date')
    
    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    events_page = paginator.get_page(page_number)
    
    return render(request, 'school/event_management.html', {'events': events_page})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def create_event_view(request):
    """Create new event"""
    if request.method == 'POST':
        form = forms.SchoolEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            
            # Send notifications to all users
            users = models.User.objects.filter(is_active=True)
            for user in users:
                services.send_notification_email.delay(
                    user.id,
                    f"New Event: {event.title}",
                    f"A new event '{event.title}' has been scheduled for {event.start_date}",
                    "general"
                )
            
            messages.success(request, 'Event created successfully!')
            return redirect('event-management')
    else:
        form = forms.SchoolEventForm()
    
    return render(request, 'school/create_event.html', {'form': form})


# Advanced Search
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def advanced_search_view(request):
    """Advanced search functionality"""
    results = []
    search_type = None
    
    if request.method == 'POST':
        form = forms.AdvancedSearchForm(request.POST)
        if form.is_valid():
            search_type = form.cleaned_data['search_type']
            query = form.cleaned_data['query']
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            class_name = form.cleaned_data['class_name']
            status = form.cleaned_data['status']
            
            if search_type == 'student':
                qs = models.StudentExtra.objects.all()
                if query:
                    qs = qs.filter(
                        Q(user__first_name__icontains=query) |
                        Q(user__last_name__icontains=query) |
                        Q(roll__icontains=query)
                    )
                if class_name:
                    qs = qs.filter(cl=class_name)
                if status:
                    qs = qs.filter(status=(status == 'active'))
                results = qs[:50]  # Limit results
                
            elif search_type == 'teacher':
                qs = models.TeacherExtra.objects.all()
                if query:
                    qs = qs.filter(
                        Q(user__first_name__icontains=query) |
                        Q(user__last_name__icontains=query)
                    )
                if status:
                    qs = qs.filter(status=(status == 'active'))
                results = qs[:50]
                
            elif search_type == 'assignment':
                qs = models.Assignment.objects.all()
                if query:
                    qs = qs.filter(
                        Q(title__icontains=query) |
                        Q(description__icontains=query)
                    )
                if class_name:
                    qs = qs.filter(class_name=class_name)
                if date_from:
                    qs = qs.filter(created_at__gte=date_from)
                if date_to:
                    qs = qs.filter(created_at__lte=date_to)
                results = qs[:50]
                
            elif search_type == 'exam':
                qs = models.Exam.objects.all()
                if query:
                    qs = qs.filter(
                        Q(name__icontains=query) |
                        Q(instructions__icontains=query)
                    )
                if class_name:
                    qs = qs.filter(class_name=class_name)
                if date_from:
                    qs = qs.filter(exam_date__gte=date_from)
                if date_to:
                    qs = qs.filter(exam_date__lte=date_to)
                results = qs[:50]
                
            elif search_type == 'book':
                qs = models.LibraryBook.objects.all()
                if query:
                    qs = qs.filter(
                        Q(title__icontains=query) |
                        Q(author__icontains=query) |
                        Q(isbn__icontains=query)
                    )
                results = qs[:50]
                
            elif search_type == 'event':
                qs = models.SchoolEvent.objects.all()
                if query:
                    qs = qs.filter(
                        Q(title__icontains=query) |
                        Q(description__icontains=query)
                    )
                if date_from:
                    qs = qs.filter(start_date__gte=date_from)
                if date_to:
                    qs = qs.filter(start_date__lte=date_to)
                results = qs[:50]
    else:
        form = forms.AdvancedSearchForm()
    
    return render(request, 'school/advanced_search.html', {
        'form': form,
        'results': results,
        'search_type': search_type
    })


# Bulk Upload
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def bulk_upload_view(request):
    """Bulk upload functionality"""
    if request.method == 'POST':
        form = forms.BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            upload_type = form.cleaned_data['upload_type']
            
            # Save uploaded file
            file_path = default_storage.save(f'temp/{file.name}', ContentFile(file.read()))
            
            try:
                if upload_type == 'students':
                    result = services.bulk_import_students(file_path)
                    if result['success']:
                        messages.success(request, f"Successfully imported {result['imported_count']} students!")
                    else:
                        messages.error(request, f"Import failed: {', '.join(result['errors'])}")
                else:
                    messages.info(request, f"Bulk upload for {upload_type} is not implemented yet.")
                    
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
            finally:
                # Clean up temp file
                default_storage.delete(file_path)
            
            return redirect('bulk-upload')
    else:
        form = forms.BulkUploadForm()
    
    return render(request, 'school/bulk_upload.html', {'form': form})


# Report Generation
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def generate_report_view(request):
    """Generate various reports"""
    if request.method == 'POST':
        form = forms.ReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            class_name = form.cleaned_data['class_name']
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            format = form.cleaned_data['format']
            
            if report_type == 'attendance':
                if not date_from or not date_to:
                    messages.error(request, 'Date range is required for attendance report.')
                    return redirect('generate-report')
                
                report_data = services.generate_attendance_report(class_name, date_from, date_to, format)
                
                if report_data:
                    response = HttpResponse(content_type='application/octet-stream')
                    if format == 'pdf':
                        response['Content-Type'] = 'application/pdf'
                        response['Content-Disposition'] = f'attachment; filename="attendance_report_{class_name}_{date_from}_{date_to}.pdf"'
                    elif format == 'excel':
                        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        response['Content-Disposition'] = f'attachment; filename="attendance_report_{class_name}_{date_from}_{date_to}.xlsx"'
                    elif format == 'csv':
                        response['Content-Type'] = 'text/csv'
                        response['Content-Disposition'] = f'attachment; filename="attendance_report_{class_name}_{date_from}_{date_to}.csv"'
                    
                    response.write(report_data.getvalue())
                    return response
                else:
                    messages.error(request, 'Error generating report.')
            else:
                messages.info(request, f'Report type "{report_type}" is not implemented yet.')
            
            return redirect('generate-report')
    else:
        form = forms.ReportForm()
    
    return render(request, 'school/generate_report.html', {'form': form})


# Real-time Notifications
@login_required
@never_cache
def notifications_view(request):
    """View user notifications"""
    notifications = models.Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    notifications_page = paginator.get_page(page_number)
    
    return render(request, 'school/notifications.html', {'notifications': notifications_page})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        notification = models.Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.is_read = True
        notification.save()
        
        return JsonResponse({'success': True})
    except models.Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})


# QR Code Generation
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def student_qr_codes_view(request):
    """Generate QR codes for students"""
    students = models.StudentExtra.objects.filter(status=True).order_by('roll')
    
    qr_codes = []
    for student in students:
        qr_code = services.generate_qr_code_for_student(student.id)
        if qr_code:
            qr_codes.append({
                'student': student,
                'qr_code': qr_code
            })
    
    return render(request, 'school/student_qr_codes.html', {'qr_codes': qr_codes})


# Performance Analytics
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def performance_analytics_view(request):
    """Student performance analytics"""
    # Get performance data
    performance_data = models.StudentPerformance.objects.all().order_by('-created_at')
    
    # Class-wise performance
    class_performance = models.StudentPerformance.objects.values('student__cl').annotate(
        avg_marks=Avg('average_marks'),
        avg_attendance=Avg('attendance_percentage')
    ).order_by('student__cl')
    
    # Subject-wise performance
    subject_performance = models.StudentPerformance.objects.values('subject__name').annotate(
        avg_marks=Avg('average_marks'),
        student_count=Count('student')
    ).order_by('-avg_marks')
    
    # Top performers
    top_performers = models.StudentPerformance.objects.order_by('-average_marks')[:10]
    
    context = {
        'performance_data': performance_data,
        'class_performance': list(class_performance),
        'subject_performance': list(subject_performance),
        'top_performers': top_performers,
    }
    
    return render(request, 'school/performance_analytics.html', context)


# System Settings
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@never_cache
def system_settings_view(request):
    """System settings management"""
    settings_objects = models.SystemSettings.objects.all().order_by('key')
    
    if request.method == 'POST':
        # Update settings
        for setting in settings_objects:
            new_value = request.POST.get(f'setting_{setting.id}')
            if new_value != setting.value:
                setting.value = new_value
                setting.save()
        
        messages.success(request, 'Settings updated successfully!')
        return redirect('system-settings')
    
    return render(request, 'school/system_settings.html', {'settings': settings_objects})


# API Endpoints for AJAX calls
@login_required
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    if is_admin(request.user):
        stats = {
            'teachers': models.TeacherExtra.objects.filter(status=True).count(),
            'students': models.StudentExtra.objects.filter(status=True).count(),
            'pending_teachers': models.TeacherExtra.objects.filter(status=False).count(),
            'pending_students': models.StudentExtra.objects.filter(status=False).count(),
        }
    elif is_teacher(request.user):
        teacher = models.TeacherExtra.objects.get(user=request.user)
        stats = {
            'assignments': models.Assignment.objects.filter(teacher=teacher).count(),
            'classes': models.Assignment.objects.filter(teacher=teacher).values('class_name').distinct().count(),
        }
    elif is_student(request.user):
        student = models.StudentExtra.objects.get(user=request.user)
        stats = {
            'assignments': models.Assignment.objects.filter(class_name=student.cl, is_active=True).count(),
            'notifications': models.Notification.objects.filter(recipient=request.user, is_read=False).count(),
        }
    else:
        stats = {}
    
    return JsonResponse(stats)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_send_notification(request):
    """API endpoint to send notification"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        title = data.get('title')
        message = data.get('message')
        notification_type = data.get('notification_type', 'general')
        
        services.send_notification_email.delay(recipient_id, title, message, notification_type)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
