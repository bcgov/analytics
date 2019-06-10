import sys
import json
from googleapiclient import sample_tools
from googleapiclient.http import build_http

discovery_doc = "gmb_discovery.json"


def main(argv):
    # Use the discovery doc to build a service that we can use to make
    # MyBusiness API calls, and authenticate the user so we can access their
    # account
    service, flags = sample_tools.init(
        argv, "mybusiness", "v4", __doc__, __file__,
        scope="https://www.googleapis.com/auth/business.manage",
        discovery_filename=discovery_doc)

    # Get the list of accounts the authenticated user has access to
    output = service.accounts().list().execute()
    print("List of Accounts:\n")
    print(json.dumps(output, indent=2) + "\n")

    firstAccount = output["accounts"][0]["name"]

    # Get the list of locations for the first account in the list
    print("List of Locations for Account " + firstAccount)
    locationsList = service.accounts().locations().list(
        parent=firstAccount).execute()
    print(json.dumps(locationsList, indent=2))

if __name__ == "__main__":
    main(sys.argv)
