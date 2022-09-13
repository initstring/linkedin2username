from datetime import timedelta
import json
import datetime
import argparse
import sys
from os.path import exists

# parse_arguments: Handle user-supplied arguments
def parse_arguments():

    desc = ('Format a json file into a Netscape cookie file')
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', '--cookiefile', type=str, action="store", 
                        default=False, required=True,
                        help='Path to a json cookie file to convert to a netscape file')
    parser.add_argument('-o', '--outfile', type=str, action="store", 
                        default="cookies_netscape.txt",
                        help='Path to an output file')

    args = parser.parse_args()

    if args.cookiefile == "":
        print("ERROR: Missing argument -c,--cookiefile ")
        parser.print_usage()
        sys.exit(1)
    
    return args

# json2NetscapeFile: Convert a json cookie file to netscape
def json2NetscapeFile(inFile, outFile):
    cookiecounter = 1
    if not exists(inFile):
        print("ERROR: file '{0}' does not exist".format(inFile))
        sys.exit(1)
    with open(outFile, "w") as cookie_handle:
        
        # Write netscape header
        cookie_handle.write("# Netscape HTTP Cookie File\n")

        # Open and read json file
        handle_cookies = open(inFile)
        obj_cookies = json.load(handle_cookies)
        handle_cookies.close()

        # Loop json dictionary and create netscape cookie string
        
        for cookie in obj_cookies:
            
            netscape_cookie = "{domain}\t{domain_notnull}\t{path}\t{secure}\t{expiration}\t{c_name}\t{c_value}".format(
                domain=cookie["domain"],
                domain_notnull=("TRUE" if cookie["domain"].startswith(".") else "FALSE"),
                path=cookie["path"],secure=cookie["secure"],
                expiration=(cookie["expirationDate"] if "expirationDate" in cookie.keys() and cookie["expirationDate"] != "" else (datetime.datetime.now()+timedelta(days=1)).timestamp()),
                c_name=cookie["name"],
                c_value=cookie["value"]
                )
            
            # Write netscape cookie string to file
            cookie_handle.write(netscape_cookie+"\n")
            cookiecounter += 1
    
    print("Parsed cookies: {0} ".format(cookiecounter))
    # Print arr_cookies
    #[print(cookie) for cookie in arr_cookies]

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Convert cookie json to netscape
    json2NetscapeFile(args.cookiefile, args.outfile)

    print("Output file: {0}".format(args.outfile))

if __name__ == "__main__":
    main()