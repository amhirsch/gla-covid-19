"""Every news release from Los Angeles County Public Health is identified by a
    unique PRID. The maps associate a date and the corresponding COVID-19
    daily news release.
"""

DAILY_STATS = {
    '2020-03-30': 2289,
    '2020-03-31': 2290,
    '2020-04-01': 2291,
    '2020-04-02': 2292,
    '2020-04-03': 2294,
    '2020-04-04': 2297,
    '2020-04-05': 2298,
    '2020-04-06': 2300,
    '2020-04-07': 2302,
    '2020-04-08': 2304,
    '2020-04-09': 2307,
    '2020-04-10': 2309,
    '2020-04-11': 2311,
    '2020-04-12': 2312,
    '2020-04-13': 2314,
    '2020-04-14': 2317,
    '2020-04-15': 2319,
    '2020-04-16': 2321,
    '2020-04-17': 2323,
    '2020-04-18': 2325,
    '2020-04-19': 2326,
    '2020-04-20': 2329,
    '2020-04-21': 2331,
    '2020-04-22': 2333,
    '2020-04-23': 2336,
    '2020-04-24': 2337,
    '2020-04-25': 2341,
    '2020-04-26': 2343,
    '2020-04-27': 2345,
    '2020-04-28': 2347,
    '2020-04-29': 2349,
    '2020-04-30': 2352,
    '2020-05-01': 2353,
    '2020-05-02': 2355,
    '2020-05-03': 2356,
    '2020-05-04': 2357,
    '2020-05-05': 2359,
    '2020-05-06': 2361,
    '2020-05-07': 2362,
    '2020-05-08': 2365,
    '2020-05-09': 2367,
    '2020-05-10': 2369,
    '2020-05-11': 2370,
    '2020-05-12': 2373,
    '2020-05-13': 2375,
    '2020-05-14': 2377,
    '2020-05-15': 2380,
    '2020-05-16': 2381,
    '2020-05-17': 2382,
    '2020-05-18': 2384,
    '2020-05-19': 2386,
    '2020-05-20': 2389,
    '2020-05-21': 2391,
    '2020-05-22': 2393,
    '2020-05-23': 2394,
    '2020-05-24': 2399,
    '2020-05-25': 2400,
    '2020-05-26': 2403,
    '2020-05-27': 2406,
    '2020-05-28': 2408,
    '2020-05-29': 2409,
    '2020-05-30': 2411,
    '2020-05-31': 2412,
    '2020-06-01': 2413,
    '2020-06-02': 2419,
    '2020-06-03': 2422,
    '2020-06-04': 2423,
    '2020-06-05': 2426,
    '2020-06-06': 2428,
    '2020-06-07': 2429,
    '2020-06-08': 2430,
    '2020-06-09': 2432,
    '2020-06-10': 2436,
    '2020-06-11': 2438,
    '2020-06-12': 2440,
    '2020-06-13': 2442,
    '2020-06-14': 2443,
    '2020-06-15': 2445,
    '2020-06-16': 2447,
    '2020-06-17': 2449,
    '2020-06-18': 2451,
    '2020-06-19': 2452,
    '2020-06-20': 2455,
    '2020-06-21': 2456,
    '2020-06-22': 2458,
    '2020-06-23': 2462,
    '2020-06-24': 2465,
    '2020-06-25': 2467,
    '2020-06-26': 2469,
    '2020-06-27': 2470,
    '2020-06-28': 2471,
    '2020-06-29': 2472,
    '2020-06-30': 2476,
    '2020-07-01': 2477,
    '2020-07-02': 2480,
    '2020-07-06': 2485,
    '2020-07-07': 2487,
    '2020-07-08': 2489,
    '2020-07-09': 2492,
    '2020-07-10': 2496,
    '2020-07-11': 2500,
    '2020-07-12': 2501,
    '2020-07-13': 2503,
    '2020-07-14': 2506,
    '2020-07-15': 2508,
    '2020-07-16': 2510,
    '2020-07-17': 2514,
    '2020-07-18': 2516,
    '2020-07-19': 2518,
    '2020-07-20': 2521,
    '2020-07-21': 2522,
    '2020-07-22': 2526,
    '2020-07-23': 2527,
    '2020-07-24': 2529,
    '2020-07-25': 2531,
    '2020-07-26': 2533,
    '2020-07-27': 2535,
    '2020-07-28': 2537,
    '2020-07-29': 2538,
    '2020-07-30': 2540,
    '2020-07-31': 2543,
    '2020-08-01': 2545,
    '2020-08-02': 2548,
    '2020-08-03': 2550,
    '2020-08-04': 2551,
    '2020-08-05': 2556,
    '2020-08-06': 2558,
    '2020-08-07': 2560,
    '2020-08-08': 2561,
    '2020-08-09': 2562,
    '2020-08-10': 2566,
    '2020-08-11': 2567,
    '2020-08-12': 2571,
    '2020-08-13': 2575,
    '2020-08-14': 2577,
    '2020-08-15': 2580,
    '2020-08-16': 2583,
    '2020-08-17': 2586,
    '2020-08-18': 2591,
    '2020-08-19': 2595,
    '2020-08-20': 2597,
    '2020-08-21': 2600,
}
