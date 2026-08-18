from django.contrib import messages
from django.shortcuts import render, redirect

from members.decorators import student_required, teacher_required
from members.models import Student

from teams.models import Team, TeamMember

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
# 1. 관리자 - 평가 회차 관리
# ==========================================
@teacher_required
def admin_evaluation_round_view(request):

    return render(
        request,
        'evaluations/admin_evaluation_round.html'
    )


# ==========================================
# 2. 관리자 - 평가 문항 관리
# ==========================================
@teacher_required
def admin_evaluation_questions_view(request):

    return render(
        request,
        'evaluations/admin_evaluation_questions.html'
    )


# ==========================================
# 3. 관리자 - 선생님 평가
# ==========================================
@teacher_required
def admin_teacher_evaluation_view(request):

    # ----------------------------------
    # 로그인 선생님
    # ----------------------------------
    teacher_id = request.session.get(
        'teacher_id'
    )

    if not teacher_id:

        messages.error(
            request,
            '선생님 로그인 정보가 없습니다.'
        )

        return redirect('login')


    # ----------------------------------
    # 현재 진행 중인 평가 회차
    # ----------------------------------
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


    # ----------------------------------
    # 프로젝트
    # ----------------------------------
    project = Project.objects.filter(
        project_id=current_round.project_id
    ).first()


    # ----------------------------------
    # 현재 프로젝트의 팀
    # ----------------------------------
    teams = Team.objects.filter(
        project_id=current_round.project_id
    ).order_by(
        'team_id'
    )


    # ----------------------------------
    # 프로젝트에 속한 학생 ID
    # ----------------------------------
    team_ids = teams.values_list(
        'team_id',
        flat=True
    )


    student_ids = TeamMember.objects.filter(
        team_id__in=team_ids
    ).values_list(
        'student_id',
        flat=True
    ).distinct()


    # ----------------------------------
    # 프로젝트 학생
    # ----------------------------------
    students = Student.objects.filter(
        student_id__in=student_ids
    ).order_by(
        'name'
    )


    # ----------------------------------
    # 팀 평가 문항
    # ----------------------------------
    team_questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='TEAM'
    ).order_by(
        'display_order'
    )


    # ----------------------------------
    # 개인 평가 문항
    # ----------------------------------
    individual_questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='INDIVIDUAL'
    ).order_by(
        'display_order'
    )


    # ----------------------------------
    # 선생님이 이미 평가한 팀
    # ----------------------------------
    completed_team_ids = list(
        TeacherTeamScore.objects.filter(
            round_id=current_round.round_id,
            teacher_id=teacher_id
        ).values_list(
            'target_team_id',
            flat=True
        ).distinct()
    )


    # ----------------------------------
    # 선생님이 이미 평가한 학생
    # ----------------------------------
    completed_student_ids = list(
        TeacherIndividualScore.objects.filter(
            round_id=current_round.round_id,
            teacher_id=teacher_id
        ).values_list(
            'target_student_id',
            flat=True
        ).distinct()
    )


    # ======================================
    # POST - 선생님 평가 제출
    # ======================================
    if request.method == 'POST':

        evaluation_type = request.POST.get(
            'evaluation_type'
        )


        # ==================================
        # A. 선생님 팀 평가
        # ==================================
        if evaluation_type == 'TEAM':

            target_team_id = request.POST.get(
                'target_team_id'
            )


            # 팀 ID 검사
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


            # 현재 프로젝트 팀인지 검사
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


            # 중복 평가 방지
            already_evaluated = (
                TeacherTeamScore.objects.filter(
                    round_id=current_round.round_id,
                    teacher_id=teacher_id,
                    target_team_id=target_team_id
                ).exists()
            )


            if already_evaluated:

                messages.warning(
                    request,
                    '이미 평가한 팀입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )


            # 평가 문항 확인
            if not team_questions.exists():

                messages.error(
                    request,
                    '등록된 팀 평가 문항이 없습니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )


            # ----------------------------------
            # 모든 문항 점수 검사
            # ----------------------------------
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


                # 1~5점
                if score_value < 1 or score_value > 5:

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


            # ----------------------------------
            # DB 저장
            # ----------------------------------
            for question, score_value in score_data:

                TeacherTeamScore.objects.create(
                    round_id=current_round.round_id,
                    teacher_id=teacher_id,
                    target_team_id=target_team_id,
                    question_id=question.question_id,
                    score=score_value
                )


            messages.success(
                request,
                f'{target_team.team_name} 팀 평가가 완료되었습니다.'
            )


            return redirect(
                'admin_teacher_evaluation'
            )


        # ==================================
        # B. 선생님 개인 평가
        # ==================================
        elif evaluation_type == 'INDIVIDUAL':

            target_student_id = request.POST.get(
                'target_student_id'
            )


            # 학생 ID 검사
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


            # 현재 프로젝트 학생인지 검사
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


            # 중복 평가 방지
            already_evaluated = (
                TeacherIndividualScore.objects.filter(
                    round_id=current_round.round_id,
                    teacher_id=teacher_id,
                    target_student_id=target_student_id
                ).exists()
            )


            if already_evaluated:

                messages.warning(
                    request,
                    '이미 평가한 학생입니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )


            # 평가 문항 확인
            if not individual_questions.exists():

                messages.error(
                    request,
                    '등록된 개인 평가 문항이 없습니다.'
                )

                return redirect(
                    'admin_teacher_evaluation'
                )


            # ----------------------------------
            # 모든 문항 점수 검사
            # ----------------------------------
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


                # 1~5점
                if score_value < 1 or score_value > 5:

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


            # ----------------------------------
            # DB 저장
            # ----------------------------------
            for question, score_value in score_data:

                TeacherIndividualScore.objects.create(
                    round_id=current_round.round_id,
                    teacher_id=teacher_id,
                    target_student_id=target_student_id,
                    question_id=question.question_id,
                    score=score_value
                )


            messages.success(
                request,
                f'{target_student.name} 학생 평가가 완료되었습니다.'
            )


            return redirect(
                'admin_teacher_evaluation'
            )


        # ==================================
        # 잘못된 평가 요청
        # ==================================
        else:

            messages.error(
                request,
                '잘못된 평가 요청입니다.'
            )

            return redirect(
                'admin_teacher_evaluation'
            )


    # ======================================
    # 진행률 계산
    # ======================================

    # 팀 평가 진행률
    team_count = teams.count()

    completed_team_count = len(
        completed_team_ids
    )


    if team_count > 0:

        team_progress = round(
            completed_team_count
            / team_count
            * 100
        )

    else:

        team_progress = 0


    # 학생 개인 평가 진행률
    student_count = students.count()

    completed_student_count = len(
        completed_student_ids
    )


    if student_count > 0:

        individual_progress = round(
            completed_student_count
            / student_count
            * 100
        )

    else:

        individual_progress = 0


    # ----------------------------------
    # HTML 전달
    # ----------------------------------
    context = {
        'project': project,
        'current_round': current_round,

        'teams': teams,
        'students': students,

        'team_questions': team_questions,
        'individual_questions': individual_questions,

        'completed_team_ids': completed_team_ids,
        'completed_student_ids': completed_student_ids,

        'team_count': team_count,
        'completed_team_count': completed_team_count,
        'team_progress': team_progress,

        'student_count': student_count,
        'completed_student_count': completed_student_count,
        'individual_progress': individual_progress,
    }


    return render(
        request,
        'evaluations/admin_teacher_evaluation.html',
        context
    )


# ==========================================
# 4. 관리자 - 평가 결과 관리
# ==========================================
@teacher_required
def admin_result_management_view(request):

    # ======================================
    # 1. 현재 평가 회차 조회
    # ======================================
    current_round = EvaluationRound.objects.order_by(
        '-round_id'
    ).first()

    if not current_round:

        return render(
            request,
            'evaluations/admin_result_management.html',
            {
                'current_round': None,
                'project': None,
                'student_results': [],
                'team_results': [],
            }
        )


    # ======================================
    # 2. 결과 공개 / 비공개 처리
    # ======================================
    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        if action == 'publish':

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
                'admin_result_management'
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
                'admin_result_management'
            )


    # ======================================
    # 3. 프로젝트 조회
    # ======================================
    project = Project.objects.filter(
        project_id=current_round.project_id
    ).first()


    # ======================================
    # 4. 프로젝트 팀 조회
    # ======================================
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


    # ======================================
    # 5. 프로젝트 학생 조회
    # ======================================
    student_ids = TeamMember.objects.filter(
        team_id__in=team_ids
    ).values_list(
        'student_id',
        flat=True
    ).distinct()


    students = Student.objects.filter(
        student_id__in=student_ids
    ).order_by(
        'student_id'
    )


    # ======================================
    # 6. 학생 결과 계산
    # ======================================
    student_results = []


    for student in students:

        # ----------------------------------
        # 학생 소속 팀
        # ----------------------------------
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

        else:

            team_average = 0


        # ==================================
        # B. 개인 상호 평가
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

        else:

            individual_average = 0


        # ==================================
        # C. 선생님 개인 평가
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

        else:

            teacher_average = 0


        # ==================================
        # D. 5점 → 100점 환산
        # ==================================
        team_score = (
            team_average
            / 5
            * 100
            if team_average
            else 0
        )


        individual_score = (
            individual_average
            / 5
            * 100
            if individual_average
            else 0
        )


        teacher_score = (
            teacher_average
            / 5
            * 100
            if teacher_average
            else 0
        )


        # ==================================
        # E. 가중치
        #
        # 팀 평가     30%
        # 개인 평가   30%
        # 선생님 평가 40%
        # ==================================
        weighted_team_score = (
            team_score
            * 0.30
        )


        weighted_individual_score = (
            individual_score
            * 0.30
        )


        weighted_teacher_score = (
            teacher_score
            * 0.40
        )


        final_score = (
            weighted_team_score
            + weighted_individual_score
            + weighted_teacher_score
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
                    round(
                        team_score,
                        2
                    ),

                'individual_score':
                    round(
                        individual_score,
                        2
                    ),

                'teacher_score':
                    round(
                        teacher_score,
                        2
                    ),

                'final_score':
                    round(
                        final_score,
                        2
                    ),
            }
        )


    # ======================================
    # 7. 학생 최종 점수순 정렬
    # ======================================
    student_results.sort(
        key=lambda x: x['final_score'],
        reverse=True
    )


    # ======================================
    # 8. 학생 석차 계산
    #
    # 동점자는 같은 등수
    # 예:
    # 95 → 1위
    # 95 → 1위
    # 90 → 3위
    # ======================================
    previous_score = None
    previous_rank = 0


    for index, result in enumerate(
        student_results,
        start=1
    ):

        if result['final_score'] != previous_score:

            previous_rank = index


        result['rank'] = previous_rank

        previous_score = result[
            'final_score'
        ]


    # ======================================
    # 9. 팀 결과 계산
    # ======================================
    team_results = []


    for team in teams:

        # ----------------------------------
        # 학생들이 해당 팀에 준 평가
        # ----------------------------------
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

        else:

            student_team_average = 0


        # ----------------------------------
        # 선생님이 해당 팀에 준 평가
        # ----------------------------------
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

        else:

            teacher_team_average = 0


        # ----------------------------------
        # 표시용 100점 환산
        # ----------------------------------
        student_team_score = (
            student_team_average
            / 5
            * 100
            if student_team_average
            else 0
        )


        teacher_team_score = (
            teacher_team_average
            / 5
            * 100
            if teacher_team_average
            else 0
        )


        team_results.append(
            {
                'team_id':
                    team.team_id,

                'team_name':
                    team.team_name,

                'student_score':
                    round(
                        student_team_score,
                        2
                    ),

                'teacher_score':
                    round(
                        teacher_team_score,
                        2
                    ),
            }
        )


    # ======================================
    # 10. HTML 전달
    # ======================================
    context = {
        'project': project,

        'current_round':
            current_round,

        'student_results':
            student_results,

        'team_results':
            team_results,
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

    # ----------------------------------
    # 로그인 학생
    # ----------------------------------
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

        return redirect('login')


    # ----------------------------------
    # 학생 팀 배정
    # ----------------------------------
    team_member = TeamMember.objects.filter(
        student_id=student_id
    ).first()


    if not team_member:

        messages.error(
            request,
            '현재 소속된 팀이 없습니다.'
        )

        return redirect('student_home')


    # ----------------------------------
    # 현재 학생 팀
    # ----------------------------------
    my_team = Team.objects.filter(
        team_id=team_member.team_id
    ).first()


    if not my_team:

        messages.error(
            request,
            '팀 정보를 찾을 수 없습니다.'
        )

        return redirect('student_home')


    # ----------------------------------
    # 프로젝트
    # ----------------------------------
    project = Project.objects.filter(
        project_id=my_team.project_id
    ).first()


    if not project:

        messages.error(
            request,
            '프로젝트 정보를 찾을 수 없습니다.'
        )

        return redirect('student_home')


    # ----------------------------------
    # 현재 진행 중인 평가 회차
    # ----------------------------------
    current_round = EvaluationRound.objects.filter(
        project_id=my_team.project_id,
        status='IN_PROGRESS'
    ).order_by(
        '-round_id'
    ).first()


    if not current_round:

        messages.warning(
            request,
            '현재 진행 중인 평가가 없습니다.'
        )

        return redirect('student_home')


    # ----------------------------------
    # 팀 평가 문항
    # ----------------------------------
    questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='TEAM'
    ).order_by(
        'display_order'
    )


    # ----------------------------------
    # 평가 대상 팀
    # 본인 팀 제외
    # ----------------------------------
    target_teams = Team.objects.filter(
        project_id=my_team.project_id
    ).exclude(
        team_id=my_team.team_id
    ).order_by(
        'team_id'
    )


    # ----------------------------------
    # 이미 평가한 팀
    # ----------------------------------
    completed_team_ids = list(
        TeamEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id
        ).values_list(
            'target_team_id',
            flat=True
        ).distinct()
    )


    # ----------------------------------
    # 팀 평가 진행률
    # ----------------------------------
    target_team_count = target_teams.count()

    completed_team_count = len(
        completed_team_ids
    )


    if target_team_count > 0:

        team_progress = round(
            completed_team_count
            / target_team_count
            * 100
        )

    else:

        team_progress = 0


    # ======================================
    # POST - 팀 평가 제출
    # ======================================
    if request.method == 'POST':

        target_team_id = request.POST.get(
            'target_team_id'
        )


        if not target_team_id:

            messages.error(
                request,
                '평가할 팀을 선택해주세요.'
            )

            return redirect('team_eval_list')


        try:

            target_team_id = int(
                target_team_id
            )

        except (TypeError, ValueError):

            messages.error(
                request,
                '잘못된 팀 정보입니다.'
            )

            return redirect('team_eval_list')


        # ----------------------------------
        # 자기 팀 평가 방지
        # ----------------------------------
        if target_team_id == my_team.team_id:

            messages.error(
                request,
                '자신의 팀은 평가할 수 없습니다.'
            )

            return redirect('team_eval_list')


        # ----------------------------------
        # 현재 프로젝트 팀인지 확인
        # ----------------------------------
        target_team = Team.objects.filter(
            team_id=target_team_id,
            project_id=my_team.project_id
        ).first()


        if not target_team:

            messages.error(
                request,
                '평가할 수 없는 팀입니다.'
            )

            return redirect('team_eval_list')


        # ----------------------------------
        # 중복 평가 방지
        # ----------------------------------
        already_evaluated = (
            TeamEvaluationScore.objects.filter(
                round_id=current_round.round_id,
                evaluator_student_id=student_id,
                target_team_id=target_team_id
            ).exists()
        )


        if already_evaluated:

            messages.warning(
                request,
                '이미 평가한 팀입니다.'
            )

            return redirect('team_eval_list')


        # ----------------------------------
        # 문항 확인
        # ----------------------------------
        if not questions.exists():

            messages.error(
                request,
                '등록된 팀 평가 문항이 없습니다.'
            )

            return redirect('team_eval_list')


        # ----------------------------------
        # 모든 점수 검증
        # ----------------------------------
        score_data = []


        for question in questions:

            score_value = request.POST.get(
                f'question_{question.question_id}'
            )


            if not score_value:

                messages.error(
                    request,
                    '모든 평가 문항에 점수를 입력해주세요.'
                )

                return redirect('team_eval_list')


            try:

                score_value = int(
                    score_value
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '잘못된 점수가 입력되었습니다.'
                )

                return redirect('team_eval_list')


            if score_value < 1 or score_value > 5:

                messages.error(
                    request,
                    '평가 점수는 1점부터 5점까지 입력할 수 있습니다.'
                )

                return redirect('team_eval_list')


            score_data.append(
                (
                    question,
                    score_value
                )
            )


        # ----------------------------------
        # DB 저장
        # ----------------------------------
        for question, score_value in score_data:

            TeamEvaluationScore.objects.create(
                round_id=current_round.round_id,
                evaluator_student_id=student_id,
                target_team_id=target_team_id,
                question_id=question.question_id,
                score=score_value
            )


        messages.success(
            request,
            f'{target_team.team_name} 평가가 완료되었습니다.'
        )


        return redirect(
            'team_eval_list'
        )


    # ----------------------------------
    # HTML 전달
    # ----------------------------------
    context = {
        'student': student,
        'project': project,
        'my_team': my_team,
        'current_round': current_round,

        'questions': questions,
        'target_teams': target_teams,
        'completed_team_ids': completed_team_ids,

        'target_team_count': target_team_count,
        'completed_team_count': completed_team_count,
        'team_progress': team_progress,
    }


    return render(
        request,
        'evaluations/team_eval_list.html',
        context
    )


# ==========================================
# 6. 학생 - 개인 평가
# ==========================================
@student_required
def individual_eval_view(request):

    # ----------------------------------
    # 로그인 학생
    # ----------------------------------
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

        return redirect('login')


    # ----------------------------------
    # 학생 팀 배정
    # ----------------------------------
    team_member = TeamMember.objects.filter(
        student_id=student_id
    ).first()


    if not team_member:

        messages.error(
            request,
            '현재 소속된 팀이 없습니다.'
        )

        return redirect('student_home')


    # ----------------------------------
    # 현재 팀
    # ----------------------------------
    my_team = Team.objects.filter(
        team_id=team_member.team_id
    ).first()


    if not my_team:

        messages.error(
            request,
            '팀 정보를 찾을 수 없습니다.'
        )

        return redirect('student_home')


    # ----------------------------------
    # 프로젝트
    # ----------------------------------
    project = Project.objects.filter(
        project_id=my_team.project_id
    ).first()


    # ----------------------------------
    # 현재 평가 회차
    # ----------------------------------
    current_round = EvaluationRound.objects.filter(
        project_id=my_team.project_id,
        status='IN_PROGRESS'
    ).order_by(
        '-round_id'
    ).first()


    if not current_round:

        messages.warning(
            request,
            '현재 진행 중인 평가가 없습니다.'
        )

        return redirect('student_home')


    # ----------------------------------
    # 개인 평가 문항
    # ----------------------------------
    questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='INDIVIDUAL'
    ).order_by(
        'display_order'
    )


    # ----------------------------------
    # 같은 팀 학생 ID
    # ----------------------------------
    team_student_ids = TeamMember.objects.filter(
        team_id=my_team.team_id
    ).values_list(
        'student_id',
        flat=True
    )


    # ----------------------------------
    # 평가 대상 학생
    # 본인 제외
    # ----------------------------------
    target_students = Student.objects.filter(
        student_id__in=team_student_ids
    ).exclude(
        student_id=student_id
    ).order_by(
        'student_id'
    )


    # ----------------------------------
    # 이미 평가한 학생
    # ----------------------------------
    completed_student_ids = list(
        IndividualEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id
        ).values_list(
            'target_student_id',
            flat=True
        ).distinct()
    )


    # ----------------------------------
    # 개인 평가 진행률
    # ----------------------------------
    target_student_count = target_students.count()

    completed_student_count = len(
        completed_student_ids
    )


    if target_student_count > 0:

        individual_progress = round(
            completed_student_count
            / target_student_count
            * 100
        )

    else:

        individual_progress = 0


    # ======================================
    # POST - 개인 평가 제출
    # ======================================
    if request.method == 'POST':

        target_student_id = request.POST.get(
            'target_student_id'
        )


        if not target_student_id:

            messages.error(
                request,
                '평가할 학생을 선택해주세요.'
            )

            return redirect('individual_eval')


        try:

            target_student_id = int(
                target_student_id
            )

        except (TypeError, ValueError):

            messages.error(
                request,
                '잘못된 학생 정보입니다.'
            )

            return redirect('individual_eval')


        # ----------------------------------
        # 자기 자신 평가 방지
        # ----------------------------------
        if target_student_id == student_id:

            messages.error(
                request,
                '자기 자신은 평가할 수 없습니다.'
            )

            return redirect('individual_eval')


        # ----------------------------------
        # 같은 팀 학생인지 확인
        # ----------------------------------
        target_student = target_students.filter(
            student_id=target_student_id
        ).first()


        if not target_student:

            messages.error(
                request,
                '평가할 수 없는 학생입니다.'
            )

            return redirect('individual_eval')


        # ----------------------------------
        # 중복 평가 방지
        # ----------------------------------
        already_evaluated = (
            IndividualEvaluationScore.objects.filter(
                round_id=current_round.round_id,
                evaluator_student_id=student_id,
                target_student_id=target_student_id
            ).exists()
        )


        if already_evaluated:

            messages.warning(
                request,
                '이미 평가한 학생입니다.'
            )

            return redirect('individual_eval')


        # ----------------------------------
        # 문항 확인
        # ----------------------------------
        if not questions.exists():

            messages.error(
                request,
                '등록된 개인 평가 문항이 없습니다.'
            )

            return redirect('individual_eval')


        # ----------------------------------
        # 모든 점수 검증
        # ----------------------------------
        score_data = []


        for question in questions:

            score_value = request.POST.get(
                f'question_{question.question_id}'
            )


            if not score_value:

                messages.error(
                    request,
                    '모든 평가 문항에 점수를 입력해주세요.'
                )

                return redirect('individual_eval')


            try:

                score_value = int(
                    score_value
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '잘못된 점수가 입력되었습니다.'
                )

                return redirect('individual_eval')


            if score_value < 1 or score_value > 5:

                messages.error(
                    request,
                    '평가 점수는 1점부터 5점까지 입력할 수 있습니다.'
                )

                return redirect('individual_eval')


            score_data.append(
                (
                    question,
                    score_value
                )
            )


        # ----------------------------------
        # DB 저장
        # ----------------------------------
        for question, score_value in score_data:

            IndividualEvaluationScore.objects.create(
                round_id=current_round.round_id,
                evaluator_student_id=student_id,
                target_student_id=target_student_id,
                question_id=question.question_id,
                score=score_value
            )


        messages.success(
            request,
            f'{target_student.name}님 평가가 완료되었습니다.'
        )


        return redirect(
            'individual_eval'
        )


    # ----------------------------------
    # HTML 전달
    # ----------------------------------
    context = {
        'student': student,
        'project': project,
        'my_team': my_team,
        'current_round': current_round,

        'questions': questions,
        'target_students': target_students,
        'completed_student_ids': completed_student_ids,

        'target_student_count': target_student_count,
        'completed_student_count': completed_student_count,
        'individual_progress': individual_progress,
    }


    return render(
        request,
        'evaluations/individual_eval.html',
        context
    )


# ==========================================
# 7. 학생 - 평가 결과 리포트
# ==========================================
@student_required
def report_view(request):

    # ----------------------------------
    # 로그인 학생
    # ----------------------------------
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

        return redirect('login')


    # ----------------------------------
    # 학생 팀 배정
    # ----------------------------------
    team_member = TeamMember.objects.filter(
        student_id=student_id
    ).first()


    if not team_member:

        return render(
            request,
            'evaluations/report.html',
            {
                'student': student,
                'result_available': False,
                'result_message': '현재 소속된 팀이 없습니다.'
            }
        )


    # ----------------------------------
    # 현재 팀
    # ----------------------------------
    my_team = Team.objects.filter(
        team_id=team_member.team_id
    ).first()


    if not my_team:

        return render(
            request,
            'evaluations/report.html',
            {
                'student': student,
                'result_available': False,
                'result_message': '팀 정보를 찾을 수 없습니다.'
            }
        )


    # ----------------------------------
    # 프로젝트
    # ----------------------------------
    project = Project.objects.filter(
        project_id=my_team.project_id
    ).first()


    # ----------------------------------
    # 결과가 공개된 최근 평가 회차
    # ----------------------------------
    current_round = EvaluationRound.objects.filter(
        project_id=my_team.project_id,
        results_public=True
    ).order_by(
        '-round_id'
    ).first()


    if not current_round:

        return render(
            request,
            'evaluations/report.html',
            {
                'student': student,
                'project': project,
                'my_team': my_team,

                'result_available': False,

                'result_message':
                    '아직 공개된 평가 결과가 없습니다.'
            }
        )


    # ======================================
    # 1. 학생 팀 평가 평균
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

    else:

        team_average = 0


    # ======================================
    # 2. 개인 상호 평가 평균
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

    else:

        individual_average = 0


    # ======================================
    # 3. 선생님 개인 평가 평균
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

    else:

        teacher_average = 0


    # ======================================
    # 4. 5점 → 100점 환산
    # ======================================
    if team_average > 0:

        team_score = (
            team_average
            / 5
            * 100
        )

    else:

        team_score = 0


    if individual_average > 0:

        individual_score = (
            individual_average
            / 5
            * 100
        )

    else:

        individual_score = 0


    if teacher_average > 0:

        teacher_score = (
            teacher_average
            / 5
            * 100
        )

    else:

        teacher_score = 0


    # ======================================
    # 5. 최종 가중치
    #
    # 학생 팀 평가 30%
    # 개인 평가 30%
    # 선생님 평가 40%
    # ======================================
    weighted_team_score = (
        team_score
        * 0.30
    )


    weighted_individual_score = (
        individual_score
        * 0.30
    )


    weighted_teacher_score = (
        teacher_score
        * 0.40
    )


    final_score = (
        weighted_team_score
        + weighted_individual_score
        + weighted_teacher_score
    )


    # ======================================
    # 6. 소수점 정리
    # ======================================
    team_average = round(
        team_average,
        2
    )


    individual_average = round(
        individual_average,
        2
    )


    teacher_average = round(
        teacher_average,
        2
    )


    team_score = round(
        team_score,
        2
    )


    individual_score = round(
        individual_score,
        2
    )


    teacher_score = round(
        teacher_score,
        2
    )


    weighted_team_score = round(
        weighted_team_score,
        2
    )


    weighted_individual_score = round(
        weighted_individual_score,
        2
    )


    weighted_teacher_score = round(
        weighted_teacher_score,
        2
    )


    final_score = round(
        final_score,
        2
    )


    # ======================================
    # 7. HTML 전달
    # ======================================
    context = {
        'student': student,

        'project': project,

        'my_team': my_team,

        'current_round': current_round,

        'result_available': True,

        # 5점 평균
        'team_average': team_average,
        'individual_average': individual_average,
        'teacher_average': teacher_average,

        # 100점 환산
        'team_score': team_score,
        'individual_score': individual_score,
        'teacher_score': teacher_score,

        # 가중치 반영
        'weighted_team_score': weighted_team_score,

        'weighted_individual_score':
            weighted_individual_score,

        'weighted_teacher_score':
            weighted_teacher_score,

        # 최종 점수
        'final_score': final_score,
    }


    return render(
        request,
        'evaluations/report.html',
        context
    )