from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Follow, Group, Post, User

LIMIT_POSTS = 10


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    user_posts = author.posts.all()
    paginator = Paginator(user_posts, LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Проверяем, что пользователь авторизован
    if user.is_authenticated:
        # Получаем список подписанных на автора пользователей
        followers = author.following.values_list('user', flat=True)
        # Проверяем вхождение текущего пользователя в список followers
        following = followers.filter(user=user).exists()
        context = {
            'author': author,
            'user_posts': user_posts,
            'page_obj': page_obj,
            'following': following,
        }
    else:
        context = {
            'author': author,
            'user_posts': user_posts,
            'page_obj': page_obj,
        }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    user = post.author
    user_posts = user.posts.all()
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'user': user,
        'post': post,
        'user_posts': user_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    else:
        return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post
                    )
    if request.user != post.author:
        raise PermissionDenied
    if request.method != 'POST':
        return render(
            request,
            'posts/create_post.html',
            {
             'form': form,
             'post': post,
             'is_edit': True,
             }
        )
    if not form.is_valid():
        return render(request,
                      'posts/create_post.html',
                      {'form': form}
                      )
    post = form.save()
    post.save()
    return redirect('posts:post_detail', post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    # Получаем список id авторов на которых подписаны
    authors = user.follower.values_list('author', flat=True)
    # Получаем список постов отфильтрованных по авторам на которых подписаны
    posts_follow = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts_follow, LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user_follow = request.user
    author_follow = get_object_or_404(User, username=username)
    # Получаем список подписанных на автора пользователей
    followers = author_follow.following.values_list('user', flat=True)
    # Проверяем вхождение текущего пользователя в список followers
    following = followers.filter(user=user_follow).exists()
    # Пользователь не должен мочь подписываться сам на себя
    if user_follow == author_follow:
        raise PermissionDenied
    # Пользователь может подписаться только один раз
    if following:
        raise PermissionDenied
    Follow.objects.create(
        user=user_follow,
        author=author_follow,
    )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user_unfollow = request.user
    author_unfollow = get_object_or_404(User, username=username)
    unfollow = Follow.objects.filter(
        user=user_unfollow,
        author=author_unfollow
    )
    unfollow.delete()
    return redirect('posts:profile', username)
