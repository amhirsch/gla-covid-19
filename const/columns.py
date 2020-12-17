TOTAL = 'Total'

DATE = 'Date'
CASES = 'Cases'
DEATHS = 'Deaths'
HOSPITALIZATIONS = 'Hospitalizations'
AGGREGATE = 'Aggregate'

NEW_CASES, NEW_DEATHS, NEW_HOSPITALIZATIONS = [
    f'New {x.lower()}' for x in (CASES, DEATHS, HOSPITALIZATIONS)
]

HEALTH_DPET = 'Health dept'

NEW_CASES_7_DAY_AVG, NEW_DEATHS_7_DAY_AVG, NEW_HOSPITALIZATIONS_7_DAY_AVG = [
    f'{x}, 7-day avg' for x in (NEW_CASES, NEW_DEATHS, NEW_HOSPITALIZATIONS)]
CASES_PER_CAPITA, DEATHS_PER_CAPITA, NEW_CASES_7_DAY_AVG_PER_CAPITA, NEW_DEATHS_7_DAY_AVG_PER_CAPITA = [
    f'{x} per 100k'
    for x in (CASES, DEATHS, NEW_CASES_7_DAY_AVG, NEW_DEATHS_7_DAY_AVG)
]
NEW_CASES_14_DAY_AVG, NEW_DEATHS_14_DAY_AVG, NEW_CASES_14_DAY_AVG_PER_CAPITA, NEW_DEATHS_14_DAY_AVG_PER_CAPITA = (
    [x.replace('7', '14') for x in (
        NEW_CASES_7_DAY_AVG, NEW_DEATHS_7_DAY_AVG,
        NEW_CASES_7_DAY_AVG_PER_CAPITA, NEW_DEATHS_7_DAY_AVG_PER_CAPITA
    )]
)

OTHER = 'Other'

AGE_GROUP = 'Age'
GENDER = 'Gender'
RACE = 'Race/Ethnicity'

RATE_SCALE = 100_000

_RATE = '{} Rate'
CASE_RATE = _RATE.format('Case')
DEATH_RATE = _RATE.format('Death')

REGION = 'Region'
SPA = 'Service Planning Area'
AREA = 'Area'
POPULATION = 'Population'
CF_OUTBREAK = 'CF Outbreak'

RESID_SETTING = 'Residential Setting'
ADDRESS = 'Address'
STAFF_CASES = 'Staff {}'.format(CASES)
RESID_CASES = 'Resident {}'.format(CASES)

OBJECTID = 'ObjectID'


def stat_by_group(stat: str, group: str) -> str:
    """Provides consistant naming to statistic descriptors"""
    return f'{stat} by {group}'

CASES_BY_AGE, CASES_BY_GENDER, CASES_BY_RACE = [
    stat_by_group(CASES, x) for x in (AGE_GROUP, GENDER, RACE)
]
DEATHS_BY_RACE = stat_by_group(DEATHS, RACE)
