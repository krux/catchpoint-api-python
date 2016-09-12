from __future__ import absolute_import
from pprint import pprint
import logging
from catchpoint import Catchpoint, CatchpointError


class Application(object):
    """
    A CLI application designed for development testing of catchpoint.
    The goal of this class is to provide a quick and dirty client of catchpoint to be used during development.
    This does not replace a proper unit test.
    """

    NAME = 'catchpoint-test'
    LOG_FORMAT = '%(asctime)s: %(name)s/%(levelname)-9s: %(message)s'

    def __init__(self, name=NAME, *arg, **kwargs):
        self.name = name

        logging.basicConfig(format=self.LOG_FORMAT, level=logging.DEBUG)
        self.catchpoint = Catchpoint(
            logger=logging.getLogger(name=self.name)
        )
        self.cred = {
            'client_id': 'RMe-Sk-jT2P1LRW1B',
            'client_secret': 'a1f57213-fdf0-4616-b2fb-4388f0a20ced',
        }

    def run(self):
        charts = self.catchpoint.favorite_charts(self.cred)
        chart_id = charts['items'][0]['id']
        pprint(self.catchpoint.favorite_details(self.cred, chart_id))
        pprint(self.catchpoint.favorite_data(self.cred, chart_id, -30, 'now'))

        nodes = self.catchpoint.nodes(self.cred)
        node_id = nodes['items'][0]['id']
        pprint(self.catchpoint.node(self.cred, node_id))


def main():
    Application().run()


# Run the application stand alone
if __name__ == '__main__':
    main()
