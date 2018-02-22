import cookielib
import os
import urllib
import urllib2
import re
import string
from BeautifulSoup import BeautifulSoup

#############################################
username = ""
password = ""
companyID = ""
searchDepth = 5
#############################################



cookie_filename = "parser.cookies.txt"

class LinkedInParser(object):

    def __init__(self, login, password):
        """ Start up... """
        self.login = login
        self.password = password

        # Simulate browser with cookies enabled
        self.cj = cookielib.MozillaCookieJar(cookie_filename)
        if os.access(cookie_filename, os.F_OK):
            self.cj.load()
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cj)
        )
        self.opener.addheaders = [
            ('User-agent', ('Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0'))
        ]

        # Login
        self.loginPage()

        title = self.loadTitle()
        print title

        self.cj.save()


    def loadPage(self, url, data=None):
        """
        Utility function to load HTML from URLs for us with hack to continue despite 404
        """
        # We'll print the url in case of infinite loop
        # print "Loading URL: %s" % url
        try:
            if data is not None:
                response = self.opener.open(url, data)
            else:
                response = self.opener.open(url)
            return ''.join(response.readlines())
        except:
            # If URL doesn't load for ANY reason, try again...
            # Quick and dirty solution for 404 returns because of network problems
            # However, this could infinite loop if there's an actual problem
            return self.loadPage(url, data)

    def loginPage(self):
        """
        Handle login. This should populate our cookie jar.
        """
        html = self.loadPage("https://www.linkedin.com/")
        soup = BeautifulSoup(html)
        try:
            csrf = soup.find(id="loginCsrfParam-login")['value']
        except:
            csrf = ''
        login_data = urllib.urlencode({
            'session_key': self.login,
            'session_password': self.password,
            'loginCsrfParam': csrf,
        })

        html = self.loadPage("https://www.linkedin.com/uas/login-submit", login_data)
        return

    def loadTitle(self):
        html = self.loadPage("https://www.linkedin.com/feed/")
        soup = BeautifulSoup(html)
        return soup.find("title")

parser = LinkedInParser(username, password)


def scrapeInfo():
    print('Starting search....')
    for page in range(0, searchDepth):
        url = 'https://www.linkedin.com/search/results/people/?facetCurrentCompany=%5B%22'+companyID+'%22%5D&page=' + str(page+1)
        result = parser.loadPage(url)
        firstName = re.findall(r'firstName&quot;:&quot;(.*?)&', result)
        lastName = re.findall(r'lastName&quot;:&quot;(.*?)&', result)
        
        for first,last in zip(firstName,lastName):
            print(first + ' ' + last)

def main():
    data = scrapeInfo()

if __name__ == "__main__":
    main()
