import csv
import json
import os.path
from typing import Any, Dict, List, Tuple, Optional

import requests

import lac_covid19.geo.geo_files as geo_files


URL_SINGLE_ADDRESS = 'https://geocoding.geo.census.gov/geocoder/locations/onelineaddress'
BENCHMARK = 'Public_AR_Current'
FORMAT = 'json'

COORDINATES = 'coordinates'

MATCH = 'Match'


def prepare_census_geocode() -> None:
    address_map = None
    with open(geo_files.RESID_ADDRESS) as f:
        address_map = json.load(f)

    census_format = []
    for location_name in address_map:
        street, city, state, zip_ = address_map[location_name].split(', ')
        census_format += ((location_name, street, city, state, zip_),)

    with open(geo_files.ADDRESS_LIST, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(census_format)


def _request_address(address: str) -> List[Dict[str, Any]]:
    payload = {
        'format': FORMAT,
        'benchmark': BENCHMARK,
        'address': address,
    }
    r = requests.get(URL_SINGLE_ADDRESS, payload)
    if r.status_code == 200:
        return json.loads(r.text)['result']['addressMatches']


def _extract_coordinates(address_match: Dict[str, Any]) -> Tuple[float, float]:
    position = address_match['coordinates']
    return position['y'], position['x']


def _interpret_census_geocode(
    query_reply: List[Dict[str, Any]]) -> Optional[Tuple[float, float]]:

    if len(query_reply) == 1:
        return _extract_coordinates(query_reply[0])

    all_positions = [_extract_coordinates(x) for x in query_reply]
    if len(set(all_positions)) == 1:
        return all_positions[0]


def query_single_address(address: str) -> Optional[Tuple[int, int]]:
    return _interpret_census_geocode(_request_address(address))


def read_geocodes():
    ADDRESS_INDEX = 1
    MATCH_INDEX = 2
    COORDINATE_INDEX = 5

    raw_geocodes = []
    unsuccessful_geocodes = []
    with open(geo_files.GEOCODE_RESULTS) as f:
        reader = csv.reader(f)
        for row in reader:
            if row[MATCH_INDEX] == MATCH:
                raw_geocodes += (row,)
            else:
                unsuccessful_geocodes += (row[ADDRESS_INDEX],)

    address_coordinates = {}

    for row in raw_geocodes:
        address = row[ADDRESS_INDEX]
        longitude, latitude = [float(x) for x
                               in row[COORDINATE_INDEX].split(',')]
        address_coordinates[address] = (latitude, longitude)


    manual_geocode = None
    with open(geo_files.MANUAL_GEOCODE) as f:
        manual_geocode = json.load(f)

    total_single_requests = len(unsuccessful_geocodes)
    current_request = 1
    for address in unsuccessful_geocodes:
        print('{} of {}: {}'.format(current_request, total_single_requests,
                                    address),
               end=' ')

        latitude, longitude = None, None
        result_msg = 'FAILED'
        new_request_coordinates = query_single_address(address)
        if new_request_coordinates:
            latitude, longitude = new_request_coordinates
            result_msg = '({}, {})'.format(latitude, longitude)
        else:
            if address in manual_geocode:
                latitude, longitude = manual_geocode.get(address)
            result_msg = ('Manual Entry')

        print(result_msg)
        address_coordinates[address] = (latitude, longitude)

        current_request += 1

    with open(geo_files.ADDRESS_GEOCODE, 'w') as f:
        json.dump(address_coordinates, f)


if __name__ == "__main__":
    pass
    # prepare_census_geocode()