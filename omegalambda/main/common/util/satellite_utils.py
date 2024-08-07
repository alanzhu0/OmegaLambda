import datetime
import logging
import requests
from skyfield.api import load, EarthSatellite, wgs84
from skyfield.framelib import ICRS
import time


TS = load.timescale()
PLANETS = load('de421.bsp')
EARTH = PLANETS['earth']
OBSERVER = wgs84.latlon(38.82817, -77.30533, 154)


def download_tle(satellite_name: str) -> str | None:
    tle_url = f"https://celestrak.org/NORAD/elements/gp.php?NAME={satellite_name}"

    for connection_attempt in range(5):
        response = requests.get(tle_url, timeout=15)
        if response.status_code != 200:
            logging.error(f"Failed to download TLE data: try {connection_attempt}")
            time.sleep(5 * connection_attempt)
            continue
        if "No GP data found" in response.text:
            logging.error("Failed to download TLE data: satellite not in catalog. Ensure the name is correct.")
            return None
        if response.text.count('\n') != 3:
            logging.error("Failed to download TLE data: multiple satellites match the specified name.")
            return None
        logging.info("TLE data downloaded successfully:")
        logging.info(response.text)
        return response.text

    logging.error("Failed to download TLE data: too many connection attempts.")
    return None


def build_satellite(satellite_name: str, tle: str | None = None) -> EarthSatellite | None:
    if tle is None:
        tle = download_tle(satellite_name)
        if tle is None:
            return None
    tle = tle.splitlines()
    sat = EarthSatellite(tle[1], tle[2], tle[0], TS)
    return sat


def get_ra_dec(sat: EarthSatellite, date: datetime.datetime | None = None) -> tuple[float, float]:
    if date:
        t = TS.from_datetime(date)
    else:
        t = TS.now()

    # difference = sat - OBSERVER
    # ra, dec, dist = difference.at(t).radec()

    observe_sat = (EARTH + OBSERVER).at(t).observe(EARTH + sat).apparent()
    ra, dec, dist = observe_sat.radec()
    return ra.hours, dec.degrees


def get_ra_dec_rates(sat: EarthSatellite, date: datetime.datetime | None = None) -> tuple[float, float]:
    if date:
        t = TS.from_datetime(date)
    else:
        t = TS.now()

    observe_sat = (EARTH + OBSERVER).at(t).observe(EARTH + sat).apparent()
    dec, ra, dist, dec_rate, ra_rate, dist_rate = observe_sat.frame_latlon_and_rates(ICRS)

    # print('Dec ', dec.degrees)
    # print('RA  ', ra.degrees)
    # print('Dist', dist.au)
    # print('Dec rate ', dec_rate.degrees.per_second)
    # print('RA rate  ', ra_rate.degrees.per_second)
    # print('Dist rate', dist_rate.km_per_s)
    # print(ra_rate.arcseconds.per_second, dec_rate.arcseconds.per_second)
    
    return ra_rate.arcseconds.per_second, dec_rate.arcseconds.per_second
