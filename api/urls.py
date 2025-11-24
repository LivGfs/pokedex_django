# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# O Router cuida de gerar as URLs para os ViewSets (CRUD)
router = DefaultRouter()
router.register(r'treinadores', views.TreinadorViewSet, basename='treinador')
router.register(r'pokemons', views.PokemonViewSet, basename='pokemon')

# As URLs da API são definidas aqui
urlpatterns = [
    # Inclui as rotas geradas pelo router (ex: /api/treinadores/, /api/pokemons/)
    path('', include(router.urls)),

    # Rota customizada para a Batalha
    path('batalha/', views.BatalhaView.as_view(), name='batalha'),
]