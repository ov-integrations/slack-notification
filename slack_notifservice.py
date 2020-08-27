from slack import WebClient

from curl import Curl
from integration_log import LogLevel, HTTPBearerAuth
from notifservice import NotificationService


class SlackNotifService(NotificationService):

    def __init__(self, service_id, process_id, ov_url, ov_access_key, ov_secret_key, log_level, 
                channel_field_name, bot_token_in_slack, max_attempts, next_attempt_delay):
        super().__init__(service_id, process_id, ov_url, ov_access_key, ov_secret_key, log_level, max_attempts, next_attempt_delay)
        
        self._channel_field_name = channel_field_name
        self._user_trackor = UserTrackor(ov_url, ov_access_key, ov_secret_key)
        self._url = ov_url
        self._client = WebClient(token=bot_token_in_slack)

    def send_notification(self, notif_queue_record):
        if not (hasattr(notif_queue_record, 'channel')) or notif_queue_record.channel is None:
            raise Exception("Notif Queue Record with ID [{}] has no channel".format(notif_queue_record.notif_queue_id))

        msg = self.message_formation(notif_queue_record)

        self._integration_log.add(LogLevel.INFO,
                                      "Sending message to [{}] Slack channel".format(notif_queue_record.channel),
                                      "Message Text: [{}]".format(msg))

        #Send your message to Slack.
        try:
            response = self._client.chat_postMessage(channel=notif_queue_record.channel, text=msg)
        except Exception as e:
            raise Exception('Error when sending message to Slack.Error: [{}]'.format(str(e)))
    
    def message_formation(self, notif_queue_record):
        attachments = ""
        for blob_id in notif_queue_record.blob_data_ids:
            attachments = attachments + self._url + "/efiles/EFileGetBlobFromDb.do?id=" + str(blob_id) + " "

        msg = notif_queue_record.subj + "\n" + notif_queue_record.msg + "\n" + self._url.replace("https://", "")
        if len(attachments) > 0:
            msg = msg + " " + "Attachments: " + attachments
        
        return msg

    def _prepare_notif_queue(self, notif_queue):
        user_ids = list(map(lambda rec: rec.user_id, notif_queue))
        if None in user_ids:
            for notif_queue_rec in notif_queue:
                if notif_queue_rec.user_id is None:
                    self._integration_log.add(LogLevel.ERROR,
                                                "Notif Queue Record doesn't have User ID. Notif Queue ID: [{}]".format(
                                                    str(notif_queue_rec.notif_queue_id)))
            user_ids = [user_id for user_id in user_ids if user_id]

        if len(user_ids) > 0:
            users = self._user_trackor.get_users_by_ids(user_ids)

            for notif_queue_rec in notif_queue:
                for user in users:
                    tid = user["trackorId"]
                    if notif_queue_rec.user_id == user["userId"]:
                        notif_queue_rec.trackor_id = tid
                        try:
                            notif_queue_rec.channel = self._user_trackor.get_channel_by_field_name_and_trackor_id(
                                self._channel_field_name,
                                tid)
                        except Exception as e:
                            self._integration_log.add(LogLevel.ERROR,
                                                        "Can't get Slack channel from User Trackor. Notif Queue ID = [{}]".format(
                                                            str(notif_queue_rec.notif_queue_id)),
                                                        str(e))

        return notif_queue

class UserTrackor:

    def __init__(self, url, access_key, secret_key):
        self._url = url
        self._auth = HTTPBearerAuth(access_key, secret_key)
        self._headers = {'content-type': 'application/json'}

    def get_channel_by_field_name_and_trackor_id(self, field_name, tid):
        url = self._url + "/api/v3/trackors/" + str(tid) + "?fields=" + field_name
        curl = Curl('GET', url, headers=self._headers, auth=self._auth)
        if len(curl.errors) > 0:
            raise Exception(curl.errors)
        return curl.jsonData[field_name]

    def get_users_by_ids(self, user_ids):
        user_ids = list(set(user_ids))
        url = self._url + "/api/internal/users?user_ids="
        url = url + ','.join([str(user_id) for user_id in user_ids])

        curl = Curl('GET', url, headers=self._headers, auth=self._auth)
        if len(curl.errors) > 0:
            raise Exception(curl.errors)
        return curl.jsonData
