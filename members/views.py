from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect

from .models import Student, Teacher
from .decorators import student_required, teacher_required


# ==========================================
# 1. 로그인
# ==========================================
def login_view(request):

    if request.method == 'POST':

        login_id = request.POST.get('login_id')
        password = request.POST.get('password')

        # ----------------------------------
        # 학생 계정 확인
        # ----------------------------------
        student = Student.objects.filter(
            login_id=login_id
        ).first()

        if student and check_password(
            password,
            student.password
        ):

            # 로그인한 학생 정보를 세션에 저장
            request.session['user_type'] = 'STUDENT'
            request.session['student_id'] = student.student_id
            request.session['user_name'] = student.name

            # 학생 홈으로 이동
            return redirect('student_home')


        # ----------------------------------
        # 튜터 계정 확인
        # ----------------------------------
        teacher = Teacher.objects.filter(
            login_id=login_id
        ).first()

        if teacher and check_password(
            password,
            teacher.password
        ):

            # 로그인한 튜터 정보를 세션에 저장
            request.session['user_type'] = 'TEACHER'
            request.session['teacher_id'] = teacher.teacher_id
            request.session['user_name'] = teacher.name

            # 관리자 대시보드로 이동
            return redirect('admin_dashboard')


        # ----------------------------------
        # 로그인 실패
        # ----------------------------------
        return render(
            request,
            'members/login.html',
            {
                'error': '아이디 또는 비밀번호가 올바르지 않습니다.'
            }
        )


    # GET 요청일 경우 로그인 화면 출력
    return render(
        request,
        'members/login.html'
    )


# ==========================================
# 2. 아이디 / 비밀번호 찾기
# ==========================================
def account_find_view(request):

    return render(
        request,
        'members/account_find.html'
    )


# ==========================================
# 3. 학생 회원가입
# ==========================================
def signup_view(request):

    if request.method == 'POST':

        # HTML에서 입력한 데이터 가져오기
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        slack_id = request.POST.get('slack_id')


        # ----------------------------------
        # 필수 입력값 확인
        # ----------------------------------
        if not login_id or not password or not name:

            return render(
                request,
                'members/signup.html',
                {
                    'error': '아이디, 비밀번호, 이름은 필수 입력 항목입니다.'
                }
            )


        # ----------------------------------
        # 비밀번호 / 비밀번호 확인 비교
        # ----------------------------------
        if password != password_confirm:

            return render(
                request,
                'members/signup.html',
                {
                    'error': '비밀번호가 일치하지 않습니다.'
                }
            )


        # ----------------------------------
        # 학생 아이디 중복 확인
        # ----------------------------------
        if Student.objects.filter(
            login_id=login_id
        ).exists():

            return render(
                request,
                'members/signup.html',
                {
                    'error': '이미 사용 중인 아이디입니다.'
                }
            )


        # ----------------------------------
        # 튜터 아이디와도 중복 확인
        # ----------------------------------
        if Teacher.objects.filter(
            login_id=login_id
        ).exists():

            return render(
                request,
                'members/signup.html',
                {
                    'error': '이미 사용 중인 아이디입니다.'
                }
            )


        # ----------------------------------
        # 새로운 학생 생성
        # ----------------------------------
        Student.objects.create(

            login_id=login_id,
            # 비밀번호는 평문으로 저장하지 않고
            # Django 방식으로 암호화해서 저장
            password=make_password(password),
            name=name,
            email=email or None,
            phone=phone or None,
            slack_id=slack_id or None
        )

        messages.success(
             request,
            f'환영합니다, {name}님! 회원가입이 완료되었습니다.'
)
        # ----------------------------------
        # 회원가입 완료
        # ----------------------------------
        return redirect('login')


    # GET 요청일 경우 회원가입 화면 출력
    return render(
        request,
        'members/signup.html'
    )


# ==========================================
# 4. 관리자 대시보드
# ==========================================
@teacher_required
def admin_dashboard_view(request):

    # 로그인하지 않은 경우
    if not request.session.get('user_type'):
        return redirect('login')

    # 학생이 관리자 페이지에 접근한 경우
    if request.session.get('user_type') != 'TEACHER':
        return redirect('student_home')

    return render(
        request,
        'members/admin_dashboard.html',
        {
            'user_name': request.session.get('user_name')
        }
    )


# ==========================================
# 5. 학생 홈
# ==========================================
@student_required
def student_home_view(request):

    # 로그인하지 않은 경우
    if not request.session.get('user_type'):
        return redirect('login')

    # 관리자가 학생 페이지에 접근한 경우
    if request.session.get('user_type') != 'STUDENT':
        return redirect('admin_dashboard')

    student_id = request.session.get('student_id')

    student = Student.objects.filter(
        student_id=student_id
    ).first()

    return render(
        request,
        'members/student_home.html',
        {
            'student': student
        }
    )


# ==========================================
# 6. 학생 관리
# ==========================================
@teacher_required
def admin_student_management_view(request):

    return render(
        request,
        'members/admin_student_management.html'
    )


# ==========================================
# 7. 로그아웃
# ==========================================
def logout_view(request):

    # 현재 로그인 세션 전체 삭제
    request.session.flush()

    # 로그인 화면으로 이동
    return redirect('login')