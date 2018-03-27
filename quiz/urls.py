from django.conf.urls import url

from quiz.views import index
from quiz.controllers import check_quiz_code, check_if_user_is_logged, get_quiz_info, send_quiz_answers, \
    get_quiz_results, register_new_user

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'api/checkquizcode/?$', check_quiz_code, name='check_quiz_code'),
    url(r'api/checkifuserislogged/?$', check_if_user_is_logged, name='check_if_user_is_logged'),
    url(r'api/getquizinfo/?$', get_quiz_info, name='get_quiz_info'),
    url(r'api/sendquizanswers/?$', send_quiz_answers, name='send_quiz_answers'),
    url(r'api/getquizresults/?$', get_quiz_results, name='get_quiz_results'),

    # old examples:
    url(r'api/registernewuser/?$', register_new_user, name='register_new_user')
]
