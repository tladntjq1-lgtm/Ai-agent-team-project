from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone

from members.decorators import (
    student_required,
    teacher_required,
)

from members.models import (
    Student,
)

from teams.models import (
    Team,
    TeamMember,
)

from .models import (
    Project,
    EvaluationRound,
    EvaluationQuestion,
    TeamEvaluationScore,
    IndividualEvaluationScore,
    TeacherTeamScore,
    TeacherIndividualScore,
)


# ==========================================
# 공통 함수 1
# 현재 프로젝트 조회
# ==========================================
def get_current_project():

    # 진행 중인 평가 회차 프로젝트 우선
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

    # 진행 중인 프로젝트
    project = Project.objects.filter(
        status='IN_PROGRESS'
    ).order_by(
        '-project_id'
    ).first()

    if project:
        return project

    # 최신 프로젝트
    return Project.objects.order_by(
        '-project_id'
    ).first()


# ==========================================
# 공통 함수 2
# 프로젝트 기준 학생 팀 배정 조회
# ==========================================
def get_student_team_member(
    student_id,
    project_id
):

    team_ids = Team.objects.filter(
        project_id=project_id
    ).values_list(
        'team_id',
        flat=True
    )

    return TeamMember.objects.filter(
        student_id=student_id,
        team_id__in=team_ids
    ).first()


# ==========================================
# 공통 함수 3
# 프로젝트 기준 학생 실제 팀 조회
# ==========================================
def get_student_team(
    student_id,
    project_id
):

    team_member = get_student_team_member(
        student_id,
        project_id
    )

    if not team_member:
        return None

    return Team.objects.filter(
        team_id=team_member.team_id,
        project_id=project_id
    ).first()


# ==========================================
# 공통 함수 4
# 최종 점수 + 등급 계산
# ==========================================
def calculate_final_grade(
    team_score,
    individual_score,
    teacher_score,
    allow_fallback=False,
):

    # ======================================
    # 정상 계산
    # 팀 30 + 개인 30 + 선생님 40
    # ======================================
    if (
        team_score is not None
        and individual_score is not None
        and teacher_score is not None
    ):

        final_score = (
            team_score * 0.30
            + individual_score * 0.30
            + teacher_score * 0.40
        )

        final_score = round(
            final_score,
            2
        )

        calculation_status = 'NORMAL'

    # ======================================
    # 일부 평가 누락
    # ======================================
    else:

        # 기본 정책:
        # 누락된 평가가 있으면 미산정
        if not allow_fallback:

            return {
                'final_score': None,
                'grade': '미산정',
                'status': 'WAITING',
            }

        # ==================================
        # 예외 계산
        # 존재하는 점수끼리 가중치 재분배
        # ==================================
        scores = []

        if team_score is not None:

            scores.append(
                (
                    team_score,
                    0.30
                )
            )

        if individual_score is not None:

            scores.append(
                (
                    individual_score,
                    0.30
                )
            )

        if teacher_score is not None:

            scores.append(
                (
                    teacher_score,
                    0.40
                )
            )

        if not scores:

            return {
                'final_score': None,
                'grade': '미산정',
                'status': 'WAITING',
            }

        total_weight = sum(
            weight
            for score, weight
            in scores
        )

        final_score = (
            sum(
                score * weight
                for score, weight
                in scores
            )
            / total_weight
        )

        final_score = round(
            final_score,
            2
        )

        calculation_status = 'FALLBACK'

    # ======================================
    # 등급
    # ======================================
    if final_score >= 90:

        grade = 'S'

    elif final_score >= 80:

        grade = 'A'

    elif final_score >= 70:

        grade = 'B'

    else:

        grade = 'C'

    return {
        'final_score': final_score,
        'grade': grade,
        'status': calculation_status,
    }


# ==========================================
# 1. 관리자 - 평가 회차 관리
# ==========================================
@teacher_required
def admin_evaluation_round_view(request):

    projects = Project.objects.all().order_by(
        '-project_id'
    )

    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        # ==================================
        # A. 평가 회차 생성
        # ==================================
        if action == 'create':

            project_id = request.POST.get(
                'project_id'
            )

            round_name = request.POST.get(
                'round_name'
            )

            start_date = request.POST.get(
                'start_date'
            )

            end_date = request.POST.get(
                'end_date'
            )

            if (
                not project_id
                or not round_name
                or not start_date
                or not end_date
            ):

                messages.error(
                    request,
                    '모든 필수 항목을 입력해주세요.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            project = Project.objects.filter(
                project_id=project_id
            ).first()

            if not project:

                messages.error(
                    request,
                    '프로젝트 정보를 찾을 수 없습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            if start_date > end_date:

                messages.error(
                    request,
                    '종료일은 시작일보다 빠를 수 없습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            EvaluationRound.objects.create(

                project_id=project.project_id,

                round_name=round_name,

                start_date=start_date,

                end_date=end_date,

                status='READY',

                results_public=False,

                created_at=timezone.now()
            )

            messages.success(
                request,
                f'{round_name} 회차가 생성되었습니다.'
            )

            return redirect(
                'admin_evaluation_round'
            )

        # ==================================
        # B. 평가 시작
        # ==================================
        elif action == 'start':

            round_id = request.POST.get(
                'round_id'
            )

            evaluation_round = (
                EvaluationRound.objects.filter(
                    round_id=round_id
                ).first()
            )

            if not evaluation_round:

                messages.error(
                    request,
                    '평가 회차를 찾을 수 없습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            if evaluation_round.status != 'READY':

                messages.warning(
                    request,
                    'READY 상태의 평가만 시작할 수 있습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            team_question_exists = (
                EvaluationQuestion.objects.filter(
                    round_id=evaluation_round.round_id,
                    question_type='TEAM'
                ).exists()
            )

            individual_question_exists = (
                EvaluationQuestion.objects.filter(
                    round_id=evaluation_round.round_id,
                    question_type='INDIVIDUAL'
                ).exists()
            )

            if (
                not team_question_exists
                or not individual_question_exists
            ):

                messages.error(
                    request,
                    '팀 평가와 개인 평가 문항을 모두 등록한 후 평가를 시작해주세요.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            EvaluationRound.objects.filter(
                round_id=evaluation_round.round_id
            ).update(
                status='IN_PROGRESS'
            )

            messages.success(
                request,
                f'{evaluation_round.round_name} 평가가 시작되었습니다.'
            )

            return redirect(
                'admin_evaluation_round'
            )

        # ==================================
        # C. 평가 종료
        # ==================================
        elif action == 'complete':

            round_id = request.POST.get(
                'round_id'
            )

            evaluation_round = (
                EvaluationRound.objects.filter(
                    round_id=round_id
                ).first()
            )

            if not evaluation_round:

                messages.error(
                    request,
                    '평가 회차를 찾을 수 없습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            if evaluation_round.status != 'IN_PROGRESS':

                messages.warning(
                    request,
                    '진행 중인 평가만 종료할 수 있습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            EvaluationRound.objects.filter(
                round_id=evaluation_round.round_id
            ).update(
                status='COMPLETED'
            )

            messages.success(
                request,
                f'{evaluation_round.round_name} 평가가 종료되었습니다.'
            )

            return redirect(
                'admin_evaluation_round'
            )

        # ==================================
        # D. READY 삭제
        # ==================================
        elif action == 'delete':

            round_id = request.POST.get(
                'round_id'
            )

            evaluation_round = (
                EvaluationRound.objects.filter(
                    round_id=round_id
                ).first()
            )

            if not evaluation_round:

                messages.error(
                    request,
                    '평가 회차를 찾을 수 없습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            if evaluation_round.status != 'READY':

                messages.error(
                    request,
                    'READY 상태의 평가 회차만 삭제할 수 있습니다.'
                )

                return redirect(
                    'admin_evaluation_round'
                )

            EvaluationQuestion.objects.filter(
                round_id=evaluation_round.round_id
            ).delete()

            evaluation_round.delete()

            messages.success(
                request,
                '평가 회차가 삭제되었습니다.'
            )

            return redirect(
                'admin_evaluation_round'
            )

    rounds = EvaluationRound.objects.all().order_by(
        '-round_id'
    )

    round_list = []

    for evaluation_round in rounds:

        project = Project.objects.filter(
            project_id=evaluation_round.project_id
        ).first()

        round_list.append(
            {
                'round':
                    evaluation_round,

                'project_name':
                    (
                        project.project_name
                        if project
                        else '-'
                    ),
            }
        )

    return render(
        request,
        'evaluations/admin_evaluation_round.html',
        {
            'projects':
                projects,

            'round_list':
                round_list,
        }
    )


# ==========================================
# 2. 관리자 - 평가 문항 관리
# ==========================================
@teacher_required
def admin_evaluation_questions_view(request):

    round_id = (
        request.GET.get('round_id')
        or request.POST.get('round_id')
    )

    if not round_id:

        evaluation_round = (
            EvaluationRound.objects.filter(
                status='READY'
            )
            .order_by(
                '-round_id'
            )
            .first()
        )

        if not evaluation_round:

            evaluation_round = (
                EvaluationRound.objects
                .order_by('-round_id')
                .first()
            )

    else:

        evaluation_round = (
            EvaluationRound.objects.filter(
                round_id=round_id
            ).first()
        )

    if not evaluation_round:

        return render(
            request,
            'evaluations/admin_evaluation_questions.html',
            {
                'current_round': None,
                'team_questions': [],
                'individual_questions': [],
                'editable': False,
            }
        )

    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        if evaluation_round.status != 'READY':

            messages.error(
                request,
                '평가 문항은 READY 상태에서만 변경할 수 있습니다.'
            )

            return redirect(
                (
                    '/admin-eval-questions/'
                    f'?round_id={evaluation_round.round_id}'
                )
            )

        if action == 'create':

            question_type = request.POST.get(
                'question_type'
            )

            question_text = request.POST.get(
                'question_text'
            )

            if question_type not in (
                'TEAM',
                'INDIVIDUAL'
            ):

                messages.error(
                    request,
                    '잘못된 평가 문항 유형입니다.'
                )

                return redirect(
                    (
                        '/admin-eval-questions/'
                        f'?round_id={evaluation_round.round_id}'
                    )
                )

            if not question_text:

                messages.error(
                    request,
                    '평가 문항을 입력해주세요.'
                )

                return redirect(
                    (
                        '/admin-eval-questions/'
                        f'?round_id={evaluation_round.round_id}'
                    )
                )

            last_question = (
                EvaluationQuestion.objects.filter(
                    round_id=evaluation_round.round_id,
                    question_type=question_type
                )
                .order_by(
                    '-display_order'
                )
                .first()
            )

            display_order = (
                last_question.display_order + 1
                if last_question
                else 1
            )

            EvaluationQuestion.objects.create(

                round_id=evaluation_round.round_id,

                question_type=question_type,

                question_text=question_text,

                display_order=display_order
            )

            messages.success(
                request,
                '평가 문항이 추가되었습니다.'
            )

        elif action == 'update':

            question_id = request.POST.get(
                'question_id'
            )

            question_text = request.POST.get(
                'question_text'
            )

            question = (
                EvaluationQuestion.objects.filter(
                    question_id=question_id,
                    round_id=evaluation_round.round_id
                ).first()
            )

            if not question:

                messages.error(
                    request,
                    '평가 문항을 찾을 수 없습니다.'
                )

            elif not question_text:

                messages.error(
                    request,
                    '평가 문항 내용을 입력해주세요.'
                )

            else:

                EvaluationQuestion.objects.filter(
                    question_id=question.question_id
                ).update(
                    question_text=question_text
                )

                messages.success(
                    request,
                    '평가 문항이 수정되었습니다.'
                )

        elif action == 'delete':

            question_id = request.POST.get(
                'question_id'
            )

            question = (
                EvaluationQuestion.objects.filter(
                    question_id=question_id,
                    round_id=evaluation_round.round_id
                ).first()
            )

            if not question:

                messages.error(
                    request,
                    '평가 문항을 찾을 수 없습니다.'
                )

            else:

                question.delete()

                messages.success(
                    request,
                    '평가 문항이 삭제되었습니다.'
                )

        return redirect(
            (
                '/admin-eval-questions/'
                f'?round_id={evaluation_round.round_id}'
            )
        )

    team_questions = EvaluationQuestion.objects.filter(
        round_id=evaluation_round.round_id,
        question_type='TEAM'
    ).order_by(
        'display_order'
    )

    individual_questions = (
        EvaluationQuestion.objects.filter(
            round_id=evaluation_round.round_id,
            question_type='INDIVIDUAL'
        ).order_by(
            'display_order'
        )
    )

    return render(
        request,
        'evaluations/admin_evaluation_questions.html',
        {
            'current_round':
                evaluation_round,

            'team_questions':
                team_questions,

            'individual_questions':
                individual_questions,

            'editable':
                evaluation_round.status == 'READY',
        }
    )


# ==========================================
# 3. 관리자 - 선생님 평가
# ==========================================
@teacher_required
def admin_teacher_evaluation_view(request):

    teacher_id = request.session.get(
        'teacher_id'
    )

    if not teacher_id:

        messages.error(
            request,
            '선생님 로그인 정보가 없습니다.'
        )

        return redirect(
            'login'
        )

    current_round = EvaluationRound.objects.filter(
        status='IN_PROGRESS'
    ).order_by(
        '-round_id'
    ).first()

    if not current_round:

        return render(
            request,
            'evaluations/admin_teacher_evaluation.html',
            {
                'current_round': None,
                'project': None,
                'teams': [],
                'students': [],
                'team_questions': [],
                'individual_questions': [],
                'completed_team_ids': [],
                'completed_student_ids': [],
                'team_count': 0,
                'completed_team_count': 0,
                'team_progress': 0,
                'student_count': 0,
                'completed_student_count': 0,
                'individual_progress': 0,
            }
        )

    project = Project.objects.filter(
        project_id=current_round.project_id
    ).first()

    teams = Team.objects.filter(
        project_id=current_round.project_id
    ).order_by(
        'team_id'
    )

    team_ids = list(
        teams.values_list(
            'team_id',
            flat=True
        )
    )

    student_ids = (
        TeamMember.objects.filter(
            team_id__in=team_ids
        )
        .values_list(
            'student_id',
            flat=True
        )
        .distinct()
    )

    students = Student.objects.filter(
        student_id__in=student_ids
    ).order_by(
        'name'
    )

    team_questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='TEAM'
    ).order_by(
        'display_order'
    )

    individual_questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='INDIVIDUAL'
    ).order_by(
        'display_order'
    )

    completed_team_ids = list(
        TeacherTeamScore.objects.filter(
            round_id=current_round.round_id,
            teacher_id=teacher_id
        )
        .values_list(
            'target_team_id',
            flat=True
        )
        .distinct()
    )

    completed_student_ids = list(
        TeacherIndividualScore.objects.filter(
            round_id=current_round.round_id,
            teacher_id=teacher_id
        )
        .values_list(
            'target_student_id',
            flat=True
        )
        .distinct()
    )

    if request.method == 'POST':

        evaluation_type = request.POST.get(
            'evaluation_type'
        )

        if evaluation_type == 'TEAM':

            target_team_id = request.POST.get(
                'target_team_id'
            )

            try:

                target_team_id = int(
                    target_team_id
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '잘못된 팀 정보입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )

            target_team = Team.objects.filter(
                team_id=target_team_id,
                project_id=current_round.project_id
            ).first()

            if not target_team:

                messages.error(
                    request,
                    '평가할 수 없는 팀입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )

            if TeacherTeamScore.objects.filter(
                round_id=current_round.round_id,
                teacher_id=teacher_id,
                target_team_id=target_team_id
            ).exists():

                messages.warning(
                    request,
                    '이미 평가한 팀입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )

            score_data = []

            for question in team_questions:

                score_value = request.POST.get(
                    f'question_{question.question_id}'
                )

                try:

                    score_value = int(
                        score_value
                    )

                except (TypeError, ValueError):

                    messages.error(
                        request,
                        '모든 문항에 점수를 입력해주세요.'
                    )

                    return redirect(
                        'admin_teacher_evaluation'
                    )

                if not 1 <= score_value <= 5:

                    messages.error(
                        request,
                        '점수는 1점부터 5점까지 입력할 수 있습니다.'
                    )

                    return redirect(
                        'admin_teacher_evaluation'
                    )

                score_data.append(
                    (
                        question,
                        score_value
                    )
                )

            for question, score_value in score_data:

                TeacherTeamScore.objects.create(

                    round_id=current_round.round_id,

                    teacher_id=teacher_id,

                    target_team_id=target_team_id,

                    question_id=question.question_id,

                    score=score_value,

                    created_at=timezone.now()
                )

            messages.success(
                request,
                f'{target_team.team_name} 팀 평가가 완료되었습니다.'
            )

            return redirect(
                'admin_teacher_evaluation'
            )

        elif evaluation_type == 'INDIVIDUAL':

            target_student_id = request.POST.get(
                'target_student_id'
            )

            try:

                target_student_id = int(
                    target_student_id
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '잘못된 학생 정보입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )

            target_student = students.filter(
                student_id=target_student_id
            ).first()

            if not target_student:

                messages.error(
                    request,
                    '평가할 수 없는 학생입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )

            if TeacherIndividualScore.objects.filter(
                round_id=current_round.round_id,
                teacher_id=teacher_id,
                target_student_id=target_student_id
            ).exists():

                messages.warning(
                    request,
                    '이미 평가한 학생입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )

            score_data = []

            for question in individual_questions:

                score_value = request.POST.get(
                    f'question_{question.question_id}'
                )

                try:

                    score_value = int(
                        score_value
                    )

                except (TypeError, ValueError):

                    messages.error(
                        request,
                        '모든 문항에 점수를 입력해주세요.'
                    )

                    return redirect(
                        'admin_teacher_evaluation'
                    )

                if not 1 <= score_value <= 5:

                    messages.error(
                        request,
                        '점수는 1점부터 5점까지 입력할 수 있습니다.'
                    )

                    return redirect(
                        'admin_teacher_evaluation'
                    )

                score_data.append(
                    (
                        question,
                        score_value
                    )
                )

            for question, score_value in score_data:

                TeacherIndividualScore.objects.create(

                    round_id=current_round.round_id,

                    teacher_id=teacher_id,

                    target_student_id=target_student_id,

                    question_id=question.question_id,

                    score=score_value,

                    created_at=timezone.now()
                )

            messages.success(
                request,
                f'{target_student.name} 학생 평가가 완료되었습니다.'
            )

            return redirect(
                'admin_teacher_evaluation'
            )

    team_count = teams.count()
    completed_team_count = len(
        completed_team_ids
    )

    team_progress = (
        round(
            completed_team_count
            / team_count
            * 100
        )
        if team_count > 0
        else 0
    )

    student_count = students.count()
    completed_student_count = len(
        completed_student_ids
    )

    individual_progress = (
        round(
            completed_student_count
            / student_count
            * 100
        )
        if student_count > 0
        else 0
    )

    return render(
        request,
        'evaluations/admin_teacher_evaluation.html',
        {
            'project':
                project,

            'current_round':
                current_round,

            'teams':
                teams,

            'students':
                students,

            'team_questions':
                team_questions,

            'individual_questions':
                individual_questions,

            'completed_team_ids':
                completed_team_ids,

            'completed_student_ids':
                completed_student_ids,

            'team_count':
                team_count,

            'completed_team_count':
                completed_team_count,

            'team_progress':
                team_progress,

            'student_count':
                student_count,

            'completed_student_count':
                completed_student_count,

            'individual_progress':
                individual_progress,
        }
    )


# ==========================================
# 4. 관리자 - 평가 결과 / 석차 관리
# ==========================================
@teacher_required
def admin_result_management_view(request):

    round_id = (
        request.GET.get('round_id')
        or request.POST.get('round_id')
    )

    if round_id:

        current_round = EvaluationRound.objects.filter(
            round_id=round_id
        ).first()

    else:

        current_round = EvaluationRound.objects.order_by(
            '-round_id'
        ).first()

    all_rounds = EvaluationRound.objects.all().order_by(
        '-round_id'
    )

    if not current_round:

        return render(
            request,
            'evaluations/admin_result_management.html',
            {
                'current_round': None,
                'all_rounds': all_rounds,
                'project': None,
                'total_students': 0,
                'total_teams': 0,
                'team_progress': 0,
                'individual_progress': 0,
                'teacher_progress': 0,
                'teacher_team_progress': 0,
                'teacher_student_progress': 0,
                'teacher_team_completed': 0,
                'teacher_student_completed': 0,
                'student_results': [],
                'team_results': [],
                'can_publish': False,
            }
        )

    project = Project.objects.filter(
        project_id=current_round.project_id
    ).first()

    teams = Team.objects.filter(
        project_id=current_round.project_id
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

    student_ids = list(
        TeamMember.objects.filter(
            team_id__in=team_ids
        )
        .values_list(
            'student_id',
            flat=True
        )
        .distinct()
    )

    students = Student.objects.filter(
        student_id__in=student_ids
    ).order_by(
        'student_id'
    )

    total_students = len(
        student_ids
    )

    # ======================================
    # POST
    # ======================================
    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        if action == 'recalculate':

            messages.success(
                request,
                '현재 평가 데이터를 기준으로 점수와 등급, 석차를 다시 계산했습니다.'
            )

            return redirect(
                (
                    '/admin-eval-result/'
                    f'?round_id={current_round.round_id}'
                )
            )

        elif action == 'publish':

            EvaluationRound.objects.filter(
                round_id=current_round.round_id
            ).update(
                results_public=True
            )

            messages.success(
                request,
                '평가 결과가 공개되었습니다.'
            )

            return redirect(
                (
                    '/admin-eval-result/'
                    f'?round_id={current_round.round_id}'
                )
            )

        elif action == 'hide':

            EvaluationRound.objects.filter(
                round_id=current_round.round_id
            ).update(
                results_public=False
            )

            messages.success(
                request,
                '평가 결과가 비공개되었습니다.'
            )

            return redirect(
                (
                    '/admin-eval-result/'
                    f'?round_id={current_round.round_id}'
                )
            )

    # ======================================
    # 학생 팀 평가 진행률
    # ======================================
    team_target_count = 0

    if total_teams > 1:

        team_target_count = (
            total_students
            * (
                total_teams - 1
            )
        )

    team_completed_count = (
        TeamEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id__in=student_ids
        )
        .values(
            'evaluator_student_id',
            'target_team_id'
        )
        .distinct()
        .count()
    )

    team_progress = (
        round(
            team_completed_count
            / team_target_count
            * 100
        )
        if team_target_count > 0
        else 0
    )

    # ======================================
    # 개인 평가 진행률
    # ======================================
    individual_target_count = 0

    for team in teams:

        member_count = TeamMember.objects.filter(
            team_id=team.team_id
        ).count()

        if member_count > 1:

            individual_target_count += (
                member_count
                * (
                    member_count - 1
                )
            )

    individual_completed_count = (
        IndividualEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id__in=student_ids
        )
        .values(
            'evaluator_student_id',
            'target_student_id'
        )
        .distinct()
        .count()
    )

    individual_progress = (
        round(
            individual_completed_count
            / individual_target_count
            * 100
        )
        if individual_target_count > 0
        else 0
    )

    # ======================================
    # 선생님 평가
    # ======================================
    teacher_team_completed = (
        TeacherTeamScore.objects.filter(
            round_id=current_round.round_id
        )
        .values(
            'target_team_id'
        )
        .distinct()
        .count()
    )

    teacher_student_completed = (
        TeacherIndividualScore.objects.filter(
            round_id=current_round.round_id
        )
        .values(
            'target_student_id'
        )
        .distinct()
        .count()
    )

    teacher_team_progress = (
        round(
            teacher_team_completed
            / total_teams
            * 100
        )
        if total_teams > 0
        else 0
    )

    teacher_student_progress = (
        round(
            teacher_student_completed
            / total_students
            * 100
        )
        if total_students > 0
        else 0
    )

    teacher_target_count = (
        total_teams
        + total_students
    )

    teacher_completed_count = (
        teacher_team_completed
        + teacher_student_completed
    )

    teacher_progress = (
        round(
            teacher_completed_count
            / teacher_target_count
            * 100
        )
        if teacher_target_count > 0
        else 0
    )

    # ======================================
    # 학생 결과
    # ======================================
    student_results = []

    for student in students:

        team_member = TeamMember.objects.filter(
            student_id=student.student_id,
            team_id__in=team_ids
        ).first()

        if not team_member:

            continue

        student_team = Team.objects.filter(
            team_id=team_member.team_id
        ).first()

        # ==================================
        # A. 학생 팀 평가
        # ==================================
        team_scores = list(
            TeamEvaluationScore.objects.filter(
                round_id=current_round.round_id,
                target_team_id=team_member.team_id
            ).values_list(
                'score',
                flat=True
            )
        )

        if team_scores:

            team_average = (
                sum(team_scores)
                / len(team_scores)
            )

            team_score = (
                team_average
                / 5
                * 100
            )

        else:

            team_score = None

        # ==================================
        # B. 개인 평가
        # ==================================
        individual_scores = list(
            IndividualEvaluationScore.objects.filter(
                round_id=current_round.round_id,
                target_student_id=student.student_id
            ).values_list(
                'score',
                flat=True
            )
        )

        if individual_scores:

            individual_average = (
                sum(individual_scores)
                / len(individual_scores)
            )

            individual_score = (
                individual_average
                / 5
                * 100
            )

        else:

            individual_score = None

        # ==================================
        # C. 선생님 평가
        # ==================================
        teacher_scores = list(
            TeacherIndividualScore.objects.filter(
                round_id=current_round.round_id,
                target_student_id=student.student_id
            ).values_list(
                'score',
                flat=True
            )
        )

        if teacher_scores:

            teacher_average = (
                sum(teacher_scores)
                / len(teacher_scores)
            )

            teacher_score = (
                teacher_average
                / 5
                * 100
            )

        else:

            teacher_score = None

        # ==================================
        # D. 최종 점수 + 등급
        # ==================================
        grade_result = calculate_final_grade(

            team_score=team_score,

            individual_score=individual_score,

            teacher_score=teacher_score,

            allow_fallback=False,
        )

        final_score = grade_result[
            'final_score'
        ]

        grade = grade_result[
            'grade'
        ]

        calculation_status = grade_result[
            'status'
        ]

        calculation_complete = (
            final_score is not None
        )

        student_results.append(
            {
                'student_id':
                    student.student_id,

                'name':
                    student.name,

                'team_name':
                    (
                        student_team.team_name
                        if student_team
                        else '-'
                    ),

                'team_score':
                    (
                        round(team_score, 2)
                        if team_score is not None
                        else None
                    ),

                'individual_score':
                    (
                        round(individual_score, 2)
                        if individual_score is not None
                        else None
                    ),

                'teacher_score':
                    (
                        round(teacher_score, 2)
                        if teacher_score is not None
                        else None
                    ),

                'final_score':
                    final_score,

                # 추가
                'grade':
                    grade,

                # 추가
                'calculation_status':
                    calculation_status,

                'calculation_complete':
                    calculation_complete,

                'rank':
                    None,
            }
        )

    # ======================================
    # 개인 석차
    # 미산정 학생 제외
    # ======================================
    completed_student_results = [
        result
        for result in student_results
        if result['final_score'] is not None
    ]

    completed_student_results.sort(
        key=lambda x: x['final_score'],
        reverse=True
    )

    previous_score = None
    previous_rank = 0

    for index, result in enumerate(
        completed_student_results,
        start=1
    ):

        if result['final_score'] != previous_score:

            previous_rank = index

        result['rank'] = previous_rank

        previous_score = result[
            'final_score'
        ]

    student_results.sort(
        key=lambda x: (
            x['final_score'] is None,
            -x['final_score']
            if x['final_score'] is not None
            else 0
        )
    )

    # ======================================
    # 팀 결과
    # ======================================
    team_results = []

    for team in teams:

        member_count = TeamMember.objects.filter(
            team_id=team.team_id
        ).count()

        student_team_scores = list(
            TeamEvaluationScore.objects.filter(
                round_id=current_round.round_id,
                target_team_id=team.team_id
            ).values_list(
                'score',
                flat=True
            )
        )

        if student_team_scores:

            student_team_average = (
                sum(student_team_scores)
                / len(student_team_scores)
            )

            student_team_score = (
                student_team_average
                / 5
                * 100
            )

        else:

            student_team_score = None

        teacher_team_scores = list(
            TeacherTeamScore.objects.filter(
                round_id=current_round.round_id,
                target_team_id=team.team_id
            ).values_list(
                'score',
                flat=True
            )
        )

        if teacher_team_scores:

            teacher_team_average = (
                sum(teacher_team_scores)
                / len(teacher_team_scores)
            )

            teacher_team_score = (
                teacher_team_average
                / 5
                * 100
            )

        else:

            teacher_team_score = None

        if (
            student_team_score is not None
            and teacher_team_score is not None
        ):

            team_total_score = (
                student_team_score
                + teacher_team_score
            ) / 2

            team_total_score = round(
                team_total_score,
                2
            )

        else:

            team_total_score = None

        team_results.append(
            {
                'team_id':
                    team.team_id,

                'team_name':
                    team.team_name,

                'member_count':
                    member_count,

                'student_score':
                    (
                        round(student_team_score, 2)
                        if student_team_score is not None
                        else None
                    ),

                'teacher_score':
                    (
                        round(teacher_team_score, 2)
                        if teacher_team_score is not None
                        else None
                    ),

                'team_score':
                    team_total_score,

                'rank':
                    None,
            }
        )

    # ======================================
    # 팀 석차
    # ======================================
    completed_team_results = [
        result
        for result in team_results
        if result['team_score'] is not None
    ]

    completed_team_results.sort(
        key=lambda x: x['team_score'],
        reverse=True
    )

    previous_score = None
    previous_rank = 0

    for index, result in enumerate(
        completed_team_results,
        start=1
    ):

        if result['team_score'] != previous_score:

            previous_rank = index

        result['rank'] = previous_rank

        previous_score = result[
            'team_score'
        ]

    team_results.sort(
        key=lambda x: (
            x['team_score'] is None,
            -x['team_score']
            if x['team_score'] is not None
            else 0
        )
    )

    missing_teacher_team_count = max(
        0,
        total_teams
        - teacher_team_completed
    )

    missing_teacher_student_count = max(
        0,
        total_students
        - teacher_student_completed
    )

    can_publish = (
        current_round.status == 'COMPLETED'
        and team_progress == 100
        and individual_progress == 100
        and teacher_progress == 100
    )

    context = {

        'current_round':
            current_round,

        'all_rounds':
            all_rounds,

        'project':
            project,

        'total_students':
            total_students,

        'total_teams':
            total_teams,

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

        'teacher_progress':
            teacher_progress,

        'teacher_team_progress':
            teacher_team_progress,

        'teacher_student_progress':
            teacher_student_progress,

        'teacher_team_completed':
            teacher_team_completed,

        'teacher_student_completed':
            teacher_student_completed,

        'teacher_target_count':
            teacher_target_count,

        'teacher_completed_count':
            teacher_completed_count,

        'missing_teacher_team_count':
            missing_teacher_team_count,

        'missing_teacher_student_count':
            missing_teacher_student_count,

        'student_results':
            student_results,

        'team_results':
            team_results,

        'can_publish':
            can_publish,
    }

    return render(
        request,
        'evaluations/admin_result_management.html',
        context
    )


# ==========================================
# 5. 학생 - 팀 평가
# ==========================================
@student_required
def team_eval_list_view(request):

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

    current_project = get_current_project()

    if not current_project:

        messages.error(
            request,
            '현재 프로젝트가 없습니다.'
        )

        return redirect(
            'student_home'
        )

    my_team = get_student_team(
        student_id,
        current_project.project_id
    )

    if not my_team:

        messages.error(
            request,
            '현재 프로젝트에서 소속된 팀이 없습니다.'
        )

        return redirect(
            'student_home'
        )

    project = current_project

    current_round = EvaluationRound.objects.filter(
        project_id=current_project.project_id,
        status='IN_PROGRESS'
    ).order_by(
        '-round_id'
    ).first()

    if not current_round:

        messages.warning(
            request,
            '현재 진행 중인 평가가 없습니다.'
        )

        return redirect(
            'student_home'
        )

    questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='TEAM'
    ).order_by(
        'display_order'
    )

    target_teams = Team.objects.filter(
        project_id=current_project.project_id
    ).exclude(
        team_id=my_team.team_id
    ).order_by(
        'team_id'
    )

    completed_team_ids = list(
        TeamEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id
        )
        .values_list(
            'target_team_id',
            flat=True
        )
        .distinct()
    )

    target_team_count = target_teams.count()

    completed_team_count = len(
        completed_team_ids
    )

    team_progress = (
        round(
            completed_team_count
            / target_team_count
            * 100
        )
        if target_team_count > 0
        else 0
    )

    if request.method == 'POST':

        target_team_id = request.POST.get(
            'target_team_id'
        )

        try:

            target_team_id = int(
                target_team_id
            )

        except (TypeError, ValueError):

            messages.error(
                request,
                '잘못된 팀 정보입니다.'
            )

            return redirect(
                'team_eval_list'
            )

        if target_team_id == my_team.team_id:

            messages.error(
                request,
                '자신의 팀은 평가할 수 없습니다.'
            )

            return redirect(
                'team_eval_list'
            )

        target_team = Team.objects.filter(
            team_id=target_team_id,
            project_id=current_project.project_id
        ).first()

        if not target_team:

            messages.error(
                request,
                '평가할 수 없는 팀입니다.'
            )

            return redirect(
                'team_eval_list'
            )

        if TeamEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id,
            target_team_id=target_team_id
        ).exists():

            messages.warning(
                request,
                '이미 평가한 팀입니다.'
            )

            return redirect(
                'team_eval_list'
            )

        score_data = []

        for question in questions:

            score_value = request.POST.get(
                f'question_{question.question_id}'
            )

            try:

                score_value = int(
                    score_value
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '모든 평가 문항에 점수를 입력해주세요.'
                )

                return redirect(
                    'team_eval_list'
                )

            if not 1 <= score_value <= 5:

                messages.error(
                    request,
                    '평가 점수는 1점부터 5점까지 입력할 수 있습니다.'
                )

                return redirect(
                    'team_eval_list'
                )

            score_data.append(
                (
                    question,
                    score_value
                )
            )

        for question, score_value in score_data:

            TeamEvaluationScore.objects.create(

                round_id=current_round.round_id,

                evaluator_student_id=student_id,

                target_team_id=target_team_id,

                question_id=question.question_id,

                score=score_value,

                created_at=timezone.now()
            )

        messages.success(
            request,
            f'{target_team.team_name} 평가가 완료되었습니다.'
        )

        return redirect(
            'team_eval_list'
        )

    return render(
        request,
        'evaluations/team_eval_list.html',
        {
            'student':
                student,

            'project':
                project,

            'my_team':
                my_team,

            'current_round':
                current_round,

            'questions':
                questions,

            'target_teams':
                target_teams,

            'completed_team_ids':
                completed_team_ids,

            'target_team_count':
                target_team_count,

            'completed_team_count':
                completed_team_count,

            'team_progress':
                team_progress,
        }
    )


# ==========================================
# 6. 학생 - 개인 평가
# ==========================================
@student_required
def individual_eval_view(request):

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

    current_project = get_current_project()

    if not current_project:

        messages.error(
            request,
            '현재 프로젝트가 없습니다.'
        )

        return redirect(
            'student_home'
        )

    my_team = get_student_team(
        student_id,
        current_project.project_id
    )

    if not my_team:

        messages.error(
            request,
            '현재 프로젝트에서 소속된 팀이 없습니다.'
        )

        return redirect(
            'student_home'
        )

    project = current_project

    current_round = EvaluationRound.objects.filter(
        project_id=current_project.project_id,
        status='IN_PROGRESS'
    ).order_by(
        '-round_id'
    ).first()

    if not current_round:

        messages.warning(
            request,
            '현재 진행 중인 평가가 없습니다.'
        )

        return redirect(
            'student_home'
        )

    questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='INDIVIDUAL'
    ).order_by(
        'display_order'
    )

    team_student_ids = TeamMember.objects.filter(
        team_id=my_team.team_id
    ).values_list(
        'student_id',
        flat=True
    )

    target_students = Student.objects.filter(
        student_id__in=team_student_ids
    ).exclude(
        student_id=student_id
    ).order_by(
        'student_id'
    )

    completed_student_ids = list(
        IndividualEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id
        )
        .values_list(
            'target_student_id',
            flat=True
        )
        .distinct()
    )

    target_student_count = target_students.count()

    completed_student_count = len(
        completed_student_ids
    )

    individual_progress = (
        round(
            completed_student_count
            / target_student_count
            * 100
        )
        if target_student_count > 0
        else 0
    )

    if request.method == 'POST':

        target_student_id = request.POST.get(
            'target_student_id'
        )

        try:

            target_student_id = int(
                target_student_id
            )

        except (TypeError, ValueError):

            messages.error(
                request,
                '잘못된 학생 정보입니다.'
            )

            return redirect(
                'individual_eval'
            )

        if target_student_id == student_id:

            messages.error(
                request,
                '자기 자신은 평가할 수 없습니다.'
            )

            return redirect(
                'individual_eval'
            )

        target_student = target_students.filter(
            student_id=target_student_id
        ).first()

        if not target_student:

            messages.error(
                request,
                '현재 같은 팀의 학생만 평가할 수 있습니다.'
            )

            return redirect(
                'individual_eval'
            )

        if IndividualEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id,
            target_student_id=target_student_id
        ).exists():

            messages.warning(
                request,
                '이미 평가한 학생입니다.'
            )

            return redirect(
                'individual_eval'
            )

        score_data = []

        for question in questions:

            score_value = request.POST.get(
                f'question_{question.question_id}'
            )

            try:

                score_value = int(
                    score_value
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '모든 평가 문항에 점수를 입력해주세요.'
                )

                return redirect(
                    'individual_eval'
                )

            if not 1 <= score_value <= 5:

                messages.error(
                    request,
                    '평가 점수는 1점부터 5점까지 입력할 수 있습니다.'
                )

                return redirect(
                    'individual_eval'
                )

            score_data.append(
                (
                    question,
                    score_value
                )
            )

        for question, score_value in score_data:

            IndividualEvaluationScore.objects.create(

                round_id=current_round.round_id,

                evaluator_student_id=student_id,

                target_student_id=target_student_id,

                question_id=question.question_id,

                score=score_value,

                created_at=timezone.now()
            )

        messages.success(
            request,
            f'{target_student.name}님 평가가 완료되었습니다.'
        )

        return redirect(
            'individual_eval'
        )

    return render(
        request,
        'evaluations/individual_eval.html',
        {
            'student':
                student,

            'project':
                project,

            'my_team':
                my_team,

            'current_round':
                current_round,

            'questions':
                questions,

            'target_students':
                target_students,

            'completed_student_ids':
                completed_student_ids,

            'target_student_count':
                target_student_count,

            'completed_student_count':
                completed_student_count,

            'individual_progress':
                individual_progress,
        }
    )


# ==========================================
# 7. 학생 - 리포트
# ==========================================
@student_required
def report_view(request):

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

    current_project = get_current_project()

    if not current_project:

        return render(
            request,
            'evaluations/report.html',
            {
                'student':
                    student,

                'result_available':
                    False,

                'result_message':
                    '현재 프로젝트가 없습니다.',
            }
        )

    my_team = get_student_team(
        student_id,
        current_project.project_id
    )

    if not my_team:

        return render(
            request,
            'evaluations/report.html',
            {
                'student':
                    student,

                'project':
                    current_project,

                'result_available':
                    False,

                'result_message':
                    '현재 프로젝트에서 소속된 팀이 없습니다.',
            }
        )

    project = current_project

    current_round = EvaluationRound.objects.filter(
        project_id=current_project.project_id,
        results_public=True
    ).order_by(
        '-round_id'
    ).first()

    if not current_round:

        return render(
            request,
            'evaluations/report.html',
            {
                'student':
                    student,

                'project':
                    project,

                'my_team':
                    my_team,

                'result_available':
                    False,

                'result_message':
                    '아직 공개된 평가 결과가 없습니다.',
            }
        )

    # ======================================
    # 학생 팀 평가
    # ======================================
    team_scores = list(
        TeamEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            target_team_id=my_team.team_id
        ).values_list(
            'score',
            flat=True
        )
    )

    if team_scores:

        team_average = (
            sum(team_scores)
            / len(team_scores)
        )

        team_score = (
            team_average
            / 5
            * 100
        )

    else:

        team_average = None
        team_score = None

    # ======================================
    # 개인 평가
    # ======================================
    individual_scores = list(
        IndividualEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            target_student_id=student_id
        ).values_list(
            'score',
            flat=True
        )
    )

    if individual_scores:

        individual_average = (
            sum(individual_scores)
            / len(individual_scores)
        )

        individual_score = (
            individual_average
            / 5
            * 100
        )

    else:

        individual_average = None
        individual_score = None

    # ======================================
    # 선생님 평가
    # ======================================
    teacher_scores = list(
        TeacherIndividualScore.objects.filter(
            round_id=current_round.round_id,
            target_student_id=student_id
        ).values_list(
            'score',
            flat=True
        )
    )

    if teacher_scores:

        teacher_average = (
            sum(teacher_scores)
            / len(teacher_scores)
        )

        teacher_score = (
            teacher_average
            / 5
            * 100
        )

    else:

        teacher_average = None
        teacher_score = None

    # ======================================
    # 최종 점수 + 등급
    # ======================================
    grade_result = calculate_final_grade(

        team_score=team_score,

        individual_score=individual_score,

        teacher_score=teacher_score,

        allow_fallback=False,
    )

    final_score = grade_result[
        'final_score'
    ]

    grade = grade_result[
        'grade'
    ]

    calculation_status = grade_result[
        'status'
    ]

    # ======================================
    # 가중 점수
    # ======================================
    weighted_team_score = (
        round(
            team_score * 0.30,
            2
        )
        if team_score is not None
        else None
    )

    weighted_individual_score = (
        round(
            individual_score * 0.30,
            2
        )
        if individual_score is not None
        else None
    )

    weighted_teacher_score = (
        round(
            teacher_score * 0.40,
            2
        )
        if teacher_score is not None
        else None
    )

    # ======================================
    # 전체 학생 석차
    # 미산정 학생은 제외
    # ======================================
    project_team_ids = list(
        Team.objects.filter(
            project_id=current_project.project_id
        ).values_list(
            'team_id',
            flat=True
        )
    )

    project_student_ids = (
        TeamMember.objects.filter(
            team_id__in=project_team_ids
        )
        .values_list(
            'student_id',
            flat=True
        )
        .distinct()
    )

    all_students = Student.objects.filter(
        student_id__in=project_student_ids
    )

    ranking_data = []

    for target_student in all_students:

        target_team = get_student_team(
            target_student.student_id,
            current_project.project_id
        )

        if not target_team:
            continue

        target_team_scores = list(
            TeamEvaluationScore.objects.filter(
                round_id=current_round.round_id,
                target_team_id=target_team.team_id
            ).values_list(
                'score',
                flat=True
            )
        )

        target_individual_scores = list(
            IndividualEvaluationScore.objects.filter(
                round_id=current_round.round_id,
                target_student_id=target_student.student_id
            ).values_list(
                'score',
                flat=True
            )
        )

        target_teacher_scores = list(
            TeacherIndividualScore.objects.filter(
                round_id=current_round.round_id,
                target_student_id=target_student.student_id
            ).values_list(
                'score',
                flat=True
            )
        )

        # 미평가 영역 존재
        if (
            not target_team_scores
            or not target_individual_scores
            or not target_teacher_scores
        ):
            continue

        target_team_score = (
            (
                sum(target_team_scores)
                / len(target_team_scores)
            )
            / 5
            * 100
        )

        target_individual_score = (
            (
                sum(target_individual_scores)
                / len(target_individual_scores)
            )
            / 5
            * 100
        )

        target_teacher_score = (
            (
                sum(target_teacher_scores)
                / len(target_teacher_scores)
            )
            / 5
            * 100
        )

        target_result = calculate_final_grade(

            team_score=target_team_score,

            individual_score=target_individual_score,

            teacher_score=target_teacher_score,

            allow_fallback=False,
        )

        if target_result[
            'final_score'
        ] is None:

            continue

        ranking_data.append(
            {
                'student_id':
                    target_student.student_id,

                'final_score':
                    target_result[
                        'final_score'
                    ],
            }
        )

    ranking_data.sort(
        key=lambda x: x['final_score'],
        reverse=True
    )

    previous_score = None
    previous_rank = 0
    student_rank = None

    for index, result in enumerate(
        ranking_data,
        start=1
    ):

        if result['final_score'] != previous_score:

            previous_rank = index

        if result['student_id'] == student_id:

            student_rank = previous_rank

        previous_score = result[
            'final_score'
        ]

    # ======================================
    # HTML
    # ======================================
    return render(
        request,
        'evaluations/report.html',
        {
            'student':
                student,

            'project':
                project,

            'my_team':
                my_team,

            'current_round':
                current_round,

            'result_available':
                True,

            # 평균
            'team_average':
                (
                    round(team_average, 2)
                    if team_average is not None
                    else None
                ),

            'individual_average':
                (
                    round(individual_average, 2)
                    if individual_average is not None
                    else None
                ),

            'teacher_average':
                (
                    round(teacher_average, 2)
                    if teacher_average is not None
                    else None
                ),

            # 100점
            'team_score':
                (
                    round(team_score, 2)
                    if team_score is not None
                    else None
                ),

            'individual_score':
                (
                    round(individual_score, 2)
                    if individual_score is not None
                    else None
                ),

            'teacher_score':
                (
                    round(teacher_score, 2)
                    if teacher_score is not None
                    else None
                ),

            # 가중
            'weighted_team_score':
                weighted_team_score,

            'weighted_individual_score':
                weighted_individual_score,

            'weighted_teacher_score':
                weighted_teacher_score,

            # 최종
            'final_score':
                final_score,

            # 등급
            'grade':
                grade,

            # 계산 상태
            'calculation_status':
                calculation_status,

            # 석차
            'student_rank':
                student_rank,

            # 석차 산정 대상 학생 수
            'total_students':
                len(
                    ranking_data
                ),
        }
    )