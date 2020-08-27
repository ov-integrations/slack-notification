import json

from slack_notifservice import SlackNotifService
from jsonschema import validate

with open('settings.json', "rb") as SFile:
    settings_data = json.loads(SFile.read().decode('utf-8'))

with open('settings_schema.json', "rb") as SFile:
    data_schema = json.loads(SFile.read().decode('utf-8'))

try:
    validate(instance=settings_data, schema=data_schema)
except Exception as e:
    raise Exception("Incorrect value in the settings file\n{}".format(str(e)))

not_specified_params = ""

if "ovUrl" in settings_data:
    ov_url = settings_data["ovUrl"]
else:
    not_specified_params += "ovUrl\n"

if "ovAccessKey" in settings_data:
    ov_access_key = settings_data["ovAccessKey"]
else:
    not_specified_params += "ovAccessKey\n"

if "ovSecretKey" in settings_data:
    ov_secret_key = settings_data["ovSecretKey"]
else:
    not_specified_params += "ovSecretKey\n"

if "serviceId" in settings_data:
    service_id = settings_data["serviceId"]
else:
    not_specified_params += "serviceId\n"

if "channelField" in settings_data:
    channel_name_field = settings_data["channelField"]
else:
    not_specified_params += "channelField\n"

if "slackBotToken" in settings_data:
    bot_token_in_slack = settings_data["slackBotToken"] 
else:
    not_specified_params += "slackBotToken\n"

max_attempts = settings_data["maxAttempts"] if "maxAttempts" in settings_data else None
next_attempt_delay = settings_data["nextAttemptDelay"] if "nextAttemptDelay" in settings_data else None

if not_specified_params:
    not_specified_params = not_specified_params.rstrip("\n")
    raise Exception("There are not enough parameters in the settings file:\n{}".format(not_specified_params))

with open('ihub_parameters.json', "rb") as SFile:
    ihub_data = json.loads(SFile.read().decode('utf-8'))

process_id = ihub_data['processId']
log_level = ihub_data['logLevel']

notification_service = SlackNotifService(service_id, process_id, ov_url, ov_access_key, ov_secret_key, log_level, channel_name_field,
                                            bot_token_in_slack, max_attempts, next_attempt_delay)
notification_service.start()
