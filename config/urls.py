from django.contrib import admin
from django.urls import path

from members import views as members_views
from teams import views as teams_views
from evaluations import views as evaluations_views


urlpatterns = [

    # ==========================================
    # Django 기본 관리자
    # ==========================================
    path(
        'admin/',
        admin.site.urls
    ),


    # ==========================================
    # Members 앱
    # ==========================================

    # 로그인
    path(
        '',
        members_views.login_view,
        name='login'
    ),

    # 로그아웃
    path(
        'logout/',
        members_views.logout_view,
        name='logout'
    ),

    # 계정 찾기
    path(
        'account-find/',
        members_views.account_find_view,
        name='account_find'
    ),

    # 회원가입
    path(
        'signup/',
        members_views.signup_view,
        name='signup'
    ),

    # 관리자 대시보드
    path(
        'admin-dashboard/',
        members_views.admin_dashboard_view,
        name='admin_dashboard'
    ),

    # 학생 홈
    path(
        'student-home/',
        members_views.student_home_view,
        name='student_home'
    ),

    # 학생 관리
    path(
        'admin-students/',
        members_views.admin_student_management_view,
        name='admin_student_management'
    ),


    # ==========================================
    # Teams 앱
    # ==========================================

    # 관리자 팀 관리
    path(
        'admin-teams/',
        teams_views.admin_team_management_view,
        name='admin_team_management'
    ),

    # 학생 내 팀
    path(
        'my-team/',
        teams_views.my_team_view,
        name='my_team'
    ),


    # ==========================================
    # Evaluations 앱 - 관리자
    # ==========================================

    # 평가 회차 관리
    path(
        'admin-eval-round/',
        evaluations_views.admin_evaluation_round_view,
        name='admin_evaluation_round'
    ),

    # 평가 문항 관리
    path(
        'admin-eval-questions/',
        evaluations_views.admin_evaluation_questions_view,
        name='admin_evaluation_questions'
    ),

    # 선생님 평가
    path(
        'admin-eval-status/',
        evaluations_views.admin_teacher_evaluation_view,
        name='admin_teacher_evaluation'
    ),

    # 평가 결과 관리
    path(
        'admin-eval-result/',
        evaluations_views.admin_result_management_view,
        name='admin_result_management'
    ),


    # ==========================================
    # Evaluations 앱 - 학생
    # ==========================================

    # 팀 평가
    path(
        'team-eval-list/',
        evaluations_views.team_eval_list_view,
        name='team_eval_list'
    ),

    # 개인 평가
    path(
        'individual-eval/',
        evaluations_views.individual_eval_view,
        name='individual_eval'
    ),

    # 리포트
    path(
        'report/',
        evaluations_views.report_view,
        name='report'
    ),
]