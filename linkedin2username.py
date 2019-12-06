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
from distutils.version import StrictVersion
import urllib.parse
import requests


                ########## BEGIN GLOBAL DECLARATIONS ##########

CURRENT_REL = '0.17'
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
GEO_REGIONS = {
    'r0':'us:0',
    'r1':'ca:0',
    'r2':'gb:0',
    'r3':'au:0|nz:0',
    'r4':'cn:0|hk:0',
    'r5':'jp:0|kr:0|my:0|np:0|ph:0|sg:0|lk:0|tw:0|th:0|vn:0',
    'r6':'in:0',
    'r7':'at:0|be:0|bg:0|hr:0|cz:0|dk:0|fi:0',
    'r8':'fr:0|de:0',
    'r9':'gr:0|hu:0|ie:0|it:0|lt:0|nl:0|no:0|pl:0|pt:0',
    'r10':'ro:0|ru:0|rs:0|sk:0|es:0|se:0|ch:0|tr:0|ua:0',
    'r11':('ar:0|bo:0|br:0|cl:0|co:0|cr:0|do:0|ec:0|gt:0|mx:0|pa:0|pe:0'
           '|pr:0|tt:0|uy:0|ve:0'),
    'r12':'af:0|bh:0|il:0|jo:0|kw:0|pk:0|qa:0|sa:0|ae:0'}

                 ########## END GLOBAL DECLARATIONS ##########

if sys.version_info < (3, 0):
    print("\nSorry mate, you'll need to use Python 3+ on this one...\n")
    sys.exit(1)


class PC:
    """PC (Print Color)
    Used to generate some colorful, relevant, nicely formatted status messages.
    """
    green = '\033[92m'
    blue = '\033[94m'
    orange = '\033[93m'
    endc = '\033[0m'
    ok_box = blue + '[*] ' + endc
    note_box = green + '[+] ' + endc
    warn_box = orange + '[!] ' + endc


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
                        '[example: "-n uber.com" would ouput jschmoe@uber.com]'
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

    args = parser.parse_args()

    # Proxy argument is fed to requests as a dictionary, setting this now:
    args.proxy_dict = {"https" : args.proxy}

    # If appending an email address, preparing this string now:
    if args.domain:
        args.domain = '@' + args.domain

    # Keywords are fed in as a list. Splitting comma-separated user input now:
    if args.keywords:
        args.keywords = args.keywords.split(',')

    # These two functions are not currently compatible, squashing this now:
    if args.keywords and args.geoblast:
        print("Sorry, keywords and geoblast are currently not compatible. "
              "Use one or the other.")
        sys.exit()

    # If password is not passed in the command line, prompt for it
    # in a more secure fashion (not shown on screen)
    args.password = args.password or getpass.getpass()

    return args


def check_li2u_version():
    """Checks GitHub for a new version

    Uses a simple regex to look at the 'releases' page on GitHub. Extracts the
    First tag found and assumes it is the latest. Compares with the global
    variable CURRENT_TAG and informs if a new version is available.
    """
    latest_rel_regex = r'/initstring/linkedin2username/tree/(.*?)"'
    session = requests.session()
    rel_url = 'https://github.com/initstring/linkedin2username/releases'
    rel_chars = re.compile(r'[^0-9\.]')

    # Scrape the page and grab the regex.
    response = session.get(rel_url)
    latest_rel = re.findall(latest_rel_regex, response.text)

    # Remove characters from tag name that will mess up version comparison.
    # Also just continue if we can't find the tags - we don't want that small
    # function to break the entire app.
    if latest_rel[0]:
        latest_rel = rel_chars.sub('', latest_rel[0])
    else:
        return

    # Check the tag found with the one defined in this script.
    if CURRENT_REL == latest_rel:
        print("")
        print(PC.ok_box + "Using version {}, which is the latest on"
              " GitHub.\n".format(CURRENT_REL))
        return
    if StrictVersion(CURRENT_REL) > StrictVersion(latest_rel):
        print("")
        print(PC.warn_box + "Using version {}, which is NEWER than {}, the"
              " latest official release. Good luck!\n"
              .format(CURRENT_REL, latest_rel))
        return
    if StrictVersion(CURRENT_REL) < StrictVersion(latest_rel):
        print("")
        print(PC.warn_box + "You are using {}, but {} is available.\n"
              "    LinkedIn changes often - this version may not work.\n"
              "    https://github.com/initstring/linkedin2username.\n"
              .format(CURRENT_REL, latest_rel))
        return


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

    # Special options below when using a proxy server. Helpful for debugging
    # the application in Burp Suite.
    if args.proxy:
        print(PC.warn_box + "Using a proxy, ignoring SSL errors."
              " Don't get pwned.")
        session.verify = False
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
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
    if response.status_code == 302 or response.status_code == 303:
        redirect = response.headers['Location']
        if 'feed' in redirect:
            print(PC.ok_box + "Successfully logged in.\n")
            return session
        if 'challenge' in redirect:
            print(PC.warn_box + "LinkedIn doesn't like something about this"
                  " login. Maybe you're being sneaky on a VPN or something."
                  " You may get an email with a verification token. You can"
                  " ignore the email. Log in from a web browser and try"
                  " again.\n")
            return False
        if 'captcha' in redirect:
            print(PC.warn_box + "You've triggered a CAPTCHA. Oops. Try logging"
                  " in with your web browser first and come back later.")
            return False

        # The below will detect some 302 that I don't yet know about.
        print(PC.warn_box + "Some unknown redirection occurred. If this"
              " persists, please open an issue on github.\n")
        return False

    # A failed logon doesn't generate a 302 at all, but simply reponds with
    # the logon page. We detect this here.
    if '<title>LinkedIn Login' in response.text:
        print(PC.warn_box + "You've been returned to a login page. Check your"
              " username and password and try again.\n")
        return False

    # If we make it past everything above, we have no idea what happened.
    # Oh well, we fail.
    print(PC.warn_box + "Some unknown error logging in. If this persists,"
          "please open an issue on github.\n")
    return False


def set_search_csrf(session):
    """Extract the required CSRF token.

    LinkedIn's search function requires a CSRF token equal to the JSESSIONID.
    """
    csrf_token = session.cookies['JSESSIONID'].replace('"', '')
    session.headers.update({'Csrf-Token': csrf_token})
    return session


def get_company_info(name, session):
    """Scapes basic company info.

    Note that not all companies fill in this info, so exceptions are provided.
    The company name can be found easily by browsing LinkedIn in a web browser,
    searching for the company, and looking at the name in the address bar.
    """
    # The following regexes may be moving targets, I will try to keep them up
    # to date. If you have issues with these, please open a ticket on GitHub.
    # Thanks!
    website_regex = r'companyPageUrl":"(http.*?)"'
    staff_regex = r'staffCount":([0-9]+),'
    id_regex = r'"objectUrn":"urn:li:company:([0-9]+)"'
    desc_regex = r'tagline":"(.*?)"'
    escaped_name = urllib.parse.quote_plus(name)

    response = session.get(('https://www.linkedin.com'
                            '/voyager/api/organization/companies?'
                            'q=universalName&universalName=' + escaped_name))

    # Some geo regions are being fed a 'lite' version of LinkedIn mobile:
    # https://bit.ly/2vGcft0
    # The following bit is a temporary fix until I can figure out a
    # low-maintenence solution that is inclusive of these areas.
    if 'mwlite' in response.text:
        print(PC.warn_box + "You are being served the 'lite' version of"
              " LinkedIn (https://bit.ly/2vGcft0) that is not yet supported"
              " by this tool. Please try again using a VPN exiting from USA,"
              " EU, or Australia.")
        print("    A permanent fix is being researched. Sorry about that!")
        sys.exit()

    # Will search for the company ID in the response. If not found, the
    # program cannot succeed and must exit.
    found_id = re.findall(id_regex, response.text)
    if not found_id:
        print(PC.warn_box + "Could not find that company name. Please"
              " double-check LinkedIn and try again.")
        sys.exit()

    # Below we will try to scrape metadata on the company. If not found, will
    # set generic strings as warnings.
    found_desc = re.findall(desc_regex, response.text)
    if not found_desc:
        found_desc = ["RegEx issues, please open a ticket on GitHub!"]
    found_staff = re.findall(staff_regex, response.text)
    if not found_staff:
        found_staff = ["RegEx issues, please open a ticket on GitHub!"]
    found_website = re.findall(website_regex, response.text)
    if not found_website:
        found_website = ["RegEx issues, please open a ticket on GitHub!"]

    print("          ID:    " + found_id[0])
    print("          Alias: " + name)
    print("          Desc:  " + found_desc[0])
    print("          Staff: " + str(found_staff[0]))
    print("          URL:   " + found_website[0])
    print("\n" + PC.ok_box + "Hopefully that's the right {}! If not,"
          "double-check LinkedIn and try again.\n".format(name))

    return(found_id[0], int(found_staff[0]))


def set_loops(staff_count, args):
    """Defines total hits to the seach API.

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

    print(PC.ok_box + "Company has {} profiles to check. Some may be"
                      " anonymous.".format(staff_count))

    # The lines below attempt to detect large result sets and compare that
    # with the command line arguments passed. The goal is to warn when you
    # may not get all the results and to suggest ways to get  more.
    if staff_count > 1000 and not args.geoblast and not args.keywords:
        print(PC.warn_box + "Note: LinkedIn limits us to a maximum of 1000"
              " results!\n"
              "    Try the --geoblast or --keywords parameter to bypass")
    elif staff_count < 1000 and args.geoblast:
        print(PC.warn_box + "Geoblast is not necessary, as this company has"
              " less than 1,000 staff. Disabling.")
        args.geoblast = False
    elif staff_count > 1000 and args.geoblast:
        print(PC.ok_box + "High staff count, geoblast is enabled. Let's rock.")
    elif staff_count > 1000 and args.keywords:
        print(PC.ok_box + "High staff count, using keywords. Hope you picked"
              " some good ones.")

    # If the user purposely restricted the search depth, they probably know
    # what they are doing, but we warn them just in case.
    if args.depth and args.depth < loops:
        print(PC.warn_box + "You defined a low custom search depth, so we"
              " might not get them all.")
    else:
        print(PC.ok_box + "Setting each iteration to a maximum of {} loops of"
              " 25 results each.".format(loops))
        args.depth = loops
    print("\n\n")
    return args


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
        region = re.sub(':', '%3A', region) # must URL encode this parameter

    # Build the base search URL.
    url = ('https://www.linkedin.com'
           '/voyager/api/search/hits'
           '?facetCurrentCompany=List({})'
           '&facetGeoRegion=List({})'
           '&keywords=List({})'
           '&q=people&maxFacetValues=15'
           '&supportedFacets=List(GEO_REGION,CURRENT_COMPANY)'
           '&count=25'
           '&origin=organization'
           '&start={}'
           .format(company_id, region, keyword, page * 25))

    # Perform the search for this iteration.
    result = session.get(url)
    return result.text


def scrape_info(session, company_id, staff_count, args):
    """Uses regexes to extract employee names.

    The data returned is similar to JSON, but not always formatted properly.
    The regex queries below will build individual lists of first and last
    names. Every search tested returns an even number of each, so we can safely
    match the two lists together to get full names.

    Has the concept of inner an outer loops. Outerloops come into play when
    using --keywords or --geoblast, both which attempt to bypass the 1,000
    record search limit.

    This function will stop searching if a loop returns 0 new names.
    """
    full_name_list = []
    print(PC.ok_box + "Starting search....\n")

    # We pass the full 'args' below as we need to define a few variables from
    # there - the loops as well as potentially disabling features that are
    # deemed unnecessary due to small result sets.
    args = set_loops(staff_count, args)

    # If we are using geoblast or keywords, we need to define a numer of
    # "outer_loops". An outer loop will be a normal LinkedIn search, maxing
    # out at 1000 results.
    if args.geoblast:
        outer_loops = range(0, len(GEO_REGIONS))
    elif args.keywords:
        outer_loops = range(0, len(args.keywords))
    else:
        outer_loops = range(0, 1)

    # Crafting the right URL is a bit tricky, so currently unnecessary
    # parameters are still being included but set to empty. You will see this
    # below with geoblast and keywords.
    for current_loop in outer_loops:
        if args.geoblast:
            region_name = 'r' + str(current_loop)
            current_region = GEO_REGIONS[region_name]
            current_keyword = ''
            print("\n" + PC.ok_box + "Looping through region {}"
                  .format(current_region))
        elif args.keywords:
            current_keyword = args.keywords[current_loop]
            current_region = ''
            print("\n" + PC.ok_box + "Looping through keyword {}"
                  .format(current_keyword))
        else:
            current_region = ''
            current_keyword = ''

        ## This is the inner loop. It will search results 25 at a time.
        for page in range(0, args.depth):
            new_names = 0
            sys.stdout.flush()
            sys.stdout.write(PC.ok_box + "Scraping results on loop "
                             + str(page+1) + "...    ")
            result = get_results(session, company_id, page, current_region,
                                 current_keyword)
            first_name = re.findall(r'"firstName":"(.*?)"', result)
            last_name = re.findall(r'"lastName":"(.*?)"', result)

            # If the list of names is empty for a page, we assume that
            # there are no more search results. Either you got them all or
            # you are not connected enough to get them all.
            if not first_name and not last_name:
                sys.stdout.write('\n')
                print(PC.ok_box + "We have hit the end of the road!"
                      " Moving on...")
                break

            # re.findall puts all first names and all last names in a list.
            # They are ordered, so the pairs should correspond with each other.
            # We parse through them all here, and see which ones are new to us.
            for first, last in zip(first_name, last_name):
                full_name = first + ' ' + last
                if full_name not in full_name_list:
                    full_name_list.append(full_name)
                    new_names += 1
            sys.stdout.write("    " + PC.ok_box + "Added " + str(new_names) +
                             " new names. Running total: "\
                             + str(len(full_name_list)) + "              \r")

            # If the user has defined a sleep between loops, we take a little
            # nap here.
            time.sleep(args.sleep)

    return full_name_list


def remove_accents(raw_text):
    """Removes common accent characters.

    Our goal is to brute force login mechanisms, and I work primary with
    companies deploying Engligh-language systems. From my experience, user
    accounts tend to be created without special accented characters. This
    function tries to swap those out for standard Engligh alphabet.
    """

    raw_text = re.sub(u"[àáâãäå]", 'a', raw_text)
    raw_text = re.sub(u"[èéêë]", 'e', raw_text)
    raw_text = re.sub(u"[ìíîï]", 'i', raw_text)
    raw_text = re.sub(u"[òóôõö]", 'o', raw_text)
    raw_text = re.sub(u"[ùúûü]", 'u', raw_text)
    raw_text = re.sub(u"[ýÿ]", 'y', raw_text)
    raw_text = re.sub(u"[ß]", 'ss', raw_text)
    raw_text = re.sub(u"[ñ]", 'n', raw_text)
    return raw_text


def clean(raw_list):
    """Removes common punctuation.

    LinkedIn users tend to add credentials to their names to look special.
    This function is based on what I have seen in large searches, and attempts
    to remove them.
    """
    clean_list = []
    allowed_chars = re.compile('[^a-zA-Z -]')
    for name in raw_list:

        # Try to transform non-English characters below.
        name = remove_accents(name)

        # The line below basically trashes anything weird left over.
        # A lot of users have funny things in their names, like () or ''
        # People like to feel special, I guess.
        name = allowed_chars.sub('', name)

        # Lower-case everything to make it easier to de-duplicate.
        name = name.lower()

        # The line below tries to consolidate white space between words
        # and get rid of leading/trailing spaces.
        name = re.sub(r'\s+', ' ', name).strip()

        # If what is left is non-empty and unique, we add it to the list.
        if name and name not in clean_list:
            clean_list.append(name)

    return clean_list


def write_files(company, domain, name_list):
    """Writes data to various formatted output files.

    After scraping and processing is complete, this function formates the raw
    names into common username formats and writes them into a directory called
    'li2u-output'.

    See in-line comments for decisions made on handling special cases.
    """

    # Check for and create an ouput directory to store the files.
    out_dir = 'li2u-output'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Define all the files names we will be creating.
    files = {}
    files['rawnames'] = open(out_dir + '/' + company + '-rawnames.txt', 'w')
    files['flast'] = open(out_dir + '/' + company + '-flast.txt', 'w')
    files['firstl'] = open(out_dir + '/' + company + '-firstl.txt', 'w')
    files['firstlast'] = open(out_dir + '/' + company + '-first.last.txt', 'w')
    files['fonly'] = open(out_dir + '/' + company + '-first.txt', 'w')
    files['lastf'] = open(out_dir + '/' + company + '-lastf.txt', 'w')

    # First, write all the raw names to a file.
    for name in name_list:
        files['rawnames'].write(name + '\n')

        # Split the name on spaces and hyphens:
        parse = re.split(' |-', name)

        # Users with hyphenated or multiple last names could have several
        # variations on the username. For a best-effort, we will try using
        # one or the other, but not both. Users with more than three names
        # will be truncated down, assuming the second of four is a middle
        # name.
        try:
            if len(parse) > 2:  # for users with more than one last name.
                first, second, third = parse[0], parse[-2], parse[-1]
                files['flast'].write(first[0] + second + domain + '\n')
                files['flast'].write(first[0] + third + domain + '\n')
                files['lastf'].write(second + first[0] + domain + '\n')
                files['lastf'].write(third + first[0] + domain + '\n')
                files['firstlast'].write(first + '.' + second + domain + '\n')
                files['firstlast'].write(first + '.' + third + domain + '\n')
                files['firstl'].write(first + second[0] + domain + '\n')
                files['firstl'].write(first + third[0] + domain + '\n')
                files['fonly'].write(first + domain + '\n')
            else:               # for users with only one last name
                first, last = parse[0], parse[-1]
                files['flast'].write(first[0] + last + domain + '\n')
                files['lastf'].write(last + first[0] + domain + '\n')
                files['firstlast'].write(first + '.' + last + domain + '\n')
                files['firstl'].write(first + last[0] + domain + '\n')
                files['fonly'].write(first + domain + '\n')

        # The exception below will try to weed out string processing errors
        # I've made in other parts of the program.
        except IndexError:
            print(PC.warn_box + "Struggled with this tricky name: '{}'."
                  .format(name))

    # Cleanly close all the files.
    for file_name in files:
        files[file_name].close()


def main():
    """Main Function"""
    print(BANNER + "\n\n\n")
    args = parse_arguments()

    # Check the version
    check_li2u_version()

    # Instantiate a session by logging in to LinkedIn.
    session = login(args)

    # If we can't get a valid session, we quit now. Specific errors are
    # printed to the console inside the login() function.
    if not session:
        sys.exit()

    # Prepare and execute the searches.
    session = set_search_csrf(session)
    company_id, staff_count = get_company_info(args.company, session)
    found_names = scrape_info(session, company_id, staff_count, args)

    # Clean up all the data.
    clean_list = clean(found_names)

    # Write the data to some files.
    write_files(args.company, args.domain, clean_list)

    # Time to get hacking.
    print("\n\n" + PC.ok_box + "All done! Check out your lovely new files in"
          "the li2u-output directory.")


if __name__ == "__main__":
    main()
