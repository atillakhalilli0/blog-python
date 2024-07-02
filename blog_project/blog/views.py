from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Article, Category, Comment, Like
from .forms import ArticleForm, CommentForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.flatpages.models import FlatPage
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib import messages
from django.contrib.auth import logout
import requests

def get_weather():
    api_key = '5f0707b776fb6676cf49c0017e4d8854'
    url = f'https://api.openweathermap.org/data/2.5/weather?q=Baku&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or 'main' not in data:
        return {
            'temperature': 'N/A',
            'description': 'N/A',
            'icon': '01d',
        }

    return {
        'temperature': data['main']['temp'],
        'description': data['weather'][0]['description'],
        'icon': data['weather'][0]['icon'],
    }

def index(request):
    weather = get_weather()
    articles = Article.objects.all()
    return render(request, 'blog/index.html', {'articles': articles, 'weather': weather})

def article_detail(request, article_id):
    weather = get_weather()
    article = get_object_or_404(Article, id=article_id)
    comments = article.comments.all()
    is_liked = request.user.is_authenticated and article.likes.filter(id=request.user.id).exists()
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            return redirect('article_detail', article_id=article.id)
    else:
        comment_form = CommentForm()
    return render(request, 'blog/article_detail.html', {
        'article': article,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'weather': weather
    })

@require_POST
def like_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user.is_authenticated:
        if article.likes.filter(id=request.user.id).exists():
            article.likes.remove(request.user)
            liked = False
        else:
            article.likes.add(request.user)
            liked = True

        likes_count = article.likes.count()
        return JsonResponse({'likes_count': likes_count, 'liked': liked})
    else:
        return JsonResponse({'error': 'You must be logged in to like an article.'}, status=403)

@login_required
def create_article(request):
    weather = get_weather()
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()
            return redirect('article_detail', article_id=article.id)
    else:
        form = ArticleForm()
    return render(request, 'blog/create_article.html', {'form': form, 'weather': weather})

def about_us(request):
    weather = get_weather()
    about_page = get_object_or_404(FlatPage, url='/about/')
    return render(request, 'blog/about_us.html', {'page': about_page, 'weather': weather})

def contact(request):
    weather = get_weather()
    contact_page = get_object_or_404(FlatPage, url='/contact/')
    return render(request, 'blog/contact.html', {'page': contact_page, 'weather': weather})

def register(request):
    weather = get_weather()
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('index')
        else:
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = UserRegistrationForm()
    return render(request, 'blog/register.html', {'form': form, 'weather': weather})

def user_login(request):
    weather = get_weather()
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'You are now logged in as {username}.')
                return redirect('index')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'blog/login.html', {'form': form, 'weather': weather})

def user_logout(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('index')
