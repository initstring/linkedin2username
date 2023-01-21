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
- metadata.txt    CSV file which is full_name,occupation

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
usage: linkedin2username.py [-h] [-p PASSWORD] [-n DOMAIN] [-d DEPTH]
                            [-s SLEEP]
                            username company

positional arguments:
  username              A valid LinkedIn username.
  company               Company name.

optional arguments:
  -h, --help            show this help message and exit
  -p PASSWORD, --password PASSWORD
                        Specify your password on in clear-text on the command
                        line. If not specified, will prompt and not display on
                        screen.
  -n DOMAIN, --domain DOMAIN
                        Append a domain name to username output. [example: '-n
                        uber.com' would ouput jschmoe@uber.com]
  -d DEPTH, --depth DEPTH
                        Search depth. If unset, will try to grab them all.
  -s SLEEP, --sleep SLEEP
                        Seconds to sleep between pages. defaults to 3.
  -x PROXY, --proxy PROXY
                        HTTPS proxy server to use. Example: "-p
                        https://localhost:8080" WARNING: WILL DISABLE SSL
                        VERIFICATION.

  -k KEYWORDS, --keywords KEYWORDS
                        Filter results by a a list of command separated
                        keywords. Will do a separate loop for each keyword,
                        potentially bypassing the 1,000 record limit.
                        [example: "-k 'sales,human resources,information
                        technology']
  -g, --geoblast        Attempts to bypass the 1,000 record search limit by
                        running multiple searches split across geographic
                        regions.
  -o OUTPUT, --output OUTPUT
                        Output Directory, defaults to li2u-output
```

# Toubleshooting
Sometimes LinkedIn does weird stuff or returns weird results. Sometimes it doesn't like you logging in from new locations. If something looks off, run the tool once or twice more. If it still isn't working, please open an issue.

Multi-factor authentication (MFA, 2FA) is not supported in this tool.

*This is a security research tool. Use only where granted explicit permission from the network owner.*
