from django.contrib import admin
from django.urls import path

# 핵심 포인트: 세 개의 서로 다른 앱에서 views.py를 가져오기 때문에 이름이 충돌해.
# 그래서 'as' 키워드를 써서 members_views, teams_views처럼 별칭을 달아 구분하는 거야.
from members import views as members_views
from teams import views as teams_views
from evaluations import views as evaluations_views

urlpatterns = [
    # Django가 기본적으로 제공하는 관리자 페이지용 라우팅
    path('admin/', admin.site.urls),

    # --- [Members 앱] 계정 및 사용자 홈 라우팅 ---
    # 빈 주소('')로 접속했을 때 바로 로그인 화면으로 연결해. 진입점 역할을 하지.
    # name='login'은 이후 HTML 파일에서 {% url 'login' %}으로 이 주소를 찾아올 때 쓸 이름표야.
    
    # 로그인
    path('', members_views.login_view, name='login'),

    # 로그아웃
    path('logout/', members_views.logout_view, name='logout'),
    
    # 계정 찾기 화면
    path('account-find/', members_views.account_find_view, name='account_find'),
    
    # 회원가입 화면
    path('signup/',members_views.signup_view, name='signup'),

    # 튜터 로그인 시 보여줄 대시보드
    path('admin-dashboard/', members_views.admin_dashboard_view, name='admin_dashboard'),
    
    # 학생 로그인 시 보여줄 홈 화면
    path('student-home/', members_views.student_home_view, name='student_home'),
    
    # 튜터의 수강생 목록 관리 화면 (과거 member_list를 대체)
    path('admin-students/', members_views.admin_student_management_view, name='admin_student_management'),


    # --- [Teams 앱] 팀 편성 및 조회 라우팅 ---
    # 튜터의 팀 편성 및 결과 통계 화면
    path('admin-teams/', teams_views.admin_team_management_view, name='admin_team_management'),
    
    # 학생의 내 팀 정보 및 팀원 프로필 조회 화면
    path('my-team/', teams_views.my_team_view, name='my_team'),


    # --- [Evaluations 앱] 평가 프로세스 라우팅 ---
    # 튜터의 전체 평가 리스트 및 회차 생성
    path('admin-eval-round/', evaluations_views.admin_evaluation_round_view, name='admin_evaluation_round'),
    
    # 튜터의 평가 문항 템플릿 생성
    path('admin-eval-questions/', evaluations_views.admin_evaluation_questions_view, name='admin_evaluation_questions'),
    
    # 튜터의 평가 진행 현황(제출률 등) 모니터링
    path('admin-eval-status/', evaluations_views.admin_teacher_evaluation_view, name='admin_teacher_evaluation'),
    
    # 튜터의 평가 최종 결과 조회 및 리포트
    path('admin-eval-result/', evaluations_views.admin_result_management_view, name='admin_result_management'),
    
    # 학생의 다른 팀 평가 진입점
    path('team-eval-list/', evaluations_views.team_eval_list_view, name='team_eval_list'),
    
    # 학생의 소속 팀원 개인 평가 진입점
    path('individual-eval/', evaluations_views.individual_eval_view, name='individual_eval'),
    
    # 학생의 최종 평가 결과 석차 리포트
    path('report/', evaluations_views.report_view, name='report'),
]