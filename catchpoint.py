import sys
import base64
from logging import getLogger
import datetime
import pytz
import requests


class CatchpointError(Exception):
    pass


class Catchpoint(object):
    _DEFAULT_HOST = "io.catchpoint.com"
    _DFFAULT_VERSION = 1
    _URL_TEMPLATE = "https://{host}/ui/api/v{version}/{uri}"

    def __init__(
        self,
        host=_DEFAULT_HOST,
        version=_DFFAULT_VERSION,
        logger=None,
    ):
        """
        Basic init method.

        - host (str): The host to connect to
        - version (int): The version of the API
        """
        self._host = host
        self._version = version
        self.content_type = "application/json"

        self._logger = logger if logger is not None else getLogger(name=self.__class__.__name__)
        self._auth = False
        self._token = None

    def _debug(self, msg):
        """
        Debug output. Set self.verbose to True to enable.
        """
        self._logger.debug(msg)

    def _connection_error(self, e):
        msg = "Unable to reach {0}: {1}".format(self._host, e)
        sys.exit(msg)

    def _authorize(self, creds):
        """
        Request an auth token.

        - creds: dict with client_id and client_secret
        """
        self._debug("Creating auth url...")
        uri = "https://{0}/ui/api/token".format(self._host)
        payload = {
            'grant_type': 'client_credentials',
            'client_id': creds['client_id'],
            'client_secret': creds['client_secret']
        }

        # make request
        self._debug("Making auth request...")
        try:
            r = requests.post(uri, data=payload)
        except requests.ConnectionError as e:
            self._connection_error(e)

        self._debug("URL: " + r.url)
        data = r.json()

        self._token = data['access_token']
        self._debug("TOKEN: " + self._token)
        self._auth = True

    def _make_request(self, uri, params=None, data=None):
        """
        Make a request with an auth token.

        - uri: URI for the new Request object.
        - params: (optional) dict or bytes to be sent in the query string for the Request.
        - data: (optional) dict, bytes, or file-like object to send in the body of the Request.
        """
        self._debug("Making request...")
        headers = {
            'Accept': self.content_type,
            'Authorization': "Bearer " + base64.b64encode(self._token)
        }

        final_url = self._URL_TEMPLATE.format(host=self._host, version=self._version, uri=uri)
        res = requests.get(final_url, headers=headers, params=params, data=data)

        if res.status_code < 200 or res.status_code > 299:
            msg = "{status_code} {reason} was returned. Body: {body}".format(
                status_code=res.status_code,
                reason=res.reason,
                body=res.content,
            )
            raise CatchpointError(msg)

        r_data = res.json()
        self._expired_token_check(r_data)

        return r_data

    def _expired_token_check(self, data):
        """
        Determine whether the token is expired. While this check could
        technically be performed before each request, it's easier to offload
        retry logic onto the script using this class to avoid too many
        req/min.

        - data: The json data returned from the API call.
        """
        if "Message" in data:
            if data['Message'].find("Expired token") != -1:
                self._debug("Token was expired and has been cleared, try again...")
                self._token = None
                self._auth = False

    def _format_time(self, startTime, endTime, tz):
        """
        Format "now" time to actual UTC time and set microseconds to 0.

        - startTime: start time of the requested data (least recent).
        - endTime: end time of the requested data (most recent).
        - tz: Timezone in tz database format (Catchpoint uses a different format).
        """
        if endTime is not None and startTime is not None:
            if endTime == "now":
                if not isinstance(startTime, int) and startTime >= 0:
                    msg = "When using relative times, startTime must be a negative number (number of minutes minus 'now')."
                    sys.exit(msg)
                try:
                    endTime = datetime.datetime.now(pytz.timezone(tz))
                    endTime = endTime.replace(microsecond=0)
                except pytz.UnknownTimeZoneError:
                    msg = "\n".join([
                        "Unknown Timezone '{0}'".format(tz),
                        "Use tz database format: http://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                    ])
                    sys.exit(msg)
                startTime = endTime + datetime.timedelta(minutes=int(startTime))
                startTime = startTime.strftime('%Y-%m-%dT%H:%M:%S')
                endTime = endTime.strftime('%Y-%m-%dT%H:%M:%S')
                self._debug("endTime: " + str(endTime))
                self._debug("startTime: " + str(startTime))

        return startTime, endTime

    def raw(self, creds, testid, startTime, endTime, tz="UTC"):
        """
        Retrieve the raw performance chart data for a given test for a time period.
        """
        if not self._auth:
            self._authorize(creds)

        startTime, endTime = self._format_time(startTime, endTime, tz)

        # prepare request
        self._debug("Creating raw_chart url...")
        params = {
            'startTime': startTime,
            'endTime': endTime
        }

        return self._make_request("performance/raw/{0}".format(testid), params)

    def favorite_charts(self, creds):
        """
        Retrieve the list of favorite charts.
        """
        if not self._auth:
            self._authorize(creds)

        # prepare request
        self._debug("Creating get_favorites url...")

        return self._make_request("performance/favoriteCharts")

    def favorite_details(self, creds, favid):
        """
        Retrieve the favorite chart details.
        """
        if not self._auth:
            self._authorize(creds)

        # prepare request
        self._debug("Creating favorite_details url...")

        return self._make_request("performance/favoriteCharts/{0}".format(favid))

    def favorite_data(
            self, creds, favid,
            startTime=None, endTime=None, tz="UTC", tests=None):
        """
        Retrieve the data for a favorite chart, optionally overriding its timeframe
        or test set.
        """
        if not self._auth:
            self._authorize(creds)

        startTime, endTime = self._format_time(startTime, endTime, tz)

        # prepare request
        self._debug("Creating favorite_data url...")

        if endTime is None or startTime is None:
            params = None
        else:
            params = {
                'startTime': startTime,
                'endTime': endTime
            }

        if tests is not None:
            params['tests'] = tests

        return self._make_request("performance/favoriteCharts/{0}/data".format(favid), params)

    def nodes(self, creds):
        """
        Retrieve the list of nodes for the API consumer.
        """
        if not self._auth:
            self._authorize(creds)

        # prepare request
        self._debug("Creating nodes url...")

        return self._make_request("nodes")

    def node(self, creds, node):
        """
        Retrieve a given node for the API consumer.
        """
        if not self._auth:
            self._authorize(creds)

        self._debug("Creating node url...")

        return self._make_request("nodes/{0}".format(node))
