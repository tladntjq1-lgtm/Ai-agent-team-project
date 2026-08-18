from django.urls import path
from members import views


urlpatterns = [
    # 새 참교육 로그인 화면
    path('', views.student_home, name='student_home'),

    # 기존 회원 관리 화면
    path('members/', views.member_list, name='member_list'),

    path(
        'members/create/',
        views.member_create,
        name='member_create'
    ),

    path(
        'members/update/<int:member_id>/',
        views.member_update,
        name='member_update'
    ),

    path(
        'members/delete/<int:member_id>/',
        views.member_delete,
        name='member_delete'
    ),
]