import os
import requests
import json
import pprint
import re
import urllib.parse

from dotenv import load_dotenv
from notion_client import Client
import wikipedia


load_dotenv()


def add_book():
  properties = get_properties()
  client = Client(auth=os.environ['NOTION_KEY'])
  client.pages.create(
    **{
      'parent': {
        'database_id': os.environ['NOTION_DATABASE_ID']
      },
      'properties': properties
    }
  )


def get_properties():
  title = ''
  while True:
    query = input('Enter title: ')
    results = wikipedia.search(query, results=1)

    if len(results ) == 0:
      print('No results.')
      continue

    title = results[0]
    break

  data = get_page_properties(title)
  results = data['results']['bindings']

  info = resp_to_dict(results)

  thumbnail, thumbnail_name = get_thumbnail(title, info['http://dbpedia.org/ontology/thumbnail'])
 
  properties = {
    'Name': {
      'title': [{
        'text': { 'content': title }
      }],
    },
    'IMG': {
      'files': [{
        'type': 'external',
        'name': thumbnail_name,
        'external': { 'url': thumbnail }
      }]
    }
  }
  print(thumbnail)

  return properties


def get_page_properties(title: str):
  encoded_title = title.replace(' ', '_')

  query = '''
    SELECT ?property ?value
    WHERE {{
      <http://dbpedia.org/resource/{encoded_title}> ?property ?value.
    }}
  '''.format(encoded_title=encoded_title)

  params = {
    'default-graph-uri': 'http://dbpedia.org',
    'query': query,
    'format': 'application/sparql-results+json',
    'timeout': '3000',
    'signal_void': 'on',
    'signal_unconnected': 'on'
  }

  url = 'https://dbpedia.org/sparql'

  resp = requests.get(url, params=params)
  return json.loads(resp.text)


def resp_to_dict(json_arr: list):
  new_dict = {}

  # There may be multiple values for the same property, but not for the ones I care about
  for pair in json_arr:
    if not_wanted(pair['value']):
      continue
    prop = pair['property']['value']
    val = pair['value']['value']
    new_dict[prop] = val

  return new_dict


def not_wanted(value: dict):
  if 'xml:lang' in value and value['xml:lang'] != 'en':
    return True
  return False


def get_thumbnail(title: str, bad_url: str):
  maybe_thumbnail_name = re.search('FilePath/(.*)\\?', bad_url)

  if maybe_thumbnail_name is None:
    print("no thumbnail")
    return ''

  thumbnail_name = urllib.parse.quote(maybe_thumbnail_name.group(1))
  all_imgs = wikipedia.WikipediaPage(title).images

  for img in all_imgs:
    if thumbnail_name in img:
      return img, thumbnail_name

  return ''

add_book()
# get_properties()
  


# prefix dbpedia: <http://dbpedia.org/resource/>
# prefix dbpedia-owl: <http://dbpedia.org/ontology/>

# select ?abstract ?thumbnail where { 
#   dbpedia:Ernest_Hemingway dbpedia-owl:abstract ?abstract ;
#                            dbpedia-owl:thumbnail ?thumbnail .
#   filter(langMatches(lang(?abstract),"en"))
# }


# prefix dbpedia: <http://dbpedia.org/resource/>
# prefix dbp: <https://dbpedia.org/property/>

# select *
# where { 
#   dbpedia:Jujutsu_Kaisen dbo:abstract ?abstract .
#   OPTIONAL { dbpedia:Jujutsu_Kaisen dbo ?author }
#   filter(langMatches(lang(?abstract),"en"))
# }


# SELECT ?property ?value
# WHERE {
#     <http://dbpedia.org/resource/Jujutsu_Kaisen> ?property ?value.
#     FILTER(LANG(?value) = "en")
# }