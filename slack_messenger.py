import time
import datetime

from slack import WebClient
from slack.errors import SlackApiError

from integration_log import LogLevel


class Slack:

    def __init__(self, bot_token_in_slack):
        self._client = WebClient(token=bot_token_in_slack)
        self._channels = []

    def send_message(self, message_data, integration_log):
        channel = next((channel for channel in self._channels if channel.get_name() == message_data["channel"]), None)
        if not channel:
            channel = Channel(message_data["channel"])
            self._channels.append(channel)

        msg = Slack.format_message(message_data)
        channel.delay_sending_messages()
        integration_log.add(LogLevel.INFO,
                                    "Sending message to [{}] Slack channel".format(channel.get_name()),
                                    "Message Text: [{}]".format(msg))
        try:
            response = self._client.chat_postMessage(channel=channel.get_name(), text=msg)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                delay = int(e.response.headers['Retry-After'])
                integration_log.add(LogLevel.WARNING,
                                    "Warning when sending message to Slack. Rate limited. Execution will continue in {} seconds.".format(delay),
                                    "Channel: [{0}]\nMessage Text: [{1}]".format(message_data["channel"], msg))
                time.sleep(delay)
                response = self._client.chat_postMessage(channel=message_data["channel"], text=msg)
            else:
                raise e

        channel.set_datetime_of_last_sent_message()


    @staticmethod
    def format_message(message_data):
        attachments = ""
        for blob_id in message_data["blob_data_ids"]:
            attachments = attachments + "\n" + message_data["ov_url"] + "/efiles/EFileGetBlobFromDb.do?id=" + str(blob_id)

        msg = message_data["subj"] + "\n" + message_data["msg"] + "\n" + message_data["ov_url"].replace("https://", "")
        if len(attachments) > 0:
            msg = msg + "\nAttachments:" + attachments
        
        return msg


class Channel:
    DELAY_SENDING_MESSAGE = 1
    
    def __init__(self, channel):
        self._channel_name = channel

    def get_name(self):
        return self._channel_name

    def set_datetime_of_last_sent_message(self):
        self._datetime_of_last_sent_message = datetime.datetime.now()

    def delay_sending_messages(self):
        if (hasattr(self, "_datetime_of_last_sent_message") and 
                (datetime.datetime.now() - self._datetime_of_last_sent_message).total_seconds() < Channel.DELAY_SENDING_MESSAGE):
            time.sleep(Channel.DELAY_SENDING_MESSAGE)