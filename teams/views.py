import random

from django.contrib import messages
from django.shortcuts import render, redirect

from members.decorators import student_required, teacher_required
from members.models import Student

from evaluations.models import (
    Project,
    EvaluationRound,
    TeamEvaluationScore,
    IndividualEvaluationScore,
    TeacherIndividualScore,
    TeacherTeamScore,
)

from .models import Team, TeamMember


# ==========================================
# 학생 최종 점수 계산 함수
# ==========================================
def calculate_student_score(
    student_id,
    evaluation_round
):

    # ======================================
    # 1. 평가 회차 프로젝트의 팀 조회
    # ======================================
    project_teams = Team.objects.filter(
        project_id=evaluation_round.project_id
    )

    project_team_ids = list(
        project_teams.values_list(
            'team_id',
            flat=True
        )
    )


    # ======================================
    # 2. 해당 프로젝트에서 학생 팀 조회
    # ======================================
    team_member = TeamMember.objects.filter(
        student_id=student_id,
        team_id__in=project_team_ids
    ).first()


    if not team_member:

        return None


    # ======================================
    # 3. 학생 팀 평가 평균
    # ======================================
    team_scores = list(
        TeamEvaluationScore.objects.filter(
            round_id=evaluation_round.round_id,
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


    # ======================================
    # 4. 개인 상호평가 평균
    # ======================================
    individual_scores = list(
        IndividualEvaluationScore.objects.filter(
            round_id=evaluation_round.round_id,
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
    # 5. 선생님 개인 평가 평균
    # ======================================
    teacher_scores = list(
        TeacherIndividualScore.objects.filter(
            round_id=evaluation_round.round_id,
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
    # 6. 평가 데이터가 아예 없는 경우
    # ======================================
    if (
        not team_scores
        and not individual_scores
        and not teacher_scores
    ):

        return None


    # ======================================
    # 7. 5점 → 100점 환산
    # ======================================
    team_score = (
        team_average
        / 5
        * 100
    )

    individual_score = (
        individual_average
        / 5
        * 100
    )

    teacher_score = (
        teacher_average
        / 5
        * 100
    )


    # ======================================
    # 8. 최종 점수
    #
    # 팀 평가     30%
    # 개인 평가   30%
    # 선생님 평가 40%
    # ======================================
    final_score = (
        team_score * 0.30
        + individual_score * 0.30
        + teacher_score * 0.40
    )


    return round(
        final_score,
        2
    )


# ==========================================
# 이전 팀원 관계 조회 함수
# ==========================================
def get_previous_teammates(evaluation_round):

    previous_teams = Team.objects.filter(
        project_id=evaluation_round.project_id
    )

    previous_teammates = {}

    for team in previous_teams:

        member_ids = list(
            TeamMember.objects.filter(
                team_id=team.team_id
            ).values_list(
                'student_id',
                flat=True
            )
        )

        for student_id in member_ids:

            previous_teammates.setdefault(
                student_id,
                set()
            )

            for teammate_id in member_ids:

                if teammate_id != student_id:

                    previous_teammates[
                        student_id
                    ].add(
                        teammate_id
                    )

    return previous_teammates


# ==========================================
# 평가 기록이 연결된 팀인지 확인
# ==========================================
def has_team_evaluation_history(team_ids):

    team_ids = list(team_ids)

    if not team_ids:
        return False

    student_team_history_exists = (
        TeamEvaluationScore.objects.filter(
            target_team_id__in=team_ids
        ).exists()
    )

    teacher_team_history_exists = (
        TeacherTeamScore.objects.filter(
            target_team_id__in=team_ids
        ).exists()
    )

    return (
        student_team_history_exists
        or teacher_team_history_exists
    )


# ==========================================
# 현재 프로젝트의 팀 편성을 안전하게 초기화
#
# 평가 기록이 존재하는 프로젝트의 팀은
# 삭제하지 않고 False를 반환합니다.
# ==========================================
def clear_current_project_teams_safely(project):

    existing_teams = Team.objects.filter(
        project_id=project.project_id
    )

    existing_team_ids = list(
        existing_teams.values_list(
            'team_id',
            flat=True
        )
    )

    if has_team_evaluation_history(
        existing_team_ids
    ):
        return False

    TeamMember.objects.filter(
        team_id__in=existing_team_ids
    ).delete()

    existing_teams.delete()

    return True


# ==========================================
# 1. 관리자 - 팀 관리
# ==========================================
@teacher_required
def admin_team_management_view(request):

    # ======================================
    # 1. 프로젝트 선택
    # ======================================
    project_id = (
        request.GET.get('project_id')
        or request.POST.get('project_id')
    )


    if not project_id:

        project = Project.objects.order_by(
            '-project_id'
        ).first()

    else:

        project = Project.objects.filter(
            project_id=project_id
        ).first()


    # ======================================
    # 2. 프로젝트가 없는 경우
    # ======================================
    if not project:

        return render(
            request,
            'teams/admin_team_management.html',
            {
                'project': None,
                'projects': [],
                'teams': [],
                'team_cards': [],
                'unassigned_students': [],
                'completed_rounds': [],
                'total_students': 0,
                'assigned_count': 0,
                'unassigned_count': 0,
            }
        )


    # ======================================
    # 3. 프로젝트 목록
    # ======================================
    projects = Project.objects.all().order_by(
        '-project_id'
    )


    # ======================================
    # 4. 균형 편성용 완료 회차
    # ======================================
    completed_rounds = EvaluationRound.objects.filter(
        status='COMPLETED'
    ).order_by(
        '-round_id'
    )


    # ======================================
    # 5. POST 처리
    # ======================================
    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )


        # ==================================
        # A. 팀 생성
        # ==================================
        if action == 'create_team':

            team_name = request.POST.get(
                'team_name'
            )


            if not team_name:

                messages.error(
                    request,
                    '팀 이름을 입력해주세요.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            if Team.objects.filter(
                project_id=project.project_id,
                team_name=team_name
            ).exists():

                messages.warning(
                    request,
                    '이미 존재하는 팀 이름입니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            Team.objects.create(
                project_id=project.project_id,
                team_name=team_name
            )


            messages.success(
                request,
                f'{team_name} 팀이 생성되었습니다.'
            )


            return redirect(
                f'/admin-teams/?project_id={project.project_id}'
            )


        # ==================================
        # B. 학생 수동 배정 / 팀 이동
        # ==================================
        elif action == 'assign_student':

            student_id = request.POST.get(
                'student_id'
            )

            team_id = request.POST.get(
                'team_id'
            )


            try:

                student_id = int(
                    student_id
                )

                team_id = int(
                    team_id
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '잘못된 학생 또는 팀 정보입니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            student = Student.objects.filter(
                student_id=student_id
            ).first()


            target_team = Team.objects.filter(
                team_id=team_id,
                project_id=project.project_id
            ).first()


            if not student or not target_team:

                messages.error(
                    request,
                    '학생 또는 팀 정보를 찾을 수 없습니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            project_team_ids = Team.objects.filter(
                project_id=project.project_id
            ).values_list(
                'team_id',
                flat=True
            )


            # 같은 프로젝트 안 기존 배정 제거
            TeamMember.objects.filter(
                student_id=student.student_id,
                team_id__in=project_team_ids
            ).delete()


            # 새 팀 배정
            TeamMember.objects.create(
                team_id=target_team.team_id,
                student_id=student.student_id
            )


            messages.success(
                request,
                f'{student.name} 학생이 {target_team.team_name}에 배정되었습니다.'
            )


            return redirect(
                f'/admin-teams/?project_id={project.project_id}'
            )


        # ==================================
        # C. 학생 팀에서 제외
        # ==================================
        elif action == 'remove_student':

            team_member_id = request.POST.get(
                'team_member_id'
            )


            try:

                team_member_id = int(
                    team_member_id
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '잘못된 팀원 정보입니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            team_member = TeamMember.objects.filter(
                team_member_id=team_member_id
            ).first()


            if not team_member:

                messages.error(
                    request,
                    '팀원 정보를 찾을 수 없습니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            team = Team.objects.filter(
                team_id=team_member.team_id,
                project_id=project.project_id
            ).first()


            if not team:

                messages.error(
                    request,
                    '현재 프로젝트의 팀원이 아닙니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            student = Student.objects.filter(
                student_id=team_member.student_id
            ).first()


            team_member.delete()


            if student:

                messages.success(
                    request,
                    f'{student.name} 학생이 팀에서 제외되었습니다.'
                )

            else:

                messages.success(
                    request,
                    '학생이 팀에서 제외되었습니다.'
                )


            return redirect(
                f'/admin-teams/?project_id={project.project_id}'
            )


        # ==================================
        # D. 팀 삭제
        # ==================================
        elif action == 'delete_team':

            team_id = request.POST.get(
                'team_id'
            )


            try:

                team_id = int(
                    team_id
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '잘못된 팀 정보입니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            team = Team.objects.filter(
                team_id=team_id,
                project_id=project.project_id
            ).first()


            if not team:

                messages.error(
                    request,
                    '팀 정보를 찾을 수 없습니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            # 평가 기록이 연결된 과거 팀은 삭제 금지
            if has_team_evaluation_history(
                [team.team_id]
            ):

                messages.error(
                    request,
                    (
                        '이 팀은 평가 기록에서 사용 중이므로 삭제할 수 없습니다. '
                        '과거 평가 기록 보존을 위해 새 프로젝트에서 팀을 편성해주세요.'
                    )
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            TeamMember.objects.filter(
                team_id=team.team_id
            ).delete()


            team_name = team.team_name


            team.delete()


            messages.success(
                request,
                f'{team_name} 팀이 삭제되었습니다.'
            )


            return redirect(
                f'/admin-teams/?project_id={project.project_id}'
            )


        # ==================================
        # E. 랜덤 자동 편성
        # ==================================
        elif action == 'random_assign':

            team_count_value = request.POST.get(
                'team_count'
            )


            try:

                team_count_value = int(
                    team_count_value
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '팀 수를 올바르게 입력해주세요.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            if team_count_value < 2:

                messages.error(
                    request,
                    '팀은 최소 2개 이상이어야 합니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            students = list(
                Student.objects.all().order_by(
                    'student_id'
                )
            )


            if not students:

                messages.error(
                    request,
                    '편성할 학생이 없습니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            if team_count_value > len(students):

                messages.error(
                    request,
                    '학생 수보다 팀 수가 많을 수 없습니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            # ----------------------------------
            # 기존 현재 프로젝트 팀 안전 초기화
            #
            # 평가 기록이 연결된 과거 프로젝트라면
            # 기존 팀을 삭제하지 않습니다.
            # ----------------------------------
            cleared = clear_current_project_teams_safely(
                project
            )


            if not cleared:

                messages.error(
                    request,
                    (
                        '현재 프로젝트에는 이미 평가 기록이 연결되어 있어 '
                        '팀을 다시 편성할 수 없습니다. '
                        '새 프로젝트를 만든 뒤 랜덤 편성을 실행해주세요.'
                    )
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            # ----------------------------------
            # 새 팀 생성
            # ----------------------------------
            new_teams = []


            for index in range(
                1,
                team_count_value + 1
            ):

                team = Team.objects.create(
                    project_id=project.project_id,
                    team_name=f'{index}팀'
                )

                new_teams.append(
                    team
                )


            # ----------------------------------
            # 학생 랜덤 섞기
            # ----------------------------------
            random.shuffle(
                students
            )


            # ----------------------------------
            # 균등 순환 배정
            # ----------------------------------
            for index, student in enumerate(
                students
            ):

                target_team = new_teams[
                    index % team_count_value
                ]


                TeamMember.objects.create(
                    team_id=target_team.team_id,
                    student_id=student.student_id
                )


            messages.success(
                request,
                f'{len(students)}명의 학생을 {team_count_value}개 팀으로 랜덤 편성했습니다.'
            )


            return redirect(
                f'/admin-teams/?project_id={project.project_id}'
            )


        # ==================================
        # F. 평가 점수 균형 편성
        # + 이전 팀원 중복 최소화
        # ==================================
        elif action == 'balanced_assign':

            team_count_value = request.POST.get(
                'team_count'
            )

            source_round_id = request.POST.get(
                'source_round_id'
            )

            try:

                team_count_value = int(
                    team_count_value
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    '팀 수를 올바르게 입력해주세요.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )

            if team_count_value < 2:

                messages.error(
                    request,
                    '팀은 최소 2개 이상이어야 합니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )

            source_round = EvaluationRound.objects.filter(
                round_id=source_round_id,
                status='COMPLETED'
            ).first()

            if not source_round:

                messages.error(
                    request,
                    '균형 편성에 사용할 완료된 평가 회차를 선택해주세요.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            # ----------------------------------
            # 과거 평가 프로젝트 자체를
            # 새 팀 편성 대상으로 사용하면 안 됨
            # ----------------------------------
            if (
                source_round.project_id
                == project.project_id
            ):

                messages.error(
                    request,
                    (
                        '기준 평가 회차가 속한 과거 프로젝트에는 '
                        '새 팀을 편성할 수 없습니다. '
                        '새 프로젝트를 선택한 뒤 균형 편성을 실행해주세요.'
                    )
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            students = list(
                Student.objects.all().order_by(
                    'student_id'
                )
            )

            if not students:

                messages.error(
                    request,
                    '편성할 학생이 없습니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )

            if team_count_value > len(students):

                messages.error(
                    request,
                    '학생 수보다 팀 수가 많을 수 없습니다.'
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )

            # ----------------------------------
            # 중요:
            # 현재 팀을 삭제하기 전에
            # 기준 회차의 과거 팀원 관계를 조회
            # ----------------------------------
            previous_teammates = (
                get_previous_teammates(
                    source_round
                )
            )

            # ----------------------------------
            # 학생별 이전 평가 점수 계산
            # ----------------------------------
            students_with_scores = []
            existing_scores = []

            for student in students:

                final_score = (
                    calculate_student_score(
                        student.student_id,
                        source_round
                    )
                )

                if final_score is not None:

                    existing_scores.append(
                        final_score
                    )

                students_with_scores.append(
                    {
                        'student':
                            student,

                        'score':
                            final_score,
                    }
                )

            # ----------------------------------
            # 점수 없는 학생은 평균점수 사용
            # ----------------------------------
            if existing_scores:

                average_score = (
                    sum(existing_scores)
                    / len(existing_scores)
                )

            else:

                average_score = 50

            average_score = round(
                average_score,
                2
            )

            for student_data in students_with_scores:

                if student_data['score'] is None:

                    student_data['score'] = (
                        average_score
                    )

            # ----------------------------------
            # 높은 점수 순 정렬
            # ----------------------------------
            students_with_scores.sort(
                key=lambda x: x['score'],
                reverse=True
            )

            # ----------------------------------
            # 현재 프로젝트 팀 안전 초기화
            #
            # 새 프로젝트에 임시 팀이 이미 있다면
            # 평가 기록이 없는 경우에만 삭제 후 재생성
            # ----------------------------------
            cleared = clear_current_project_teams_safely(
                project
            )


            if not cleared:

                messages.error(
                    request,
                    (
                        '현재 프로젝트의 팀이 이미 평가 기록에서 사용 중입니다. '
                        '과거 기록을 보호하기 위해 자동 재편성을 중단했습니다. '
                        '새 프로젝트에서 다시 시도해주세요.'
                    )
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )

            # ----------------------------------
            # 새 팀 생성
            # ----------------------------------
            new_teams = []

            for index in range(
                1,
                team_count_value + 1
            ):

                team = Team.objects.create(
                    project_id=project.project_id,
                    team_name=f'{index}팀'
                )

                new_teams.append(
                    team
                )

            # ----------------------------------
            # 팀별 현재 상태
            # ----------------------------------
            team_states = []

            for team in new_teams:

                team_states.append(
                    {
                        'team':
                            team,

                        'members':
                            [],

                        'total_score':
                            0,
                    }
                )

            # 팀 최대 인원
            max_team_size = (
                len(students)
                + team_count_value
                - 1
            ) // team_count_value

            total_repeat_count = 0

            # ----------------------------------
            # 실제 배정
            #
            # 1순위 이전 팀원 중복 최소
            # 2순위 팀 인원 최소
            # 3순위 팀 누적점수 최소
            # ----------------------------------
            for student_data in students_with_scores:

                student = student_data[
                    'student'
                ]

                student_score = student_data[
                    'score'
                ]

                old_teammates = (
                    previous_teammates.get(
                        student.student_id,
                        set()
                    )
                )

                candidate_teams = []

                for team_state in team_states:

                    if len(
                        team_state['members']
                    ) >= max_team_size:

                        continue

                    repeat_count = sum(
                        1
                        for member_id
                        in team_state['members']
                        if member_id
                        in old_teammates
                    )

                    candidate_teams.append(
                        {
                            'state':
                                team_state,

                            'repeat_count':
                                repeat_count,
                        }
                    )

                candidate_teams.sort(
                    key=lambda item: (
                        item['repeat_count'],
                        len(
                            item['state'][
                                'members'
                            ]
                        ),
                        item['state'][
                            'total_score'
                        ],
                    )
                )

                selected = candidate_teams[0]

                target_state = selected[
                    'state'
                ]

                total_repeat_count += selected[
                    'repeat_count'
                ]

                TeamMember.objects.create(
                    team_id=target_state[
                        'team'
                    ].team_id,
                    student_id=student.student_id
                )

                target_state[
                    'members'
                ].append(
                    student.student_id
                )

                target_state[
                    'total_score'
                ] += student_score

            messages.success(
                request,
                (
                    f'{source_round.round_name}의 평가 점수를 기준으로 '
                    f'{len(students)}명을 {team_count_value}개 팀으로 '
                    '점수 균형 + 이전 팀원 중복 최소화 방식으로 편성했습니다. '
                    f'(이전 팀원 중복 {total_repeat_count}건)'
                )
            )

            return redirect(
                f'/admin-teams/?project_id={project.project_id}'
            )


        # ==================================
        # G. 전체 팀 초기화
        # ==================================
        elif action == 'reset_teams':

            teams = Team.objects.filter(
                project_id=project.project_id
            )


            team_ids = list(
                teams.values_list(
                    'team_id',
                    flat=True
                )
            )


            if has_team_evaluation_history(
                team_ids
            ):

                messages.error(
                    request,
                    (
                        '현재 프로젝트에는 평가 기록이 연결된 팀이 있어 '
                        '전체 팀 초기화를 할 수 없습니다. '
                        '과거 평가 기록은 보존되어야 합니다.'
                    )
                )

                return redirect(
                    f'/admin-teams/?project_id={project.project_id}'
                )


            TeamMember.objects.filter(
                team_id__in=team_ids
            ).delete()


            teams.delete()


            messages.success(
                request,
                '현재 프로젝트의 팀 편성이 초기화되었습니다.'
            )


            return redirect(
                f'/admin-teams/?project_id={project.project_id}'
            )


    # ======================================
    # 6. GET - 현재 프로젝트 팀 목록
    # ======================================
    teams = Team.objects.filter(
        project_id=project.project_id
    ).order_by(
        'team_id'
    )


    # ======================================
    # 7. 팀별 학생 정보
    # ======================================
    team_cards = []

    assigned_student_ids = []


    for team in teams:

        team_members = TeamMember.objects.filter(
            team_id=team.team_id
        ).order_by(
            'team_member_id'
        )


        member_cards = []


        for team_member in team_members:

            student = Student.objects.filter(
                student_id=team_member.student_id
            ).first()


            if student:

                assigned_student_ids.append(
                    student.student_id
                )


                member_cards.append(
                    {
                        'team_member_id':
                            team_member.team_member_id,

                        'student':
                            student,
                    }
                )


        team_cards.append(
            {
                'team':
                    team,

                'members':
                    member_cards,

                'member_count':
                    len(member_cards),
            }
        )


    # ======================================
    # 8. 미배정 학생
    # ======================================
    unassigned_students = Student.objects.exclude(
        student_id__in=assigned_student_ids
    ).order_by(
        'name'
    )


    # ======================================
    # 9. 통계
    # ======================================
    total_students = Student.objects.count()

    assigned_count = len(
        set(assigned_student_ids)
    )

    unassigned_count = (
        total_students
        - assigned_count
    )


    # ======================================
    # 10. HTML 전달
    # ======================================
    context = {
        'project':
            project,

        'projects':
            projects,

        'teams':
            teams,

        'team_cards':
            team_cards,

        'unassigned_students':
            unassigned_students,

        'completed_rounds':
            completed_rounds,

        'total_students':
            total_students,

        'assigned_count':
            assigned_count,

        'unassigned_count':
            unassigned_count,
    }


    return render(
        request,
        'teams/admin_team_management.html',
        context
    )


# ==========================================
# 2. 학생 - 내 팀
# ==========================================
@student_required
def my_team_view(request):

    # ======================================
    # 1. 로그인 학생
    # ======================================
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


    # ======================================
    # 2. 현재 프로젝트 조회
    #
    # MVP에서는 가장 최근 프로젝트 사용
    # ======================================
    current_project = Project.objects.order_by(
        '-project_id'
    ).first()


    # ======================================
    # 3. 프로젝트가 없는 경우
    # ======================================
    if not current_project:

        return render(
            request,
            'teams/my_team.html',
            {
                'student': student,
                'project': None,
                'has_team': False,
            }
        )


    # ======================================
    # 4. 현재 프로젝트 팀 ID
    # ======================================
    current_project_team_ids = Team.objects.filter(
        project_id=current_project.project_id
    ).values_list(
        'team_id',
        flat=True
    )


    # ======================================
    # 5. 현재 프로젝트에서
    #    학생의 팀 배정 조회
    # ======================================
    team_member = TeamMember.objects.filter(
        student_id=student_id,
        team_id__in=current_project_team_ids
    ).first()


    # ======================================
    # 6. 팀 미배정
    # ======================================
    if not team_member:

        return render(
            request,
            'teams/my_team.html',
            {
                'student': student,
                'project': current_project,
                'has_team': False,
            }
        )


    # ======================================
    # 7. 실제 팀 조회
    # ======================================
    team = Team.objects.filter(
        team_id=team_member.team_id,
        project_id=current_project.project_id
    ).first()


    if not team:

        return render(
            request,
            'teams/my_team.html',
            {
                'student': student,
                'project': current_project,
                'has_team': False,
            }
        )


    # ======================================
    # 8. 같은 팀 학생 ID
    # ======================================
    team_student_ids = TeamMember.objects.filter(
        team_id=team.team_id
    ).values_list(
        'student_id',
        flat=True
    )


    # ======================================
    # 9. 같은 팀 학생 정보
    # ======================================
    team_students = Student.objects.filter(
        student_id__in=team_student_ids
    ).order_by(
        'student_id'
    )


    # ======================================
    # 10. HTML 전달
    # ======================================
    context = {
        'student':
            student,

        'team':
            team,

        'project':
            current_project,

        'team_students':
            team_students,

        'has_team':
            True,
    }


    return render(
        request,
        'teams/my_team.html',
        context
    )