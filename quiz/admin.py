from django.contrib import admin
from quiz.models import Question, Quiz, QuizStats, Option, Answer
from django.utils.html import format_html


class QuizAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'code', 'is_published', 'start_time', 'end_time', 'created_at', 'modified_at')
    list_filter = ('start_time', 'end_time')
    search_fields = ['name']


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'level', 'question_text', 'is_published', 'correct_answer', 'question_type', 'image_tag',
                    'points', 'question_duration', 'created_at', 'modified_at')
    list_filter = ('quiz',)
    search_fields = ['quiz__name', 'question']

    def image_tag(self, obj):
        if obj.image:
            return format_html('<a href="/media/{}"><img width="50px" height="50px" src="/media/{}" /></a>' \
                               .format(obj.image, obj.image))
        else:
            return "No image"


class OptionAdmin(admin.ModelAdmin):
    list_display = ('option_text', 'image_tag', 'question', 'is_valid', 'created_at', 'modified_at')

    def image_tag(self, obj):
        if obj.image:
            return format_html('<a href="/media/{}"><img width="50px" height="50px" src="/media/{}" /></a>' \
                               .format(obj.image, obj.image))
        else:
            return "No logo"


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'answer_text', 'answer_option', 'is_valid', 'points', 'answer_duration')


class QuizStatsAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'user', 'points', 'answers_duration', 'created_at', 'modified_at')
    list_filter = ('quiz', 'user')
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'quiz__name']


admin.site.register(Question, QuestionAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(QuizStats, QuizStatsAdmin)
