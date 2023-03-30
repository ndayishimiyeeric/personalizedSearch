from settings import *
import spacy
import numpy as np
import requests
from requests.exceptions import RequestException
import pandas as pd
from storage import DBStorage
from urllib.parse import quote_plus
from datetime import datetime

nlp = spacy.load("en_core_web_md")


def search_api(query, pages=int(RESULT_COUNT / 10)):
    """Search Google API for query and return results as a list of dicts."""
    results = []
    search_criteria = {
        "topics": set(),
        "locations": set(),
        "dates": set(),
    }
    search_doc = nlp(query)
    for token in search_doc:
        if token.ent_type_ == "GPE":
            search_criteria["locations"].add(token.text.lower())
        elif token.ent_type_ == "DATE":
            search_criteria["dates"].add(token.text.lower())
        else:
            if token.pos_ == "NOUN":
                search_criteria["topics"].add(token.lemma_.lower())
            elif token.pos_ == "VERB":
                search_criteria["topics"].add(token.lemma_.lower())
    for i in range(0, pages):
        start = i * 10 + 1
        url = SEARCH_URL.format(
            key=SEARCH_KEY,
            cx=SEARCH_CX,
            query=quote_plus(query),
            start=start
        )
        try:
            response = requests.get(url)
            data = response.json()
            results += data["items"]
        except RequestException as e:
            print(e)

    res_df = pd.DataFrame.from_dict(results)
    res_df['rank'] = list(range(1, res_df.shape[0] + 1))
    res_df = res_df[['link', 'rank', 'title', 'snippet']]
    return res_df


def scrape_page(links):
    html = []
    for link in links:
        try:
            response = requests.get(link, timeout=5)
            html.append(response.text)
        except RequestException as e:
            print(e)
            html.append('')
    return html


def search(query):
    columns = ['query', 'rank', 'link', 'title', 'snippet', 'html', 'created']
    storage = DBStorage()

    stored_results = storage.query_results(query)
    if stored_results.shape[0] > 0:
        stored_results['created'] = pd.to_datetime(stored_results['created'])
        return stored_results[columns]

    results = search_api(query)
    results['html'] = scrape_page(results['link'])
    results = results[results['html'].str.len() > 0].copy()

    results['query'] = query
    results['created'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    results = results[columns]
    results.apply(lambda x: storage.insert_row(x), axis=1)

    return results
