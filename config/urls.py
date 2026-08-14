from django.urls import path
from members import views

urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('create/', views.member_create, name='member_create'),
    path(
        'update/<int:member_id>/',
        views.member_update,
        name='member_update'
    ),
    path(
        'delete/<int:member_id>/',
        views.member_delete,
        name='member_delete'
    ),
]
