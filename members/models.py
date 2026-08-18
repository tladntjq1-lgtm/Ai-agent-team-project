from django.db import models


class Member(models.Model):
    id = models.AutoField(
        primary_key=True,
        db_column='member_id'
    )

    name = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    age = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members'


class Student(models.Model):
    student_id = models.AutoField(
        primary_key=True
    )

    login_id = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=100)

    email = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    phone = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )

    slack_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    note = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    updated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."students"'


class Teacher(models.Model):
    teacher_id = models.AutoField(
        primary_key=True
    )

    login_id = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=100)

    email = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."teachers"'