import csv
import io
import json
import simplejson

import pandas as pd
import requests
from django.http import HttpResponse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def index(request):
    response = json.dumps([{}])
    return HttpResponse(response, content_type='text/json')


def massDataDump(request):
    count = 1
    index = 0
    f = io.open("full_dataset.csv", "w", newline="", encoding="utf-8")
    writer = csv.writer(f)
    films = ([])
    while True:
        # Retrieve API Responses
        details_response = requests.get(
            f'https://api.themoviedb.org/3/movie/{count}?api_key=1866f49ed1f23d71e5cbc668c0ab5bf8&language=en-US')
        keywords_response = requests.get(
            f'https://api.themoviedb.org/3/movie/{count}/keywords?api_key=1866f49ed1f23d71e5cbc668c0ab5bf8')
        credits_response = requests.get(
            f'https://api.themoviedb.org/3/movie/{count}/credits?api_key=1866f49ed1f23d71e5cbc668c0ab5bf8&language=en-US')

        details_data = json.loads(details_response.text)
        keywords_data = json.loads(keywords_response.text)
        credits_data = json.loads(credits_response.text)

        # Check if valid response
        if 'genres' in details_data and 'keywords' in keywords_data and 'cast' in credits_data:
            # Format responses for CSV
            genres, production_companies, spoken_languages, keywords, cast = "", "", "", "", ""
            for item in details_data['genres']:
                genres = genres + item['name'] + " "
            for item in details_data['production_companies']:
                production_companies = production_companies + item['name'] + " "
            for item in details_data['spoken_languages']:
                spoken_languages = spoken_languages + item['name'] + " "
            for item in keywords_data['keywords']:
                keywords = keywords + item['name'] + " "
            for item in credits_data['cast']:
                cast = cast + item['name'] + " "

            # Append to array
            films.append(
                (index,
                 details_data['id'],
                 details_data['title'],
                 details_data['overview'],
                 details_data['poster_path'],
                 genres,
                 production_companies,
                 spoken_languages,
                 keywords,
                 cast))
            index = index + 1
        count = count + 1
        if count == 300:  # Total ID number
            break
    # Create CSV
    writer.writerow(
        ('index', 'id', 'title', 'overview', 'poster path', 'genres', 'production companies', 'spoken languages',
         'keywords', 'credits'))
    writer.writerows(films)
    f.close()
    # TODO: Return proper response
    return HttpResponse("<html>Success</html>")


def getRecommendations(request):

    def find_id(index):
        return df[df.index == index]["id"].values[0]

    def find_title(index):
        return df[df.index == index]["title"].values[0]

    def find_overview(index):
        return df[df.index == index]["overview"].values[0]

    def find_poster_path(index):
        return df[df.index == index]["poster path"].values[0]

    def get_index_from_id(id):
        return df[df.id == int(id)]["index"].values[0]

    # This is the ID of the film.
    film_id = request.GET.get('id', '')
    # These are the parameters for recommendation
    use_title = request.GET.get('title', 'false')
    use_genres = request.GET.get('genres', 'false')
    use_production_companies = request.GET.get('production_companies', 'false')
    use_spoken_languages = request.GET.get('spoken_languages', 'false')
    use_keywords = request.GET.get('keywords', 'false')
    use_credits = request.GET.get('credits', 'false')

    df = pd.read_csv("full_dataset.csv")

    # Select Features
    features = []
    if use_title == "true":
        features.append('title')
    if use_genres == "true":
        features.append('genres')
    if use_production_companies == "true":
        features.append('production companies')
    if use_spoken_languages == "true":
        features.append('spoken languages')
    if use_keywords == "true":
        features.append('keywords')
    if use_credits == "true":
        features.append('credits')

    # Combine all Features
    for feature in features:
        df[feature] = df[feature].fillna('')

    def combine_features(row):
        combined_features = ""
        if use_title == "true":
            combined_features = combined_features + row['title'] + " "
        if use_genres == "true":
            combined_features = combined_features + row['genres'] + " "
        if use_production_companies == "true":
            combined_features = combined_features + row['production companies'] + " "
        if use_spoken_languages == "true":
            combined_features = combined_features + row['spoken languages'] + " "
        if use_keywords == "true":
            combined_features = combined_features + row['keywords'] + " "
        if use_credits == "true":
            combined_features = combined_features + row['credits'] + " "

        return combined_features

    df["combined_features"] = df.apply(combine_features, axis=1)

    # Create Count Matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(df["combined_features"])

    # Compute Cosine Similarity
    cosine_sim = cosine_similarity(count_matrix)

    # Get Index of Film From Title
    film_index = get_index_from_id(film_id)
    similar_films = list(enumerate(cosine_sim[film_index]))
    sorted_similar_films = sorted(similar_films, key=lambda x: x[1], reverse=True)

    # Get List of Similar Films
    count = 0
    data = []
    for film in sorted_similar_films[1:]:
        data.append({
            "id": str(find_id(film[0])),
            "title": find_title(film[0]),
            "overview": find_overview(film[0]),
            "poster_path": find_poster_path(film[0])
        })
        count = count + 1
        if count > 20:
            break

    dump = simplejson.dumps(data, ignore_nan=True)
    return HttpResponse(dump, content_type="application/json")
