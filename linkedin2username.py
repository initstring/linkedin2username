#!/usr/bin/env python3

"""
linkedin2username by initstring (github.com/initstring)

OSINT tool to discover likely usernames and email addresses for employees
of a given company on LinkedIn. This tool actually logs in with your valid
account in order to extract the most results.
"""

import os
import sys
import re
import time
import argparse
import json
import urllib.parse
import requests
import urllib3

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

BANNER = r"""

                            .__  .__________
                            |  | |__\_____  \ __ __
                            |  | |  |/  ____/|  |  \
                            |  |_|  /       \|  |  /
                            |____/__\_______ \____/
                               linkedin2username

                                   Spray away.
                              github.com/initstring

"""

# The dictionary below contains geo region codes. Because we are limited to 1000 results per search,
# we can use this to batch searches across regions and get more results.
# I found this in some random JS, so who knows if it will change.
# https://static.licdn.com/aero-v1/sc/h/6pw526ylxpzsa7nu7ht18bo8y
GEO_REGIONS = {
    "ar": "100446943",
    "at": "103883259",
    "au": "101452733",
    "be": "100565514",
    "bg": "105333783",
    "ca": "101174742",
    "ch": "106693272",
    "cl": "104621616",
    "de": "101282230",
    "dk": "104514075",
    "es": "105646813",
    "fi": "100456013",
    "fo": "104630756",
    "fr": "105015875",
    "gb": "101165590",
    "gf": "105001561",
    "gp": "104232339",
    "gr": "104677530",
    "gu": "107006862",
    "hr": "104688944",
    "hu": "100288700",
    "is": "105238872",
    "it": "103350119",
    "li": "100878084",
    "lu": "104042105",
    "mq": "103091690",
    "nl": "102890719",
    "no": "103819153",
    "nz": "105490917",
    "pe": "102927786",
    "pl": "105072130",
    "pr": "105245958",
    "pt": "100364837",
    "py": "104065273",
    "re": "104265812",
    "rs": "101855366",
    "ru": "101728296",
    "se": "105117694",
    "sg": "102454443",
    "si": "106137034",
    "tw": "104187078",
    "ua": "102264497",
    "us": "103644278",
    "uy": "100867946",
    "ve": "101490751"
}


class NameMutator():
    """
    This class handles all name mutations.

    Init with a raw name, and then call the individual functions to return a mutation.
    """
    def __init__(self, name):
        self.name = self.clean_name(name)
        self.name = self.split_name(self.name)

    @staticmethod
    def clean_name(name):
        """
        Removes common punctuation.

        LinkedIn users tend to add credentials to their names to look special.
        This function is based on what I have seen in large searches, and attempts
        to remove them.
        """
        # Lower-case everything to make it easier to de-duplicate.
        name = name.lower()

        # Use case for tool is mostly standard English, try to standardize common non-English
        # characters.
        name = re.sub("[àáâãäå]", 'a', name)
        name = re.sub("[èéêë]", 'e', name)
        name = re.sub("[ìíîï]", 'i', name)
        name = re.sub("[òóôõö]", 'o', name)
        name = re.sub("[ùúûü]", 'u', name)
        name = re.sub("[ýÿ]", 'y', name)
        name = re.sub("[ß]", 'ss', name)
        name = re.sub("[ñ]", 'n', name)

        # Get rid of all things in parenthesis. Lots of people put various credentials, etc
        name = re.sub(r'\([^()]*\)', '', name)

        # The lines below basically trash anything weird left over.
        # A lot of users have funny things in their names, like () or ''
        # People like to feel special, I guess.
        allowed_chars = re.compile('[^a-zA-Z -]')
        name = allowed_chars.sub('', name)

        # Next, we get rid of common titles. Thanks ChatGPT for the help.
        titles = ['mr', 'miss', 'mrs', 'phd', 'prof', 'professor', 'md', 'dr', 'mba']
        pattern = "\\b(" + "|".join(titles) + ")\\b"
        name = re.sub(pattern, '', name)

        # The line below tries to consolidate white space between words
        # and get rid of leading/trailing spaces.
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    @staticmethod
    def split_name(name):
        """
        Takes a name (string) and returns a list of individual name-parts (dict).

        Some people have funny names. We assume the most important names are:
        first name, last name, and the name right before the last name (if they have one)
        """
        # Split on spaces and dashes (included repeated)
        parsed = re.split(r'[\s-]+', name)

        # Iterate and remove empty strings
        parsed = [part for part in parsed if part]

        # Discard people without at least a first and last name
        if len(parsed) < 2:
            return None

        if len(parsed) > 2:
            split_name = {'first': parsed[0], 'second': parsed[-2], 'last': parsed[-1]}
        else:
            split_name = {'first': parsed[0], 'second': '', 'last': parsed[-1]}

        # Final sanity check to not proceed without first and last name
        if not split_name['first'] or not split_name['last']:
            return None

        return split_name

    def f_last(self):
        """jsmith"""
        names = set()
        names.add(self.name['first'][0] + self.name['last'])

        if self.name['second']:
            names.add(self.name['first'][0] + self.name['second'])

        return names

    def f_dot_last(self):
        """j.smith"""
        names = set()
        names.add(self.name['first'][0] + '.' + self.name['last'])

        if self.name['second']:
            names.add(self.name['first'][0] + '.' + self.name['second'])

        return names

    def last_f(self):
        """smithj"""
        names = set()
        names.add(self.name['last'] + self.name['first'][0])

        if self.name['second']:
            names.add(self.name['second'] + self.name['first'][0])

        return names

    def first_dot_last(self):
        """john.smith"""
        names = set()
        names.add(self.name['first'] + '.' + self.name['last'])

        if self.name['second']:
            names.add(self.name['first'] + '.' + self.name['second'])

        return names

    def first_l(self):
        """johns"""
        names = set()
        names.add(self.name['first'] + self.name['last'][0])

        if self.name['second']:
            names.add(self.name['first'] + self.name['second'][0])

        return names

    def first(self):
        """john"""
        names = set()
        names.add(self.name['first'])

        return names


def parse_arguments():
    """
    Handle user-supplied arguments
    """
    desc = ('OSINT tool to generate lists of probable usernames from a'
            ' given company\'s LinkedIn page. This tool may break when'
            ' LinkedIn changes their site. Please open issues on GitHub'
            ' to report any inconsistencies, and they will be quickly fixed.')
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--company', type=str, action='store',
                        required=True,
                        help='Company name exactly as typed in the company '
                        'linkedin profile page URL.')
    parser.add_argument('-n', '--domain', type=str, action='store',
                        default='',
                        help='Append a domain name to username output. '
                        '[example: "-n uber.com" would output jschmoe@uber.com]'
                        )
    parser.add_argument('-d', '--depth', type=int, action='store',
                        default=False,
                        help='Search depth (how many loops of 50). If unset, '
                        'will try to grab them all.')
    parser.add_argument('-s', '--sleep', type=int, action='store', default=0,
                        help='Seconds to sleep between search loops.'
                        ' Defaults to 0.')
    parser.add_argument('-x', '--proxy', type=str, action='store',
                        default=False,
                        help='Proxy server to use. WARNING: WILL DISABLE SSL '
                        'VERIFICATION. [example: "-p https://localhost:8080"]')
    parser.add_argument('-k', '--keywords', type=str, action='store',
                        default=False,
                        help='Filter results by a a list of command separated '
                        'keywords. Will do a separate loop for each keyword, '
                        'potentially bypassing the 1,000 record limit. '
                        '[example: "-k \'sales,human resources,information '
                        'technology\']')
    parser.add_argument('-g', '--geoblast', default=False, action="store_true",
                        help='Attempts to bypass the 1,000 record search limit'
                        ' by running multiple searches split across geographic'
                        ' regions.')
    parser.add_argument('-o', '--output', default="li2u-output", action="store",
                        help='Output Directory, defaults to li2u-output')

    args = parser.parse_args()

    # Proxy argument is fed to requests as a dictionary, setting this now:
    args.proxy_dict = {"https": args.proxy}

    # If appending an email address, preparing this string now:
    if args.domain:
        args.domain = '@' + args.domain

    # Keywords are fed in as a list. Splitting comma-separated user input now:
    if args.keywords:
        args.keywords = args.keywords.split(',')

    # These two functions are not currently compatible, squashing this now:
    if args.keywords and args.geoblast:
        print("Sorry, keywords and geoblast are currently not compatible. Use one or the other.")
        sys.exit()

    return args


def get_webdriver():
    """
    Try to get a working Selenium browser driver
    """
    for browser in [webdriver.Firefox, webdriver.Chrome]:
        try:
            return browser()
        except WebDriverException:
            continue
    return None


def login():
    """Creates a new authenticated session.

    This now uses Selenium because I got very tired playing cat/mouse
    with LinkedIn's login process.
    """
    driver = get_webdriver()

    if driver is None:
        print("[!] Could not find a supported browser for Selenium. Exiting.")
        sys.exit(1)

    driver.get("https://linkedin.com/login")

    # Pause until the user lets us know the session is good.
    print("[*] Log in to LinkedIn. Leave the browser open and press enter when ready...")
    input("Ready? Press Enter!")

    selenium_cookies = driver.get_cookies()
    driver.quit()

    # Initialize and return a requests session
    session = requests.Session()
    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    # Add headers required for this tool to function
    mobile_agent = ('Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 '
                    'Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) '
                    'Version/4.0 Mobile Safari/534.30')
    session.headers.update({'User-Agent': mobile_agent,
                            'X-RestLi-Protocol-Version': '2.0.0',
                            'X-Li-Track': '{"clientVersion":"1.13.1665"}'})

    # Set the CSRF token
    session = set_csrf_token(session)

    return session


def set_csrf_token(session):
    """Extract the required CSRF token.

    Some functions requires a CSRF token equal to the JSESSIONID.
    """
    csrf_token = session.cookies['JSESSIONID'].replace('"', '')
    session.headers.update({'Csrf-Token': csrf_token})
    return session


def get_company_info(name, session):
    """Scrapes basic company info.

    Note that not all companies fill in this info, so exceptions are provided.
    The company name can be found easily by browsing LinkedIn in a web browser,
    searching for the company, and looking at the name in the address bar.
    """
    escaped_name = urllib.parse.quote_plus(name)

    response = session.get(('https://www.linkedin.com'
                            '/voyager/api/organization/companies?'
                            'q=universalName&universalName=' + escaped_name))

    if response.status_code == 404:
        print("[!] Could not find that company name. Please double-check LinkedIn and try again.")
        sys.exit()

    if response.status_code != 200:
        print("[!] Unexpected HTTP response code when trying to get the company info:")
        print(f"    {response.status_code}")
        sys.exit()

    # Some geo regions are being fed a 'lite' version of LinkedIn mobile:
    # https://bit.ly/2vGcft0
    # The following bit is a temporary fix until I can figure out a
    # low-maintenance solution that is inclusive of these areas.
    if 'mwlite' in response.text:
        print("[!] You are being served the 'lite' version of"
              " LinkedIn (https://bit.ly/2vGcft0) that is not yet supported"
              " by this tool. Please try again using a VPN exiting from USA,"
              " EU, or Australia.")
        print("    A permanent fix is being researched. Sorry about that!")
        sys.exit()

    try:
        response_json = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        print("[!] Yikes! Could not decode JSON when getting company info! :(")
        print("Here's the first 200 characters of the HTTP reply which may help in debugging:\n\n")
        print(response.text[:200])
        sys.exit()

    company = response_json["elements"][0]

    found_name = company.get('name', "NOT FOUND")
    found_desc = company.get('tagline', "NOT FOUND")
    found_staff = company['staffCount']
    found_website = company.get('companyPageUrl', "NOT FOUND")

    # We need the numerical id to search for employee info. This one requires some finessing
    # as it is a portion of a string inside the key.
    # Example: "urn:li:company:1111111111" - we need that 1111111111
    found_id = company['trackingInfo']['objectUrn'].split(':')[-1]

    print("          Name: " + found_name)
    print("          ID: " + found_id)
    print("          Desc:  " + found_desc)
    print("          Staff: " + str(found_staff))
    print("          URL:   " + found_website)
    print(f"\n[*] Hopefully that's the right {name}! If not, check LinkedIn and try again.\n")

    return (found_id, found_staff)


def set_outer_loops(args):
    """
    Sets the number of loops to perform during the scraping sessions
    """
    # If we are using geoblast or keywords, we need to define a numer of
    # "outer_loops". An outer loop will be a normal LinkedIn search, maxing
    # out at 1000 results.
    if args.geoblast:
        outer_loops = range(0, len(GEO_REGIONS))
    elif args.keywords:
        outer_loops = range(0, len(args.keywords))
    else:
        outer_loops = range(0, 1)

    return outer_loops


def set_inner_loops(staff_count, args):
    """Defines total hits to the search API.

    Sets a maximum amount of loops based on either the number of staff
    discovered in the get_company_info function or the search depth argument
    provided by the user. This limit is PER SEARCH, meaning it may be
    exceeded if you use the geoblast or keyword feature.

    Loops may stop early if no more matches are found or if a single search
    exceeds LinkedIn's 1000 non-commercial use limit.

    """

    # We will look for 50 names on each loop. So, we set a maximum amount of
    # loops to the amount of staff / 50 +1 more to catch remainders.
    loops = int((staff_count / 50) + 1)

    print(f"[*] Company has {staff_count} profiles to check. Some may be anonymous.")

    # The lines below attempt to detect large result sets and compare that
    # with the command line arguments passed. The goal is to warn when you
    # may not get all the results and to suggest ways to get  more.
    if staff_count > 1000 and not args.geoblast and not args.keywords:
        print("[!] Note: LinkedIn limits us to a maximum of 1000"
              " results!\n"
              "    Try the --geoblast or --keywords parameter to bypass")
    elif staff_count < 1000 and args.geoblast:
        print("[!] Geoblast is not necessary, as this company has"
              " less than 1,000 staff. Disabling.")
        args.geoblast = False
    elif staff_count > 1000 and args.geoblast:
        print("[*] High staff count, geoblast is enabled. Let's rock.")
    elif staff_count > 1000 and args.keywords:
        print("[*] High staff count, using keywords. Hope you picked"
              " some good ones.")

    # If the user purposely restricted the search depth, they probably know
    # what they are doing, but we warn them just in case.
    if args.depth and args.depth < loops:
        print("[!] You defined a low custom search depth, so we"
              " might not get them all.\n\n")
    else:
        print(f"[*] Setting each iteration to a maximum of {loops} loops of"
              " 50 results each.\n\n")
        args.depth = loops

    return args.depth, args.geoblast


def get_results(session, company_id, page, region, keyword):
    """Scrapes raw data for processing.

    The URL below is what the LinkedIn mobile HTTP site queries when manually
    scrolling through search results.

    The mobile site defaults to using a 'count' of 10, but testing shows that
    50 is allowed. This behavior will appear to the web server as someone
    scrolling quickly through all available results.
    """

    # Build the base search URL.
    url = ('https://www.linkedin.com/voyager/api/graphql?variables=('
           f'start:{page * 50},'
           f'query:('
           f'{f"keywords:{keyword}," if keyword else ""}'
           'flagshipSearchIntent:SEARCH_SRP,'
           f'queryParameters:List((key:currentCompany,value:List({company_id})),'
           f'{f"(key:geoUrn,value:List({region}))," if region else ""}'
           '(key:resultType,value:List(PEOPLE))'
           '),'
           'includeFiltersInResponse:false'
           '),count:50)'
           '&queryId=voyagerSearchDashClusters.66adc6056cf4138949ca5dcb31bb1749')

    # Perform the search for this iteration.
    result = session.get(url)
    return result


def find_employees(result):
    """
    Takes the text response of an HTTP query, converts to JSON, and extracts employee details.

    Returns a list of dictionary items, or False if none found.
    """
    found_employees = []

    try:
        result_json = json.loads(result)
    except json.decoder.JSONDecodeError:
        print("\n[!] Yikes! Could not decode JSON when scraping this loop! :(")
        print("I'm going to bail on scraping names now, but this isn't normal. You should "
              "troubleshoot or open an issue.")
        print("Here's the first 200 characters of the HTTP reply which may help in debugging:\n\n")
        print(result[:200])
        return False

    # Walk the data, being careful to avoid key errors
    data = result_json.get('data', {})
    search_clusters = data.get('searchDashClustersByAll', {})
    elements = paging = search_clusters.get('elements', [])
    paging = search_clusters.get('paging', {})
    total = paging.get('total', 0)

    # If we've ended up with empty dicts or zero results left, bail out
    if total == 0:
        return False

    # The "elements" list is the mini-profile you see when scrolling through a
    # company's employees. It does not have all info on the person, like their
    # entire job history. It only has some basics.
    found_employees = []
    for element in elements:
        # For some reason it's nested
        for item_body in element.get('items', []):
            # Info we want is all under 'entityResult'
            entity = item_body.get('item', {}).get('entityResult', {})

            # There's some useless entries we need to skip over
            if not entity:
                continue

            # There is no first/last name fields anymore so we're taking the full name
            full_name = entity['title']['text'].strip()

            # The name may include extras like "Dr" at the start, so we do some basic stripping
            if full_name[:3] == 'Dr ':
                full_name = full_name[4:]

            # Some users are missing a primary subtitle
            occupation = entity.get('primarySubtitle', {}).get('text', '') if entity.get('primarySubtitle') else ''

            found_employees.append({'full_name': full_name, 'occupation': occupation})

    return found_employees


def do_loops(session, company_id, outer_loops, args):
    """
    Performs looping where the actual HTTP requests to scrape names occurs

    This is broken into an individual function both to reduce complexity but also to
    allow a Ctrl-C to happen and to still write the data we've scraped so far.

    The mobile site used returns proper JSON, which is parsed in this function.

    Has the concept of inner an outer loops. Outerloops come into play when
    using --keywords or --geoblast, both which attempt to bypass the 1,000
    record search limit.

    This function will stop searching if a loop returns 0 new names.
    """
    # Crafting the right URL is a bit tricky, so currently unnecessary
    # parameters are still being included but set to empty. You will see this
    # below with geoblast and keywords.
    employee_list = []

    # We want to be able to break here with Ctrl-C and still write the names we have
    try:
        for current_loop in outer_loops:
            if args.geoblast:
                region_name, region_id = list(GEO_REGIONS.items())[current_loop]
                current_region = region_id
                current_keyword = ''
                print(f"\n[*] Looping through region {region_name}")
            elif args.keywords:
                current_keyword = args.keywords[current_loop]
                current_region = ''
                print(f"\n[*] Looping through keyword {current_keyword}")
            else:
                current_region = ''
                current_keyword = ''

            # This is the inner loop. It will search results 50 at a time.
            for page in range(0, args.depth):
                new_names = 0

                sys.stdout.flush()
                sys.stdout.write(f"[*] Scraping results on loop {str(page+1)}...    ")
                result = get_results(session, company_id, page, current_region, current_keyword)

                if result.status_code != 200:
                    print(f"\n[!] Yikes, got an HTTP {result.status_code}. This is not normal")
                    print("Bailing from loops, but you should troubleshoot.")
                    break

                # Commercial Search Limit might be triggered
                if "UPSELL_LIMIT" in result.text:
                    sys.stdout.write('\n')
                    print("[!] You've hit the commercial search limit! "
                          "Try again on the 1st of the month. Sorry. :(")
                    break

                found_employees = find_employees(result.text)

                if not found_employees:
                    sys.stdout.write('\n')
                    print("[*] We have hit the end of the road! Moving on...")
                    break

                new_names += len(found_employees)
                employee_list.extend(found_employees)

                sys.stdout.write(f"    [*] Added {str(new_names)} new names. "
                                 f"Running total: {str(len(employee_list))}"
                                 "              \r")

                # If the user has defined a sleep between loops, we take a little
                # nap here.
                time.sleep(args.sleep)
    except KeyboardInterrupt:
        print("\n\n[!] Caught Ctrl-C. Breaking loops and writing files")

    return employee_list


def write_lines(employees, name_func, domain, outfile):
    """
    Helper function to mutate names and write to an outfile

    Needs to be called with a string variable in name_func that matches the class method
    name in the NameMutator class.
    """
    for employee in employees:
        mutator = NameMutator(employee["full_name"])
        if mutator.name:
            for name in getattr(mutator, name_func)():
                outfile.write(name + domain + '\n')


def write_files(company, domain, employees, out_dir):
    """Writes data to various formatted output files.

    After scraping and processing is complete, this function formats the raw
    names into common username formats and writes them into a directory called
    li2u-output unless specified.

    See in-line comments for decisions made on handling special cases.
    """

    # Check for and create an output directory to store the files.
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Write out all the raw and mutated names to files
    with open(f'{out_dir}/{company}-rawnames.txt', 'w', encoding='utf-8') as outfile:
        for employee in employees:
            outfile.write(employee['full_name'] + '\n')

    with open(f'{out_dir}/{company}-metadata.txt', 'w', encoding='utf-8') as outfile:
        outfile.write('full_name,occupation\n')
        for employee in employees:
            outfile.write(employee['full_name'] + ',' + employee["occupation"] + '\n')

    with open(f'{out_dir}/{company}-flast.txt', 'w', encoding='utf-8') as outfile:
        write_lines(employees, 'f_last', domain, outfile)

    with open(f'{out_dir}/{company}-f.last.txt', 'w', encoding='utf-8') as outfile:
        write_lines(employees, 'f_dot_last', domain, outfile)

    with open(f'{out_dir}/{company}-firstl.txt', 'w', encoding='utf-8') as outfile:
        write_lines(employees, 'first_l', domain, outfile)

    with open(f'{out_dir}/{company}-first.last.txt', 'w', encoding='utf-8') as outfile:
        write_lines(employees, 'first_dot_last', domain, outfile)

    with open(f'{out_dir}/{company}-first.txt', 'w', encoding='utf-8') as outfile:
        write_lines(employees, 'first', domain, outfile)

    with open(f'{out_dir}/{company}-lastf.txt', 'w', encoding='utf-8') as outfile:
        write_lines(employees, 'last_f', domain, outfile)


def main():
    """Main Function"""
    print(BANNER + "\n\n\n")
    args = parse_arguments()

    # Instantiate a session by logging in to LinkedIn.
    session = login()

    # If we can't get a valid session, we quit now. Specific errors are
    # printed to the console inside the login() function.
    if not session:
        sys.exit()

    # Special options below when using a proxy server. Helpful for debugging
    # the application in Burp Suite.
    if args.proxy:
        print("[!] Using a proxy, ignoring SSL errors. Don't get pwned.")
        session.verify = False
        urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
        session.proxies.update(args.proxy_dict)

    # Get basic company info
    print("[*] Trying to get company info...")
    company_id, staff_count = get_company_info(args.company, session)

    # Define inner and outer loops
    print("[*] Calculating inner and outer loops...")
    args.depth, args.geoblast = set_inner_loops(staff_count, args)
    outer_loops = set_outer_loops(args)

    # Do the actual searching
    print("[*] Starting search.... Press Ctrl-C to break and write files early.\n")
    employees = do_loops(session, company_id, outer_loops, args)

    # Write the data to some files.
    write_files(args.company, args.domain, employees, args.output)

    # Time to get hacking.
    print(f"\n\n[*] All done! Check out your lovely new files in {args.output}")


if __name__ == "__main__":
    main()
