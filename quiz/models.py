from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    name = models.CharField(max_length=64, verbose_name=u'Exam name', default='Quiz')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=30, blank=False, null=False, unique=True)
    is_published = models.BooleanField(default=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    # Defaults:
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<username>/quiz/<filename>
    return '{0}/quiz/{1}'.format(instance.quiz.user.username, filename)


class Question(models.Model):
    QUESTION_TYPES = (
        ('TEXT', 'text'),
        ('NUMBER', 'number'),
        ('SCORE', 'score'),
        ('OPTION', 'option'),
        ('OPTIONS', 'many options'),
        ('ORDER', ' order')
    )
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    question_text = models.CharField(max_length=300, blank=False, null=False)
    is_published = models.BooleanField(default=True)
    correct_answer = models.CharField(max_length=300, blank=True, null=True)
    has_options = models.BooleanField(default=False)
    question_type = models.CharField(max_length=7, choices=QUESTION_TYPES, default='TEXT')
    image = models.ImageField(upload_to=user_directory_path, blank=True, verbose_name='Quiz Image')
    points = models.IntegerField(default=0)
    question_duration = models.IntegerField(default=30, verbose_name='Question time in seconds')
    # Defaults:
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("quiz", "level")

    def __str__(self):
        return self.question_text


def option_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<username>/quiz/option/<filename>
    return '{0}/quiz/option/{1}'.format(instance.question.quiz.user.username, filename)


class Option(models.Model):
    option_text = models.CharField(max_length=300, blank=False, null=False)
    question = models.ForeignKey(Question, related_name='answer_options', on_delete=models.CASCADE)
    is_valid = models.BooleanField(default=False)
    image = models.ImageField(upload_to=option_directory_path, blank=True, verbose_name='Quiz Option Image')
    # Defaults:
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question.question_text + ":" + self.option_text


class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Answer\'s text')
    answer_option = models.ForeignKey(Option, blank=True, null=True, on_delete=models.SET_NULL)
    is_valid = models.BooleanField(default=False)
    points = models.IntegerField(default=0)
    answer_duration = models.IntegerField(default=0, verbose_name='Answer time in milliseconds')
    # Defaults:
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "question")

    def __str__(self):
        if self.answer_text:
            return self.answer_text
        elif self.answer_option:
            return self.answer_option.option_text


class QuizStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.DO_NOTHING)
    points = models.IntegerField(default=0)
    answers_duration = models.IntegerField(default=0, verbose_name='Answers time in milliseconds')
    # Defaults:
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "quiz")

    def __str__(self):
        return str(self.quiz.name) + " of " + str(self.user.username)

