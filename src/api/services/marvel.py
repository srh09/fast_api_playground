import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import aiohttp
from requests import HTTPError

from core.config import MARVEL_PRIVATE_KEY, MARVEL_PUBLIC_KEY
from models.character import Character
from models.comic import Comic

MARVEL_BASE_URL = 'https://gateway.marvel.com/v1/public'
MAX_RESULTS = 50  # Iron man has 2600 comics alone... Remove this if you want all data.


def _get_credentials():
    """
    :return: Credential string needed to access Marvel API.
    """
    ts = round(datetime.utcnow().timestamp())
    hash = hashlib.md5(f'{ts}{MARVEL_PRIVATE_KEY}{MARVEL_PUBLIC_KEY}'.encode()).hexdigest()
    return f'apikey={MARVEL_PUBLIC_KEY}&ts={ts}&hash={hash}'


async def _send_get_request(uri: str):
    """
    :param str uri: URI for resource to be fetched.
    :return: Results of requested resource.
    :raise HTTPError: If non 200 response from resource.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(uri) as response:
            if response.status != 200:
                raise HTTPError(f'Status: {response.status}, URI: {uri}, Reason: {response.reason}')
            return await response.json()


async def semaphore_gather(tasks, task_limit):
    """
    Limits the max concurrent asyncio tasks.
    """
    semaphore = asyncio.Semaphore(task_limit)

    async def _wrap_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(_wrap_task(t) for t in tasks))


async def get_character_by_id(marvel_id: int) -> Character:
    """
    :param int marvel_id: Marvel API id of the Character to be found.
    :return: The requested Character.
    :raise TypeError: If invalid marvel_id was given as an argument.
    """
    response = await _send_get_request(f'{MARVEL_BASE_URL}/characters/{marvel_id}?{_get_credentials()}')

    if not response['data']['results']:  # Somehow an invalid id was recorded.
        raise TypeError('No Character found for given marvel_id.')

    result = response['data']['results'][0]
    print(f'Character {result["name"]} from Marvel-----------')
    return Character(**{
        'marvel_id': result['id'],
        'comic_count': result['comics']['available'],
        'series_count': result['series']['available'],
        'stories_count': result['stories']['available'],
        'name': result['name'],
        'description': result['description'],
        'thumbnail': f'{result["thumbnail"]["path"]}.{result["thumbnail"]["extension"]}',
    })


async def get_character_by_name(name: str) -> Optional[Character]:
    """
    :param str name: Name of the Character to find.
    :return: The named Character if found.
    """
    response = await _send_get_request(f'{MARVEL_BASE_URL}/characters?name={name}&{_get_credentials()}')

    if not response['data']['results']:
        return None  # Marvel API didn't match a Character to the given Name.

    result = response['data']['results'][0]
    return Character(**{
        'marvel_id': result['id'],
        'comic_count': result['comics']['available'],
        'series_count': result['series']['available'],
        'stories_count': result['stories']['available'],
        'name': result['name'],
        'description': result['description'],
        'thumbnail': f'{result["thumbnail"]["path"]}.{result["thumbnail"]["extension"]}',
    })


async def get_comics_by_character_id(marvel_id: int) -> Tuple[List[Dict], Set]:
    """
    :param int marvel_id: Marvel API id of the Character to be referenced.
    :return: List Comics and affiliated Character marvel_ids
    :raise Exception: exception on http error TODO
    """
    offset = 0
    increment = 25
    uri = f'{MARVEL_BASE_URL}/characters/{marvel_id}/comics?{_get_credentials()}&limit={increment}'
    results = []

    while True:  # We don't know the total until first response is received.
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{uri}&offset={offset}') as response:
                if response.status != 200:
                    # TODO Handle error.
                    raise HTTPError(f'Status: {response.status}, URI: {uri}, Reason: {response.reason}')
                response = await response.json()
                results.extend(response['data']['results'])
                offset += response['data']['count']
                if offset >= response['data']['total']:
                    break
                if len(results) >= MAX_RESULTS:
                    break

    # Organize the results.
    comics_relationships: List[Dict] = []
    unique_character_ids = set()
    for result in results:
        # Get the url_detail property for Comic
        url_detail = None
        for url in result['urls']:
            if url['type'] == 'detail':
                url_detail = url['url']
                break

        # Extract the Comic and its Character relationships.
        character_ids = [int(item['resourceURI'].split('/')[-1]) for item in result['characters']['items']]
        unique_character_ids.update(character_ids)
        print(f'storing comic {result["title"]} from marvel-----------')
        comics_relationships.append({
            'comic': Comic(**{
                'marvel_id': result['id'],
                'issue_number': result['issueNumber'],
                'page_count': result['pageCount'],
                'isbn': result['isbn'],
                'title': result['title'],
                'description': result['description'] or '',
                'url_detail': url_detail,
                'thumbnail': f'{result["thumbnail"]["path"]}.{result["thumbnail"]["extension"]}',
            }),
            'character_ids': character_ids
        })
    return comics_relationships, unique_character_ids
