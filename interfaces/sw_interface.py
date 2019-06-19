import configparser
from cryptography.fernet import Fernet
import csv
from dateutil.parser import parse
import getpass
import json
from orionsdk import SwisClient
from pathlib import Path
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings


class SolarWindsInterface:

    disable_warnings(InsecureRequestWarning)

    def __init__(self, username, password):
        self.swis = self.auth(username, password)
        self.data_path = Path('data/')
        self.results = None
        self.nodes = None
        self.uris = None
        self.custom_props = None

    def auth(self, username, password):
        server = ""
        return SwisClient(server, username, password)

    def query(self, query_str, node=None):
        print("Sending query to SolarWinds.")
        if node is None:
            self.results = self.swis.query(query_str)
        else:
            self.results = self.swis.query(query_str % str(tuple(node)))
        print("Query received from SolarWinds.")

        return self.results

    def set_uris(self, uris):
        query_str = """SELECT TOP 10 NodeName, NodeID, Uri
                       FROM Orion.Nodes
                       WHERE Uri IN %s"""
        self.query(query_str, nodes=uris)
        self.collect_uris()

        return self.nodes

    def collect_uris(self):
        if self.results is None:
            print("Query never made to SolarWinds.")
            print("Use set_uris() if you're providing your own list of URIs")
            return
        self.nodes = {line['SysName']: line['Uri'] for line in
                      self.results['results']}
        self.uris = [k for k, v in self.nodes.items()]
        return self.nodes

    def check_alerts(self):
        print("Requesting alert suppression states")
        invoke_results = self.swis.invoke(
                                          'Orion.AlertSuppression',
                                          'GetAlertSuppressionState',
                                          self.uris
                                          )
        print("Received alert suppression states")

        states = {line['EntityUri']: line['SuppressionMode'] for line in
                  invoke_results}

        for uri, state in states.items():
            if state == 0:
                print("%s: NOT suppressed" % self.nodes[uri])
            elif state == 1:
                print("%s: suppressed" % self.nodes[uri])
            elif state == 2:
                print("%s: PARENT suppressed" % self.nodes[uri])
            elif state == 3:
                print("%s: suppression scheduled" % self.nodes[uri])
            elif state == 4:
                print("%s: PARENT suppression scheduled" % self.nodes[uri])

        return states

    def suppress_alerts(self, start, end):
        if self.nodes is None:
            self.collect_uris()
        try:
            start = parse(start)
            end = parse(end)
        except ValueError:
            print("Invalid start or end time")
            return
        print("Suppressing alerts FROM - UNTIL: ")
        print("%s - %s" % (str(start), str(end)))

        self.swis.invoke('Orion.AlertSuppression', 'SuppressAlerts', self.uris, start, end)
        print("Finished suppressing alerts")
        states = self.check_alerts()

        return states

    def read_custom_properties(self, uri):
        properties = self.swis.read(uri + '/CustomProperties')
        self.custom_props = json.dumps(properties, indent=4)

        return self.custom_props

    def change_custom_properties(self, uri, updated_props):
        for k, v in updated_props.items():
            self.swis.update(uri + '/CustomProperties', **{k: v})
        #print("Updating Custom Properties")

        return 1
