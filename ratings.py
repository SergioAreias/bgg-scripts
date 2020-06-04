import logging
import requests
import time

from xml.etree import ElementTree

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
        'Host': 'boardgamegeek.com',
        'User-Agent': 'Mozilla/5.0 Gecko/20100101 Firefox/76.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }

BGG_API_URL = 'https://boardgamegeek.com/xmlapi2/'
BGG_API_THING = BGG_API_URL + 'thing?id={}&stats=1'
BGG_API_SEARCH = BGG_API_URL + 'search?query={}&type=boardgame'
MAX_ATTEMPTS = 3


def _extract_rating(response):
    # TODO Some games do not have ratings (e.g. The Crystal Maze: Eastern Zone Mini Game)
    # I am also ignoring any failures related with the XPath
    tree = ElementTree.fromstring(response.content)
    avg = tree.find('item/statistics/ratings/average').attrib['value']
    return str(round(float(avg), 2))


def _get_rating(game_id, game_name):
    if not game_id:
        return ''

    logger.info(game_id)
    try:
        res = requests.get(BGG_API_THING.format(game_id), headers=HEADERS, timeout=10)

        if res.status_code >= 400:
            logger.error('Failed to get the rating for {} using ID {}'.format(game_name, game_id))
            return ''

        return _extract_rating(res)
    except:
        logger.exception('Failed to get the rating for {} using ID {}'.format(game_name, game_id))
        return ''


def _extract_id(response):
    # TODO Assumes that the first entry in the list is the one that we are looking for
    # This is not always true if you are looking for the latest version (e.g. Cosmic Encounter)
    tree = ElementTree.fromstring(response.content)
    return tree.find('item').attrib['id']


def _get_id(game, attempts=0):
    try:
        res = requests.get(BGG_API_SEARCH.format(game), headers=HEADERS, timeout=10)

        if res.status_code == 202 or res.status_code == 429:
            # TODO Use a proper rate limiter
            if attempts < MAX_ATTEMPTS:
                time.sleep(2)
                return _get_id(game, attempts + 1)
        elif res.status_code == 200:
            return _extract_id(res)
        else:
            logger.error('Failed to get the ID for {}'.format(game))
            logger.error('Status: {} - Reason: {}', res.status_code, res.reason)
    except:
        logger.exception('Failed to get the ID for {}'.format(game))

    return None


def main():
    # Loads a file with one game per line and outputs a csv file
    with open("games.csv") as _in:
        with open("out.csv", "w") as _out:
            for line in _in:
                # TODO Ignore empty lines
                game = line.rstrip()
                logger.info('[' + game + ']')

                game_id = _get_id(game)
                rating = _get_rating(game_id, game)
                _out.write(game + ',' + rating + '\n')


if __name__ == '__main__':
    main()
