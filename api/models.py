# api/models.py
from django.db import models

# Model base para incluir 'criado_em' e 'atualizado_em'
class TimeStampedModel(models.Model):
    """
    Modelo Abstrato que define os campos de data de criação e atualização.
    """
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        # Define que este modelo não deve criar uma tabela no DB
        abstract = True 

# 1. Modelo Treinador
class Treinador(TimeStampedModel):
    """
    Representa um Treinador de Pokémon.
    """
    # ID (AutoField) é adicionado automaticamente pelo Django
    nome = models.CharField(max_length=100)
    idade = models.PositiveIntegerField()
    
    # Relacionamento M2M:
    # Um treinador pode ter vários pokémons, e um pokémon pode 
    # pertencer a vários treinadores (via o modelo PokemonsDoTreinador).
    pokemons = models.ManyToManyField(
        'Pokemon', 
        through='PokemonsDoTreinador', 
        related_name='treinadores'
    )

    def __str__(self):
        return self.nome

# 2. Modelo Pokémon
class Pokemon(TimeStampedModel):
    """
    Representa um Pokémon.
    Os dados (foto, altura, peso) são preenchidos automaticamente
    ao salvar, consumindo a PokeAPI.
    """
    # ID (AutoField) é adicionado automaticamente
    nome = models.CharField(max_length=100, unique=True) # Nome deve ser único
    foto = models.URLField(blank=True, null=True)
    altura = models.PositiveIntegerField(blank=True, null=True) # Em decímetros (como na PokeAPI)
    peso = models.PositiveIntegerField(blank=True, null=True) # Em hectogramas (como na PokeAPI)

    def __str__(self):
        return self.nome

# 3. Modelo PokemonsDoTreinador (Modelo 'Through')
class PokemonsDoTreinador(models.Model):
    """
    Modelo intermediário que liga Treinador e Pokémon.
    Define a relação N:N (M2M).
    """
    treinador = models.ForeignKey(Treinador, on_delete=models.CASCADE)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    
    # Define que a combinação de treinador e pokemon deve ser única
    class Meta:
        unique_together = [['treinador', 'pokemon']]

    def __str__(self):
        return f"{self.treinador.nome} possui {self.pokemon.nome}"