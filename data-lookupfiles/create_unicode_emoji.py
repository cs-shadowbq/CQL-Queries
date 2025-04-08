# MIT License
# Copyright (c) 2025 Scott MacGregor

# The script can be run from the command line with the following command:
# Usage:
# python create_unicode_emoji.py --output emoji.csv

# usage: create_unicode_emoji.py[-h][-k][-o OUTPUT]
#
# Download and process emoji data.
#
# options:
#  -h, --help            show this help message and exit
#  -k, --ignore - ssl      Ignore SSL certificate warnings
#  -o OUTPUT, --output OUTPUT
#  Output CSV file name

# Summary:
# The output file will be created in the current directory with the name emoji.csv by default
# The output file will contain the following columns:
# char,name,ISO3166-1-Alpha-2,ISO3166-1-Alpha-3,region_name,sub_region_name,tld

# The script will download the emoji.json file from unpkg.com and the country-codes.csv from datasets(github)
# and process them to create the emoji.csv file.

# Reference:
# unpkg.com/emoji.json@15.1.0/emoji.json
# The emoji.json file available from unpkg.com, is an extracted npm package that parses the official Unicode emoji "emoji-test.txt" file
# https://www.npmjs.com/package/emoji.json | https://github.com/amio/emoji.json

# github.com/datasets/country-codes/blob/main/data/country-codes.csv
# The country-codes.csv file is available at datasets on github from the datahub.io project

# Import necessary libraries
import requests
import os
import csv

import json
import logging
import sys
import argparse

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VERSION = "1.0"
EMOJI_VERSION = "15.1.0"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# logger.setLevel(logging.WARNING)


# Function to download a file from a URL and ignore SSL certificate warnings
def download_file_ignore_ssl(url, local_filename):
    logger.info(f"Downloading {url} to {local_filename}")
    response = requests.get(url, stream=True, verify=False)
    if response.status_code == 200:
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded {local_filename}")
    else:
        logger.error(f"Failed to download {url}: {response.status_code}")
        sys.exit(1)


def download_file(url, local_filename):
    logger.info(f"Downloading {url} to {local_filename}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded {local_filename}")
    else:
        logger.error(f"Failed to download {url}: {response.status_code}")
        sys.exit(1)


# File to download
# https://unpkg.com/emoji.json@15.1.0/emoji.json

# in the json file there is an entry like this:
# {"codes": "1F1FF 1F1E6", "char": "🇿🇦", "name": "flag: South Africa", "category": "Flags (country-flag)", "group": "Flags", "subgroup": "country-flag"},

# Download the emoji.json file
def download_emoji_json(ignore_ssl):
    url = "https://unpkg.com/emoji.json@15.1.0/emoji.json"
    local_filename = "npm-emoji.json"
    if ignore_ssl:
        download_file_ignore_ssl(url, local_filename)
    else:
        download_file(url, local_filename)
    return local_filename

# File to download
# https://github.com/datasets/country-codes/blob/main/data/country-codes.csv


# The CSV file has the following columns:
# FIFA,Dial,ISO3166-1-Alpha-3,MARC,is_independent,ISO3166-1-numeric,GAUL,FIPS,WMO,ISO3166-1-Alpha-2,ITU,IOC,DS,UNTERM Spanish Formal,Global Code,Intermediate Region Code,official_name_fr,UNTERM French Short,ISO4217-currency_name,UNTERM Russian Formal,UNTERM English Short,ISO4217-currency_alphabetic_code,Small Island Developing States (SIDS),UNTERM Spanish Short,ISO4217-currency_numeric_code,UNTERM Chinese Formal,UNTERM French Formal,UNTERM Russian Short,M49,Sub-region Code,Region Code,official_name_ar,ISO4217-currency_minor_unit,UNTERM Arabic Formal,UNTERM Chinese Short,Land Locked Developing Countries (LLDC),Intermediate Region Name,official_name_es,UNTERM English Formal,official_name_cn,official_name_en,ISO4217-currency_country_name,Least Developed Countries (LDC),Region Name,UNTERM Arabic Short,Sub-region Name,official_name_ru,Global Name,Capital,Continent,TLD,Languages,Geoname ID,CLDR display name,EDGAR,wikidata_id
# ZIM,263,ZWE,rh,Yes,716,271,ZI,ZW,ZW,ZWE,ZIM,ZW,la República de Zimbabwe,1,14,Zimbabwe,Zimbabwe (le),Zimbabwe Gold,Республика Зимбабве,Zimbabwe,ZWG,,Zimbabwe,924,津巴布韦共和国,la République du Zimbabwe,Зимбабве,716,202,2,زمبابوي,2,جمهورية زمبابوي,津巴布韦,x,Eastern Africa,Zimbabwe,the Republic of Zimbabwe,津巴布韦,Zimbabwe,ZIMBABWE,,Africa,زمبابوي,Sub-Saharan Africa,Зимбабве,World,Harare,AF,.zw,"en-ZW,sn,nr,nd",878675,Zimbabwe,Y5,https://www.wikidata.org/wiki/Q954
# Download the country-codes.csv file
def download_country_codes(ignore_ssl):
    url = "https://raw.githubusercontent.com/datasets/country-codes/main/data/country-codes.csv"
    local_filename = "country-codes.csv"
    if ignore_ssl:
        download_file_ignore_ssl(url, local_filename)
    else:
        download_file(url, local_filename)
    return local_filename


# Function to return the ISO3166-1-Alpha-2, ISO3166-1-Alpha-3 from the 'UNTERM English Short' of the country
def get_country_code(lookup, country_codes):

    # replace ampersand with 'and'
    lookup = lookup.replace('&', 'and')
    lookup = lookup.replace('St. ', 'Saint ')

    # downcase the lookup string
    lookup = lookup.lower()

    for row in country_codes:
        if row['UNTERM English Short'].lower() == lookup:
            return row['ISO3166-1-Alpha-2'], row['ISO3166-1-Alpha-3']
        # drop (the) from the country name
        elif row['UNTERM English Short'].split(' (')[0].lower() == lookup:
            return row['ISO3166-1-Alpha-2'], row['ISO3166-1-Alpha-3']
        elif row['ISO4217-currency_country_name'].lower() == lookup:
            return row['ISO3166-1-Alpha-2'], row['ISO3166-1-Alpha-3']
        elif row['CLDR display name'].lower() == lookup.replace('ü', 'u'):
            return row['ISO3166-1-Alpha-2'], row['ISO3166-1-Alpha-3']

    # hard coded exceptions
    if lookup == 'South Korea'.lower():
        return 'KR', 'KOR'
    if lookup == 'North Korea'.lower():
        return 'KP', 'PRK'
    if lookup == 'United States'.lower():
        return 'US', 'USA'
    if lookup == 'United Kingdom'.lower():
        return 'GB', 'GBR'
    if lookup == 'United Arab Emirates'.lower():
        return 'AE', 'ARE'
    if lookup == 'russia'.lower():
        return 'RU', 'RUS'
    if lookup == 'United Nations'.lower():
        return 'UN', 'UNK'
    if lookup == 'European Union'.lower():
        return 'EU', 'EUN'
    if lookup == 'saint vincent and grenadines'.lower():
        return 'VC', 'VCT'
    if lookup == 'heard and mcdonald islands'.lower():
        return 'HM', 'HMD'
    if lookup == 'south georgia and south sandwich islands'.lower():
        return 'GS', 'SGS'
    if lookup == 'u.s. outlying islands'.lower():
        return 'UM', 'UMI'
    if lookup == 'U.S. Virgin Islands'.lower():
        return 'VI', 'VIR'
    if lookup == 'british virgin islands'.lower():
        return 'VG', 'VGB'
    if lookup == 'falkland islands'.lower():
        return 'FK', 'FLK'
    if lookup == 'vatican city'.lower():
        return 'VA', 'VAT'
    if lookup == 'diego garcia'.lower():
        return 'DG', 'DGA'
    if lookup == 'ascension island'.lower():
        return 'AC', 'ASC'
    if lookup == 'tristan da cunha'.lower():
        return 'TA', 'TAC'
    if lookup == 'são tomé and príncipe'.lower():
        return 'ST', 'STP'
    if lookup == 'Caribbean Netherlands'.lower():
        return 'BQ', 'BES'
    if lookup == 'pitcairn islands'.lower():
        return 'PN', 'PCN'
    if lookup == 'Clipperton Island'.lower():
        return 'CP', 'CPT'
    if lookup == 'Côte d’Ivoire'.lower():
        return 'CI', 'CIV'

    # Other hard coded exceptions
    if lookup == 'kosovo'.lower():
        return 'XK', 'XKX'
    if lookup == 'Palestinian Territories'.lower():
        return 'PS', 'PSE'
    if lookup == 'wales'.lower():
        return 'GB-WLS', 'GBW'
    if lookup == 'scotland'.lower():
        return 'GB-SCT', 'GBS'
    if lookup == 'england'.lower():
        return 'GB-ENG', 'GBE'
    if lookup == 'northern ireland'.lower():
        return 'GB-NIR', 'GBN'
    if lookup == 'Hong Kong SAR China'.lower():
        return 'HK', 'HKG'
    if lookup == 'Macao SAR China'.lower():
        return 'MO', 'MAC'
    if lookup == 'ceuta and melilla'.lower():
        return 'ES-CE', 'ESM'
    if lookup == 'Canary Islands'.lower():
        return 'ES-CN', 'CNY'

    # log the lookup string if not found
    logger.warning(f"Country code not found for {lookup}")

    return None, None


# Read the country codes CSV file and return a list of dictionaries
def read_country_codes(file):
    country_codes = []
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            country_codes.append(row)
    return country_codes


# Function to get the Continent and Region to the country codes
def get_continent_region(iso_alpha_3, country_codes):
    logger.info(f"Getting continent and region for {iso_alpha_3}")
    for row in country_codes:
        if row['ISO3166-1-Alpha-3'] == iso_alpha_3:
            if row['Region Name'] == '':
                pass
            else:
                return row['Region Name'], row['Sub-region Name']

    # Hard coded exceptions
    if iso_alpha_3 == 'XKX':
        return 'Europe', 'Western Europe'
    if iso_alpha_3 == 'PS':
        return 'Asia', 'Western Asia'
    if iso_alpha_3 == 'GBW':
        return 'Europe', 'Northern Europe'
    if iso_alpha_3 == 'GBS':
        return 'Europe', 'Northern Europe'
    if iso_alpha_3 == 'GBE':
        return 'Europe', 'Northern Europe'
    if iso_alpha_3 == 'GBN':
        return 'Europe', 'Northern Europe'
    if iso_alpha_3 == 'HKG':
        return 'Asia', 'Eastern Asia'
    if iso_alpha_3 == 'MAC':
        return 'Asia', 'Eastern Asia'
    if iso_alpha_3 == 'TAC':
        return 'Africa', 'Sub-Saharan Africa'
    if iso_alpha_3 == 'DGA':
        return 'Africa', 'Sub-Saharan Africa'
    if iso_alpha_3 == 'CPT':
        return 'North America', 'Caribbean'
    if iso_alpha_3 == 'CNY':
        return 'Europe', 'Southern Europe'
    if iso_alpha_3 == 'ASC':
        return 'Africa', 'Sub-Saharan Africa'
    if iso_alpha_3 == 'UNK':
        return 'Global', 'Global'
    if iso_alpha_3 == 'EUN':
        return 'Europe', 'Northern Europe'
    if iso_alpha_3 == 'ATA':
        return 'Antarctica', 'Antarctica'
    if iso_alpha_3 == "ESM":
        return 'Europe', 'Southern Europe'

    return None, None


# Function to get the TLD for the country codes
def get_tld(iso_alpha_2, country_codes):
    logger.info(f"Getting TLD for {iso_alpha_2}")
    for row in country_codes:
        if row['ISO3166-1-Alpha-2'] == iso_alpha_2:
            return row['TLD']
    # Hard coded exceptions
    if iso_alpha_2 == 'XK':
        return '.xk'
    if iso_alpha_2 == 'PS':
        return '.ps'
    if iso_alpha_2 == 'GB-WLS':
        return '.wales'
    if iso_alpha_2 == 'GB-SCT':
        return '.scotland'
    if iso_alpha_2 == 'GB-ENG':
        return '.england'
    if iso_alpha_2 == 'GB-NIR':
        return '.northernireland'
    if iso_alpha_2 == "ES-CE":
        return '.es'
    if iso_alpha_2 == 'HK':
        return '.hk'
    if iso_alpha_2 == 'MO':
        return '.mo'
    if iso_alpha_2 == 'TA':
        return '.ta'
    if iso_alpha_2 == 'UN':
        return '.un'
    if iso_alpha_2 == 'EU':
        return '.eu'
    if iso_alpha_2 == 'AC':
        return '.ac'
    if iso_alpha_2 == 'DG':
        return '.dg'
    if iso_alpha_2 == 'CP':
        return '.cp'

    return None


# Function to process the emoji.json file and return a list of dictionaries
def process_emoji_json(file, country_codes):
    with open(file, 'r', encoding='utf-8') as f:
        emoji_data = json.load(f)

    emoji_list = []

    for entry in emoji_data:

        if 'flag: ' in entry['name']:

            # Extract the country name from the entry

            # log the country name
            logger.info(f"Processing entry: {entry['name']}")

            country_name = entry['name'].split(': ')[1]
            # Get the ISO3166-1-Alpha-2 code from the country name
            iso_alpha_2, iso_alpha_3 = get_country_code(country_name, country_codes)

            region_name, sub_region_name = get_continent_region(iso_alpha_3, country_codes)

            tld = get_tld(iso_alpha_2, country_codes)

            emoji_list.append({
                'char': entry['char'],
                'name': country_name,
                'region_name': region_name,
                'sub_region_name': sub_region_name,
                'ISO3166-1-Alpha-2': iso_alpha_2,
                'ISO3166-1-Alpha-3': iso_alpha_3,
                'tld': tld
            })
    return emoji_list


# Function to write the emoji list to a CSV file
def write_emoji_csv(emoji_list, output_file):
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['char', 'name', 'region_name', 'sub_region_name', 'ISO3166-1-Alpha-2', 'ISO3166-1-Alpha-3', 'tld'])
        writer.writeheader()
        for emoji in emoji_list:
            writer.writerow(emoji)
    logger.info(f"Wrote {len(emoji_list)} emojis to {output_file}")


# Function to write the emoji list to a JSON file
def write_emoji_json(emoji_list, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(emoji_list, f, ensure_ascii=False, indent=4)
    logger.info(f"Wrote {len(emoji_list)} emojis to {output_file}")


# Main function to download, process and write the emoji CSV file
def main():
    # Parse command line arguments

    description = "Create a country code lookup files for ISO3166-1 Alpha2 and Alpha3 to Emoji (" + EMOJI_VERSION + ") Country Flags and TLD."

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Enable verbose output')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + VERSION, help='Show version number and exit')

    fetch = parser.add_argument_group('Fetch options')
    # use local file if available
    fetch.add_argument('--use-cached', action='store_true', default=False, help='Use local emoji and country-codes files if available')
    fetch.add_argument('--local-emoji-filepath', type=str, default='emoji.json', help='Use local emoji.json file if available')
    fetch.add_argument('--local-country-codes-filepath', type=str, default='country-codes.csv', help='Use local country-codes.csv file if available')
    fetch.add_argument('-k', '--ignore-ssl', action='store_true', default=False, help='Ignore SSL certificate warnings')
    # add argument group
    group = parser.add_argument_group('Output options')
    group.add_argument('-j', '--json', action='store_true', default=False, help='Output JSON file instead of CSV')
    group.add_argument('-o', '--output', type=str, default='cc_lookup.csv', help='Output file name default: cc_lookup.csv or cc_lookup.json')
    group.add_argument('-x', '--no-cleanup', action='store_true', default=False, help='Do not delete downloaded files after processing')

    args = parser.parse_args()
    ignore_ssl = args.ignore_ssl
    if args.verbose:
        logger.setLevel(logging.INFO)
        logger.debug("Verbose output enabled")
    else:
        logger.setLevel(logging.WARNING)
    logger.info(f"Version: {VERSION}")

    if args.use_cached:
        logger.info("Using cached files")
        emoji_json_file = args.local_emoji_filepath
        country_codes_file = args.local_country_codes_filepath
    else:
        emoji_json_file = download_emoji_json(ignore_ssl)
        country_codes_file = download_country_codes(ignore_ssl)
        logger.info("Downloaded files")

    # Read the country codes
    country_codes = read_country_codes(country_codes_file)

    # Process the emoji JSON file
    emoji_list = process_emoji_json(emoji_json_file, country_codes)

    # Write the emoji list to a CSV file
    if args.json:
        output_file = args.output.replace('.csv', '.json')
        write_emoji_json(emoji_list, output_file)
    else:
        write_emoji_csv(emoji_list, args.output)

    # Clean up downloaded files
    if not args.no_cleanup:
        logger.info("Cleaning up downloaded files")
        try:
            os.remove(emoji_json_file)
            os.remove(country_codes_file)
        except OSError as e:
            logger.error(f"Error deleting file: {e}")
    else:
        logger.info("Not cleaning up downloaded files")

    logger.info("Done")


if __name__ == '__main__':
    main()
