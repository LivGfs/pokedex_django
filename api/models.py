# api/models.py
from django.db import models
import requests  # Importação obrigatória para consumir a PokeAPI

# 1. Modelo Base (Abstrato)
class TimeStampedModel(models.Model):
    """
    Modelo base para adicionar data de criação e atualização em todas as tabelas.
    """
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # Define que este modelo não cria tabela no banco

# 2. Exceção Customizada
class PokeAPIError(Exception):
    """Exceção para erros relacionados à busca na PokeAPI."""
    pass

# 3. Modelo Treinador
class Treinador(TimeStampedModel):
    nome = models.CharField(max_length=100)
    idade = models.PositiveIntegerField()
    # Relacionamento ManyToMany com Pokemon através de uma tabela intermediária
    pokemons = models.ManyToManyField(
        'Pokemon', 
        through='PokemonsDoTreinador', 
        related_name='treinadores'
    )

    def __str__(self):
        return self.nome

# 4. Modelo Pokémon
class Pokemon(TimeStampedModel):
    # Atenção: Este modelo NÃO é abstrato. Ele cria a tabela no banco.
    nome = models.CharField(max_length=100, unique=True)
    foto = models.URLField(blank=True, null=True)
    altura = models.PositiveIntegerField(blank=True, null=True)
    peso = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.nome

    def _buscar_dados_pokeapi(self):
        """
        Método privado que conecta na API externa para preencher os dados.
        """
        # Se os dados já existem, não faz a requisição novamente
        if self.foto and self.altura and self.peso:
            return

        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{self.nome.lower()}"
            response = requests.get(url)
            
            if response.status_code == 404:
                raise PokeAPIError(f"Pokémon '{self.nome}' não encontrado na PokeAPI.")
            
            response.raise_for_status()
            
            data = response.json()
            
            self.altura = data.get('height')
            self.peso = data.get('weight')
            
            # Tenta pegar a arte oficial, se não der, pega o sprite padrão
            sprites = data.get('sprites', {})
            self.foto = sprites.get('other', {}).get('official-artwork', {}).get('front_default')
            if not self.foto:
                self.foto = sprites.get('front_default')

        except requests.RequestException as e:
            raise PokeAPIError(f"Erro ao acessar a PokeAPI: {e}")

    def save(self, *args, **kwargs):
        """
        Intercepta o salvamento para buscar dados antes de gravar no banco.
        """
        is_new = self.pk is None or kwargs.get('force_insert', False)
        
        if is_new:
            self._buscar_dados_pokeapi()
            
        super().save(*args, **kwargs)

# 5. Modelo Intermediário (Relação Treinador <-> Pokémon)
class PokemonsDoTreinador(models.Model):
    treinador = models.ForeignKey(Treinador, on_delete=models.CASCADE)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = [['treinador', 'pokemon']]

    def __str__(self):
        return f"{self.treinador.nome} possui {self.pokemon.nome}"