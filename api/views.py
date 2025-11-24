# api/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Treinador, Pokemon, PokemonsDoTreinador
from .serializers import (
    TreinadorSerializer, 
    PokemonSerializer, 
    PokemonsDoTreinadorSerializer,
    BatalhaSerializer
)

# === ViewSet do Treinador (CRUD + Ações de Pokémon) ===

class TreinadorViewSet(viewsets.ModelViewSet):
    """
    API para CRUD de Treinadores.
    Inclui ações para adicionar e remover pokémons.
    """
    queryset = Treinador.objects.all().prefetch_related('pokemons') # Otimiza a busca dos pokémons
    serializer_class = TreinadorSerializer

    # 'ModelViewSet' já fornece:
    # list()     (GET /treinadores/)
    # create()   (POST /treinadores/)
    # retrieve() (GET /treinadores/{id}/)
    # update()   (PUT /treinadores/{id}/)
    # partial_update() (PATCH /treinadores/{id}/)
    # destroy()  (DELETE /treinadores/{id}/)

    # --- Ação customizada para ADICIONAR Pokémon ---
    @action(detail=True, methods=['post'], url_path='adicionar-pokemon')
    def adicionar_pokemon(self, request, pk=None):
        """
        Adiciona um Pokémon a um Treinador.
        Espera um JSON: {"pokemon": <id_do_pokemon>}
        """
        treinador = self.get_object() # Pega o treinador (baseado no 'pk' da URL)
        
        # Valida o ID do pokémon enviado no JSON
        serializer = PokemonsDoTreinadorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        pokemon = serializer.validated_data['pokemon']

        # Verifica se o treinador já possui este pokémon
        if PokemonsDoTreinador.objects.filter(treinador=treinador, pokemon=pokemon).exists():
            return Response(
                {"detail": "Treinador já possui este Pokémon."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Adiciona a relação
        PokemonsDoTreinador.objects.create(treinador=treinador, pokemon=pokemon)
        
        # Retorna o treinador atualizado
        return Response(TreinadorSerializer(treinador).data, status=status.HTTP_201_CREATED)

    # --- Ação customizada para REMOVER Pokémon ---
    @action(detail=True, methods=['post'], url_path='remover-pokemon')
    def remover_pokemon(self, request, pk=None):
        """
        Remove um Pokémon de um Treinador.
        Espera um JSON: {"pokemon": <id_do_pokemon>}
        """
        treinador = self.get_object()
        
        serializer = PokemonsDoTreinadorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        pokemon = serializer.validated_data['pokemon']

        # Tenta encontrar e deletar a relação
        relacao = PokemonsDoTreinador.objects.filter(treinador=treinador, pokemon=pokemon)
        
        if not relacao.exists():
            return Response(
                {"detail": "Treinador não possui este Pokémon."},
                status=status.HTTP_404_NOT_FOUND
            )

        relacao.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


# === ViewSet do Pokémon (CRUD) ===

class PokemonViewSet(viewsets.ModelViewSet):
    """
    API para CRUD de Pokémons.
    Ao criar (POST), apenas o 'nome' é necessário.
    """
    queryset = Pokemon.objects.all()
    serializer_class = PokemonSerializer

# === View da Batalha ===

class BatalhaView(APIView):
    """
    API para Batalha de Pokémons.
    Recebe dois IDs de Pokémon e retorna o vencedor.
    """
    
    def post(self, request):
        serializer = BatalhaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Pega os IDs validados
        pokemon_1_id = serializer.validated_data['pokemon_1_id']
        pokemon_2_id = serializer.validated_data['pokemon_2_id']

        # Busca os Pokémons (e trata se não existirem)
        p1 = get_object_or_404(Pokemon, pk=pokemon_1_id)
        p2 = get_object_or_404(Pokemon, pk=pokemon_2_id)

        # 1. Verifica se são do mesmo time
        # Busca treinadores em comum
        treinadores_p1 = set(PokemonsDoTreinador.objects.filter(pokemon=p1).values_list('treinador_id', flat=True))
        treinadores_p2 = set(PokemonsDoTreinador.objects.filter(pokemon=p2).values_list('treinador_id', flat=True))

        # 'intersection' encontra os IDs em comum
        if treinadores_p1.intersection(treinadores_p2):
            return Response(
                {"detail": "Batalha inválida: Os Pokémons são do mesmo time!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Regra da Batalha (Peso)
        if p1.peso > p2.peso:
            vencedor = p1
            perdedor = p2
            mensagem = f"{vencedor.nome} (Peso: {vencedor.peso}) venceu {perdedor.nome} (Peso: {perdedor.peso})!"
        elif p2.peso > p1.peso:
            vencedor = p2
            perdedor = p1
            mensagem = f"{vencedor.nome} (Peso: {vencedor.peso}) venceu {perdedor.nome} (Peso: {perdedor.peso})!"
        else:
            # 3. Regra do Empate
            vencedor = None
            mensagem = f"Empate! {p1.nome} e {p2.nome} têm o mesmo peso ({p1.peso})."

        # Monta a resposta
        resultado = {
            "mensagem": mensagem,
            "vencedor": PokemonSerializer(vencedor).data if vencedor else None,
            "pokemon_1": PokemonSerializer(p1).data,
            "pokemon_2": PokemonSerializer(p2).data,
        }
        
        return Response(resultado, status=status.HTTP_200_OK)