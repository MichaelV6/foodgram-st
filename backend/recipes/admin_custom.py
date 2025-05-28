from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render

class CustomAdminSite(AdminSite):
    site_header = "Foodgram Администрирование"
    site_title = "Foodgram Admin"
    index_title = "Добро пожаловать в панель администрирования Foodgram"
    
    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        

        custom_app_list = []
        

        recipes_models = []
        favorites_models = []
        

        users_models = []
        

        ingredients_models = []
        
        for app in app_list:
            if app['app_label'] == 'recipes':
                for model in app['models']:
                    model_name = model['object_name']
                    if model_name in ['Recipe', 'RecipeIngredient']:
                        recipes_models.append(model)
                    elif model_name in ['Favorite', 'ShoppingCart']:
                        favorites_models.append(model)
                    elif model_name in ['User', 'Subscription']:
                        users_models.append(model)
                    elif model_name == 'Ingredient':
                        ingredients_models.append(model)
        

        if recipes_models:
            custom_app_list.append({
                'name': 'Рецепты',
                'app_label': 'recipes_group',
                'models': recipes_models,
                'has_module_perms': True,
            })
        
        if favorites_models:
            custom_app_list.append({
                'name': 'Избранное и корзина',
                'app_label': 'favorites_group', 
                'models': favorites_models,
                'has_module_perms': True,
            })
            
        if users_models:
            custom_app_list.append({
                'name': 'Пользователи',
                'app_label': 'users_group',
                'models': users_models,
                'has_module_perms': True,
            })
            
        if ingredients_models:
            custom_app_list.append({
                'name': 'Ингредиенты',
                'app_label': 'ingredients_group',
                'models': ingredients_models,
                'has_module_perms': True,
            })
        
        for app in app_list:
            if app['app_label'] not in ['recipes']:
                custom_app_list.append(app)
                
        return custom_app_list

admin_site = CustomAdminSite(name='custom_admin')