from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect

from .models import Student, Teacher
from .decorators import student_required, teacher_required

from teams.models import Team, TeamMember

from evaluations.models import (
    Project,
    EvaluationRound,
    TeamEvaluationScore,
    IndividualEvaluationScore,
)


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

            # 로그인 학생 정보 세션 저장
            request.session['user_type'] = 'STUDENT'
            request.session['student_id'] = student.student_id
            request.session['user_name'] = student.name

            return redirect('student_home')


        # ----------------------------------
        # 선생님 계정 확인
        # ----------------------------------
        teacher = Teacher.objects.filter(
            login_id=login_id
        ).first()

        if teacher and check_password(
            password,
            teacher.password
        ):

            # 로그인 선생님 정보 세션 저장
            request.session['user_type'] = 'TEACHER'
            request.session['teacher_id'] = teacher.teacher_id
            request.session['user_name'] = teacher.name

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

        login_id = request.POST.get('login_id')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        slack_id = request.POST.get('slack_id')


        # ----------------------------------
        # 필수 입력 확인
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
        # 비밀번호 확인
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
        # 학생 아이디 중복
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
        # 선생님 아이디와도 중복 방지
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
        # 학생 DB 저장
        # ----------------------------------
        Student.objects.create(
            login_id=login_id,
            password=make_password(password),
            name=name,
            email=email or None,
            phone=phone or None,
            slack_id=slack_id or None
        )


        # 회원가입 완료 메시지
        messages.success(
            request,
            f'환영합니다, {name}님! 회원가입이 완료되었습니다.'
        )

        return redirect('login')


    return render(
        request,
        'members/signup.html'
    )


# ==========================================
# 4. 관리자 대시보드
# ==========================================
@teacher_required
def admin_dashboard_view(request):

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

    # ==========================================
    # 1. 로그인 학생 ID
    # ==========================================
    student_id = request.session.get(
        'student_id'
    )


    # ==========================================
    # 2. 학생 정보 조회
    # ==========================================
    student = Student.objects.filter(
        student_id=student_id
    ).first()


    # ==========================================
    # 3. 기본값
    # ==========================================
    team = None
    team_students = []
    project = None
    current_round = None

    team_target_count = 0
    team_completed_count = 0
    team_progress = 0

    individual_target_count = 0
    individual_completed_count = 0
    individual_progress = 0

    overall_progress = 0


    # ==========================================
    # 4. 학생의 팀 배정 조회
    # ==========================================
    team_member = TeamMember.objects.filter(
        student_id=student_id
    ).first()


    # ==========================================
    # 5. 팀에 배정된 학생
    # ==========================================
    if team_member:

        # ----------------------------------
        # 현재 학생의 팀
        # ----------------------------------
        team = Team.objects.filter(
            team_id=team_member.team_id
        ).first()


        # ----------------------------------
        # 같은 팀 학생 ID
        # ----------------------------------
        team_student_ids = TeamMember.objects.filter(
            team_id=team_member.team_id
        ).values_list(
            'student_id',
            flat=True
        )


        # ----------------------------------
        # 같은 팀 실제 학생 정보
        # ----------------------------------
        team_students = Student.objects.filter(
            student_id__in=team_student_ids
        ).order_by(
            'student_id'
        )


        # ======================================
        # 6. 프로젝트 조회
        # ======================================
        if team:

            project = Project.objects.filter(
                project_id=team.project_id
            ).first()


            # ==================================
            # 7. 현재 평가 회차 조회
            # IN_PROGRESS 우선
            # 없으면 READY
            # ==================================
            current_round = EvaluationRound.objects.filter(
                project_id=team.project_id,
                status='IN_PROGRESS'
            ).order_by(
                '-round_id'
            ).first()


            if not current_round:

                current_round = EvaluationRound.objects.filter(
                    project_id=team.project_id,
                    status='READY'
                ).order_by(
                    '-round_id'
                ).first()


        # ======================================
        # 8. 평가 진행률 계산
        # ======================================
        if current_round and team:

            # ----------------------------------
            # 팀 평가 대상 수
            # 현재 프로젝트의 다른 팀 전체
            # ----------------------------------
            team_target_count = Team.objects.filter(
                project_id=team.project_id
            ).exclude(
                team_id=team.team_id
            ).count()


            # ----------------------------------
            # 실제 평가한 팀 수
            # 같은 팀에 대해 여러 문항이 있어도
            # target_team_id 기준 DISTINCT
            # ----------------------------------
            team_completed_count = (
                TeamEvaluationScore.objects.filter(
                    round_id=current_round.round_id,
                    evaluator_student_id=student_id
                )
                .values(
                    'target_team_id'
                )
                .distinct()
                .count()
            )


            # ----------------------------------
            # 팀 평가 진행률
            # ----------------------------------
            if team_target_count > 0:

                team_progress = round(
                    team_completed_count
                    / team_target_count
                    * 100
                )


            # ----------------------------------
            # 개인 평가 대상 수
            # 본인 제외 같은 팀원
            # ----------------------------------
            individual_target_count = (
                team_students.exclude(
                    student_id=student_id
                ).count()
            )


            # ----------------------------------
            # 실제 평가한 팀원 수
            # 같은 사람에 대해 여러 문항이 있어도
            # target_student_id 기준 DISTINCT
            # ----------------------------------
            individual_completed_count = (
                IndividualEvaluationScore.objects.filter(
                    round_id=current_round.round_id,
                    evaluator_student_id=student_id
                )
                .values(
                    'target_student_id'
                )
                .distinct()
                .count()
            )


            # ----------------------------------
            # 개인 평가 진행률
            # ----------------------------------
            if individual_target_count > 0:

                individual_progress = round(
                    individual_completed_count
                    / individual_target_count
                    * 100
                )


            # ----------------------------------
            # 전체 평가 진행률
            # 팀 평가 + 개인 평가 단순 평균
            # ----------------------------------
            overall_progress = round(
                (
                    team_progress
                    + individual_progress
                )
                / 2
            )


    # ==========================================
    # 9. Template 전달 데이터
    # ==========================================
    context = {

        # 학생
        'student': student,

        # 팀
        'team': team,
        'team_students': team_students,
        'has_team': team is not None,

        # 프로젝트 / 평가 회차
        'project': project,
        'current_round': current_round,

        # 팀 평가
        'team_target_count': team_target_count,
        'team_completed_count': team_completed_count,
        'team_progress': team_progress,

        # 개인 평가
        'individual_target_count': individual_target_count,
        'individual_completed_count': individual_completed_count,
        'individual_progress': individual_progress,

        # 전체 진행률
        'overall_progress': overall_progress,
    }


    return render(
        request,
        'members/student_home.html',
        context
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

    return redirect('login')