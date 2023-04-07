def search_destination(alerting_client, name):
    try:
        # Get all destinations
        response = alerting_client.get_destination()
        # Find the destination with the given name
        find_destination = next((x for x in response['destinations'] if x['name'] == name), None)
        # Return the ID of the destination, if found
        return find_destination['id'] if find_destination else ''
    except:
        # Log the error and return an empty string
        print(f"Error searching destination {name!r}")
        return ''


def create_slack_destination(alerting_client, name, webhook_url):
    # Define the destination object with the given name and Slack webhook URL
    destination = {
        "name": name,
        "type": "slack",
        "slack": {
            "url": webhook_url
        }
    }
    # Check if a destination with the given name already exists
    destination_id = search_destination(alerting_client, name)
    if destination_id:
        # If a destination already exists, log a message and return its ID
        print(f"Destination {name!r} already exists, ID: {destination_id!r}")
        return destination_id
    try:
        # If the destination doesn't exist, create it and return its ID
        response = alerting_client.create_destination(destination)
        destination_id = response['_id']
        print(f"Successfully created destination {destination_id}")
        return destination_id
    except:
        # Log the error and return an empty string
        print(f"Error creating destination {name!r}")
        return ''


def search_monitor(alerting_client, name):
    try:
        # Search for a monitor with the given name
        response = alerting_client.search_monitor({
            "query": {
                "match": {
                    "monitor.name": name
                }
            }
        })
        # Return the ID of the first matching monitor, if found
        return response['hits']['hits'][0]['_id'] if response['hits']['hits'] else ''
    except:
        # Log the error and return an empty string
        print(f"Error searching monitor {name!r}")
        return ''


def create_monitor(alerting_client, name, indices, error_count, destination_id):
    # Check if a monitor with the same name already exists
    monitor_id = search_monitor(alerting_client, name)

    # Define the search query to be used in the monitor
    search_query = {
        "indices": indices,
        "query": {
            "size": 0,
            "aggregations": {},
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": "{{period_end}}||-5m",
                                    "lte": "{{period_end}}",
                                    "format": "epoch_millis"
                                }
                            }
                        },
                        {"match_phrase": {"log": "\"level=error\""}}
                    ]
                }
            }
        }
    }

    # Define the monitor object with the specified name, search query, and alert trigger
    monitor = {
        "name": name,
        "type": "monitor",
        "monitor_type": "query_level_monitor",
        "schedule": {"period": {"interval": 5, "unit": "MINUTES"}},
        "inputs": [{"search": search_query}],
        "triggers": [
            {
                "name": "error_trigger",
                "severity": "3",
                "condition": {
                    "script": {
                        "source": f"ctx.results[0].hits.total.value > {error_count}",
                        "lang": "painless"
                    }
                },
                "actions": [
                    {
                        "name": "slack_destination",
                        "destination_id": destination_id,
                        "subject_template": {"lang": "mustache", "source": "error > 1 in 5 minutes"},
                        "message_template": {
                            "lang": "mustache",
                            "source": "Monitor {{ctx.monitor.name}} just entered alert status. Please investigate the issue.\n  - Trigger: {{ctx.trigger.name}}\n  - Severity: {{ctx.trigger.severity}}\n  - Period start: {{ctx.periodStart}}\n  - Period end: {{ctx.periodEnd}}"
                        },
                        "throttle_enabled": "true",
                        "throttle": {"value": 10, "unit": "MINUTES"}
                    }
                ]
            }
        ]
    }

    if not monitor_id:
        response = alerting_client.create_monitor(monitor)
        id = response['_id']
        print(f'Successfully created monitor {id}')
        return id
    else:
        print(f'Monitor {name!r} already exist, id: {monitor_id!r}')
