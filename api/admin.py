from django.contrib import admin
from .models import Treinador, Pokemon, PokemonsDoTreinador

admin.site.register(Treinador)
admin.site.register(Pokemon)
admin.site.register(PokemonsDoTreinador)
