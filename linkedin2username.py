# -*- coding: utf-8 -*-

import re
import string
import time
import unicodedata
import argparse
import getpass
import requests
import urllib


# Handle arguments before moving on....
parser = argparse.ArgumentParser()
parser.add_argument("username", type=str, help="A valid LinkedIn username.", action='store')
parser.add_argument("company", type=str, help="Numerical company ID assigned by LinkedIn", action='store')
parser.add_argument("-p", "--password", type=str, help="Optionally specific password on \
                     the command line. If not specified, will prompt and not display on screen.", action='store')
parser.add_argument("-d", "--depth", type=int, help="Search depth. Defaults to 1000 pages or end of list.", action='store')
parser.add_argument("-s", "--sleep", type=int, help="Seconds to sleep between pages. \
                     defaults to 1.", action='store')
args = parser.parse_args()

username = args.username
companyID = args.company

if args.depth:
    searchDepth = args.depth
else:
    searchDepth = 1000

if args.sleep:
    pageDelay = args.sleep
else:
    pageDelay = 1

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
    loginCSRF = re.findall(r'name="loginCsrfParam".*?value="(.*?)"', anonResponse.text)[0]

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

def search_users(session, companyID, page):
    url = 'https://linkedin.com/'
    url += 'voyager/api/search/hits?count=10&guides=facetCurrentCompany-%3E'
    url += companyID
    url += '&origin=OTHER&q=guided&start='
    url += str(page*10)
    result = session.get(url)
    return result.text

def scrape_info(session):
    fullNameList = []
    print('[+] Starting search....')
    for page in range(0, searchDepth):
        print('[+] OK, looking for results on page ' + str(page+1))
        result = search_users(session, companyID, page)
        firstName = re.findall(r'"firstName":"(.*?)"', result)
        lastName = re.findall(r'"lastName":"(.*?)"', result)
        if len(firstName) == 0 and len(lastName) == 0:
            print('[+] We have hit the end of the road! Moving on...')
            break
        for first,last in zip(firstName,lastName):
            fullName = first + ' ' + last
            if fullName not in fullNameList:
                fullNameList.append(fullName)
        print('    [+] We have a total of ' + str(len(fullNameList)) + ' names so far...')
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
    string = re.sub(u"[ß]", 'b', string)
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

def main():
    session = login(username, password)
    session = set_search_csrf(session)
    foundNames  = scrape_info(session)
    cleanList = clean(foundNames)
    write_files(cleanList)
    print('All done! Check out your lovely new files.')

if __name__ == "__main__":
    main()
