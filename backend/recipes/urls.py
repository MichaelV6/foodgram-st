from django.urls import path
from . import views

urlpatterns = [
    path('recipes/<int:recipe_id>/', views.recipe_short_link, name='recipe-short-link'),
]