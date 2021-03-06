# Slack-notification

Processes the OneVizion notification queue to send messages to the [Slack](https://slack.com/intl/en-ru/help/articles/115004071768-What-is-Slack-) channel specified in the User trackor.

## Requirements
- Python 3.6 and above
- Requests - [library for python](https://requests.readthedocs.io/en/master/)
- slackclient - [Slack Developer Kit for Python](https://slack.dev/python-slackclient/)
- jsonschema - [Implementation of JSON Schema for Python](https://python-jsonschema.readthedocs.io/en/stable/)

## Slack Configuration
1. Log into Slack.
2. Create an app. Notifications from OneVizion to Slack will be sent on behalf of this application. [Basic app setup](https://api.slack.com/authentication/basics)
- Required Bot Token Scopes:
  * chat:write
  * chat:write.public

- Further, for the integration to work (sending messages to Slack), Bot User OAuth Access Token will be required.

## Usage
1. On a Trackor type that is checked as 'Is OneVizion User', add a field that will store the name or id of the Slack channel. The integration will send notifications to this Slack channel for the user.
2. Create a new [Notification Service](https://onevizion.atlassian.net/wiki/spaces/USER/pages/280363093/Notification+and+Rule+Services) in OneVizion. All settings of this service are ignored by Integration, use random values for required fields.
3. Install this integration. This can be done on the [Integration Hub](https://onevizion.atlassian.net/wiki/spaces/USER/pages/279642117/Integration+Hub) page.
4. Create dedicated account for integration with following privs:
    * WEB_SERVICES R
    * ADMIN_NOTIF_QUEUE RE
    * ADMIN_USERS R
    * ADMIN_INTEGRATION_LOG RA
    * \<User Trackor Type\> R
    * \<User Trackor Type Tab containing channelField\> R
5. Create an "API" security token for the account created on step 4
6. Fill the integration settings file
    - ovUrl - OneVizion URL
    - ovAccessKey - OneVizion API Security Token Access Key
    - ovSecretKey - OneVizion API Security Token Secret Key
    - serviceId - ID of the Notification Service createf at step 2
    - channelField - The name of the field which contains the Slack channel of the recipient. Recipient is a user trackor related with User ID from the Notif Queue record.
    - slackBotToken - Bot User OAuth Access Token
    - maxAttempts - The number of attempts to send message. The parameter is optional, it can be omitted from the settings file. The default will be 1
    - nextAttemptDelay - The delay in seconds before the next message sending after an unsuccessful attempt. The parameter is optional, it can be omitted from the settings file. The default will be 30.
7. Enable the integration

To create Slack notifications select newly created Notification Service in "Notif Service" drop-down on [Notification](https://onevizion.atlassian.net/wiki/spaces/USER/pages/279609506/Notifications) admin form. OneVizion URL is automatically added to the end of the message for clarity.

Example of settings.json

```json
{
    "ovUrl": "https://test.onevizion.com",
    "ovAccessKey": "*****",
    "ovSecretKey": "*****",
    "serviceId" : 1000043,
    "channelField" : "U_CHANNEL",
    "slackBotToken" : "*****",
    "maxAttempts" : 1,
    "nextAttemptDelay" : 30
}
```