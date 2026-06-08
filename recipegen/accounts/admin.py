from django.contrib import admin
from .models import Profile, Recipe, RecipeHistory, UserRecipeInteraction

admin.site.register(Profile)
admin.site.register(Recipe)
admin.site.register(RecipeHistory)
admin.site.register(UserRecipeInteraction)
