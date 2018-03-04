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
$ python linkedin2username.py myname@email.com 361843
```

Here's how to get that company ID (I will automate this later):
1. Log in to LinkedIn
2. Find a comapny's overview page (ie https://www.linkedin.com/company/uber/)
3. Hover over "See all xxx employees on LinkedIn"
4. Look for the ID number in "facetCurrentCompany" in the URL. (Uber is 361843).

# Full Help
```
usage: linkedin2username.py username company [-p PASSWORD] [-d DEPTH] [-s SLEEP]

positional arguments:
  username              A valid LinkedIn username.
  company               Numerical company ID assigned by LinkedIn
                        (search company employees and look at URL on website to find)

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
