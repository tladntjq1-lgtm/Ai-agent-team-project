from django.shortcuts import render, redirect, get_object_or_404

from .models import Member
from .forms import MemberForm


# 1. 회원 목록
def member_list(request):
    members = Member.objects.all()

    return render(
        request,
        'members/member_list.html',
        {'members': members}
    )


# 2. 회원 등록
def member_create(request):
    if request.method == "POST":
        form = MemberForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('member_list')

    else:
        form = MemberForm()

    return render(
        request,
        'members/member_create.html',
        {'form': form}
    )


# 3. 회원 수정
def member_update(request, member_id):
    member = get_object_or_404(
        Member,
        pk=member_id
    )

    if request.method == "POST":
        form = MemberForm(
            request.POST,
            instance=member
        )

        if form.is_valid():
            form.save()
            return redirect('member_list')

    else:
        form = MemberForm(
            instance=member
        )

    return render(
        request,
        'members/member_update.html',
        {
            'form': form,
            'member': member
        }
    )


# 4. 회원 삭제
def member_delete(request, member_id):
    member = get_object_or_404(Member, pk=member_id)

    if request.method == "POST":
        member.delete()

    return redirect('member_list')