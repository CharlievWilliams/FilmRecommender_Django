import csv
import io
import json

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
                (index, details_data['id'],
                 details_data['title'],
                 genres,
                 production_companies,
                 spoken_languages,
                 keywords,
                 cast))
            index = index + 1
        count = count + 1
        if count == 500:
            break
    # Create CSV
    writer.writerow(
        ('index', 'id', 'title', 'genres', 'production companies', 'spoken languages', 'keywords', 'credits'))
    writer.writerows(films)
    f.close()
    # TODO: Return proper response
    return HttpResponse("<html>Success</html>")


def getRecommendations(request):
    def get_id_from_index(index):
        return df[df.index == index]["id"].values[0]

    def get_index_from_id(id):
        return df[df.id == int(id)]["index"].values[0]

    query = request.GET.get('id', '')  # This is the ID of the film.

    df = pd.read_csv("full_dataset.csv")

    # Select Features
    features = ['title', 'genres', 'production companies', 'spoken languages', 'keywords', 'credits']

    # Combine all Features
    for feature in features:
        df[feature] = df[feature].fillna('')

    def combine_features(row):
        return row['title'] + " " + row['genres'] + " " + row['production companies'] + " " + row[
            'spoken languages'] + " " + row['keywords'] + " " + row['credits']

    df["combined_features"] = df.apply(combine_features, axis=1)

    # Create Count Matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(df["combined_features"])

    # Compute Cosine Similarity
    cosine_sim = cosine_similarity(count_matrix)

    # Get Index of Movie From Title
    movie_index = get_index_from_id(query)
    similar_movies = list(enumerate(cosine_sim[movie_index]))
    sorted_similar_films = sorted(similar_movies, key=lambda x: x[1], reverse=True)

    # Get List of Similar Films
    count = 0
    films = []
    for movie in sorted_similar_films:
        films.append(str(get_id_from_index(movie[0])))
        count = count + 1
        if count > 10:
            break

    data = {
        'id': [films[0], films[1], films[2], films[3], films[4], films[5], films[6], films[7], films[8], films[9]]
    }
    dump = json.dumps(data)
    return HttpResponse(dump, content_type="application/json")
