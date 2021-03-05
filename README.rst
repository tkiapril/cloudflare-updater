CloudFlare DNS Updater
----------------------

A software to update the CloudFlare DNS records automatically.

Refer to config.yaml.example and create your config.yaml file. It is strongly recommended to set the file permissions
to 0600 to prevent unauthorized users from accessing your API token, which can be used to alter your DNS records.

You can use timers such as systemd timers or cron to regulary update your DNS records.
