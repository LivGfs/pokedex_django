from django.test import TestCase

# api/tests.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Pokemon, Treinador, PokemonsDoTreinador
from unittest.mock import patch # Para "mockar" (simular) a PokeAPI

# Dados de exemplo para o MOCK da PokeAPI
MOCK_POKEAPI_DATA_PIKACHU = {
    'height': 4,
    'weight': 60,
    'sprites': {
        'front_default': 'http://pokeapi.co/pikachu.png',
        'other': {'official-artwork': {'front_default': 'http://pokeapi.co/pikachu-official.png'}}
    }
}
MOCK_POKEAPI_DATA_CHARIZARD = {
    'height': 17,
    'weight': 905,
    'sprites': {'front_default': 'http://pokeapi.co/charizard.png'}
}

class APITests(APITestCase):

    def setUp(self):
        # Configuração inicial para os testes
        self.treinador_ash = Treinador.objects.create(nome="Ash", idade=10)
        
        # Usamos @patch para simular a PokeAPI e evitar chamadas reais
        # nos testes, o que os torna lentos e dependentes da internet.
        
        # Mock para o Pikachu
        with patch('requests.get') as mock_get:
            # Configura o mock para retornar sucesso (200) e os dados do Pikachu
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_POKEAPI_DATA_PIKACHU
            # Criamos o Pokémon (o .save() vai chamar o mock)
            self.pikachu = Pokemon.objects.create(nome="Pikachu")
            
        # Mock para o Charizard
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_POKEAPI_DATA_CHARIZARD
            self.charizard = Pokemon.objects.create(nome="Charizard")

    # === Testes do CRUD (Exemplo) ===

    def test_criar_treinador(self):
        """ Testa a criação de um novo treinador (POST /api/treinadores/) """
        url = reverse('treinador-list') # Pega a URL ('/api/treinadores/')
        data = {'nome': 'Misty', 'idade': 11}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Treinador.objects.count(), 2) # Ash + Misty
        self.assertEqual(Treinador.objects.get(id=response.data['id']).nome, 'Misty')

    def test_criar_pokemon_pokeapi(self):
        """ Testa se o Pokemon.save() preencheu os dados da PokeAPI (do mock) """
        self.assertEqual(self.pikachu.peso, 60)
        self.assertEqual(self.pikachu.altura, 4)
        self.assertEqual(self.pikachu.foto, 'http://pokeapi.co/pikachu-official.png')

    def test_criar_pokemon_nao_encontrado(self):
        """ Testa o erro 404 da PokeAPI ao criar Pokémon (POST /api/pokemons/) """
        url = reverse('pokemon-list')
        
        # Mock de erro 404 da PokeAPI
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            
            data = {'nome': 'PokemonInexistente'}
            response = self.client.post(url, data, format='json')
            
            # O Serializer deve capturar o PokeAPIError e retornar 400
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            # Verifica se o Pokémon não foi criado
            self.assertFalse(Pokemon.objects.filter(nome='PokemonInexistente').exists())

    # === Testes da Lógica de Batalha ===
    
    def test_batalha_vitoria_por_peso(self):
        """ Testa a Batalha onde P1 (Charizard) ganha de P2 (Pikachu) """
        url = reverse('batalha') # /api/batalha/
        data = {
            "pokemon_1_id": self.charizard.id, # Peso 905
            "pokemon_2_id": self.pikachu.id   # Peso 60
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica se o ID do vencedor é o do Charizard
        self.assertEqual(response.data['vencedor']['id'], self.charizard.id)
        self.assertIn("venceu", response.data['mensagem'])

    def test_batalha_empate(self):
        """ Testa a Batalha com empate """
        # Cria um "clone" do Pikachu com o mesmo peso
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_POKEAPI_DATA_PIKACHU
            pikachu_clone = Pokemon.objects.create(nome="PikachuClone")
        
        url = reverse('batalha')
        data = {
            "pokemon_1_id": self.pikachu.id, # Peso 60
            "pokemon_2_id": pikachu_clone.id # Peso 60
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['vencedor']) # Vencedor deve ser nulo
        self.assertIn("Empate", response.data['mensagem'])

    def test_batalha_mesmo_time(self):
        """ Testa a regra que impede Pokémons do mesmo treinador de batalhar """
        # Adiciona os dois pokémons ao Ash
        PokemonsDoTreinador.objects.create(treinador=self.treinador_ash, pokemon=self.pikachu)
        PokemonsDoTreinador.objects.create(treinador=self.treinador_ash, pokemon=self.charizard)

        url = reverse('batalha')
        data = {
            "pokemon_1_id": self.pikachu.id,
            "pokemon_2_id": self.charizard.id
        }
        response = self.client.post(url, data, format='json')

        # Deve retornar erro 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mesmo time", response.data['detail'])
