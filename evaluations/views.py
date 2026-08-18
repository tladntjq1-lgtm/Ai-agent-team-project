from django.shortcuts import render, redirect

from members.decorators import student_required, teacher_required


# ==========================================
# 1. 관리자 - 평가 회차 관리
# ==========================================
# 튜터가 전체 평가 리스트를 확인하고
# 새로운 평가 회차(프로젝트)를 생성하는 진입점.
#
# 추후:
# 시작일 / 종료일에 따른 평가 상태
# READY / IN_PROGRESS / COMPLETED 등의
# 상태 판별 및 변경 로직 추가 예정
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
# 튜터가 새 회차 생성 시
# 팀 평가 / 개인 평가 문항을 설정하는 화면.
#
# 추후:
# READY 상태에서만 문항
# 추가 / 수정 / 삭제 가능하도록 구현
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
# 튜터가 특정 평가의 진행률과
# 미제출자 명단을 확인하는 화면.
#
# 추후:
# 전체 인원 대비
# 팀 평가 / 개인 평가 제출률 계산
# ==========================================
@teacher_required
def admin_teacher_evaluation_view(request):

    return render(
        request,
        'evaluations/admin_teacher_evaluation.html'
    )


# ==========================================
# 4. 관리자 - 평가 결과 관리
# ==========================================
# 튜터가 수강생별 평가 결과와
# 최종 점수 등을 확인하는 화면.
#
# 추후:
# 최종 점수 / 석차 계산 및
# 결과 공개 기능 추가
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
# 학생이 다른 팀을 평가하는 화면.
#
# 추후:
# - 본인 팀 평가 금지
# - 이미 평가한 팀 중복 평가 금지
# - 평가 문항 DB 조회
# - 평가 결과 DB 저장
# ==========================================
@student_required
def team_eval_list_view(request):

    # ----------------------------------
    # POST
    # 평가 제출
    # ----------------------------------
    if request.method == 'POST':

        # 현재는 DB 저장 전 테스트 단계
        print(
            "넘어온 팀 평가 데이터:",
            request.POST
        )

        return redirect(
            'team_eval_list'
        )


    # ----------------------------------
    # GET
    # 테스트용 팀 평가 문항
    # ----------------------------------
    mock_questions = [
        {
            "id": 1,
            "text": "프로젝트 목표를 명확히 이해하고 진행하였는가?"
        },
        {
            "id": 2,
            "text": "팀 간의 의견 조율이 원활하게 이루어졌는가?"
        },
        {
            "id": 3,
            "text": "결과물의 완성도가 요구사항을 충족하는가?"
        },
        {
            "id": 4,
            "text": "문제 발생 시 논리적인 해결책을 제시하였는가?"
        },
        {
            "id": 5,
            "text": "전반적인 협업 태도가 우수하였는가?"
        },
    ]

    context = {
        # 현재는 테스트용 데이터
        'target_team': 'Team 2',

        'questions': mock_questions,
    }

    return render(
        request,
        'evaluations/team_eval_list.html',
        context
    )


# ==========================================
# 6. 학생 - 개인 평가
# ==========================================
# 학생이 자신과 같은 팀에 속한
# 팀원들을 개인 평가하는 화면.
#
# 추후:
# - 본인 제외
# - 같은 팀원만 표시
# - 중복 평가 금지
# - 평가 결과 DB 저장
# ==========================================
@student_required
def individual_eval_view(request):

    # ----------------------------------
    # POST
    # 개인 평가 제출
    # ----------------------------------
    if request.method == 'POST':

        print(
            "개인 평가 넘어온 데이터:",
            request.POST
        )

        return redirect(
            'individual_eval'
        )


    # ----------------------------------
    # GET
    # 테스트용 개인 평가 문항
    # ----------------------------------
    mock_questions = [
        {
            "id": 1,
            "text": "팀 프로젝트에 적극적으로 참여했나요?"
        },
        {
            "id": 2,
            "text": "맡은 역할과 업무를 책임감 있게 수행했나요?"
        },
        {
            "id": 3,
            "text": "팀원들과 원활하게 소통하고 협업했나요?"
        },
    ]

    context = {
        'questions': mock_questions,
    }

    return render(
        request,
        'evaluations/individual_eval.html',
        context
    )


# ==========================================
# 7. 학생 - 평가 결과 리포트
# ==========================================
# 평가 종료 후 학생이
# 자신의 최종 평가 결과를 확인하는 화면.
#
# 최종 평가 가중치:
# - 학생 팀 평가 30%
# - 개인 평가 30%
# - 선생님 평가 40%
#
# 추후:
# 평가 결과가 공개 상태일 때만
# 점수 / 석차 / 팀 결과 표시
# ==========================================
@student_required
def report_view(request):

    return render(
        request,
        'evaluations/report.html'
    )