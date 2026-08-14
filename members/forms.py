from django import forms
from .models import Member  # 아까 연동해둔 모델 가져오기

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        # 화면에서 입력받을 필드들만 골라줍니다.
        fields = ['name', 'email', 'age']
        