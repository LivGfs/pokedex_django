# api/serializers.py
from rest_framework import serializers
from .models import Treinador, Pokemon, PokemonsDoTreinador, PokeAPIError

# === Serializer do Pokémon ===
class PokemonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        # Define os campos que a API irá expor
        fields = ['id', 'nome', 'foto', 'altura', 'peso', 'criado_em', 'atualizado_em']
        # Define quais campos são "somente leitura" no CRUD
        # O usuário só envia o 'nome', o resto é preenchido automaticamente
        read_only_fields = ['foto', 'altura', 'peso', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        """
        Sobrescreve a criação para tratar o erro da PokeAPI
        de forma amigável para o usuário da API.
        """
        try:
            # Chama Pokemon.objects.create(**validated_data)
            # que por sua vez chama o Pokemon.save()
            return super().create(validated_data)
        except PokeAPIError as e:
            # Converte o erro de lógica (Python) em um erro de validação (API)
            raise serializers.ValidationError(str(e))

# === Serializer do Treinador ===

# Usamos um Serializer de Pokémon mais simples para listar 
# os pokémons dentro do Treinador (para não mostrar todos os detalhes)
class PokemonSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        fields = ['id', 'nome', 'foto']

class TreinadorSerializer(serializers.ModelSerializer):
    # 'pokemons' não é um campo do DB, é o M2M
    # Usamos o serializer simples para mostrar os pokémons
    pokemons = PokemonSimplesSerializer(many=True, read_only=True)

    class Meta:
        model = Treinador
        fields = ['id', 'nome', 'idade', 'criado_em', 'atualizado_em', 'pokemons']
        read_only_fields = ['pokemons']

# === Serializer para a Relação (Adicionar/Remover) ===
class PokemonsDoTreinadorSerializer(serializers.ModelSerializer):
    """
    Serializer usado para adicionar ou remover pokémons de um treinador.
    """
    # Usamos 'PrimaryKeyRelatedField' para aceitar apenas o ID do pokémon no JSON
    pokemon = serializers.PrimaryKeyRelatedField(
        queryset=Pokemon.objects.all()
    )

    # O treinador será pego da URL, não do JSON

    class Meta:
        model = PokemonsDoTreinador
        fields = ['pokemon'] # Apenas o ID do pokémon é esperado

# === Serializer para a Batalha ===
class BatalhaSerializer(serializers.Serializer):
    """
    Serializer que não está ligado a um Model.
    Usado apenas para validar os dados de entrada da API de batalha.
    """
    pokemon_1_id = serializers.IntegerField(required=True)
    pokemon_2_id = serializers.IntegerField(required=True)