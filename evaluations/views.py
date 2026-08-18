from django.shortcuts import render

# 튜터가 전체 평가 리스트를 확인하고 새로운 평가 회차(프로젝트)를 생성하는 진입점. 
# (시작일/종료일에 따른 평가의 상태[진행 중, 완료]를 자동으로 업데이트하거나 판별하는 로직이 필요해.)
def admin_evaluation_round_view(request):
    return render(request, 'evaluations/admin_evaluation_round.html')

# 튜터가 새 회차 생성 시 팀/개인 평가 문항 템플릿을 설정하는 화면. 
# (사용자가 문항을 동적으로 추가하거나 삭제할 수 있으므로, 가변적인 폼(Form) 데이터를 받아서 DB에 저장하는 처리가 까다로울 수 있어.)
def admin_evaluation_questions_view(request):
    return render(request, 'evaluations/admin_evaluation_questions.html')

# 튜터가 특정 평가의 진행률(개인/팀 제출률)과 미제출자 명단을 실시간으로 모니터링하는 현황판. 
# (전체 인원 대비 제출 인원을 계산하는 통계 쿼리 최적화가 중요해. 쿼리가 무거워지면 페이지 로딩이 느려질 수 있거든.)
def admin_teacher_evaluation_view(request):
    return render(request, 'evaluations/admin_teacher_evaluation.html')

# 튜터가 최종적으로 수강생별 상세 평가 결과를 시각화된 그래프와 함께 조회하는 화면. 
# (프론트엔드 차트 라이브러리(예: Chart.js)에 넘겨줄 데이터를 JSON 형태로 가공해서 전달하는 로직이 필수적이야.)
def admin_result_management_view(request):
    return render(request, 'evaluations/admin_result_management.html')

# 학생이 다른 팀을 평가하기 위해 대상 팀을 선택하고 문항에 답을 제출하는 화면. 
# (자신의 팀은 평가 목록에서 제외하는 필터링과, 이미 평가한 팀을 중복 평가하지 못하도록 막는 검증(Validation) 로직이 들어가야 해.)
def team_eval_list_view(request):
    return render(request, 'evaluations/team_eval_list.html')

# 학생이 자신과 같은 팀에 속한 팀원들을 개인 평가하는 화면. 
# (본인을 제외한 팀원 목록만 노출해야 하며, 모달에서 제출된 각 문항의 1~5점 척도 점수들을 DB의 평가 결과 테이블에 정확히 맵핑해 저장해야 해.)
def individual_eval_view(request):
    return render(request, 'evaluations/individual_eval.html')

# 평가가 모두 종료된 후, 학생이 자신의 최종 합산 점수와 전체 석차를 확인하는 리포트 화면. 
# (공개 설정이 된 평가 결과만 보여줘야 하며, [팀 점수 40% + 개인 점수 60%] 같은 가중치 수식 계산이 뷰 혹은 모델 단에서 수행되어야 해.)
def report_view(request):
    return render(request, 'evaluations/report.html')