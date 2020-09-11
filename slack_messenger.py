import time
import datetime

from slack import WebClient
from slack.errors import SlackApiError

from integration_log import LogLevel


class Slack:

    def __init__(self, bot_token_in_slack):
        self._client = WebClient(token=bot_token_in_slack)
        self._channels = []

    def send_message(self, message, integration_log):
        channel = next((channel for channel in self._channels if channel.get_name() == message.channel), None)
        if not channel:
            channel = SlackChannel(message.channel)
            self._channels.append(channel)

        message_text = Slack.format_message(message)
        channel.delay_sending_messages()
        integration_log.add(LogLevel.INFO,
                                    "Sending message to [{}] Slack channel".format(channel.get_name()),
                                    "Message Text: [{}]".format(message_text))
        try:
            response = self._client.chat_postMessage(channel=channel.get_name(), text=message_text)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                delay = int(e.response.headers['Retry-After'])
                integration_log.add(LogLevel.WARNING,
                                    "Warning when sending message to Slack. Rate limited. Execution will continue in {} seconds.".format(delay),
                                    "Channel: [{0}]\nMessage Text: [{1}]".format(message.channel, message_text))
                time.sleep(delay)
                response = self._client.chat_postMessage(channel=message.channel, text=message_text)
            else:
                raise e

        channel.set_datetime_of_last_sent_message()


    @staticmethod
    def format_message(message):
        attachments = ""
        for blob_id in message.blob_data_ids:
            attachments = attachments + "\n" + message.ov_url + "/efiles/EFileGetBlobFromDb.do?id=" + str(blob_id)

        msg = message.subj + "\n" + message.body + "\n" + message.ov_url.replace("https://", "")
        if len(attachments) > 0:
            msg = msg + "\nAttachments:" + attachments
        
        return msg


class SlackChannel:
    DELAY_SENDING_MESSAGE = 1
    
    def __init__(self, channel):
        self._channel_name = channel
        self._datetime_of_last_sent_message = datetime.datetime.min

    def get_name(self):
        return self._channel_name

    def set_datetime_of_last_sent_message(self):
        self._datetime_of_last_sent_message = datetime.datetime.now()

    def delay_sending_messages(self):
        if (datetime.datetime.now() - self._datetime_of_last_sent_message).total_seconds() < SlackChannel.DELAY_SENDING_MESSAGE:
            time.sleep(SlackChannel.DELAY_SENDING_MESSAGE)


class SlackMessage:

    def __init__(self, notif_queue_record, ov_url):
        self.channel = notif_queue_record.channel
        self.subj = notif_queue_record.subj
        self.body = notif_queue_record.msg
        self.blob_data_ids = notif_queue_record.blob_data_ids
        self.ov_url = ov_url