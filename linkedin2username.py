# -*- coding: utf-8 -*-

import re
import string
import time
import unicodedata
import argparse
import getpass
import requests
import urllib
import sys
import os


# Print a cool banner
BANNER="""
                            .__  .__________
                            |  | |__\_____  \ __ __
                            |  | |  |/  ____/|  |  \\
                            |  |_|  /       \|  |  /
                            |____/__\_______ \____/
                               linkedin2username
                 Thanks to all the smart people on StackOverflow.
                        I hope you get in. - initstring\n\n\n\n"""

# Handle arguments before moving on....
parser = argparse.ArgumentParser()
parser.add_argument('username', type=str, help='A valid LinkedIn username.', action='store')
parser.add_argument('company', type=str, help='Company name.', action='store')
parser.add_argument('-p', '--password', type=str, help='Specify your password on in clear-text on \
                     the command line. If not specified, will prompt and not display on screen.', action='store')
parser.add_argument('-n', '--domain', type=str, help='Append a domain name to username output. \
                     [example: "-n uber.com" would ouput jschmoe@uber.com]', action='store')
parser.add_argument('-d', '--depth', type=int, help='Search depth. If unset, will try to grab them all.', action='store')
parser.add_argument('-s', '--sleep', type=int, help='Seconds to sleep between pages. \
                     defaults to 3.', action='store')
args = parser.parse_args()

username = args.username
company = args.company
if args.domain:
    domain = '@' + args.domain
else:
    domain = ''
searchDepth = args.depth or ''
pageDelay = args.sleep or 3
password = args.password or getpass.getpass()

# Set up some nice colors
class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
okBox = bcolors.OKGREEN + '[+] ' + bcolors.ENDC
warnBox = bcolors.WARNING + '[!] ' + bcolors.ENDC


def login(username, password):
    """Creates a new authenticated session.
    
    Note that a mobile user agent is used.
    Parsing using the desktop results proved extremely difficult, as shared connections would be returned
    in a manner that was indistinguishable from the desired targets.

    The function will check for common failure scenarios - the most common is logging in from a new location.
    Accounts using multi-factor auth are not yet supported and will produce an error
    """
    session = requests.session()
    mobileAgent = 'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Droid Build/FRG22D) AppleWebKit/533.1 (KHTML, like Gecko) \
                   Version/4.0 Mobile Safari/533.1'
    session.headers.update({'User-Agent': mobileAgent})
    anonResponse = session.get('https://www.linkedin.com/')
    try:
        loginCSRF = re.findall(r'name="loginCsrfParam".*?value="(.*?)"', anonResponse.text)[0]
    except:
        print('Having trouble with loading the page... try the command again.')
        exit()

    authPayload = {
        'session_key': username,
        'session_password': password,
        'loginCsrfParam': loginCSRF
        }

    response = session.post('https://www.linkedin.com/uas/login-submit', data=authPayload)

    if bool(re.search('<title>*?LinkedIn*?</title>', response.text)):
        print(okBox + 'Successfully logged in.\n')
        return session
    elif '<title>Sign-In Verification</title>' in response.text:
        print(warnBox + 'LinkedIn doesn\'t like something about this login. Maybe you\'re being sneaky on a VPN or')
        print('    something. You may get an email with a verification token. You can ignore that.')
        print('    Try logging in with the same account in your browser first, then try this tool again.\n')
        exit()
    elif '<title>Sign In</title>' in response.text:
        print(warnBox + 'You\'ve been returned to the login page. Check your password and try again.\n')
        exit()
    elif '<title>Security Verification' in response.text:
        print(warnBox + 'You\'ve triggered the security verification. Please verify your login details and try again.\n')
        exit()
    else:
        print(warnBox + 'Some unknown error logging in. If this persists, please open an issue on github.\n')
        exit()

def get_company_info(name, session):
    """Scapes basic company info.

    Note that not all companies fill in this info, so exceptions are provided. The company name can be found easily
    by browsing LinkedIn in a web browser, searching for the company, and looking at the name in the address bar.
    """
    # The following regexes may be moving targets, I will try to keep them up to date.
    # If you have issues with these, please open a ticket on GitLab. Thanks!
    companyRegex = r'linkedin\.voyager\.organization\.Company.*?;name&quot;:&quot;(.*?)&quot;'
    staffRegex = r';staffCount&quot;:(.*?),&'
    idRegex = r'normalized_company:(.*?)[&,]'
    descRegex = r'localizedName&quot;:&quot;(.*?)&quot'

    response = session.get('https://linkedin.com/company/' + name)
    try:
        foundID = re.findall(idRegex, response.text)[0]
    except:
        print(warnBox + 'Could not find that company name. Please double-check LinkedIn and try again.')
        exit()
    try:
        foundDesc = re.findall(descRegex, response.text)[0]
    except:
        foundDesc = "RegEx issues, please open a ticket on GitLab!"
    try:
        foundName = re.findall(companyRegex, response.text)[0]
    except:
        foundName = "RegEx issues, please open a ticket on GitLab!"
    try:
        foundStaff = re.findall(staffRegex, response.text)[0]
    except:
        foundStaff = "RegEx issues, please open a ticket on GitLab!"
    print('          Found: ' + foundName)
    print('          ID:    ' + foundID)
    print('          Desc:  ' + foundDesc)
    print('          Staff: ' + str(foundStaff))
    print('\n' + okBox + 'Hopefully that\'s the right ' + name + '! If not, double-check LinkedIn and try again.\n')
    return(foundID, int(foundStaff))

def set_search_csrf(session):
    """Extract the required CSRF token.
    
    LinkedIn's search function requires a CSRF token equal to the JSESSIONID.
    """
    session.headers.update({'Csrf-Token': session.cookies['JSESSIONID'].replace('"', '')})
    return session

def set_loops(staffCount):
    """Defines total hits to the seach API.

    Sets a total amount of loops based on either the number of staff discovered in the get_company_info function
    or the search depth argument provided by the user. LinkedIn currently restricts these searches to a limit of 1000.
    I have not implemented that limit in this application, just in case they change their mind. Either way, this
    application will stop searching when no more results are provided.
    """
    global searchDepth
    print(okBox + 'Company has ' + str(staffCount) + ' profiles to check. Some may be anonymous.')
    if staffCount > 1000:
      print(warnBox + 'Note: LinkedIn limits us to a maximum of 1000 results!')
    loops = int((staffCount / 25) + 1)
    if searchDepth != '' and searchDepth < loops:
        print(warnBox + 'You defined a low custom search depth, so we might not get them all.')
    else:
        print(okBox + 'Setting search to ' + str(loops) + ' loops of 25 results each.')
        searchDepth = loops
    print('\n\n')
    return searchDepth

def get_results(session, companyID, page):
    """Scrapes raw data for processing.

    The URL below is what the LinkedIn mobile application queries when manually scrolling through search results.
    The mobile app defaults to using a 'count' of 10, but testing shows that 25 is allowed. This behavior will appear
    to the web server as someone scrolling quickly through all available results.
    """
    url = 'https://linkedin.com'
    url += '/voyager/api/search/hits?count=25&guides=facetCurrentCompany-%3E'
    url += companyID
    url += '&origin=OTHER&q=guided&start='
    url += str(page*25)
    result = session.get(url)
    return result.text

def scrape_info(session, companyID, staffCount):
    """Uses regexes to extract employee names.

    The data returned is similar to JSON, but not always formatted properly. The regex queries below will build
    individual lists of first and last names. Every search tested returns an even number of each, so we can safely
    match the two lists together to get full names.

    This function will stop searching if a loop returns 0 new names.
    """
    fullNameList = []
    print(okBox + 'Starting search....\n')
    set_loops(staffCount)
    for page in range(0, searchDepth):
        newNames = 0
        sys.stdout.flush()
        sys.stdout.write(okBox + 'OK, looking for results on loop numer ' + str(page+1) + '...        ')
        result = get_results(session, companyID, page)
        firstName = re.findall(r'"firstName":"(.*?)"', result)
        lastName = re.findall(r'"lastName":"(.*?)"', result)
        if len(firstName) == 0 and len(lastName) == 0:
            sys.stdout.write('\n')
            print(okBox + 'We have hit the end of the road! Moving on...')
            break
        for first,last in zip(firstName,lastName):
            fullName = first + ' ' + last
            if fullName not in fullNameList:
                fullNameList.append(fullName)
                newNames +=1
        sys.stdout.write('    ' + okBox + 'Added ' + str(newNames) + ' new names. Running total: '\
                         + str(len(fullNameList)) + '              \r')
        time.sleep(pageDelay)
    return fullNameList

def remove_accents(string):
    """Removes common accent characters.

    Our goal is to brute force login mechanisms, and I work primary with companies deploying Engligh-language
    systems. From my experience, user accounts tend to be created without special accented characters. This function
    tries to swap those out for standard Engligh alphabet.
    """
    try:               # Python 2
        if not isinstance(string, unicode):
            string = unicode(string, encoding='utf-8')
    except NameError:  # Python 3
        pass

    string = re.sub(u"[àáâãäå]", 'a', string)
    string = re.sub(u"[èéêë]", 'e', string)
    string = re.sub(u"[ìíîï]", 'i', string)
    string = re.sub(u"[òóôõö]", 'o', string)
    string = re.sub(u"[ùúûü]", 'u', string)
    string = re.sub(u"[ýÿ]", 'y', string)
    string = re.sub(u"[ß]", 'ss', string)
    string = re.sub(u"[ñ]", 'n', string)
    return string

def clean(list):
    """Removes common punctuation.

    LinkedIn users tend to add credentials to their names to look special. This function is based on what I have seen
    in large searches, and attempts to remove them.
    """
    cleanList = []
    allowedChars = re.compile('[^a-zA-Z ]')
    for name in list:
        name = re.sub(r'[,(/:].*', '', name)
        name = re.sub(r'[\.\']', '', name)
        name = remove_accents(name)
        name = allowedChars.sub('', name)
        name = name.lower()
        name = re.sub('\s+', ' ', name).strip()
        if name not in cleanList:
            cleanList.append(name)
    return cleanList

def write_files(company, list):
    """Writes data to various formatted output files.

    After scraping and processing is complete, this function formates the raw names into common username formats
    and writes them into a directory called 'li2u-output'.

    See in-line comments for decisions made on handling special cases.
    """
    dir = 'li2u-output'
    if not os.path.exists(dir):
            os.makedirs(dir)
    rawnames = open(dir + '/' + company + '-rawnames.txt', 'w')
    flast = open(dir + '/' + company + '-flast.txt', 'w')
    firstl = open(dir + '/' + company + '-firstl.txt', 'w')
    firstlast = open(dir + '/' + company + '-first.last.txt', 'w')
    fonly = open(dir + '/' + company + '-first.txt', 'w')
    for name in list:
        try:
            rawnames.write(name + '\n')
            parse = re.split(' |-', name)         # Split the name on spaces and hyphens
            
            # Users with hyphenated or multiple last names could have several variations on the username.
            # For a best-effort, we will try using one or the other, but not both. Users with more than three
            # names will be truncated down, assuming the second of four is a middle name.
            if len(parse) > 2:              # this is for users with more than one last name.
               first, second, third = parse[0], parse[-2], parse[-1]
               flast.write(first[0] + second + domain + '\n')
               flast.write(first[0] + third + domain + '\n')
               firstlast.write(first + '.' + second + domain + '\n')
               firstlast.write(first + '.' + third + domain + '\n')
               firstl.write(first + second[0] + domain + '\n')
               firstl.write(first + third[0] + domain + '\n')
               fonly.write(first + domain + '\n')
            else:                           # this is for users with only one last name
                first, last = parse[0], parse[-1]
                flast.write(first[0] + last + domain + '\n')
                firstlast.write(first + '.' + last + domain + '\n')
                firstl.write(first + last[0] + domain + '\n')
                fonly.write(first + domain + '\n')
        except Exception:
            continue
    for f in (rawnames, flast, firstl, firstlast, fonly):
        f.close()

def main():
    print(BANNER)
    session = login(username, password)
    session = set_search_csrf(session)
    companyID,staffCount = get_company_info(company, session)
    foundNames  = scrape_info(session, companyID, staffCount)
    cleanList = clean(foundNames)
    write_files(company, cleanList)
    print('\n\n' + okBox + 'All done! Check out your lovely new files in the li2u-output directory.')

if __name__ == "__main__":
    main()
