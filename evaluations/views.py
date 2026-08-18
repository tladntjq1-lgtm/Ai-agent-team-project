from django.contrib import messages
from django.shortcuts import render, redirect

from members.decorators import student_required, teacher_required
from members.models import Student

from teams.models import Team, TeamMember

from .models import (
    EvaluationRound,
    EvaluationQuestion,
    TeamEvaluationScore,
    IndividualEvaluationScore,
)


# ==========================================
# 1. 관리자 - 평가 회차
# ==========================================
@teacher_required
def admin_evaluation_round_view(request):

    return render(
        request,
        'evaluations/admin_evaluation_round.html'
    )


# ==========================================
# 2. 관리자 - 평가 문항
# ==========================================
@teacher_required
def admin_evaluation_questions_view(request):

    return render(
        request,
        'evaluations/admin_evaluation_questions.html'
    )


# ==========================================
# 3. 관리자 - 평가 진행 현황
# ==========================================
@teacher_required
def admin_teacher_evaluation_view(request):

    return render(
        request,
        'evaluations/admin_teacher_evaluation.html'
    )


# ==========================================
# 4. 관리자 - 평가 결과
# ==========================================
@teacher_required
def admin_result_management_view(request):

    return render(
        request,
        'evaluations/admin_result_management.html'
    )


# ==========================================
# 5. 학생 - 팀 평가
# ==========================================
@student_required
def team_eval_list_view(request):

    # ======================================
    # 로그인 학생
    # ======================================
    student_id = request.session.get(
        'student_id'
    )

    student = Student.objects.filter(
        student_id=student_id
    ).first()


    # ======================================
    # 학생 팀 배정
    # ======================================
    team_member = TeamMember.objects.filter(
        student_id=student_id
    ).first()


    if not team_member:

        messages.error(
            request,
            '현재 소속된 팀이 없습니다.'
        )

        return redirect(
            'student_home'
        )


    # ======================================
    # 현재 학생 팀
    # ======================================
    my_team = Team.objects.filter(
        team_id=team_member.team_id
    ).first()


    if not my_team:

        messages.error(
            request,
            '팀 정보를 찾을 수 없습니다.'
        )

        return redirect(
            'student_home'
        )


    # ======================================
    # 현재 평가 회차
    # ======================================
    current_round = EvaluationRound.objects.filter(
        project_id=my_team.project_id,
        status='IN_PROGRESS'
    ).order_by(
        '-round_id'
    ).first()


    # 평가 진행 중인 회차가 없는 경우
    if not current_round:

        messages.warning(
            request,
            '현재 진행 중인 평가가 없습니다.'
        )

        return redirect(
            'student_home'
        )


    # ======================================
    # 팀 평가 문항
    # ======================================
    questions = EvaluationQuestion.objects.filter(
        round_id=current_round.round_id,
        question_type='TEAM'
    ).order_by(
        'display_order'
    )


    # ======================================
    # 평가 대상 팀
    #
    # 같은 프로젝트
    # + 자기 팀 제외
    # ======================================
    target_teams = Team.objects.filter(
        project_id=my_team.project_id
    ).exclude(
        team_id=my_team.team_id
    ).order_by(
        'team_id'
    )


    # ======================================
    # 이미 평가한 팀
    # ======================================
    completed_team_ids = list(
        TeamEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id
        ).values_list(
            'target_team_id',
            flat=True
        ).distinct()
    )


    # ======================================
    # POST
    # 평가 제출
    # ======================================
    if request.method == 'POST':

        target_team_id = request.POST.get(
            'target_team_id'
        )


        # ----------------------------------
        # 대상 팀 값 확인
        # ----------------------------------
        if not target_team_id:

            messages.error(
                request,
                '평가할 팀을 선택해주세요.'
            )

            return redirect(
                'team_eval_list'
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


        # ----------------------------------
        # 자기 팀 평가 방지
        # ----------------------------------
        if target_team_id == my_team.team_id:

            messages.error(
                request,
                '자신의 팀은 평가할 수 없습니다.'
            )

            return redirect(
                'team_eval_list'
            )


        # ----------------------------------
        # 다른 프로젝트 팀 평가 방지
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

            return redirect(
                'team_eval_list'
            )


        # ----------------------------------
        # 중복 평가 방지
        # ----------------------------------
        already_evaluated = TeamEvaluationScore.objects.filter(
            round_id=current_round.round_id,
            evaluator_student_id=student_id,
            target_team_id=target_team_id
        ).exists()


        if already_evaluated:

            messages.warning(
                request,
                '이미 평가한 팀입니다.'
            )

            return redirect(
                'team_eval_list'
            )


        # ======================================
        # 모든 문항 점수 검증
        # ======================================
        score_data = []


        for question in questions:

            score_value = request.POST.get(
                f'question_{question.question_id}'
            )


            # 문항 누락
            if not score_value:

                messages.error(
                    request,
                    '모든 평가 문항에 점수를 입력해주세요.'
                )

                return redirect(
                    'team_eval_list'
                )


            try:

                score_value = int(
                    score_value
                )

            except ValueError:

                messages.error(
                    request,
                    '잘못된 점수가 입력되었습니다.'
                )

                return redirect(
                    'team_eval_list'
                )


            # 1~5점 제한
            if score_value < 1 or score_value > 5:

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


        # ======================================
        # DB 저장
        # ======================================
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


    # ======================================
    # HTML 전달
    # ======================================
    context = {

        'student': student,

        'my_team': my_team,

        'current_round': current_round,

        'questions': questions,

        'target_teams': target_teams,

        'completed_team_ids': completed_team_ids,
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

    return render(
        request,
        'evaluations/individual_eval.html'
    )


# ==========================================
# 7. 학생 - 리포트
# ==========================================
@student_required
def report_view(request):

    return render(
        request,
        'evaluations/report.html'
    )