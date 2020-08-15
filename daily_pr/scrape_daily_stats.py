"""Scrapes statistics from the daily COVID-19 briefing published by the Los
    Angeles County Department of Public Health.
"""

import datetime as dt
import json
import os
import pickle
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

import bs4
import requests

import lac_covid19.const as const
import lac_covid19.const.paths as paths
import lac_covid19.daily_pr.bad_data as bad_data
import lac_covid19.daily_pr.lacph_prid as lacph_prid

DATE = const.DATE

LACPH_PR_URL_BASE = 'http://www.publichealth.lacounty.gov/phcommon/public/media/mediapubhpdetail.cfm?prid='  # pylint: disable=line-too-long
RE_DATE = re.compile('[A-Z][a-z]+ \d{2}, 20\d{2}')

RE_TESTING_1 = re.compile(
    'testing\s+results\s+available.+\s([\d,]{6,})\s+individuals.+\s(\d{1,2})%.+testing\s+positive')  # pylint: disable=line-too-long

RE_TESTING_2 = re.compile(
    'Testing\s+results\s+are\s+available\s+for.*\s([\d,]{6,})\s+individuals,?\s+with\s+(\d{1,2})%\s+of\s+(all\s+)?people\s+testing\s+positive'  # pylint: disable=line-too-long
)

RE_NEW_DEATHS_CASES = re.compile(
    '([\d,]+)\s+new\s+deaths\s+and\s+([\d,]+)\s+new\s+cases'
)

RE_UNDER_INVESTIGATION = re.compile('Under Investigation')

HEADER_CASE_COUNT = re.compile(
    'Laboratory Confirmed Cases.*\s([\d,]+)\s+Total Cases')
HEADER_DEATH = re.compile('Deaths\s+([\d,]+)')
ENTRY_BY_DEPT = re.compile(
    '(Los Angeles County \(excl\. LB and Pas\)|{}|{})[\s-]*(\d+)'
    .format(const.hd.LONG_BEACH, const.hd.PASADENA))

LAC_ONLY = '\(Los Angeles County Cases Only-excl LB and Pas\)'

HEADER_AGE_GROUP = re.compile('Age Group {}'.format(LAC_ONLY))
ENTRY_AGE = re.compile('(\d+ to \d+|over \d+)(\s*--\s*|\s+)(\d+)')

HEADER_HOSPITAL = re.compile('Hospitalization')
ENTRY_HOSPITAL = re.compile('([A-Z][A-Za-z() ]+[)a-z])\s*(\d+)')

HEADER_GENDER = re.compile('Gender {}'.format(LAC_ONLY))
ENTRY_GENDER = re.compile('(Mm*ale|{}|{})\s+(\d+)'.format(const.FEMALE,
                                                          const.OTHER))

HEADER_RACE_CASE = re.compile('(?<!Deaths )Race/Ethnicity {}'.format(LAC_ONLY))
HEADER_RACE_DEATH = re.compile('Deaths Race/Ethnicity {}'.format(LAC_ONLY))
ENTRY_RACE = re.compile('([A-Z][A-Za-z/ ]+[a-z])\s+(\d+)')

HEADER_LOC = re.compile('CITY / COMMUNITY\** \(Rate\**\)')
RE_LOC = re.compile(
    '([A-Z][A-Za-z/\-\. ]+[a-z]\**)\s+([0-9]+|--)\s+\(\s+(--|[0-9]+|[0-9]+\.[0-9]+)\s\)')  # pylint: disable=line-too-long

EXTENDED_HTML = tuple([dt.date(*x) for x in bad_data.BAD_HTML_FORMAT])
FORMAT_START_HOSPITAL_NESTED = dt.date(2020, 4, 4)
FORMAT_START_AGE_NESTED = dt.date(2020, 4, 4)
CORR_FACILITY_RECORDED = dt.date(2020, 5, 14)

DIR_RESP_CACHE = paths.DIR_CACHED_HTML
DIR_PARSED_PR = paths.DIR_PARSED_JSON
LACPH = 'lacph'

HTML = 'html'
JSON = 'json'

TOTAL_HOSPITALIZATIONS = 'Hospitalized (Ever)'


def local_filename(pr_date: dt.date, deparment: str, extenstion: str) -> str:
    """Provides consistant naming to local files generated by program."""
    return '{}-{}.{}'.format(pr_date.isoformat(), deparment, extenstion)


def _str_to_int(number: str) -> int:
    """Parses a string to an integer with safegaurds for commas in numerical
        representation.
    """
    return int(number.replace(',', ''))


def _date_to_tuple(date_: dt.date) -> Tuple[int, int, int]:
    return date_.year, date_.month, date_.day


def _cache_write_generic(contents: Any, date_: dt.date, directory: str,
                         extension: str, assert_check: Callable,
                         write_func: Callable) -> None:
    """Customizable function to write some file contents to a local cache
    directory.

    Args:
        contents: The data to be written out.
        date_: The date in relationship to the contents.
        dir: The local directory holding the output file.
        extension: The appropriate exension for the output file.
        assert_check: A function to check the validity of the output data.
            This takes contents as the only input and returns a boolean.
        write_func: A function used to put contents into the file output.
            This takes a text I/O object and contents and writes out.
    """

    if not assert_check(contents):
        raise ValueError('Attempted to write data which does not pass '
                         'correctness test.')

    cache_dir = os.path.join(os.path.dirname(__file__), directory)
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)

    filename = local_filename(date_, LACPH, extension)
    with open(os.path.join(cache_dir, filename), 'w') as f:
        write_func(f, contents)


def _cache_read_generic(date_: dt.date, directory: str, extension: str,
                        read_func: Callable) -> Optional[Any]:
    """Customizable function to read file contents.

    Args:
        date_: The content date of the function to read.
        directory: The local directory where the file could be found if such
            file exists.
        extension: The file extension.
        read_func: A function to read in the file properly. It takes a text
            I/O as the single output.

    Returns:
        If the file exists, it returns what is returned by read_func when
        passed the target file text I/O object. If the file does not exist,
        it returns None.
    """

    file_ = os.path.join(os.path.dirname(__file__), directory,
                         local_filename(date_, LACPH, extension))

    if os.path.isfile(file_):
        with open(file_, 'r') as f:
            return read_func(f)
    return None


def _cache_write_html_resp(resp: str, pr_date: dt.date) -> None:
    """Writes a local copy of Los Angeles County COVID-19 daily briefings."""

    _cache_write_generic(resp, pr_date, DIR_RESP_CACHE, HTML,
                         (lambda r: isinstance(r, str)),
                         (lambda f, r: f.write(r)))


def _cache_read_html_resp(pr_date: dt.date) -> str:
    """Attempts to read local copy of daily LACPH COVID-19 briefings and
    automatically resorts to online request if local copy is unavalible.
    """

    resp = _cache_read_generic(pr_date, DIR_RESP_CACHE, HTML,
                               (lambda f: f.read()))

    if resp is None:
        resp = _request_pr_online(pr_date)
        _cache_write_html_resp(resp, pr_date)

    return resp


def _json_import(dict_content: Dict) -> Dict[str, Any]:
    """Modifies an imported JSON representation of parsed statistics
        into a more applicable Python data structure.

    The date is converted from ISO 8601 to a date object. Cases by area are
    converted to tuples.
    """
    dict_content[DATE] = dt.date.fromisoformat(dict_content[DATE])
    dict_content[const.AREA] = tuple(map(tuple, dict_content[const.AREA]))


def _json_export(dict_content: Dict) -> Dict[str, Any]:
    """Modifies a Python dictionary to be exported to JSON to compatible data
    types.

    Date is converted from a date object to a string ISO 8601 representation.
    """
    dict_content[DATE] = dict_content[DATE].isoformat()


def _cache_write_parsed(daily_stats: Dict[str, Any]) -> None:
    """Exports parsed version of LACPH daily COVID-19 briefings as JSON."""

    stats_date = daily_stats[DATE]
    _json_export(daily_stats)
    _cache_write_generic(daily_stats, stats_date, DIR_PARSED_PR, JSON,
                         (lambda x: isinstance(x, dict)),
                         (lambda f, x: json.dump(x, f)))


def _cache_read_parsed(pr_date: dt.date) -> Dict[str, Any]:
    """Reads in previously parsed daily LACPH briefing."""

    imported = _cache_read_generic(pr_date, DIR_PARSED_PR, JSON, json.load)

    # Convert date string into date object
    if imported is not None:
        _json_import(imported)

    return imported


def _request_pr_online(pr_date: dt.date) -> str:
    """Requests the press release online and caches a valid response."""

    prid = lacph_prid.DAILY_STATS[pr_date.isoformat()]
    r = requests.get(LACPH_PR_URL_BASE + str(prid))
    if r.status_code == 200:
        _cache_write_html_resp(r.text, pr_date)
        return r.text

    raise requests.exceptions.ConnectionError(
        'Cannot retrieve the press release statement')


def fetch_press_release(
        date_: Tuple[int, int, int], cached: bool = True) -> List[bs4.Tag]:
    """Fetches the HTML of press releases for the given dates. The source can
    come from cache or by fetching from the internet.

    Args:
        dates: An interable whose elements are three element tuples. Each
            tuple contains integers of the form (year, month, day) representing
            the desired press release.
        cached: A flag which determines if the sourced from a local cache of
            fetched press releases or requests the page from the deparment's
            website. Any online requests will be cached regardless of flag.

    Returns:
        A list of BeautifulSoup tags containing the requested press releases.
        The associated date can be retrived with the get_date function.
    """

    pr_date = dt.date.fromisoformat(date_)
    pr_html_text = ''

    if cached:
        pr_html_text = _cache_read_html_resp(pr_date)
    else:
        pr_html_text = _request_pr_online(pr_date)

    # Parse the HTTP response
    entire = bs4.BeautifulSoup(pr_html_text, 'html.parser')
    daily_pr = None
    # Some HTML may be broken causing the minimum section to be parsed include
    # the entire document - at the expense of memory overhead
    if pr_date in EXTENDED_HTML:
        daily_pr = entire
    else:
        daily_pr = entire.find('div', class_='container p-4')
    assert pr_date == _get_date(entire)

    return daily_pr


def _get_date(pr_html: bs4.BeautifulSoup) -> dt.date:
    """Finds the date from the HTML press release. This makes an assumption
    the first date in the press release is the date of release."""

    date_text = RE_DATE.search(pr_html.get_text()).group()
    return dt.datetime.strptime(date_text, '%B %d, %Y').date()


def _get_new_cases_deaths(pr_html: bs4.BeautifulSoup) -> Tuple[int, int]:
    """Extracts the daily new deaths and cases."""
    date_tuple = _date_to_tuple(_get_date(pr_html))
    if date_tuple in bad_data.HARDCODE_NEW_CASES_DEATHS.keys():
        return bad_data.HARDCODE_NEW_CASES_DEATHS[date_tuple]

    result = RE_NEW_DEATHS_CASES.search(pr_html.get_text())
    deaths, cases = None, None
    if result:
        deaths = _str_to_int(result.group(1))
        cases = _str_to_int(result.group(2))
    return cases, deaths


def _get_testing(pr_html: bs4.BeautifulSoup) -> Optional[Tuple[int, int]]:
    """Extacts the number of test results and percent of positive tests."""

    pr_text = pr_html.get_text()
    # Try both testing patterns
    result = RE_TESTING_1.search(pr_text)
    if result is None:
        result = RE_TESTING_2.search(pr_text)

    num_tests, pos_rate = None, None
    if result:
        num_tests = _str_to_int(result.group(1))
        pos_rate = int(result.group(2))
    return num_tests, pos_rate


def _isolate_html_general(
        daily_pr: bs4.Tag, header_pattern: re.Pattern, nested: bool) -> str:
    """Narrows down the section of HTML which must be parsed for data
        extraction.

    There exist entries which cannot be distinguished by regex. Hence, this
    function ensures the extracted data is what we think it is.
    In some cases, this saves future computation resources.

    Args:
        daily_pr: A BeutifulSoup tag containing all the contents for a daily
            COVID-19 briefing.
        header_pattern: A regular expression which uniquely identifies the
            desired section.
        nested: The HTML structure for these documents is not consistant
            between headers and days. If True, the header bold tag is enclosed
            within a paragraph tag that has an unordered list a few elements
            over. If False, the header bold tag is at the same nesting as the
            unordered list containing the data.
    """

    for bold_tag in daily_pr.find_all('b'):
        if header_pattern.match(bold_tag.get_text(strip=True)):
            if nested:
                return bold_tag.parent.find('ul').get_text()
            return bold_tag.next_sibling.next_sibling.get_text()
    return ''


def _isolate_html_age_group(daily_pr: bs4.Tag) -> str:
    nested = _get_date(daily_pr) >= FORMAT_START_AGE_NESTED
    return _isolate_html_general(daily_pr, HEADER_AGE_GROUP, nested)


def _isolate_html_hospital(daily_pr: bs4.Tag) -> str:
    nested = _get_date(daily_pr) >= FORMAT_START_HOSPITAL_NESTED
    return _isolate_html_general(daily_pr, HEADER_HOSPITAL, nested)


def _isolate_html_area(daily_pr: bs4.Tag) -> str:
    # The usage of location header is unpredictable, so just check against
    # the entire daily press release.
    return daily_pr.get_text()


def _isolate_html_gender(daily_pr: bs4.Tag) -> str:
    return _isolate_html_general(daily_pr, HEADER_GENDER, True)


def _isolate_html_race_cases(daily_pr: bs4.Tag) -> str:
    return _isolate_html_general(daily_pr, HEADER_RACE_CASE, True)


def _isolate_html_race_deaths(daily_pr: bs4.Tag) -> str:
    return _isolate_html_general(daily_pr, HEADER_RACE_DEATH, True)


def _parse_list_entries_general(
        pr_text: str, entry_regex: re.Pattern) -> Dict[str, int]:
    """Helper function for the common pattern where text entries are
    followed by a count statistic.

    Args:
        pr_text: Raw text with the data to be extracted. This is intended to
            be taken from a BeautifulSoup Tag's get_text() function.
        entry_regex: The regular expression which defines the entry and its
            corresponding statistic. The function needs the passed regex to
            utilize groups to identify the entry and data. The first group
            being the textual representation of the group and the last group
            being the statistic, represented by a numeral.

    Returns:
        A dictionary whose keys are the text entries and values are the
        corresponding statistic, converted to an integer. Note the key
        "Under Investigation" will be omitted as it is not useful for the
        purposes of this project.
    """

    result = {}
    entries_extracted = entry_regex.findall(pr_text)

    for entry in entries_extracted:
        name = entry[0]
        stat = entry[-1]
        if not RE_UNDER_INVESTIGATION.match(name):
            result[name] = _str_to_int(stat)

    return result


def _parse_total_by_dept_general(
        daily_pr: bs4.Tag, header_pattern: re.Pattern) -> Dict[str, int]:
    """Generalized parsing when a header has a total statistic followed by a
    per public health department breakdown.

    See parse_cases and parse_deaths for examples.
    """

    by_dept_raw = _isolate_html_general(daily_pr, header_pattern, True)
    # The per department breakdown statistics
    result = _parse_list_entries_general(by_dept_raw, ENTRY_BY_DEPT)

    # The cumultive count across departments
    total = None
    for bold_tag in daily_pr.find_all('b'):
        match_attempt = header_pattern.search(bold_tag.get_text(strip=True))
        if match_attempt:
            total = _str_to_int(match_attempt.group(1))
            break
    result[const.TOTAL] = total

    return result


def _parse_cases(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Parses the total COVID-19 cases in Los Angeles County,
    including Long Beach and Pasadena.

    SAMPLE:
    Laboratory Confirmed Cases -- 44988 Total Cases*

        Los Angeles County (excl. LB and Pas) -- 42604
        Long Beach -- 1553
        Pasadena -- 831
    RETURNS:
    {
        "Total": 44988,
        "Los Angeles County (excl. LB and Pas)": 42604,
        "Long Beach": 1553,
        "Pasadena": 831
    }
    """

    return _parse_total_by_dept_general(daily_pr, HEADER_CASE_COUNT)


def _parse_deaths(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Parses the total COVID-19 deaths from Los Angeles County,
    including Long Beach and Pasadena.

    SAMPLE:
    Deaths 2104
        Los Angeles County (excl. LB and Pas) 1953
        Long Beach 71
        Pasadena 80
    RETURNS:
    {
        "Total": 2104,
        "Los Angeles County (excl. LB and Pas)": 1953,
        "Long Beach": 71,
        "Pasadena": 80
    }
    """

    return _parse_total_by_dept_general(daily_pr, HEADER_DEATH)


def _parse_hospital(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Parses the hospitalizations due to COVID-19.

    SAMPLE:
    Hospitalization
        Hospitalized (Ever) 6177
    RETURNS:
    {
        "Hospitalized (Ever)": 6177
    }
    """

    return _parse_list_entries_general(_isolate_html_hospital(daily_pr),
                                       ENTRY_HOSPITAL)


def _parse_age_cases(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Parses the age breakdown of COVID-19 cases in Los Angeles County.

    SAMPLE:
    Age Group (Los Angeles County Cases Only-excl LB and Pas)
        0 to 17 -- 1795
        18 to 40 --15155
        41 to 65 --17106
        over 65 --8376
        Under Investigation --172
    RETURNS:
    {
        "0 to 17": 1795,
        "18 to 40": 15155
        "41 to 65": 17106
        "over 65": 8376
    }
    """
    return _parse_list_entries_general(_isolate_html_age_group(daily_pr),
                                       ENTRY_AGE)


def _parse_gender(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Parses the age breakdown of COVID-19 cases in Los Angeles County.

    SAMPLE:
    Gender (Los Angeles County Cases Only-excl LB and Pas)
        Female 31109
        Male 32202
        Other 10
        Under Investigation 339
    RETURNS:
    {
        "Female": 31109,
        "Male": 32202,
        "Other": 10
    }

    """

    result = _parse_list_entries_general(_isolate_html_gender(daily_pr),
                                         ENTRY_GENDER)

    # Correct spelling error on some releases
    old_keys = list(result.keys())
    for key in old_keys:
        if key == 'Mmale':
            result[const.MALE] = result.pop(key)

    return result


def _parse_race_cases(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Parses the race breakdown of COVID-19 cases in Los Angeles County.

    SAMPLE:
    Race/Ethnicity (Los Angeles County Cases Only-excl LB and Pas)
        American Indian/Alaska Native 60
        Asian 3376
        ...
        Other 8266
        Under Investigation 19606
    RETURNS:
    {
        "American Indian/Alaska Native": 60,
        "Asian": 3376,
        ...
        "Other": 8266
    }
    """
    return _parse_list_entries_general(_isolate_html_race_cases(daily_pr),
                                       ENTRY_RACE)


def _parse_race_deaths(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Parses the race breakdown of COVID-19 deaths in Los Angeles County.

    See parse_race_cases for an example.
    """
    return _parse_list_entries_general(_isolate_html_race_deaths(daily_pr),
                                       ENTRY_RACE)


def _parse_area(daily_pr: bs4.Tag) -> Dict[str, int]:
    """Returns the per area count of COVID-19 cases.

    SAMPLE:
    CITY / COMMUNITY (Rate**)
        City of Burbank 371 ( 346.15 )
        City of Lancaster* 821 ( 508 )
        Los Angeles - Sherman Oaks 216 ( 247.55 )
        Los Angeles - Van Nuys 629 ( 674.94 )
        Unincorporated - Lake Los Angeles 28 ( 215.48 )
        Unincorporated - Palmdale 4 ( 475.06 )
    RETURNS:
    {
        "City of Burbank": (371, 346.15, False),
        "City of Lancaster": (831, 508, True),
        "Los Angeles - Sherman Oaks": (216, 247.55, False),
        "Los Angeles - Van Nuys": (629, 674.94, False),
        "Unincorporated - Lake Los Angeles": (23, 215.48, False),
        "Unincorporated - Palmdale": (4, 475.06, False)
    }
    """

    areas_raw = _isolate_html_area(daily_pr)
    area_extracted = RE_LOC.findall(areas_raw)
    pr_date = _get_date(daily_pr)

    ASTERISK = '*'  # pylint: disable=invalid-name
    NODATA = '--'  # pylint: disable=invalid-name

    for i in range(len(area_extracted)):  # pylint: disable=consider-using-enumerate
        name, cases, rate = area_extracted[i]
        cf_recorded = pr_date >= CORR_FACILITY_RECORDED
        cf_outbreak = False if cf_recorded else None

        if name[-1] == ASTERISK:
            name = name.rstrip(ASTERISK)
            if cf_recorded:
                cf_outbreak = True

        if cases == NODATA:
            cases = None
            rate = None
        else:
            cases = int(cases)
            rate = float(rate)

        area_extracted[i] = name, cases, rate, cf_outbreak

    return area_extracted


def _parse_entire_day(daily_pr: bs4.Tag) -> Dict[str, Any]:
    """Parses each section of the daily COVID-19 report and places everything
        in a single object.
    """

    cases_by_dept = _parse_cases(daily_pr)
    tests_available, positive_tests = _get_testing(daily_pr)
    new_cases, new_deaths = _get_new_cases_deaths(daily_pr)

    cases_by_area = _parse_area(daily_pr)

    date_ = _get_date(daily_pr)

    lb_pas_cf = False if date_ >= CORR_FACILITY_RECORDED else None

    long_beach_cases = cases_by_dept[const.hd.LONG_BEACH]
    long_beach_rate = round(
        long_beach_cases / const.hd.POPULATION_LONG_BEACH * const.RATE_SCALE,
        2)  # pylint: disable=old-division
    cases_by_area.append((const.hd.CSA_LB, long_beach_cases,
                          long_beach_rate, lb_pas_cf))
    pasadena_cases = cases_by_dept[const.hd.PASADENA]
    pasadena_rate = round(
        pasadena_cases / const.hd.POPULATION_PASADENA * const.RATE_SCALE, 2)  # pylint: disable=old-division
    cases_by_area.append((const.hd.CSA_PAS, pasadena_cases, pasadena_rate,
                          lb_pas_cf))

    cases_by_area = tuple(cases_by_area)

    return {
        DATE: date_,
        const.CASES: cases_by_dept[const.TOTAL],
        const.DEATHS: _parse_deaths(daily_pr)[const.TOTAL],
        const.HOSPITALIZATIONS:
            _parse_hospital(daily_pr)[TOTAL_HOSPITALIZATIONS],
        const.NEW_CASES: new_cases,
        const.NEW_DEATHS: new_deaths,
        const.TEST_RESULTS: tests_available,
        const.PERCENT_POSITIVE_TESTS: positive_tests,
        const.CASES_BY_AGE: _parse_age_cases(daily_pr),
        const.CASES_BY_GENDER: _parse_gender(daily_pr),
        const.CASES_BY_RACE: _parse_race_cases(daily_pr),
        const.DEATHS_BY_RACE: _parse_race_deaths(daily_pr),
        const.AREA: cases_by_area
    }


def query_single_date(date_: str, cached: bool = True) -> Dict[str, Any]:
    """This puts together all the steps to go from a given date to a parsed
        response of daily COVID-19 data in Los Angeles County.

    The function can check for an already parsed response stored as JSON before
    the expensive task of fetching and parsing the report.
    """

    result = None

    if cached:
        result = _cache_read_parsed(dt.date.fromisoformat(date_))

    if result is None:
        result = _parse_entire_day(fetch_press_release(date_))
        _cache_write_parsed(result)

    return result


def query_all_dates(cached: bool = True) -> Tuple[Dict[str, Any], ...]:
    """Frontend to query_single_date for every date which daily COVID-19
        statistics have been released. Caches the result to reduce need for more
        I/O operations later.
    """

    result = tuple(
        [query_single_date(x, cached) for x in lacph_prid.DAILY_STATS])

    with open(paths.RAW_DATA, 'wb') as f:
        pickle.dump(result, f)

    return result


if __name__ == "__main__":
    query_all_dates()

    # debug_raw_pr = tuple([fetch_press_release(x)
    #                       for x in lacph_prid.DAILY_STATS])
    # today_parse = _parse_entire_day(debug_raw_pr[-1])
    # another_parse = _parse_entire_day(debug_raw_pr[12])
