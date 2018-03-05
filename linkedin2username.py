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

# Check version requirement
if sys.version_info[0] >= 3:
    print("Sorry, Python 2 only for now...")
    exit()

# Handle arguments before moving on....
parser = argparse.ArgumentParser()
parser.add_argument("username", type=str, help="A valid LinkedIn username.", action='store')
parser.add_argument("company", type=str, help="Numerical company ID assigned by LinkedIn", action='store')
parser.add_argument("-p", "--password", type=str, help="Optionally specific password on \
                     the command line. If not specified, will prompt and not display on screen.", action='store')
parser.add_argument("-d", "--depth", type=int, help="Search depth. If unset, will try to grab them all.", action='store')
parser.add_argument("-s", "--sleep", type=int, help="Seconds to sleep between pages. \
                     defaults to 3.", action='store')
args = parser.parse_args()

username = args.username
companyID = args.company

if args.depth:
    searchDepth = args.depth
else:
    searchDepth = ''

if args.sleep:
    pageDelay = args.sleep
else:
    pageDelay = 3

if args.password:
    password = args.password
else:
    password = getpass.getpass()


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

    if '<title>LinkedIn</title>' in response.text:
        print('[+] Successfully logged in.')
        return session
    else:
        print('[!] Could not log in!')
        exit()

def set_search_csrf(session):
    # Search requires a CSRF token equal to the JSESSIONID.
    jsession = (session.cookies['JSESSIONID'])
    jsession = re.sub('"', '', jsession)
    session.headers.update({'Csrf-Token': jsession})
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

def scrape_info(session):
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
    if type(string) is not unicode:
        string = unicode(string, encoding='utf-8')

    string = re.sub(u"[àáâãäå]", 'a', string)
    string = re.sub(u"[èéêë]", 'e', string)
    string = re.sub(u"[ìíîï]", 'i', string)
    string = re.sub(u"[òóôõö]", 'o', string)
    string = re.sub(u"[ùúûü]", 'u', string)
    string = re.sub(u"[ýÿ]", 'y', string)
    string = re.sub(u"[ß]", 'ss', string)
    return string

def clean(list):
    cleanList = []
    ascii = set(string.printable)
    for name in list:
        name = re.sub(r'[,(].*', '', name) # People have a habit of listing lame creds after their name. Gone!
        name = re.sub(r'\.', '', name)
        name = remove_accents(name)
        name = filter(lambda x: x in ascii, name) # gets rid of any special characters we missed.
        name = name.strip()
        if name not in cleanList:
            cleanList.append(name)
    return cleanList

def write_files(list):
    rawnames = open('rawnames.txt', 'w')
    flast = open('flast.txt', 'w')
    firstl = open('firstl.txt', 'w')
    firstlast = open('first.last.txt', 'w')
    for name in list:
        try:
            rawnames.write(name + '\n')
            parse = name.split(' ')
            flast.write(parse[0][0] + parse[-1] + '\n')
            firstlast.write(parse[0] + '.' + parse[-1] + '\n')
            firstl.write(parse[0] + parse[-1][0] + '\n')
        except:
            continue

def print_banner():
    print('                            .__  .__________                     ')
    print('                            |  | |__\_____  \ __ __              ')
    print('                            |  | |  |/  ____/|  |  \             ')
    print('                            |  |_|  /       \|  |  /             ')
    print('                            |____/__\_______ \____/              ')
    print('                               linkedin2username                 ')
    print('                                                                 ')
    print('                 Thanks to all the smart people on StackOverflow.')
    print('                        I hope you get in. - initstring          ')
    print('\n\n\n')

def main():
    print_banner()
    session = login(username, password)
    session = set_search_csrf(session)
    foundNames  = scrape_info(session)
    cleanList = clean(foundNames)
    write_files(cleanList)
    print('\n\nAll done! Check out your lovely new files.')

if __name__ == "__main__":
    main()
