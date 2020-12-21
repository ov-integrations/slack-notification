This is the Rule that creates a Notification for the User who has the Slack Channel field filled.
The configured integration will view this Notification and send a message to Slack, to the channel specified in the Slack Channel field.


# Requirements
*The components required for the integration to work are installed. [More details.]()
*Integration configured. [More details.](https://github.com/ov-integrations/slack-notification)

# Installation 

1. Import components. Select all components to import.
2. After import, you need to open the 'Send Notification for Slack Integration' rule.
3. On the PL/SQL Tab, replace the values ​​of the variables:
	* v_program_id
	* v_service_name - Notification Service name, созданного во время настройки интеграции
	* v_channel_field_name - это channelField в settings.json
	![picture](img/plsqlTab.png)
4. Enable Rule.
