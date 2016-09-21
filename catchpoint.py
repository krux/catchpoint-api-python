import sys
import base64
from logging import getLogger
from datetime import datetime, timedelta, MINYEAR
import pytz
import requests


class CatchpointError(Exception):
    pass


class Catchpoint(object):
    DEFAULT_HOST = "io.catchpoint.com"
    DFFAULT_VERSION = 1

    _URL_TEMPLATE = "https://{host}/ui/api/v{version}/{uri}"
    _TOKEN_URL_TEMPLATE = "https://{host}/ui/api/token"
    _TOKEN_EXPIRATION_SAFETY_BUFFER = 60  # seconds

    def __init__(
        self,
        client_id,
        client_secret,
        host=DEFAULT_HOST,
        version=DFFAULT_VERSION,
        logger=None,
    ):
        """
        Basic init method.

        :param client_id: The Key given to your Pull API Consumer
        :type client_id: str
        :param client_secret: The Secret given to your Pull API Consumer
        :type client_secret: str
        :param host: The host to connect to
        :type host: str
        :param version: The version of the API
        :type version: int
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._host = host
        self._version = version

        self._logger = logger if logger is not None else getLogger(name=self.__class__.__name__)
        self._headers = {
            'Accept': 'application/json',
        }
        # Arbitrarily chosen date time in the past. Chosen so that a token will
        # be requested before the first call.
        self._token_expires_on = datetime(MINYEAR, 1, 1, tzinfo=pytz.utc)

    def _get_headers(self):
        """
        Gets the required headers for the API request. If access token has expired, automatically requests
        a new one and adds that to the header.

        :return: The headers for the API request
        :rtype: dict
        """
        now = datetime.now(tz=pytz.utc).replace(microsecond=0)
        if self._token_expires_on < now:
            # Remove old authentication header
            if "Authorization" in self._headers:
                del self._headers["Authorization"]

            # Retrieve the new authentication token
            self._logger.debug("Creating auth url...")
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
            self._logger.debug("Access token: " + access_token)
            self._headers["Authorization"] = "Bearer " + base64.b64encode(access_token)

            # Remember the expiry datetime
            # GOTCHA: Take out 60 seconds from the expiry just to be safe. I don't want this to fail because
            #         either it took me more than a second to get this request or took them more than a second to
            #         get the last request.
            self._token_expires_on = now + timedelta(seconds=(int(auth_token["expires_in"]) - self._TOKEN_EXPIRATION_SAFETY_BUFFER))
            self._logger.debug("Expires at: " + self._token_expires_on.isoformat())

        return self._headers

    def _call(self, url, *args, **kwargs):
        """
        Calls the given URL. Requests a new access token if needed.

        :param url: Relative path URL (i.e. performance/favoriteCharts) unique to the endpoint.
                    The full URL is deduced based on _URL_TEMPLATE.
        :type url: str
        :param args: Ordered arguments passed directly to requests.request() via _make_request()
        :type args: list
        :param kwargs: Keyword arguments passed directly to requests.request() via _make_request()
        :type kwargs: dict
        :return: Result of the request, parsed as JSON.
        :rtype: dict
        """
        self._logger.debug("Making request...")

        final_url = self._URL_TEMPLATE.format(host=self._host, version=self._version, uri=url)
        return self._make_request(
            url=final_url,
            headers=self._get_headers(),
            *args,
            **kwargs
        )

    def _make_request(self, *args, **kwargs):
        """
        A simple wrapper around requests.request(). If response is 2**, returns JSON parsed response as a dictionary.
        Otherwise, raises a CatchpointError.

        :param args: Ordered arguments passed directly to requests.request()
        :type args: list
        :param kwargs: Keyword arguments passed directly to requests.request()
        :type kwargs: dict
        :raise: :py:class:`CatchpointError` if response is not 2**.
        :return: Result of the request, parsed as JSON.
        :rtype: dict
        """
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
                    endTime = datetime.now(pytz.timezone(tz))
                    endTime = endTime.replace(microsecond=0)
                except pytz.UnknownTimeZoneError:
                    msg = "\n".join([
                        "Unknown Timezone '{0}'".format(tz),
                        "Use tz database format: http://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                    ])
                    sys.exit(msg)
                startTime = endTime + timedelta(minutes=int(startTime))
                startTime = startTime.strftime('%Y-%m-%dT%H:%M:%S')
                endTime = endTime.strftime('%Y-%m-%dT%H:%M:%S')
                self._logger.debug("endTime: " + str(endTime))
                self._logger.debug("startTime: " + str(startTime))

        return startTime, endTime

    def raw(self, testid, startTime, endTime, tz="UTC"):
        """
        Retrieve the raw performance chart data for a given test for a time period.

        .. seealso:: https://io.catchpoint.com/ui/Help/Detail/GET-api-vversion-performance-raw-testId_showOnlyPushApiFailed_startTime_endTime

        :param testid: ID of the test to get performance data from
        :type testid: str
        :param startTime: Start time to gather the data from. Either in '%m-%d-%Y %H:%M' format or a negative integer
                          if endTime is 'now'
        :type startTime: str | int
        :param endTime: End time to gather the data to. Either in '%m-%d-%Y %H:%M' format or 'now'
        :type endTime: str
        :param tz: pytz recognized timezone name
        :type tz: str
        """
        startTime, endTime = self._format_time(startTime, endTime, tz)

        # prepare request
        self._logger.debug("Creating raw_chart url...")
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

        .. seealso:: https://io.catchpoint.com/ui/Help/Detail/GET-api-vversion-performance-favoriteCharts
        """
        # prepare request
        self._logger.debug("Creating get_favorites url...")

        return self._call(
            method="GET",
            url="performance/favoriteCharts",
        )

    def favorite_details(self, favid):
        """
        Retrieve the favorite chart details.

        .. seealso:: https://io.catchpoint.com/ui/Help/Detail/GET-api-vversion-performance-favoriteCharts-id

        :param favid: ID of the favorite chart
        :type favid: str
        """
        # prepare request
        self._logger.debug("Creating favorite_details url...")

        return self._call(
            method="GET",
            url="performance/favoriteCharts/{0}".format(favid),
        )

    def favorite_data(self, favid, startTime=None, endTime=None, tz="UTC", tests=None):
        """
        Retrieve the data for a favorite chart, optionally overriding its timeframe
        or test set.

        .. seealso:: https://io.catchpoint.com/ui/Help/Detail/GET-api-vversion-performance-favoriteCharts-id-data

        :param favid: ID of the favorite chart
        :type favid: str
        :param startTime: Start time to gather the data from. Either in '%m-%d-%Y %H:%M' format or a negative integer
                          if endTime is 'now'
        :type startTime: str | int
        :param endTime: End time to gather the data to. Either in '%m-%d-%Y %H:%M' format or 'now'
        :type endTime: str
        :param tz: pytz recognized timezone name
        :type tz: str
        :param tests: Comma delimited list of test IDs
        :type tests: str
        """
        startTime, endTime = self._format_time(startTime, endTime, tz)

        # prepare request
        self._logger.debug("Creating favorite_data url...")

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

        .. seealso:: https://io.catchpoint.com/ui/Help/Detail/GET-api-vversion-nodes
        """
        # prepare request
        self._logger.debug("Creating nodes url...")

        return self._call(
            method="GET",
            url="nodes",
        )

    def node(self, node):
        """
        Retrieve a given node for the API consumer.

        .. seealso:: https://io.catchpoint.com/ui/Help/Detail/GET-api-vversion-nodes-id

        :param node: ID of the node to retrieve
        :type node: str
        """
        self._logger.debug("Creating node url...")

        return self._call(
            method="GET",
            url="nodes/{0}".format(node),
        )
