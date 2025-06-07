from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Category, Post, Comment
from .forms import PostForm, CommentForm, UserForm


User = get_user_model()


def post_list(request):
    posts = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).annotate(comment_count=Count('comment')).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=datetime.now()
    ).order_by('-pub_date')
    template_name = 'blog/index.html'
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template_name, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template_name = 'blog/detail.html'
    if request.user != post.author:
        post = get_object_or_404(
            Post,
            id=post_id,
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now())
    form = CommentForm(request.POST or None)
    comments = Comment.objects.select_related(
        'author').filter(post=post)
    context = {'post': post,
               'form': form,
               'comments': comments}
    return render(request, template_name, context)


@login_required
def create_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    template_name = 'blog/create.html'
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, template_name, context)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template_name = 'blog/create.html'
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {'form': form,
               'is_edit': True}
    return render(request, template_name, context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template_name = 'blog/create.html'
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', request.user)
    context = {'post': post}
    return render(request, template_name, context)


def category_posts(request, category_slug):
    template_name = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).annotate(comment_count=Count('comment')).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=datetime.now(),
        category=category
    ).order_by('-pub_date')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template_name, context)


def profile(request, username):
    template_name = 'blog/profile.html'
    profile = get_object_or_404(User, username=username)
    if request.user == profile:
        posts = Post.objects.select_related(
            'category', 'location', 'author'
        ).annotate(comment_count=Count('comment')).filter(
            author=profile
        ).order_by('-pub_date')
    else:
        posts = Post.objects.select_related(
            'category', 'location', 'author'
        ).annotate(comment_count=Count('comment')).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now(),
            author=profile
        ).order_by('-pub_date')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': profile,
        'page_obj': page_obj
    }
    return render(request, template_name, context)


@login_required
def edit_profile(request):
    profile = get_object_or_404(
        User,
        username=request.user)
    template_name = 'blog/user.html'
    form = UserForm(request.POST or None, instance=profile)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, template_name, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post=post_id)
    template_name = 'blog/comment.html'
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {'comment': comment,
               'form': form}
    return render(request, template_name, context)


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post=post_id)
    template_name = 'blog/comment.html'
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id)
    context = {
        'comment': comment,
        'is_delete': True
    }
    return render(request, template_name, context)
