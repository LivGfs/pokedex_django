# api/models.py
from django.db import models

import requests # Importe o requests no início do arquivo

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
    





# ... (Model TimeStampedModel e Treinador) ...

# Crie uma exceção customizada (melhor que travar o app)
class PokeAPIError(Exception):
    pass

# 2. Modelo Pokémon (Atualizado)
class Pokemon(TimeStampedModel):
    # ... (Campos id, nome, foto, altura, peso) ...

    def __str__(self):
        return self.nome

    def _buscar_dados_pokeapi(self):
        """
        Método privado para buscar dados na PokeAPI.
        """
        # Se já temos os dados (ex: em uma atualização), não busca de novo
        if self.foto and self.altura and self.peso:
            return

        try:
            # URL da PokeAPI (sempre minúsculas)
            url = f"https://pokeapi.co/api/v2/pokemon/{self.nome.lower()}"
            response = requests.get(url)

            # Se o Pokémon não for encontrado (404)
            if response.status_code == 404:
                raise PokeAPIError(f"Pokémon '{self.nome}' não encontrado na PokeAPI.")

            # Se outro erro ocorrer
            response.raise_for_status() # Levanta exceção para erros HTTP (4xx, 5xx)

            data = response.json()

            # Atualiza os campos do objeto (self)
            self.altura = data.get('height')
            self.peso = data.get('weight')

            # Pega a foto oficial (ou a 'front_default' se não houver)
            sprites = data.get('sprites', {})
            self.foto = sprites.get('other', {}).get('official-artwork', {}).get('front_default')
            if not self.foto:
                self.foto = sprites.get('front_default')

        except requests.RequestException as e:
            # Trata erros de conexão, timeout, etc.
            raise PokeAPIError(f"Erro ao acessar a PokeAPI: {e}")

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para buscar dados da PokeAPI
        antes de salvar no banco.
        """
        # 'self.pk' (primary key) só existe se o objeto já está no banco
        # 'force_insert' é usado para garantir que a busca ocorra na criação
        is_new = self.pk is None or kwargs.get('force_insert', False)

        if is_new:
            # (A exceção PokeAPIError será propagada se ocorrer)
            self._buscar_dados_pokeapi() 

        # Chama o método save original
        super().save(*args, **kwargs)

# ... (Model PokemonsDoTreinador) ...