from django.shortcuts import render

from members.decorators import student_required, teacher_required

# 튜터가 팀을 편성하고 결과를 확인(통계 요약, 인원 수정)하는 화면. 
# (가중치 기반의 팀 편성 알고리즘이 실행되고, 인원 추가/제외 시 DB 트랜잭션이 안전하게 처리되어야 하는, 이 프로젝트에서 가장 복잡한 로직이 담길 곳이야.)
@teacher_required
def admin_team_management_view(request):
    return render(request, 'teams/admin_team_management.html')

# 학생이 자신의 소속 팀명과 팀원들의 상세 프로필을 확인하는 화면. 
# (요청한 학생의 user_id를 기준으로 속한 팀 테이블을 조인(Join)하여 팀원 목록을 가져오는 쿼리가 필요해.)
@student_required
def my_team_view(request):
    return render(request, 'teams/my_team.html')


