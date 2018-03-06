# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn. Works with Python2.

This is a pure web-scraper, no API key required. You use your valid LinkedIn username and password to login, it will create several lists of possible username formats for all employees of a company you point it at.

Use an account with a lot of connections, otherwise you'll get crappy results.

Here's what you get:
- first.last.txt: Usernames like Joe.Schmoe
- flast.txt:      Usernames like JSchmoe
- firstl.txt:     Usernames like JoeS
- rawnames.txt:   Full name like Joe Schmoe

Optionally, the tool will append @domain.xxx to the usernames.

# Example
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
```

# Toubleshooting
Sometimes LinkedIn does weird stuff or returns weird results. Sometimes it doesn't like you logging in from new locations. If something looks off, run the tool once or twice more. If it still isn't working, please open an issue.
