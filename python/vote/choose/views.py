from django.template import loader  # type: ignore
from django.http import HttpResponse, JsonResponse  # type: ignore
from django.shortcuts import render, redirect, get_object_or_404  # type: ignore

from .forms import CustomUserCreationForm, CreateContentForVote
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import Content, Vote

# Create your views here.


def index(request):
    template = loader.get_template("choose/index.html")
    return HttpResponse(template.render())


# Функция регистрации
def user_register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Создаём пользователя
            # Автоматически логиним после регистрации
            auth_login(request, user)
            # Перенаправляем на главную страницу
            return redirect("choose:index")
    else:
        form = CustomUserCreationForm()  # Пустая форма для отображения
    return render(request, "choose/register.html", {"form": form})


# Функция логина


def user_login(request):  # Переименована функция для предотвращения рекурсии
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)  # Логиним пользователя
            # Перенаправляем на главную страницу
            return redirect("choose:logined-page")
        else:
            return render(
                request, "choose/login.html", {"error": "Неверный логин или пароль"}
            )
    return render(request, "choose/login.html")  # Отображаем форму логина


@login_required
def logined_page(request):
    return render(request, "choose/logined-page.html")


# Функция логаута


def user_logout(request):  # Переименована для предотвращения рекурсии
    auth_logout(request)  # Выход из системы
    return redirect("choose:user-login")  # Перенаправляем на страницу логина


def vote_page(request):
    return render(request, "choose/vote.html")


@login_required  # Убедитесь, что пользователь авторизован
def create_content(request):
    if request.method == "POST":
        title = request.POST.get("title")  # Получаем данные из формы
        body = request.POST.get("body")  # Добавляем поле body

        # Создаем новый объект Content
        Content.objects.create(user=request.user, title=title, body=body)

        # Перенаправляем на страницу успеха или обратно на голосование
        return redirect("choose:vote-success")  # Укажите реальный URL

    # Возвращаем форму для создания контента
    return render(request, "choose/vote.html")


def vote_success(request):
    return render(
        request,
        "choose/vote_success.html",
        {"message": "Content created successfully!"},
    )


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Content, Vote


@login_required
def show_votes(request):
    if request.method == "POST":
        content_id = request.POST.get("content_id")
        vote_type = request.POST.get("vote_type")

        # Получаем объект контента
        content = get_object_or_404(Content, id=content_id)

        # Проверяем, голосовал ли пользователь ранее за этот контент
        existing_vote = Vote.objects.filter(voter=request.user, content=content).first()
        if existing_vote:
            # Если пользователь уже голосовал, обновляем голос
            existing_vote.vote_type = vote_type
            existing_vote.save()
        else:
            # Если голос первый, создаём новый
            Vote.objects.create(
                voter=request.user, content=content, vote_type=vote_type
            )

        # Возвращаем JSON-ответ, если голосование происходит через AJAX
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Vote registered!"})

        # Перенаправляем на страницу голосования
        return redirect("choose:vote-page")

    # Считаем голоса для каждого контента и добавляем проценты как атрибуты
    contents = Content.objects.all()

    for content in contents:
        votes = Vote.objects.filter(content=content)
        up_count = votes.filter(vote_type="up").count()
        down_count = votes.filter(vote_type="down").count()
        total_votes = up_count + down_count

        # Добавляем динамические атрибуты к каждому объекту content
        content.up_percent = (100 * up_count) / total_votes if total_votes > 0 else 0
        content.down_percent = (
            (100 * down_count) / total_votes if total_votes > 0 else 0
        )
        content.total_votes = total_votes

    # Передаём данные в шаблон
    return render(request, "choose/show-votes.html", {"contents": contents})


# @login_required
# def show_percent(request):

# '''
# this is commentaris

# added other 2 lines
# '''
