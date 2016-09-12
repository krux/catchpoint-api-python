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

    def run(self):
        pprint(self.catchpoint.favorite_data({
            'client_id': 'RMe-Sk-jT2P1LRW1B',
            'client_secret': 'a1f57213-fdf0-4616-b2fb-4388f0a20ced',
        }, 69259, -1, 'now', 'asgklrjbalkwbjrlkBEWR'))


def main():
    Application().run()


# Run the application stand alone
if __name__ == '__main__':
    main()
