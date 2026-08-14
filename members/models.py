from django.db import models

class Member(models.Model):
    id = models.AutoField(primary_key=True, db_column='member_id')
    
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    age = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members'