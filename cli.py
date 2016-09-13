from __future__ import absolute_import
import logging
from pprint import pprint

from catchpoint import Catchpoint


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
            client_id='RMe-Sk-jT2P1LRW1B',
            client_secret='a1f57213-fdf0-4616-b2fb-4388f0a20ced',
            logger=logging.getLogger(name=self.name)
        )

    def run(self):
        charts = self.catchpoint.favorite_charts()
        chart_id = charts['items'][0]['id']
        pprint(self.catchpoint.favorite_details(chart_id))
        pprint(self.catchpoint.favorite_data(chart_id))
        pprint(self.catchpoint.favorite_data(chart_id, -30, 'now'))

        nodes = self.catchpoint.nodes()
        node_id = nodes['items'][0]['id']
        pprint(self.catchpoint.node(node_id))


def main():
    Application().run()


# Run the application stand alone
if __name__ == '__main__':
    main()
