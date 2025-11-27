from rest_framework import serializers
from .models import Treinador, Pokemon, PokemonsDoTreinador, PokeAPIError
# Serializers (Serializadores) traduzem os Models (objetos Python) para JSON (que a API envia/recebe) e vice-versa.
#  Serializer do Pokémon 
class PokemonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        # Define os campos que a API irá expor
        fields = ['id', 'nome', 'foto', 'altura', 'peso', 'criado_em', 'atualizado_em']
        # Define quais campos são "somente leitura" no CRUD
        # O usuário só envia o 'nome', o resto é preenchido automaticamente
        read_only_fields = ['foto', 'altura', 'peso', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except PokeAPIError as e:
            raise serializers.ValidationError(str(e))

#Serializer do Treinador

# Usamos um Serializer de Pokémon mais simples para listar 
# os pokémons dentro do Treinador (para não mostrar todos os detalhes)
class PokemonSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        fields = ['id', 'nome', 'foto']

class TreinadorSerializer(serializers.ModelSerializer):
    # 'pokemons' é o M2M - muitos para muitos
    pokemons = PokemonSimplesSerializer(many=True, read_only=True)

    class Meta:
        model = Treinador
        fields = ['id', 'nome', 'idade', 'criado_em', 'atualizado_em', 'pokemons']
        read_only_fields = ['pokemons']

# Serializer para a Relação 
class PokemonsDoTreinadorSerializer(serializers.ModelSerializer):

    pokemon = serializers.PrimaryKeyRelatedField(
        queryset=Pokemon.objects.all()
    )


    class Meta:
        model = PokemonsDoTreinador
        fields = ['pokemon'] 

#Serializer para a Batalha
class BatalhaSerializer(serializers.Serializer):
    
    pokemon_1_id = serializers.IntegerField(required=True)
    pokemon_2_id = serializers.IntegerField(required=True)