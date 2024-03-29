from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .utils import paginate
from .models import Post, Group, User, Follow
from .forms import CommentForm, PostForm


@cache_page(20)
def index(request):
    posts = Post.objects.select_related('group')
    page_obj = paginate(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = paginate(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author', 'group')
    page_obj = paginate(request, posts)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)

    context = {
        'form': form,
        'is_edit': False
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post
    )
    if post.author != request.user:
        return redirect('posts:index')
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
        'post': post
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_follow_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related(
        'author',
        'group'
    )
    page_obj = paginate(request, post_follow_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    is_following = Follow.objects.filter(user=request.user.id, author=author)
    if request.user != author and not is_following.exists():
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.get(
        user=request.user,
        author__username=username
    ).delete()
    return redirect('posts:profile', username=username)
