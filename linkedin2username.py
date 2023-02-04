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
import getpass
import json
import urllib.parse
import requests
import urllib3

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

# The dictionary below is a best-effort attempt to spread a search load
# across sets of geographic locations. This can bypass the 1000 result
# search limit as we are now allowed 1000 per geo set.
# developer.linkedin.com/docs/v1/companies/targeting-company-shares#additionalcodes
GEO_REGIONS = {
    'r0': 'us:0',
    'r1': 'ca:0',
    'r2': 'gb:0',
    'r3': 'au:0|nz:0',
    'r4': 'cn:0|hk:0',
    'r5': 'jp:0|kr:0|my:0|np:0|ph:0|sg:0|lk:0|tw:0|th:0|vn:0',
    'r6': 'in:0',
    'r7': 'at:0|be:0|bg:0|hr:0|cz:0|dk:0|fi:0',
    'r8': 'fr:0|de:0',
    'r9': 'gr:0|hu:0|ie:0|it:0|lt:0|nl:0|no:0|pl:0|pt:0',
    'r10': 'ro:0|ru:0|rs:0|sk:0|es:0|se:0|ch:0|tr:0|ua:0',
    'r11': ('ar:0|bo:0|br:0|cl:0|co:0|cr:0|do:0|ec:0|gt:0|mx:0|pa:0|pe:0'
            '|pr:0|tt:0|uy:0|ve:0'),
    'r12': 'af:0|bh:0|il:0|jo:0|kw:0|pk:0|qa:0|sa:0|ae:0'}


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
        parsed = re.split(' |-', name)

        if len(parsed) > 2:
            split_name = {'first': parsed[0], 'second': parsed[-2], 'last': parsed[-1]}
        else:
            split_name = {'first': parsed[0], 'second': '', 'last': parsed[-1]}

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

    parser.add_argument('-u', '--username', type=str, action='store',
                        required=True,
                        help='A valid LinkedIn username.')
    parser.add_argument('-c', '--company', type=str, action='store',
                        required=True,
                        help='Company name exactly as typed in the company '
                        'linkedin profile page URL.')
    parser.add_argument('-p', '--password', type=str, action='store',
                        help='Specify your password in clear-text on the '
                        'command line. If not specified, will prompt and '
                        'obfuscate as you type.')
    parser.add_argument('-n', '--domain', type=str, action='store',
                        default='',
                        help='Append a domain name to username output. '
                        '[example: "-n uber.com" would output jschmoe@uber.com]'
                        )
    parser.add_argument('-d', '--depth', type=int, action='store',
                        default=False,
                        help='Search depth (how many loops of 25). If unset, '
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

    # If password is not passed in the command line, prompt for it
    # in a more secure fashion (not shown on screen)
    args.password = args.password or getpass.getpass()

    return args


def login(args):
    """Creates a new authenticated session.

    Note that a mobile user agent is used. Parsing using the desktop results
    proved extremely difficult, as shared connections would be returned in
    a manner that was indistinguishable from the desired targets.

    The other header matters as well, otherwise advanced search functions
    (region and keyword) will not work.

    The function will check for common failure scenarios - the most common is
    logging in from a new location. Accounts using multi-factor auth are not
    yet supported and will produce an error.
    """
    session = requests.session()

    # The following are known errors that require the user to log in via the web
    login_problems = ['challenge', 'captcha', 'manage-account', 'add-email']

    # Special options below when using a proxy server. Helpful for debugging
    # the application in Burp Suite.
    if args.proxy:
        print("[!] Using a proxy, ignoring SSL errors. Don't get pwned.")
        session.verify = False
        urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
        session.proxies.update(args.proxy_dict)

    # Our search and regex will work only with a mobile user agent and
    # the correct REST protocol specified below.
    mobile_agent = ('Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 '
                    'Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) '
                    'Version/4.0 Mobile Safari/534.30')
    session.headers.update({'User-Agent': mobile_agent,
                            'X-RestLi-Protocol-Version': '2.0.0'})

    # We wll grab an anonymous response to look for the CSRF token, which
    # is required for our logon attempt.
    anon_response = session.get('https://www.linkedin.com/login')
    login_csrf = re.findall(r'name="loginCsrfParam" value="(.*?)"',
                            anon_response.text)
    if login_csrf:
        login_csrf = login_csrf[0]
    else:
        print("Having trouble loading login page... try the command again.")
        sys.exit()

    # Define the data we will POST for our login.
    auth_payload = {
        'session_key': args.username,
        'session_password': args.password,
        'isJsEnabled': 'false',
        'loginCsrfParam': login_csrf
        }

    # Perform the actual login. We disable redirects as we will use that 302
    # as an indicator of a successful logon.
    response = session.post('https://www.linkedin.com/checkpoint/lg/login-submit'
                            '?loginSubmitSource=GUEST_HOME',
                            data=auth_payload, allow_redirects=False)

    # Define a successful login by the 302 redirect to the 'feed' page. Try
    # to detect some other common logon failures and alert the user.
    if response.status_code in (302, 303):
        # Add CSRF token for all additional requests
        session = set_csrf_token(session)
        redirect = response.headers['Location']
        if 'feed' in redirect:
            return session
        if 'add-phone' in redirect:
            # Skip the prompt to add a phone number
            url = 'https://www.linkedin.com/checkpoint/post-login/security/dismiss-phone-event'
            response = session.post(url)
            if response.status_code == 200:
                return session
            print("[!] Could not skip phone prompt. Log in via the web and then try again.\n")

        elif any(x in redirect for x in login_problems):
            print("[!] LinkedIn has a message for you that you need to address. "
                  "Please log in using a web browser first, and then come back and try again.")
        else:
            # The below will detect some 302 that I don't yet know about.
            print("[!] Some unknown redirection occurred. If this persists, please open an issue "
                  "and include the info below:")
            print("DEBUG INFO:")
            print(f"LOCATION: {redirect}")
            print(f"RESPONSE TEXT:\n{response.text}")

        return False

    # A failed logon doesn't generate a 302 at all, but simply responds with
    # the logon page. We detect this here.
    if '<title>LinkedIn Login' in response.text:
        print("[!] Check your username and password and try again.\n")
        return False

    # If we make it past everything above, we have no idea what happened.
    # Oh well, we fail.
    print("[!] Some unknown error logging in. If this persists, please open an issue on github.\n")
    print("DEBUG INFO:")
    print(f"RESPONSE CODE: {response.status_code}")
    print(f"RESPONSE TEXT:\n{response.text}")
    return False


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

    # We will look for 25 names on each loop. So, we set a maximum amount of
    # loops to the amount of staff / 25 +1 more to catch remainders.
    loops = int((staff_count / 25) + 1)

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
              " 25 results each.\n\n")
        args.depth = loops

    return args.depth, args.geoblast


def get_results(session, company_id, page, region, keyword):
    """Scrapes raw data for processing.

    The URL below is what the LinkedIn mobile HTTP site queries when manually
    scrolling through search results.

    The mobile site defaults to using a 'count' of 10, but testing shows that
    25 is allowed. This behavior will appear to the web server as someone
    scrolling quickly through all available results.
    """
    # When using the --geoblast feature, we need to inject our set of region
    # codes into the search parameter.
    if region:
        region = re.sub(':', '%3A', region)  # must URL encode this parameter

    # Build the base search URL.
    url = ('https://www.linkedin.com'
           '/voyager/api/search/hits'
           f'?facetCurrentCompany=List({company_id})'
           f'&facetGeoRegion=List({region})'
           f'&keywords=List({keyword})'
           '&q=people&maxFacetValues=15'
           '&supportedFacets=List(GEO_REGION,CURRENT_COMPANY)'
           '&count=25'
           '&origin=organization'
           f'&start={page * 25}')

    # Perform the search for this iteration.
    result = session.get(url)
    return result


def find_employees(result):
    """
    Takes the text response of an HTTP query, converst to JSON, and extracts employee details.

    Retuns a list of dictionary items, or False if none found.
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

    # When you get to the last page of results, the next page will have an empty
    # "elements" list.
    if not result_json['elements']:
        return False

    # The "elements" list is the mini-profile you see when scrolling through a
    # company's employees. It does not have all info on the person, like their
    # entire job history. It only has some basics.
    for body in result_json['elements']:
        profile = (body['hitInfo']
                       ['com.linkedin.voyager.search.SearchProfile']
                       ['miniProfile'])
        full_name = f"{profile['firstName']} {profile['lastName']}"
        employee = {'full_name': full_name,
                    'occupation': profile['occupation']}

        # Some employee names are not disclosed and return empty. We don't want those.
        if len(employee['full_name']) > 1:
            found_employees.append(employee)

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
                region_name = 'r' + str(current_loop)
                current_region = GEO_REGIONS[region_name]
                current_keyword = ''
                print(f"\n[*] Looping through region {current_region}")
            elif args.keywords:
                current_keyword = args.keywords[current_loop]
                current_region = ''
                print(f"\n[*] Looping through keyword {current_keyword}")
            else:
                current_region = ''
                current_keyword = ''

            # This is the inner loop. It will search results 25 at a time.
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
    session = login(args)

    # If we can't get a valid session, we quit now. Specific errors are
    # printed to the console inside the login() function.
    if not session:
        sys.exit()

    print("[*] Successfully logged in.")

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
