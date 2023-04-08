import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch
from opensearchpy.plugins.alerting import AlertingClient
from helper import create_slack_destination, create_monitor

load_dotenv()

# Load environment variables
host = os.getenv('HOST')
port = os.getenv('PORT')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
webhook_url = os.getenv('WEBHOOK_URL')
indices = os.getenv('INDICES').split(",")

# Initialize OpenSearch client
client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_compress=True,
    http_auth=(username, password),
    use_ssl=True,
    verify_certs=True,
    ssl_assert_hostname=False,
    ssl_show_warn=False
)

# Initialize Alerting client
alerting_client = AlertingClient(client)

# Create Slack destination and monitor
destination_id = create_slack_destination(alerting_client, "slack_destination", webhook_url)
error_monitor_id = create_monitor(alerting_client, "error_monitor", indices, destination_id, "error")
fatal_monitor_id = create_monitor(alerting_client, "fatal_monitor", indices, destination_id, "fatal")