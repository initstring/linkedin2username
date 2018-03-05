# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn. Works with Python2.

This is a pure web-scraper, no API key required. You use your valid LinkedIn username and password to login, it will create several lists of possible username formats for all employees of a company you point it at.

Use an account with a lot of connections, otherwise you'll get crappy results.

Here's what you get:
- first.last.txt: Usernames like Joe.Schmoe
- flast.txt:      Usernames like JSchmoe
- firstl.txt:     Usernames like JoeS
- rawnames.txt:   Full name like Joe Schmoe

# Example
Here's an example to pull all employees of Uber:
```
$ python linkedin2username.py myname@email.com uber-com
```

# Full Help
```
usage: linkedin2username.py username company [-p PASSWORD] [-d DEPTH] [-s SLEEP]

positional arguments:
  username              A valid LinkedIn username.
  company               Company name.

optional arguments:
  -h, --help            show this help message and exit
  -p PASSWORD, --password PASSWORD
                        Optionally specific password on the command line. If
                        not specified, will prompt and not display on screen.
  -d DEPTH, --depth DEPTH
                        Search depth. If unset, will try to grab them all.
  -s SLEEP, --sleep SLEEP
                        Seconds to sleep between pages. defaults to 3
```
