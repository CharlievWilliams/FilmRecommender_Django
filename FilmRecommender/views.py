import json
import requests
from django.http import HttpResponse


def index(request):
    response = json.dumps([{}])
    return HttpResponse(response, content_type='text/json')


def getRecommendations(request):
    query = request.GET.get('name', '')  # This is the ID of the film.
    print(query)
    response = requests.get(f'https://api.themoviedb.org/3/movie/{query}/credits?api_key=1866f49ed1f23d71e5cbc668c0ab5bf8&language=en-US')
    return HttpResponse(response, content_type='text/json')


def oldHome(request):
    query = request.GET.get('name', '')  # This is the name of the film. This will eventually reference the film ID specifically
    print(query)
    response = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key=1866f49ed1f23d71e5cbc668c0ab5bf8&language=en-US&query={query}&page=1&include_adult=false')
    return HttpResponse(response, content_type='text/json')
