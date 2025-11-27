from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'treinadores', views.TreinadorViewSet, basename='treinador')
router.register(r'pokemons', views.PokemonViewSet, basename='pokemon')


urlpatterns = [
    
    path('', include(router.urls)),

    
    path('batalha/', views.BatalhaView.as_view(), name='batalha'),
]