from functools import wraps
from django.shortcuts import redirect


# ==========================================
# 학생 전용
# ==========================================
def student_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user_type = request.session.get('user_type')

        # 로그인하지 않은 경우
        if not user_type:
            return redirect('login')

        # 학생이 아닌 경우
        if user_type != 'STUDENT':
            return redirect('admin_dashboard')

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ==========================================
# 선생님 전용
# ==========================================
def teacher_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user_type = request.session.get('user_type')

        # 로그인하지 않은 경우
        if not user_type:
            return redirect('login')

        # 선생님이 아닌 경우
        if user_type != 'TEACHER':
            return redirect('student_home')

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper