from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Recipe, RecipeHistory, UserRecipeInteraction
from ml_model.recommend import (
    recommend_recipe, get_ingredient_categories, collaborative_recommend
)


# ─────────────────────────────────────────────
# Public views
# ─────────────────────────────────────────────

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('dashboard')

    return render(request, 'signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
        return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

@login_required
def dashboard_view(request):
    categories = get_ingredient_categories()
    collab_recipes = collaborative_recommend(request.user, n=3)
    return render(request, 'dashboard.html', {
        'categories': categories,
        'collab_recipes': collab_recipes,
    })


# ─────────────────────────────────────────────
# Recommend
# ─────────────────────────────────────────────

@login_required
def recommend_recipe_view(request):
    if request.method == 'POST':
        selected_ingredients = request.POST.getlist('ingredients')
        diet        = request.POST.get('diet', 'all')           # all / veg / nonveg
        difficulty  = request.POST.get('difficulty', 'all')     # all / easy / medium / hard
        match_mode  = request.POST.get('match_mode', 'strict')  # strict / flexible
        use_ml      = request.POST.get('use_ml', 'false') == 'true'

        diet_arg       = None if diet == 'all' else diet
        difficulty_arg = None if difficulty == 'all' else difficulty

        recipes = recommend_recipe(
            selected_ingredients,
            diet=diet_arg,
            difficulty=difficulty_arg,
            match_mode=match_mode,
            use_ml=use_ml,
        )

        return render(request, 'recommend.html', {
            'recipes': recipes,
            'selected_ingredients': selected_ingredients,
            'diet': diet,
            'difficulty': difficulty,
            'match_mode': match_mode,
            'use_ml': use_ml,
        })

    return redirect('dashboard')


# ─────────────────────────────────────────────
# Save Recipe
# ─────────────────────────────────────────────

@login_required
def save_recipe(request):
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        ingredients = request.POST.get('ingredients', '')
        steps       = request.POST.get('steps', '')
        difficulty  = request.POST.get('difficulty_level', 'easy').lower()
        is_veg      = request.POST.get('is_veg', 'true') == 'true'

        if name:
            # Avoid duplicate saves
            if not RecipeHistory.objects.filter(user=request.user, title=name).exists():
                RecipeHistory.objects.create(
                    user=request.user,
                    title=name,
                    ingredients=ingredients,
                    instructions=steps,
                    difficulty_level=difficulty,
                    is_veg=is_veg,
                )

            # Log for collaborative filtering
            UserRecipeInteraction.objects.get_or_create(
                user=request.user,
                recipe_title=name,
                defaults={'ingredients': ingredients},
            )

    return redirect('history')


# ─────────────────────────────────────────────
# History
# ─────────────────────────────────────────────

@login_required
def history_view(request):
    query      = request.GET.get('q', '').strip()
    fav_only   = request.GET.get('favorites', '') == '1'
    diet_filter = request.GET.get('diet', 'all')

    recipes = RecipeHistory.objects.filter(user=request.user)

    if query:
        recipes = recipes.filter(title__icontains=query)
    if fav_only:
        recipes = recipes.filter(is_favorite=True)
    if diet_filter == 'veg':
        recipes = recipes.filter(is_veg=True)
    elif diet_filter == 'nonveg':
        recipes = recipes.filter(is_veg=False)

    return render(request, 'history.html', {
        'recipes': recipes,
        'query': query,
        'fav_only': fav_only,
        'diet_filter': diet_filter,
    })


@login_required
@require_POST
def toggle_favorite(request, pk):
    recipe = get_object_or_404(RecipeHistory, pk=pk, user=request.user)
    recipe.is_favorite = not recipe.is_favorite
    recipe.save()
    return JsonResponse({'is_favorite': recipe.is_favorite})


@login_required
@require_POST
def delete_history(request, pk):
    recipe = get_object_or_404(RecipeHistory, pk=pk, user=request.user)
    recipe.delete()
    return JsonResponse({'deleted': True})


# ─────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    saved_count = RecipeHistory.objects.filter(user=request.user).count()
    fav_count   = RecipeHistory.objects.filter(user=request.user, is_favorite=True).count()

    return render(request, 'profile.html', {
        'u_form': u_form,
        'p_form': p_form,
        'saved_count': saved_count,
        'fav_count': fav_count,
    })
