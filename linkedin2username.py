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

BANNER="""
                            .__  .__________
                            |  | |__\_____  \ __ __
                            |  | |  |/  ____/|  |  \\
                            |  |_|  /       \|  |  /
                            |____/__\_______ \____/
                               linkedin2username
                 Thanks to all the smart people on StackOverflow.
                        I hope you get in. - initstring\n\n\n\n"""

# Check version requirement
if sys.version_info[0] >= 3:
    print('Sorry, Python 2 only for now...')
    exit()

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


def login(username, password):
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

    if bool(re.search('<title>*LinkedIn*</title>', response.text)): # users get slightly different responses here
        print('[+] Successfully logged in.\n')
        return session
    elif '<title>Sign-In Verification</title>' in response.text:
        print('[!] LinkedIn doesn\'t like something about this login. Maybe you\'re being sneaky on a VPN or')
        print('    something. You may get an email with a verification token. You can ignore that.')
        print('    Try logging in with the same account in your browser first, then try this tool again.\n')
        exit()
    elif '<title>Sign In</title>' in response.text:
        print('[!] You\'ve been returned to the login page. Check your password and try again.\n')
        exit()
    elif '<title>Security Verification' in response.text:
        print('[!] You\'ve triggered the security verification. Please verify your login details and try again.\n')
        exit()
    else:
        print('[!] Some unknown error logging in. If this persists, please open an issue on github.\n')
        exit()

def get_company_info(name, session):
    response = session.get('https://linkedin.com/company/' + name)
    try:
        foundID = re.findall(r'normalized_company:(.*?)[&,]', response.text)[0]             # response can vary
    except:
        print('[!] Could not find that company name. Please double-check LinkedIn and try again.')
        exit()
    foundName = re.findall(r'companyUniversalName.*?3D(.*?)"', response.text)[0]
    foundDesc = re.findall(r'localizedName&quot;:&quot;(.*?)&quot', response.text)[0]
    print('\n')
    print('          [+] Found: ' + foundName)
    print('          [+] ID:    ' + foundID)
    print('          [+] Desc:  ' + foundDesc)
    print('\n[+] Hopefully that\'s the right ' + name + '! If not, double-check LinkedIn and try again.\n')
    return(foundID)

def set_search_csrf(session):
    # Search requires a CSRF token equal to the JSESSIONID.
    session.headers.update({'Csrf-Token': session.cookies['JSESSIONID'].replace('"', '')})
    return session

def get_total_count(result):
    global searchDepth
    totalCount = int(re.findall(r'totalResultCount":(.*?),', result)[0])
    print('[+] Company has ' + str(totalCount) + ' profiles to check. Some may be anonymous.')
    loops = int((totalCount / 25) + 1)
    if searchDepth != '' and searchDepth < loops:
        print('[!] You defined a low custom search depth, so we might not get them all.')
    else:
        print('[+] Setting search to ' + str(loops) + ' loops of 25 results each.')
        searchDepth = loops
    print('\n\n')
    return searchDepth

def get_results(session, companyID, page):
    url = 'https://linkedin.com/'
    url += 'voyager/api/search/hits?count=25&guides=facetCurrentCompany-%3E'
    url += companyID
    url += '&origin=OTHER&q=guided&start='
    url += str(page*25)
    result = session.get(url)
    return result.text

def scrape_info(session, companyID):
    fullNameList = []
    print('[+] Starting search....\n')
    get_total_count(get_results(session, companyID, 1))
    for page in range(0, searchDepth):
        newNames = 0
        print('[+] OK, looking for results on loop numer ' + str(page+1))
        result = get_results(session, companyID, page)
        firstName = re.findall(r'"firstName":"(.*?)"', result)
        lastName = re.findall(r'"lastName":"(.*?)"', result)
        if len(firstName) == 0 and len(lastName) == 0:
            print('[+] We have hit the end of the road! Moving on...')
            break
        for first,last in zip(firstName,lastName):
            fullName = first + ' ' + last
            if fullName not in fullNameList:
                fullNameList.append(fullName)
                newNames +=1
        print('    [+] Added ' + str(newNames) + ' new names.')
        time.sleep(pageDelay)
    return fullNameList

def remove_accents(string):
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
    cleanList = []
    allowedChars = re.compile('[^a-zA-Z ]')
    for name in list:
        name = re.sub(r'[,(/:].*', '', name) # People have a habit of listing lame creds after their name. Gone!
        name = re.sub(r'[\.\']', '', name)  # Getting rid of dots and slashes, while preserving text around them.
        name = remove_accents(name)
        name = allowedChars.sub('',name)    # Gets rid of any remaining special characters in the name
        if name not in cleanList:
            cleanList.append(name)
    return cleanList

def write_files(company, list):
    dir = 'li2u-output'
    if not os.path.exists(dir):
            os.makedirs(dir)
    rawnames = open(dir + '/' + company + '-rawnames.txt', 'w')
    flast = open(dir + '/' + company + '-flast.txt', 'w')
    firstl = open(dir + '/' + company + '-firstl.txt', 'w')
    firstlast = open(dir + '/' + company + '-first.last.txt', 'w')
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
            else:                           # this is for users with only one last name
                first, last = parse[0], parse[-1]
                flast.write(first[0] + last + domain + '\n')
                firstlast.write(first + '.' + last + domain + '\n')
                firstl.write(first + last[0] + domain + '\n')
        except Exception:
            continue
    for f in (rawnames, flast, firstl, firstlast):
        f.close()

def main():
    print(BANNER)
    session = login(username, password)
    session = set_search_csrf(session)
    companyID = get_company_info(company, session)
    foundNames  = scrape_info(session, companyID)
    cleanList = clean(foundNames)
    write_files(company, cleanList)
    print('\n\nAll done! Check out your lovely new files in the li2u-output directory.')

if __name__ == "__main__":
    main()
