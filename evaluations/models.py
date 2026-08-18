from django.db import models


# ==========================================
# 1. 프로젝트
# ==========================================
class Project(models.Model):

    project_id = models.AutoField(
        primary_key=True
    )

    project_name = models.CharField(
        max_length=100
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    end_date = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=50
    )

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."projects"'


# ==========================================
# 2. 평가 회차
# ==========================================
class EvaluationRound(models.Model):

    round_id = models.AutoField(
        primary_key=True
    )

    project_id = models.IntegerField()

    round_name = models.CharField(
        max_length=100
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    end_date = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=50
    )

    results_public = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."evaluation_rounds"'


# ==========================================
# 3. 평가 문항
# ==========================================
class EvaluationQuestion(models.Model):

    question_id = models.AutoField(
        primary_key=True
    )

    round_id = models.IntegerField()

    question_type = models.CharField(
        max_length=20
    )

    question_text = models.CharField(
        max_length=500
    )

    display_order = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"cham_edu"."evaluation_questions"'


# ==========================================
# 4. 팀 평가 점수
# ==========================================
class TeamEvaluationScore(models.Model):

    score_id = models.AutoField(
        primary_key=True
    )

    round_id = models.IntegerField()

    evaluator_student_id = models.IntegerField()

    target_team_id = models.IntegerField()

    question_id = models.IntegerField()

    score = models.IntegerField()

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."team_evaluation_scores"'


# ==========================================
# 5. 개인 평가 점수
# ==========================================
class IndividualEvaluationScore(models.Model):

    score_id = models.AutoField(
        primary_key=True
    )

    round_id = models.IntegerField()

    evaluator_student_id = models.IntegerField()

    target_student_id = models.IntegerField()

    question_id = models.IntegerField()

    score = models.IntegerField()

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = '"cham_edu"."individual_evaluation_scores"'