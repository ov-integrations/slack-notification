import time
from abc import ABC, abstractmethod
from enum import Enum

from curl import Curl
from integration_log import IntegrationLog, LogLevel, HTTPBearerAuth


class NotificationService(ABC):

    def __init__(self, service_id, process_id, ov_url, ov_access_key, ov_secret_key, log_level, 
                max_attempts, next_attempt_delay):
        self._notif_queue_api = NotifQueueApi(service_id, ov_url, ov_access_key, ov_secret_key)
        self._max_attempts = max_attempts or 1
        self._next_attempt_delay = next_attempt_delay or 30
        self._integration_log = IntegrationLog(process_id, ov_url, ov_access_key, ov_secret_key, log_level, True)

    def start(self):
        self._integration_log.add(LogLevel.INFO, "Starting Integration")
        attempts = 0

        self._integration_log.add(LogLevel.INFO, "Receiving Notif Queue")
        notif_queue_json = self._notif_queue_api.get_notif_queue()
        self._integration_log.add(LogLevel.DEBUG, "Notif Queue json data", str(notif_queue_json))

        try:
            notif_queue = self._convert_notif_queue_json_to_list(notif_queue_json)
        except Exception as e:
            self._integration_log.add(LogLevel.ERROR, "Can't convert Notif Queue json data to list", str(e))
            raise Exception("Can't convert Notif Queue json data to list") from e

        prepared_notif_queue = []
        try:
            prepared_notif_queue = self._prepare_notif_queue(notif_queue)
        except Exception as e:
            self._integration_log.add(LogLevel.ERROR, "Can't prepare Notif Queue to send", str(e))
            raise Exception("Can't prepare Notif Queue to send") from e

        self._integration_log.add(LogLevel.INFO, "Notif Queue size: [{}]".format(len(prepared_notif_queue)))

        while len(prepared_notif_queue) > 0 and attempts < self._max_attempts:
            if attempts > 0:
                self._integration_log.add(LogLevel.INFO, "Attempt Number [{}]".format(attempts + 1))

            for notif_queue_rec in prepared_notif_queue:
                self._integration_log.add(LogLevel.INFO,
                                              "Sending Notif Queue Record with id = [{}]".format(
                                                  notif_queue_rec.notif_queue_id))
                notif_queue_rec.status = NotifQueueStatus.SENDING.name
                self._notif_queue_api.update_notif_queue_rec_status_by_object(notif_queue_rec)

                try:
                    self.send_notification(notif_queue_rec)
                except Exception as e:
                    self._notif_queue_api.add_new_attempt(notif_queue_rec.notif_queue_id, str(e))
                    self._integration_log.add(LogLevel.ERROR,
                                                  "Can't send Notif Queue Record with id = [{}]".format(
                                                      notif_queue_rec.notif_queue_id),
                                                  str(e))
                    if len(e.args) > 1:
                        time.sleep(int(e.args[1]))

                    if attempts + 1 == self._max_attempts:
                        notif_queue_rec.status = NotifQueueStatus.FAIL.name
                    else:
                        notif_queue_rec.status = NotifQueueStatus.FAIL_WILL_RETRY.name

                else:
                    notif_queue_rec.status = NotifQueueStatus.SUCCESS.name

                self._notif_queue_api.update_notif_queue_rec_status_by_object(notif_queue_rec)

            prepared_notif_queue = list(
                filter(lambda rec: rec.status != NotifQueueStatus.SUCCESS.name, prepared_notif_queue))
            attempts += 1

            if len(prepared_notif_queue) > 0 and self._max_attempts > attempts:
                self._integration_log.add(LogLevel.WARNING,
                                              "Can't send [{0}] notifications. Next try in [{1}] seconds".format(
                                                  len(prepared_notif_queue),
                                                  self._next_attempt_delay))
                time.sleep(self._next_attempt_delay)

        if len(prepared_notif_queue) > 0:
            self._integration_log.add(LogLevel.ERROR,
                                          "Can't send [{}] notifications. All attempts have been exhausted.".format(
                                              len(prepared_notif_queue)))

        self._integration_log.add(LogLevel.INFO, "Integration has been completed")

    @staticmethod
    def _convert_notif_queue_json_to_list(json_data):
        notif_queue = []
        for json_obj in json_data:
            notif_queue.append(NotifQueueRecord(json_obj))
        return notif_queue

    @abstractmethod
    def send_notification(self, notif_queue_record):
        pass

    def _prepare_notif_queue(self, notif_queue):
        return notif_queue


class NotifQueueApi:
    def __init__(self, service_id, url, ov_access_key, ov_secret_key):
        self._service_id = service_id
        self._url = url
        self._auth = HTTPBearerAuth(ov_access_key, ov_secret_key)
        self._headers = {'content-type': 'application/json'}

    def get_notif_queue(self):
        url = self._url + "/api/internal/notif/queue?service_id=" + str(self._service_id)
        curl = Curl('GET', url, headers=self._headers, auth=self._auth)
        if len(curl.errors) > 0:
            raise Exception(curl.errors)
        return curl.jsonData

    def update_notif_queue_rec_status(self, notif_queue_rec_id, status):
        url = self._url + "/api/internal/notif/queue/" + str(notif_queue_rec_id) + "/update_status?status=" + status
        curl = Curl('PATCH', url, headers=self._headers, auth=self._auth)
        if len(curl.errors) > 0:
            raise Exception(curl.errors)

    def add_new_attempt(self, notif_queue_rec_id, error_message):
        url = self._url + "/api/internal/notif/queue/" + str(
            notif_queue_rec_id) + "/attempts?error_code=" + error_message
        curl = Curl('POST', url, headers=self._headers, auth=self._auth)
        if len(curl.errors) > 0:
            raise Exception(curl.errors)

    def update_notif_queue_rec_status_by_object(self, notif_queue_rec):
        self.update_notif_queue_rec_status(notif_queue_rec.notif_queue_id, notif_queue_rec.status)


class NotifQueueRecord:

    def __init__(self, json_object):
        self.notif_queue_id = json_object['notifQueueId']
        self.user_id = json_object['userId']
        self.sender = json_object['sender']
        self.to_address = json_object['toAddress']
        self.cc = json_object['cc']
        self.bcc = json_object['bcc']
        self.subj = json_object['subj']
        self.reply_to = json_object['replyTo']
        self.created_ts = json_object['createdTs']
        self.status = json_object['status']
        self.msg = json_object['msg']
        self.html = json_object['html']
        self.blob_data_ids = json_object['blobDataIds']


class NotifQueueStatus(Enum):
    BUILDING = 0
    NOT_SENT = 1
    SENDING = 2
    FAIL_WILL_RETRY = 3
    FAIL = 4
    SUCCESS = 5
