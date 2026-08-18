from django.db import models


class Team(models.Model):
    team_id = models.AutoField(
        primary_key=True
    )

    project_id = models.IntegerField()

    team_name = models.CharField(
        max_length=100
    )

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."teams"'


class TeamMember(models.Model):
    team_member_id = models.AutoField(
        primary_key=True
    )

    team_id = models.IntegerField()

    student_id = models.IntegerField()

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."team_members"'