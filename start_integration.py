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

ov_url = settings_data["ovUrl"]
ov_access_key = settings_data["ovAccessKey"]
ov_secret_key = settings_data["ovSecretKey"]
service_id = settings_data["serviceId"]
channel_field = settings_data["channelField"]
bot_token_in_slack = settings_data["slackBotToken"]

max_attempts = settings_data["maxAttempts"] if "maxAttempts" in settings_data else None
next_attempt_delay = settings_data["nextAttemptDelay"] if "nextAttemptDelay" in settings_data else None

with open('ihub_parameters.json', "rb") as SFile:
    ihub_data = json.loads(SFile.read().decode('utf-8'))

process_id = ihub_data['processId']
log_level = ihub_data['logLevel']

notification_service = SlackNotifService(service_id, process_id, ov_url, ov_access_key, ov_secret_key, log_level, channel_field,
                                            bot_token_in_slack, max_attempts, next_attempt_delay)
notification_service.start()
