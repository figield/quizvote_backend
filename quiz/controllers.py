import secrets
import string

from django.utils import timezone
from django.http import JsonResponse
import json
from django.contrib.auth import login, authenticate
from quiz.models import Quiz, Question, Answer, Option, QuizStats
from django.contrib.auth.models import User


# @csrf_protect
def check_quiz_code(request):
    context = dict()
    context['exists'] = False
    if request.method == 'POST':
        json_data = json.loads(request.body.decode('utf-8'))
        code = json_data.get('code')
        context['exists'] = Quiz.objects.filter(code=code, is_published=True).exists()
    return JsonResponse(context)


def check_if_user_is_logged(request):
    context = dict()
    context['loggedUser'] = False
    context['isOrganiser'] = False
    context['username'] = ''
    user = request.user
    if not user.is_anonymous:
        context['loggedUser'] = True
        context['isOrganiser'] = user.is_staff
        context['username'] = user.username
    else:
        context['username'] = create_and_login_user(request)
        context['loggedUser'] = True

    return JsonResponse(context)


def create_and_login_user(request, username="", raw_password=""):
    if not username:
        username = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(7))

    if not raw_password:
        raw_password = "_temporary_"

    u = User.objects.create_user(username, email="test@test.test", password=raw_password)
    u.is_superuser = False
    u.is_staff = False
    # TODO: add user to quiz group
    u.save()

    user = authenticate(username=username, password=raw_password)
    login(request, user)
    return user.username


# @csrf_protect
def get_quiz_info(request):
    context = dict()
    context['status'] = "no_quiz"
    if request.method == 'POST':  # and not request.user.is_anonymous:
        json_data = json.loads(request.body.decode('utf-8'))
        code = json_data.get('code')
        quizes = Quiz.objects.filter(code=code, is_published=True)
        if quizes:
            quiz = quizes[0]
            start_time = quiz.start_time
            end_time = quiz.end_time
            now = timezone.now()
            context['start_time'] = start_time
            context['end_time'] = end_time
            if (now > start_time) and (now < end_time):
                context['status'] = "play_now"
                # get questions
                questions = Question.objects.filter(quiz=quiz, is_published=True).order_by('level')
                if questions:
                    context['has_questions'] = True
                    context['questions'] = questions_to_list(questions)
            elif now > end_time:
                context['status'] = "ended"
                # TODO: get results
            elif now < start_time:
                context['status'] = "not_started"

    return JsonResponse(context)


def questions_to_list(questions):
    questions_list = list()
    for q in questions:
        qd = dict()
        qd['question_id'] = q.id
        qd['level'] = q.level
        qd['question_text'] = q.question_text
        qd['question_type'] = q.question_type
        if q.question_type == 'OPTION':
            qd['options'] = options_to_list(q)

        if q.question_type == 'OPTIONS':
            qd['many_options'] = options_to_list(q)

        if q.image:
            qd['has_image'] = True
            qd['image'] = q.image.url
        else:
            qd['has_image'] = False
        qd['points'] = q.points
        qd['question_duration'] = q.question_duration
        questions_list.append(qd)
    return questions_list


def options_to_list(question):
    options_list = list()
    options_objs = question.answer_options.all()
    for o in options_objs:
        od = dict()
        od['option_text'] = o.option_text
        od['option_id'] = o.id
        if o.image:
            od['image'] = o.image.url
        options_list.append(od)
    return options_list

    # {'username': 'admin',
    # 'quiz': '1',
    # 'answers': [
    # {'question': '1',
    #  'answer': '3', // or 'Lewandowski' or '1:2', or '1,4,3,2',
    #  'duration': '2000', // ms
    # },
    # {'question': '2',
    #  'answer': '1'
    #  'duration': '2300', // ms
    # }]}


# @csrf_protect
def send_quiz_answers(request):
    context = dict()
    if request.method == 'POST' and not request.user.is_anonymous:
        json_data = json.loads(request.body.decode('utf-8'))
        username = json_data.get('username')
        if username == request.user.username:
            quiz_code = json_data.get('quiz')
            answers_list = json_data.get('answers')
            context = save_answers(request.user, quiz_code, answers_list)
    return JsonResponse(context)


def save_answers(user, quiz_code, answers_list):
    context = dict()
    quizes = Quiz.objects.filter(code=quiz_code, is_published=True)
    context['success'] = False
    if quizes:
        quiz_obj = quizes[0]
        now = timezone.now()
        if now > quiz_obj.end_time:
            context['result'] = "too late"
            # answers will be not saved when is too late
        else:
            saved = False
            for answer_dict in answers_list:
                result = save_answer(user, quiz_obj, answer_dict)
                saved = saved and result
            context['all_saved'] = saved
            context['success'] = True
    return context


def save_answer(user, quiz_obj, answer_dict):
    if not answer_dict.get('answer'):
        return False

    result = False
    questions = Question.objects.filter(quiz=quiz_obj, id=answer_dict.get('question'))
    if questions:
        question_obj = questions[0]
        # check if there is already answer for such question
        if Answer.objects.filter(user=user,
                                 question=question_obj).exists():
            return False
        question_type = question_obj.question_type
        if question_type == 'OPTION':
            result = validate_and_save_option_answer(user, quiz_obj, question_obj, answer_dict)
        elif question_type == 'OPTIONS':
            result = validate_and_save_options_answer(user, quiz_obj,  question_obj, answer_dict)
        else:
            # the rest of answers is handled as a text type answer
            result = validate_and_save_text_answer(user, quiz_obj, question_obj, answer_dict)

    return result


# EXAMPLE
# {'question': '1',
#  'answer': '3',
#  'duration': '2000', // ms
# },

def validate_and_save_option_answer(user, quiz_obj, question_obj, answer_dict):
    correctness = False
    option_id = int(answer_dict.get('answer'))

    # validate answer
    options_objs = Option.objects.filter(question=question_obj, id=option_id)
    if options_objs:
        option_obj = options_objs[0]
        correctness = option_obj.is_valid
        points = 0
        if correctness:
            points = question_obj.points
        # save
        answer_duration = int(answer_dict.get('duration'))
        Answer.objects.create(user=user,
                              question=question_obj,
                              answer_option=option_obj,
                              is_valid=correctness,
                              points=points,
                              answer_duration=answer_duration)
        update_quiz_stats(user, quiz_obj, points, answer_duration)
    return correctness


# EXAMPLE
# {'question': '1',
#  'answer': '1,4,3,2',
#  'duration': '2000', // ms
# },
# TODO: test changes!!!
def validate_and_save_options_answer(user, quiz_obj, question_obj, answer_dict):
    result = False
    # TODO
    # answer_obj = Answer.objects.get_or_create(user=user, question=question )
    # TODO: updated QuizStats
    #     update_quiz_stats(user, quiz_obj, points, answer_duration)
    return result


# EXAMPLE
# {'question': '1',
#  'answer': 'some text',
#  'duration': '2000', // ms
# },

def validate_and_save_text_answer(user, quiz_obj, question_obj, answer_dict):
    correctness = False
    answer_txt = answer_dict.get('answer')

    # validate answer
    points = 0
    if answer_txt == question_obj.correct_answer:
        correctness = True
        points = question_obj.points

    answer_duration = int(answer_dict.get('duration'))
    # save
    Answer.objects.create(user=user,
                          question=question_obj,
                          answer_text=answer_txt,
                          is_valid=correctness,
                          points=points,
                          answer_duration=answer_duration)
    update_quiz_stats(user, quiz_obj, points, answer_duration)
    return correctness


def update_quiz_stats(user, quiz, points, answer_duration):
    stats_obj, _created = QuizStats.objects.get_or_create(user=user, quiz=quiz)
    stats_obj.points = stats_obj.points + points
    stats_obj.answers_duration = stats_obj.answers_duration + answer_duration
    stats_obj.save()


# @csrf_protect
def get_quiz_results(request):
    context = dict()
    if request.method == 'POST': # and not request.user.is_anonymous:
        json_data = json.loads(request.body.decode('utf-8'))
        code = json_data.get('code')
        quizes = Quiz.objects.filter(code=code, is_published=True)
        if quizes:
            quiz = quizes[0]
            stats_obj = QuizStats.objects.filter(quiz=quiz)
            context['code'] = code
            context['stats'] = convert_stats_to_json(stats_obj)

    return JsonResponse(context)


def convert_stats_to_json(stats_obj):
    l = list()
    for qs in stats_obj:
        d = dict()
        d['points'] = qs.points
        d['answers_duration'] = qs.answers_duration
        d['username'] = qs.username
        l.append(d)
    return l


# @csrf_protect
def register_new_user(request):
    context = get_default_register_context()
    if request.method == 'POST':
        json_data = json.loads(request.body.decode('utf-8'))
        context['email'] = json_data.get('email')
        username = json_data.get('name')
        context['username'] = username
        context['exist'] = User.objects.filter(username=username).exists()
        if not request.user.is_anonymous:
            context['login_as'] = request.user.username
        else:
            context['login_as'] = create_and_login_user(request)

    return JsonResponse(context)


def get_default_register_context():
    context = dict()
    context['email'] = ''
    context['username'] = ''
    context['exist'] = False
    context['login'] = False
    context['login_as'] = ''
    return context