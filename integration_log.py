import json
import requests
from enum import Enum
from curl import Curl


class IntegrationLog(object):

    def __init__(self, process_id, url, username, password, log_level_name, ov_token=False):
        self._url = url
        self._process_id = process_id
        if ov_token == True:
            self._auth = HTTPBearerAuth(username, password)
        else:
            self._auth = requests.auth.HTTPBasicAuth(username, password)
        self._ov_log_level = LogLevel.get_log_level_by_name(log_level_name)

    def add(self, log_level, message, description=""):
        if log_level.log_level_id <= self._ov_log_level.log_level_id:
            parameters = {'message': message, 'description': description, 'log_level_name': log_level.log_level_name}
            json_data = json.dumps(parameters)
            headers = {'content-type': 'application/json'}
            url_log = self._url + "/api/v3/integrations/runs/" + str(self._process_id) + "/logs"
            curl = Curl('POST', url_log, data=json_data, headers=headers, auth=self._auth)
            if len(curl.errors) > 0:
                raise Exception(curl.errors)
            return curl.jsonData
    

class LogLevel(Enum):
    ERROR = (0, "Error")
    WARNING = (1, "Warning")
    INFO = (2, "Info")
    DEBUG = (3, "Debug")

    def __init__(self, log_level_id, log_level_name):
        self.log_level_id = log_level_id
        self.log_level_name = log_level_name
    
    @staticmethod
    def get_log_level_by_name(ov_log_level_name):
        for log_level in list(LogLevel):
            if log_level.log_level_name == ov_log_level_name:
                return log_level
        raise Exception("Cannot find the log level called '{}'".format(ov_log_level_name))
    

class HTTPBearerAuth(requests.auth.AuthBase):
	def __init__(self, ov_access_key, ov_secret_key):
		self.access_key = ov_access_key
		self.secret_key = ov_secret_key

	def __call__(self, request):
		request.headers['Authorization'] = 'Bearer ' + self.access_key + ':' + self.secret_key
		return request