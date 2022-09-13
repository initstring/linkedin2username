# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn.

This is a pure web-scraper, no API key required. You use your valid LinkedIn username and password to login, it will create several lists of possible username formats for all employees of a company you point it at.

Use an account with a lot of connections, otherwise you'll get crappy results. Adding a couple connections at the target company should help - this tool will work up to third degree connections. Note that [LinkedIn will cap search results](https://www.linkedin.com/help/linkedin/answer/129/what-you-get-when-you-search-on-linkedin?lang=en) to 1000 employees max. You can use the features '--geoblast' or '--keywords' to bypass this limit. Look at help below for more details.

**WARNING**: LinkedIn has recently (Sept 2020) been hitting li2u users with the monthly commercial search limit. It's a bit mysterious as to when/why this happens. When you hit the limit, you won't be able to search again until the 1st of the month. If you know of a workaround, please let me know.

Here's what you get:
- first.last.txt: Usernames like Joe.Schmoe
- f.last.txt:     Usernames like J.Schmoe
- flast.txt:      Usernames like JSchmoe
- firstl.txt:     Usernames like JoeS
- first.txt       Usernames like Joe
- lastf.txt       Usernames like SchmoeJ
- rawnames.txt:   Full name like Joe Schmoe

Optionally, the tool will append @domain.xxx to the usernames.

# Example
You'll need to provide the tool with LinkedIn's company name. You can find that by looking at the URL for the company's page. It should look something like `https://linkedin.com/company/uber-com`. It may or may not be as simple as the exact name of the company.

Here's an example to pull all employees of Uber:
```
$ python linkedin2username.py myname@email.com uber-com
```

Here's an example to pull a shorter list and append the domain name @uber.com to them:
```
$ python linkedin2username.py myname@email.com uber-com -d 5 -n 'uber.com'
```

# Full Help
```
usage: linkedin2username.py [-h] [-u USERNAME] -c COMPANY [-p PASSWORD] 
[-n DOMAIN] [-d DEPTH] [-s SLEEP] [-x PROXY] [-k KEYWORDS] [-f COOKIEFILE]
[-g]

OSINT tool to generate lists of probable usernames from a given company's
LinkedIn page. This tool may break when LinkedIn changes their site. Please
open issues on GitHub to report any inconsistencies, and they will be quickly
fixed.

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        A valid LinkedIn username.
  -c COMPANY, --company COMPANY
                        Company name exactly as typed in the company linkedin
                        profile page URL.
  -p PASSWORD, --password PASSWORD
                        Specify your password in clear-text on the command
                        line. If not specified, will prompt and obfuscate as you type.
  -n DOMAIN, --domain DOMAIN
                        Append a domain name to username output. [example: "-n
                        uber.com" would output jschmoe@uber.com]
  -d DEPTH, --depth DEPTH
                        Search depth (how many loops of 25). If unset, will try
                        to grab them all.
  -s SLEEP, --sleep SLEEP
                        Seconds to sleep between search loops. Defaults to 0.
  -x PROXY, --proxy PROXY
                        Proxy server to use. WARNING: WILL DISABLE SSL
                        VERIFICATION. [example: "-p https://localhost:8080"]        
  -k KEYWORDS, --keywords KEYWORDS
                        Filter results by a a list of command separated
                        keywords. Will do a separate loop for each keyword,
                        potentially bypassing the 1,000 record limit. 
                        [example: 
                        "-k 'sales,humanresources,informationtechnology']
  -f COOKIEFILE, --cookiefile COOKIEFILE
                        Path to a Netscape cookie file to import instead of
                        authenticating with username/password combo.
  -g, --geoblast        Attempts to bypass the 1,000 record search limit by
                        running multiple searches split across geographic
                        regions.
```

# Scripts
`convertCookies.py` - Convert a json cookie file to a Netscape cookie file. Helpful to convert a cookie export from a web browser extension such as [cookie-editor](https://github.com/moustachauve/cookie-editor)

# Toubleshooting
Sometimes LinkedIn does weird stuff or returns weird results. Sometimes it doesn't like you logging in from new locations. If something looks off, run the tool once or twice more. If it still isn't working, please open an issue.

Multi-factor authentication (MFA, 2FA) is not supported in this tool.

*This is a security research tool. Use only where granted explicit permission from the network owner.*
