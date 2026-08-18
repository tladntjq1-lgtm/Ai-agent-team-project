from django.shortcuts import render

# 튜터와 학생이 시스템에 진입하는 첫 관문. 
# (추후 POST 요청이 들어오면 ID/PW를 DB와 대조하고 세션을 생성하는 인증 로직이 추가되어야 해.)
def login_view(request):
    return render(request, 'members/login.html')

# 분실된 계정(아이디/비밀번호) 정보를 찾는 화면. 
# (실제 서비스라면 입력한 정보 기반으로 DB를 조회하고, 이메일 발송이나 임시 비밀번호 생성 로직이 연결될 곳이야.)
def account_find_view(request):
    return render(request, 'members/account_find.html')

# 튜터 로그인 직후 진입하는 대시보드. 
# (현재 진행 중인 프로젝트 목록과 요약 통계 데이터를 DB에서 쿼리하여 컨텍스트로 넘겨주는 작업이 필요해.)
def admin_dashboard_view(request):
    return render(request, 'members/admin_dashboard.html')

# 학생 로그인 직후 진입하는 홈 화면. 
# (로그인한 학생의 세션을 기반으로 소속 팀 유무를 판단하고, 현재 진행 중인 평가 회차와 진행률 데이터를 조건별로 다르게 렌더링해야 하는 분기 처리가 핵심이야.)
def student_home_view(request):
    return render(request, 'members/student_home.html')

# 튜터가 전체 수강생 목록을 조회하고 권한을 수정하는 관리 화면. 
# (수강생 수가 많아질 것을 대비해 검색, 필터링, 그리고 Pagination(페이징) 기능이 필수로 들어가야 할 뷰야.)
def admin_student_management_view(request):
    return render(request, 'members/admin_student_management.html')