from django.urls import path
from . import views

urlpatterns = [
    path('',              views.home_view,            name='home'),
    path('signup/',       views.signup_view,           name='signup'),
    path('login/',        views.login_view,            name='login'),
    path('logout/',       views.logout_view,           name='logout'),
    path('dashboard/',    views.dashboard_view,        name='dashboard'),
    path('recommend/',    views.recommend_recipe_view, name='recommend'),
    path('save-recipe/',  views.save_recipe,           name='save_recipe'),
    path('history/',      views.history_view,          name='history'),
    path('profile/',      views.profile_view,          name='profile'),
    path('history/favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
    path('history/delete/<int:pk>/',   views.delete_history,  name='delete_history'),
]
