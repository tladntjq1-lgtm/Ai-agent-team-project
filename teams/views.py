from django.contrib import messages
from django.shortcuts import render, redirect

from members.decorators import student_required, teacher_required
from members.models import Student

from evaluations.models import Project

from .models import Team, TeamMember


# ==========================================
# 1. 관리자 - 팀 관리
# ==========================================
@teacher_required
def admin_team_management_view(request):

    return render(
        request,
        'teams/admin_team_management.html'
    )


# ==========================================
# 2. 학생 - 내 팀
# ==========================================
@student_required
def my_team_view(request):

    # ----------------------------------
    # 로그인 학생 ID
    # ----------------------------------
    student_id = request.session.get(
        'student_id'
    )


    # ----------------------------------
    # 로그인 학생 정보
    # ----------------------------------
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


    # ----------------------------------
    # 현재 팀 배정
    # ----------------------------------
    team_member = TeamMember.objects.filter(
        student_id=student_id
    ).first()


    if not team_member:

        return render(
            request,
            'teams/my_team.html',
            {
                'student': student,
                'has_team': False,
            }
        )


    # ----------------------------------
    # 현재 팀
    # ----------------------------------
    team = Team.objects.filter(
        team_id=team_member.team_id
    ).first()


    if not team:

        return render(
            request,
            'teams/my_team.html',
            {
                'student': student,
                'has_team': False,
            }
        )


    # ----------------------------------
    # 프로젝트
    # ----------------------------------
    project = Project.objects.filter(
        project_id=team.project_id
    ).first()


    # ----------------------------------
    # 같은 팀 학생 ID
    # ----------------------------------
    team_student_ids = TeamMember.objects.filter(
        team_id=team.team_id
    ).values_list(
        'student_id',
        flat=True
    )


    # ----------------------------------
    # 실제 팀원 정보
    # ----------------------------------
    team_students = Student.objects.filter(
        student_id__in=team_student_ids
    ).order_by(
        'student_id'
    )


    context = {
        'student': student,

        'team': team,

        'project': project,

        'team_students': team_students,

        'has_team': True,
    }


    return render(
        request,
        'teams/my_team.html',
        context
    )