import sys
import base64
from logging import getLogger
from DateTime import DateTime
import pytz
import requests


class CatchpointError(Exception):
    pass


class Catchpoint(object):
    _DEFAULT_HOST = "io.catchpoint.com"
    _DFFAULT_VERSION = 1
    _URL_TEMPLATE = "https://{host}/ui/api/v{version}/{uri}"
    _TOKEN_URL_TEMPLATE = "https://{host}/ui/api/token"

    def __init__(
        self,
        client_id,
        client_secret,
        host=_DEFAULT_HOST,
        version=_DFFAULT_VERSION,
        logger=None,
    ):
        """
        Basic init method.

        - host (str): The host to connect to
        - version (int): The version of the API
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._host = host
        self._version = version

        self._logger = logger if logger is not None else getLogger(name=self.__class__.__name__)
        self._headers = {
            'Accept': 'application/json',
        }
        # GOTCHA: Arbitrarily chosen date time in the past
        self._token_expires_on = DateTime(0)

    def _debug(self, msg):
        """
        Debug output. Set self.verbose to True to enable.
        """
        self._logger.debug(msg)

    def _get_header(self):
        """
        Request an auth token.

        - creds: dict with client_id and client_secret
        """
        if self._token_expires_on.isPast():
            # Remove old authentication header
            if "Authorization" in self._headers:
                self._headers.pop("Authorization")

            # Retrieve the new authentication token
            self._debug("Creating auth url...")
            uri = self._TOKEN_URL_TEMPLATE.format(host=self._host)
            auth_token = self._make_request(
                method="POST",
                url=uri,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers=self._headers,
            )

            # Set the new token in header
            access_token = auth_token["access_token"]
            self._debug("Access token: " + access_token)
            self._headers["Authorization"] = "Bearer " + base64.b64encode(access_token)

            # Remember the expiry datetime
            # GOTCHA: Take out 60 seconds from the expiry just to be safe
            expire_time_epoch = DateTime().timeTime() + int(auth_token["expires_in"]) - 60
            self._token_expires_on = DateTime(expire_time_epoch)
            self._debug("Expires at: " + self._token_expires_on.ISO8601())

        return self._headers

    def _call(self, url, *args, **kwargs):
        """
        Make a request with an auth token.

        - uri: URI for the new Request object.
        - params: (optional) dict or bytes to be sent in the query string for the Request.
        - data: (optional) dict, bytes, or file-like object to send in the body of the Request.
        """
        self._debug("Making request...")

        final_url = self._URL_TEMPLATE.format(host=self._host, version=self._version, uri=url)
        return self._make_request(
            url=final_url,
            headers=self._get_header(),
            *args,
            **kwargs
        )

    def _make_request(self, *args, **kwargs):
        res = requests.request(*args, **kwargs)

        if res.status_code < 200 or res.status_code > 299:
            msg = "{status_code} {reason} was returned. Body: {body}".format(
                status_code=res.status_code,
                reason=res.reason,
                body=res.content,
            )
            raise CatchpointError(msg)

        return res.json()

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
                    endTime = DateTime.now(pytz.timezone(tz))
                    endTime = endTime.replace(microsecond=0)
                except pytz.UnknownTimeZoneError:
                    msg = "\n".join([
                        "Unknown Timezone '{0}'".format(tz),
                        "Use tz database format: http://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                    ])
                    sys.exit(msg)
                startTime = endTime + DateTime.timedelta(minutes=int(startTime))
                startTime = startTime.strftime('%Y-%m-%dT%H:%M:%S')
                endTime = endTime.strftime('%Y-%m-%dT%H:%M:%S')
                self._debug("endTime: " + str(endTime))
                self._debug("startTime: " + str(startTime))

        return startTime, endTime

    def raw(self, testid, startTime, endTime, tz="UTC"):
        """
        Retrieve the raw performance chart data for a given test for a time period.
        """
        startTime, endTime = self._format_time(startTime, endTime, tz)

        # prepare request
        self._debug("Creating raw_chart url...")
        params = {
            'startTime': startTime,
            'endTime': endTime
        }

        return self._call(
            method="GET",
            url="performance/raw/{0}".format(testid),
            params=params,
        )

    def favorite_charts(self):
        """
        Retrieve the list of favorite charts.
        """
        # prepare request
        self._debug("Creating get_favorites url...")

        return self._call(
            method="GET",
            url="performance/favoriteCharts",
        )

    def favorite_details(self, favid):
        """
        Retrieve the favorite chart details.
        """
        # prepare request
        self._debug("Creating favorite_details url...")

        return self._call(
            method="GET",
            url="performance/favoriteCharts/{0}".format(favid),
        )

    def favorite_data(self, favid, startTime=None, endTime=None, tz="UTC", tests=None):
        """
        Retrieve the data for a favorite chart, optionally overriding its timeframe
        or test set.
        """
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

        return self._call(
            method="GET",
            url="performance/favoriteCharts/{0}/data".format(favid),
            params=params,
        )

    def nodes(self):
        """
        Retrieve the list of nodes for the API consumer.
        """
        # prepare request
        self._debug("Creating nodes url...")

        return self._call(
            method="GET",
            url="nodes",
        )

    def node(self, node):
        """
        Retrieve a given node for the API consumer.
        """
        self._debug("Creating node url...")

        return self._call(
            method="GET",
            url="nodes/{0}".format(node),
        )
