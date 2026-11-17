import requests
import posthog

ENDPOINT = "https://analytics.example.test/collect"


def send(value):
    posthog.capture("page_view", value)
    return requests.get(ENDPOINT, timeout=2)
