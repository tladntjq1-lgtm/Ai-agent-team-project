from django.contrib import messages

from django.contrib.auth.hashers import (
    check_password,
    make_password,
)

from django.db.models import Q

from django.shortcuts import (
    render,
    redirect,
)

from django.utils import timezone


from .models import (
    Student,
    Teacher,
)

from .decorators import (
    student_required,
    teacher_required,
)


from teams.models import (
    Team,
    TeamMember,
)


from evaluations.models import (
    Project,
    EvaluationRound,
    TeamEvaluationScore,
    IndividualEvaluationScore,
    TeacherTeamScore,
    TeacherIndividualScore,
)


# ==========================================
# 공통 함수 1
# 현재 프로젝트
# ==========================================
def get_current_project():

    # ======================================
    # 1. IN_PROGRESS 평가 회차의 프로젝트 우선
    # ======================================
    current_round = EvaluationRound.objects.filter(
        status='IN_PROGRESS'
    ).order_by(
        '-round_id'
    ).first()

    if current_round:

        project = Project.objects.filter(
            project_id=current_round.project_id
        ).first()

        if project:

            return project


    # ======================================
    # 2. IN_PROGRESS 프로젝트
    # ======================================
    project = Project.objects.filter(
        status='IN_PROGRESS'
    ).order_by(
        '-project_id'
    ).first()

    if project:

        return project


    # ======================================
    # 3. READY 프로젝트
    # ======================================
    project = Project.objects.filter(
        status='READY'
    ).order_by(
        '-project_id'
    ).first()

    if project:

        return project


    # ======================================
    # 4. 마지막 프로젝트
    # ======================================
    return Project.objects.order_by(
        '-project_id'
    ).first()


# ==========================================
# 공통 함수 2
# 현재 프로젝트의 학생 팀 조회
# ==========================================
def get_student_team(
    student_id,
    project_id
):

    team_ids = Team.objects.filter(
        project_id=project_id
    ).values_list(
        'team_id',
        flat=True
    )

    team_member = TeamMember.objects.filter(
        student_id=student_id,
        team_id__in=team_ids
    ).first()

    if not team_member:

        return None

    return Team.objects.filter(
        team_id=team_member.team_id,
        project_id=project_id
    ).first()


# ==========================================
# 공통 함수 3
# 평가 상태 문자열 계산
# ==========================================
def get_progress_status(
    completed_count,
    target_count
):

    if target_count <= 0:

        return 'NOT_APPLICABLE'

    if completed_count <= 0:

        return 'NOT_STARTED'

    if completed_count >= target_count:

        return 'COMPLETED'

    return 'IN_PROGRESS'


# ==========================================
# 1. 로그인
# ==========================================
def login_view(request):

    if request.method == 'POST':

        login_id = request.POST.get(
            'login_id'
        )

        password = request.POST.get(
            'password'
        )

        # ==================================
        # 학생 로그인
        # ==================================
        student = Student.objects.filter(
            login_id=login_id
        ).first()

        if student and check_password(
            password,
            student.password
        ):

            request.session.flush()

            request.session[
                'user_type'
            ] = 'STUDENT'

            request.session[
                'student_id'
            ] = student.student_id

            request.session[
                'user_name'
            ] = student.name

            return redirect(
                'student_home'
            )

        # ==================================
        # 선생님 로그인
        # ==================================
        teacher = Teacher.objects.filter(
            login_id=login_id
        ).first()

        if teacher and check_password(
            password,
            teacher.password
        ):

            request.session.flush()

            request.session[
                'user_type'
            ] = 'TEACHER'

            request.session[
                'teacher_id'
            ] = teacher.teacher_id

            request.session[
                'user_name'
            ] = teacher.name

            return redirect(
                'admin_dashboard'
            )

        # ==================================
        # 로그인 실패
        # ==================================
        return render(
            request,
            'members/login.html',
            {
                'error':
                    '아이디 또는 비밀번호가 올바르지 않습니다.'
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
# 3. 회원가입
# ==========================================
def signup_view(request):

    if request.method == 'POST':

        login_id = request.POST.get(
            'login_id'
        )

        password = request.POST.get(
            'password'
        )

        password_confirm = request.POST.get(
            'password_confirm'
        )

        name = request.POST.get(
            'name'
        )

        email = request.POST.get(
            'email'
        )

        phone = request.POST.get(
            'phone'
        )

        slack_id = request.POST.get(
            'slack_id'
        )

        # ==================================
        # 필수 입력
        # ==================================
        if (
            not login_id
            or not password
            or not name
        ):

            return render(
                request,
                'members/signup.html',
                {
                    'error':
                        '아이디, 비밀번호, 이름은 필수 입력 항목입니다.'
                }
            )

        # ==================================
        # 비밀번호 확인
        # ==================================
        if password != password_confirm:

            return render(
                request,
                'members/signup.html',
                {
                    'error':
                        '비밀번호가 일치하지 않습니다.'
                }
            )

        # ==================================
        # 아이디 중복
        # ==================================
        if Student.objects.filter(
            login_id=login_id
        ).exists():

            return render(
                request,
                'members/signup.html',
                {
                    'error':
                        '이미 사용 중인 아이디입니다.'
                }
            )

        if Teacher.objects.filter(
            login_id=login_id
        ).exists():

            return render(
                request,
                'members/signup.html',
                {
                    'error':
                        '이미 사용 중인 아이디입니다.'
                }
            )

        # ==================================
        # 학생 생성
        # ==================================
        create_data = {

            'login_id':
                login_id,

            'password':
                make_password(
                    password
                ),

            'name':
                name,

            'email':
                email or None,

            'phone':
                phone or None,

            'slack_id':
                slack_id or None,
        }

        try:

            create_data[
                'created_at'
            ] = timezone.now()

            Student.objects.create(
                **create_data
            )

        except TypeError:

            create_data.pop(
                'created_at',
                None
            )

            Student.objects.create(
                **create_data
            )

        messages.success(
            request,
            f'환영합니다, {name}님! 회원가입이 완료되었습니다.'
        )

        return redirect(
            'login'
        )

    return render(
        request,
        'members/signup.html'
    )


# ==========================================
# 4. 관리자 대시보드
# ==========================================
@teacher_required
def admin_dashboard_view(request):

    teacher_id = request.session.get(
        'teacher_id'
    )

    user_name = request.session.get(
        'user_name'
    )

    current_project = get_current_project()

    current_round = None

    total_students = Student.objects.count()

    total_teams = 0

    team_evaluation_target_count = 0
    team_evaluation_completed_count = 0
    team_evaluation_progress = 0

    individual_evaluation_target_count = 0
    individual_evaluation_completed_count = 0
    individual_evaluation_progress = 0

    teacher_target_count = 0
    teacher_completed_count = 0
    teacher_progress = 0

    teacher_team_completed_count = 0
    teacher_student_completed_count = 0

    if current_project:

        teams = Team.objects.filter(
            project_id=current_project.project_id
        ).order_by(
            'team_id'
        )

        team_ids = list(
            teams.values_list(
                'team_id',
                flat=True
            )
        )

        total_teams = len(
            team_ids
        )

        project_student_ids = list(
            TeamMember.objects.filter(
                team_id__in=team_ids
            )
            .values_list(
                'student_id',
                flat=True
            )
            .distinct()
        )

        current_round = EvaluationRound.objects.filter(
            project_id=current_project.project_id,
            status='IN_PROGRESS'
        ).order_by(
            '-round_id'
        ).first()

        if not current_round:

            current_round = EvaluationRound.objects.filter(
                project_id=current_project.project_id,
                status='READY'
            ).order_by(
                '-round_id'
            ).first()

        if current_round:

            # ==============================
            # 학생 팀 평가
            # ==============================
            if total_teams > 1:

                team_evaluation_target_count = (
                    len(
                        project_student_ids
                    )
                    * (
                        total_teams - 1
                    )
                )

            team_evaluation_completed_count = (
                TeamEvaluationScore.objects.filter(
                    round_id=current_round.round_id,
                    evaluator_student_id__in=project_student_ids
                )
                .values(
                    'evaluator_student_id',
                    'target_team_id'
                )
                .distinct()
                .count()
            )

            if team_evaluation_target_count > 0:

                team_evaluation_progress = round(
                    team_evaluation_completed_count
                    / team_evaluation_target_count
                    * 100
                )

            # ==============================
            # 개인 평가
            # ==============================
            for team in teams:

                member_count = (
                    TeamMember.objects.filter(
                        team_id=team.team_id
                    )
                    .count()
                )

                if member_count > 1:

                    individual_evaluation_target_count += (
                        member_count
                        * (
                            member_count - 1
                        )
                    )

            individual_evaluation_completed_count = (
                IndividualEvaluationScore.objects.filter(
                    round_id=current_round.round_id,
                    evaluator_student_id__in=project_student_ids
                )
                .values(
                    'evaluator_student_id',
                    'target_student_id'
                )
                .distinct()
                .count()
            )

            if individual_evaluation_target_count > 0:

                individual_evaluation_progress = round(
                    individual_evaluation_completed_count
                    / individual_evaluation_target_count
                    * 100
                )

            # ==============================
            # 선생님 평가
            # ==============================
            teacher_team_completed_count = (
                TeacherTeamScore.objects.filter(
                    round_id=current_round.round_id,
                    teacher_id=teacher_id
                )
                .values(
                    'target_team_id'
                )
                .distinct()
                .count()
            )

            teacher_student_completed_count = (
                TeacherIndividualScore.objects.filter(
                    round_id=current_round.round_id,
                    teacher_id=teacher_id
                )
                .values(
                    'target_student_id'
                )
                .distinct()
                .count()
            )

            teacher_target_count = (
                total_teams
                + len(
                    project_student_ids
                )
            )

            teacher_completed_count = (
                teacher_team_completed_count
                + teacher_student_completed_count
            )

            if teacher_target_count > 0:

                teacher_progress = round(
                    teacher_completed_count
                    / teacher_target_count
                    * 100
                )

    context = {

        'user_name':
            user_name,

        'current_project':
            current_project,

        'current_round':
            current_round,

        'total_students':
            total_students,

        'total_teams':
            total_teams,

        'team_evaluation_progress':
            team_evaluation_progress,

        'team_evaluation_target_count':
            team_evaluation_target_count,

        'team_evaluation_completed_count':
            team_evaluation_completed_count,

        'individual_evaluation_progress':
            individual_evaluation_progress,

        'individual_evaluation_target_count':
            individual_evaluation_target_count,

        'individual_evaluation_completed_count':
            individual_evaluation_completed_count,

        'teacher_progress':
            teacher_progress,

        'teacher_target_count':
            teacher_target_count,

        'teacher_completed_count':
            teacher_completed_count,

        'teacher_team_completed_count':
            teacher_team_completed_count,

        'teacher_student_completed_count':
            teacher_student_completed_count,
    }

    return render(
        request,
        'members/admin_dashboard.html',
        context
    )


# ==========================================
# 5. 학생 홈
# ==========================================
@student_required
def student_home_view(request):

    student_id = request.session.get(
        'student_id'
    )

    student = Student.objects.filter(
        student_id=student_id
    ).first()

    if not student:

        messages.error(
            request,
            '학생 정보를 찾을 수 없습니다.'
        )

        return redirect(
            'login'
        )

    team = None
    team_students = Student.objects.none()

    project = None
    current_round = None

    team_target_count = 0
    team_completed_count = 0
    team_progress = 0

    individual_target_count = 0
    individual_completed_count = 0
    individual_progress = 0

    overall_progress = 0

    # ======================================
    # 현재 프로젝트
    # IN_PROGRESS 평가 회차 프로젝트 우선
    # ======================================
    current_project = get_current_project()

    if current_project:

        team = get_student_team(
            student_id,
            current_project.project_id
        )

        if team:

            project = current_project

            team_student_ids = TeamMember.objects.filter(
                team_id=team.team_id
            ).values_list(
                'student_id',
                flat=True
            )

            team_students = Student.objects.filter(
                student_id__in=team_student_ids
            ).order_by(
                'student_id'
            )

            # ==================================
            # 현재 진행 중인 평가
            # ==================================
            current_round = EvaluationRound.objects.filter(
                project_id=current_project.project_id,
                status='IN_PROGRESS'
            ).order_by(
                '-round_id'
            ).first()

            # ==================================
            # READY는 화면 표시용으로만 fallback
            # ==================================
            if not current_round:

                current_round = EvaluationRound.objects.filter(
                    project_id=current_project.project_id,
                    status='READY'
                ).order_by(
                    '-round_id'
                ).first()

            if current_round:

                # --------------------------
                # 팀 평가 대상
                # --------------------------
                team_target_count = Team.objects.filter(
                    project_id=current_project.project_id
                ).exclude(
                    team_id=team.team_id
                ).count()

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

                if team_target_count > 0:

                    team_progress = round(
                        team_completed_count
                        / team_target_count
                        * 100
                    )

                # --------------------------
                # 개인 평가 대상
                # --------------------------
                individual_target_count = (
                    team_students.exclude(
                        student_id=student_id
                    ).count()
                )

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

                if individual_target_count > 0:

                    individual_progress = round(
                        individual_completed_count
                        / individual_target_count
                        * 100
                    )

                overall_progress = round(
                    (
                        team_progress
                        + individual_progress
                    )
                    / 2
                )

    context = {

        'student':
            student,

        'team':
            team,

        'team_students':
            team_students,

        'has_team':
            team is not None,

        'project':
            project,

        'current_round':
            current_round,

        'team_target_count':
            team_target_count,

        'team_completed_count':
            team_completed_count,

        'team_progress':
            team_progress,

        'individual_target_count':
            individual_target_count,

        'individual_completed_count':
            individual_completed_count,

        'individual_progress':
            individual_progress,

        'overall_progress':
            overall_progress,
    }

    return render(
        request,
        'members/student_home.html',
        context
    )


# ==========================================
# 6. 관리자 - 학생 관리
# ==========================================
@teacher_required
def admin_student_management_view(request):

    current_project = get_current_project()

    if current_project:

        teams = Team.objects.filter(
            project_id=current_project.project_id
        ).order_by(
            'team_id'
        )

    else:

        teams = Team.objects.none()

    team_ids = list(
        teams.values_list(
            'team_id',
            flat=True
        )
    )

    # ======================================
    # POST
    # ======================================
    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        # ==================================
        # 학생 등록
        # ==================================
        if action == 'create':

            login_id = request.POST.get(
                'login_id'
            )

            name = request.POST.get(
                'name'
            )

            email = request.POST.get(
                'email'
            )

            phone = request.POST.get(
                'phone'
            )

            slack_id = request.POST.get(
                'slack_id'
            )

            note = request.POST.get(
                'note'
            )

            team_id = request.POST.get(
                'team_id'
            )

            password = request.POST.get(
                'password'
            )

            if (
                not login_id
                or not name
            ):

                messages.error(
                    request,
                    '아이디와 이름은 필수입니다.'
                )

                return redirect(
                    'admin_student_management'
                )

            if (
                Student.objects.filter(
                    login_id=login_id
                ).exists()
                or
                Teacher.objects.filter(
                    login_id=login_id
                ).exists()
            ):

                messages.error(
                    request,
                    '이미 사용 중인 아이디입니다.'
                )

                return redirect(
                    'admin_student_management'
                )

            if not password:

                password = '1234'

            create_data = {

                'login_id':
                    login_id,

                'password':
                    make_password(
                        password
                    ),

                'name':
                    name,

                'email':
                    email or None,

                'phone':
                    phone or None,

                'slack_id':
                    slack_id or None,

                'note':
                    note or None,
            }

            try:

                create_data[
                    'created_at'
                ] = timezone.now()

                student = Student.objects.create(
                    **create_data
                )

            except TypeError:

                create_data.pop(
                    'created_at',
                    None
                )

                student = Student.objects.create(
                    **create_data
                )

            if (
                team_id
                and team_id != 'UNASSIGNED'
            ):

                target_team = Team.objects.filter(
                    team_id=team_id,
                    project_id=(
                        current_project.project_id
                        if current_project
                        else -1
                    )
                ).first()

                if target_team:

                    TeamMember.objects.create(
                        team_id=target_team.team_id,
                        student_id=student.student_id
                    )

            messages.success(
                request,
                (
                    f'{student.name} 학생이 등록되었습니다. '
                    f'초기 비밀번호는 {password}입니다.'
                )
            )

            return redirect(
                'admin_student_management'
            )

        # ==================================
        # 학생 수정
        # ==================================
        elif action == 'update':

            student_id = request.POST.get(
                'student_id'
            )

            student = Student.objects.filter(
                student_id=student_id
            ).first()

            if not student:

                messages.error(
                    request,
                    '학생 정보를 찾을 수 없습니다.'
                )

                return redirect(
                    'admin_student_management'
                )

            login_id = request.POST.get(
                'login_id'
            )

            name = request.POST.get(
                'name'
            )

            email = request.POST.get(
                'email'
            )

            phone = request.POST.get(
                'phone'
            )

            slack_id = request.POST.get(
                'slack_id'
            )

            note = request.POST.get(
                'note'
            )

            team_id = request.POST.get(
                'team_id'
            )

            if (
                not login_id
                or not name
            ):

                messages.error(
                    request,
                    '아이디와 이름은 필수입니다.'
                )

                return redirect(
                    'admin_student_management'
                )

            duplicate_student = Student.objects.filter(
                login_id=login_id
            ).exclude(
                student_id=student.student_id
            ).exists()

            duplicate_teacher = Teacher.objects.filter(
                login_id=login_id
            ).exists()

            if (
                duplicate_student
                or duplicate_teacher
            ):

                messages.error(
                    request,
                    '이미 사용 중인 아이디입니다.'
                )

                return redirect(
                    'admin_student_management'
                )

            update_data = {

                'login_id':
                    login_id,

                'name':
                    name,

                'email':
                    email or None,

                'phone':
                    phone or None,

                'slack_id':
                    slack_id or None,

                'note':
                    note or None,
            }

            try:

                update_data[
                    'updated_at'
                ] = timezone.now()

                Student.objects.filter(
                    student_id=student.student_id
                ).update(
                    **update_data
                )

            except Exception:

                update_data.pop(
                    'updated_at',
                    None
                )

                Student.objects.filter(
                    student_id=student.student_id
                ).update(
                    **update_data
                )

            if current_project:

                TeamMember.objects.filter(
                    student_id=student.student_id,
                    team_id__in=team_ids
                ).delete()

                if (
                    team_id
                    and team_id != 'UNASSIGNED'
                ):

                    target_team = Team.objects.filter(
                        team_id=team_id,
                        project_id=current_project.project_id
                    ).first()

                    if target_team:

                        TeamMember.objects.create(
                            team_id=target_team.team_id,
                            student_id=student.student_id
                        )

            messages.success(
                request,
                f'{name} 학생 정보가 수정되었습니다.'
            )

            return redirect(
                'admin_student_management'
            )

    # ======================================
    # GET 검색 / 필터
    # ======================================
    search = request.GET.get(
        'search',
        ''
    ).strip()

    team_filter = request.GET.get(
        'team',
        ''
    )

    evaluation_filter = request.GET.get(
        'evaluation_status',
        ''
    )

    students = Student.objects.all().order_by(
        'student_id'
    )

    if search:

        students = students.filter(

            Q(
                name__icontains=search
            )

            |

            Q(
                email__icontains=search
            )

            |

            Q(
                login_id__icontains=search
            )

            |

            Q(
                slack_id__icontains=search
            )
        )

    current_round = None

    if current_project:

        current_round = EvaluationRound.objects.filter(
            project_id=current_project.project_id,
            status='IN_PROGRESS'
        ).order_by(
            '-round_id'
        ).first()

        if not current_round:

            current_round = EvaluationRound.objects.filter(
                project_id=current_project.project_id,
                status='READY'
            ).order_by(
                '-round_id'
            ).first()

    student_rows = []

    for student in students:

        team = None

        if current_project:

            team = get_student_team(
                student.student_id,
                current_project.project_id
            )

        # ==================================
        # 팀 필터
        # ==================================
        if team_filter:

            if team_filter == 'UNASSIGNED':

                if team:

                    continue

            else:

                try:

                    filter_team_id = int(
                        team_filter
                    )

                except ValueError:

                    filter_team_id = None

                if (
                    not team
                    or team.team_id != filter_team_id
                ):

                    continue

        team_target_count = 0
        team_completed_count = 0
        team_status = 'NOT_APPLICABLE'

        individual_target_count = 0
        individual_completed_count = 0
        individual_status = 'NOT_APPLICABLE'

        if (
            current_round
            and team
        ):

            # ==============================
            # 팀 평가
            # ==============================
            team_target_count = Team.objects.filter(
                project_id=current_project.project_id
            ).exclude(
                team_id=team.team_id
            ).count()

            team_completed_count = (
                TeamEvaluationScore.objects.filter(
                    round_id=current_round.round_id,
                    evaluator_student_id=student.student_id
                )
                .values(
                    'target_team_id'
                )
                .distinct()
                .count()
            )

            team_status = get_progress_status(
                team_completed_count,
                team_target_count
            )

            # ==============================
            # 개인 평가
            # ==============================
            team_member_student_ids = TeamMember.objects.filter(
                team_id=team.team_id
            ).values_list(
                'student_id',
                flat=True
            )

            individual_target_count = Student.objects.filter(
                student_id__in=team_member_student_ids
            ).exclude(
                student_id=student.student_id
            ).count()

            individual_completed_count = (
                IndividualEvaluationScore.objects.filter(
                    round_id=current_round.round_id,
                    evaluator_student_id=student.student_id
                )
                .values(
                    'target_student_id'
                )
                .distinct()
                .count()
            )

            individual_status = get_progress_status(
                individual_completed_count,
                individual_target_count
            )

        # ==================================
        # 평가 필터
        # ==================================
        if evaluation_filter:

            if evaluation_filter == 'COMPLETED':

                if not (
                    team_status == 'COMPLETED'
                    and
                    individual_status == 'COMPLETED'
                ):

                    continue

            elif evaluation_filter == 'IN_PROGRESS':

                if not (
                    team_status == 'IN_PROGRESS'
                    or
                    individual_status == 'IN_PROGRESS'
                ):

                    continue

            elif evaluation_filter == 'NOT_STARTED':

                if not (
                    team_status == 'NOT_STARTED'
                    and
                    individual_status == 'NOT_STARTED'
                ):

                    continue

        student_rows.append(
            {
                'student':
                    student,

                'team':
                    team,

                'team_status':
                    team_status,

                'team_target_count':
                    team_target_count,

                'team_completed_count':
                    team_completed_count,

                'individual_status':
                    individual_status,

                'individual_target_count':
                    individual_target_count,

                'individual_completed_count':
                    individual_completed_count,
            }
        )

    # ======================================
    # 전체 통계
    # ======================================
    total_students = Student.objects.count()

    assigned_student_ids = set()

    if current_project:

        assigned_student_ids = set(
            TeamMember.objects.filter(
                team_id__in=team_ids
            ).values_list(
                'student_id',
                flat=True
            )
        )

    assigned_count = len(
        assigned_student_ids
    )

    unassigned_count = max(
        0,
        total_students
        - assigned_count
    )

    context = {

        'current_project':
            current_project,

        'current_round':
            current_round,

        'teams':
            teams,

        'student_rows':
            student_rows,

        'total_students':
            total_students,

        'assigned_count':
            assigned_count,

        'unassigned_count':
            unassigned_count,

        'search':
            search,

        'team_filter':
            team_filter,

        'evaluation_filter':
            evaluation_filter,

        'filtered_count':
            len(
                student_rows
            ),
    }

    return render(
        request,
        'members/admin_student_management.html',
        context
    )


# ==========================================
# 7. 로그아웃
# ==========================================
def logout_view(request):

    request.session.flush()

    return redirect(
        'login'
    )