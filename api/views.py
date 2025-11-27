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


class TreinadorViewSet(viewsets.ModelViewSet):
    queryset = Treinador.objects.all().prefetch_related('pokemons') 
    serializer_class = TreinadorSerializer

    @action(detail=True, methods=['post'], url_path='adicionar-pokemon')
    def adicionar_pokemon(self, request, pk=None):

        treinador = self.get_object() 
        serializer = PokemonsDoTreinadorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        pokemon = serializer.validated_data['pokemon']

        if PokemonsDoTreinador.objects.filter(treinador=treinador, pokemon=pokemon).exists():
            return Response(
                {"detail": "Treinador já possui este Pokémon."},
                status=status.HTTP_400_BAD_REQUEST
            )


        PokemonsDoTreinador.objects.create(treinador=treinador, pokemon=pokemon)
        

        return Response(TreinadorSerializer(treinador).data, status=status.HTTP_201_CREATED)

 
    @action(detail=True, methods=['post'], url_path='remover-pokemon')
    def remover_pokemon(self, request, pk=None):
  
        treinador = self.get_object()
        
        serializer = PokemonsDoTreinadorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        pokemon = serializer.validated_data['pokemon']


        relacao = PokemonsDoTreinador.objects.filter(treinador=treinador, pokemon=pokemon)
        
        if not relacao.exists():
            return Response(
                {"detail": "Treinador não possui este Pokémon."},
                status=status.HTTP_404_NOT_FOUND
            )

        relacao.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class PokemonViewSet(viewsets.ModelViewSet):

    queryset = Pokemon.objects.all()
    serializer_class = PokemonSerializer


class BatalhaView(APIView):
   
    
    def post(self, request):
        serializer = BatalhaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

      
        pokemon_1_id = serializer.validated_data['pokemon_1_id']
        pokemon_2_id = serializer.validated_data['pokemon_2_id']

      
        p1 = get_object_or_404(Pokemon, pk=pokemon_1_id)
        p2 = get_object_or_404(Pokemon, pk=pokemon_2_id)

      
        treinadores_p1 = set(PokemonsDoTreinador.objects.filter(pokemon=p1).values_list('treinador_id', flat=True))
        treinadores_p2 = set(PokemonsDoTreinador.objects.filter(pokemon=p2).values_list('treinador_id', flat=True))

       
        if treinadores_p1.intersection(treinadores_p2):
            return Response(
                {"detail": "Batalha inválida: Os Pokémons são do mesmo time!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        if p1.peso > p2.peso:
            vencedor = p1
            perdedor = p2
            mensagem = f"{vencedor.nome} (Peso: {vencedor.peso}) venceu {perdedor.nome} (Peso: {perdedor.peso})!"
        elif p2.peso > p1.peso:
            vencedor = p2
            perdedor = p1
            mensagem = f"{vencedor.nome} (Peso: {vencedor.peso}) venceu {perdedor.nome} (Peso: {perdedor.peso})!"
        else:
            
            vencedor = None
            mensagem = f"Empate! {p1.nome} e {p2.nome} têm o mesmo peso ({p1.peso})."

        
        resultado = {
            "mensagem": mensagem,
            "vencedor": PokemonSerializer(vencedor).data if vencedor else None,
            "pokemon_1": PokemonSerializer(p1).data,
            "pokemon_2": PokemonSerializer(p2).data,
        }
        
        return Response(resultado, status=status.HTTP_200_OK)