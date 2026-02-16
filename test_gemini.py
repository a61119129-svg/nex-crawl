#!/usr/bin/env python3
"""Quick test of Gemini API key."""
import urllib.request
import json
import sys

API_KEY = "AIzaSyA9cLV0wxElzckCefQLPYTOgXJzBd4DiwU"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

data = json.dumps({
    "contents": [{"parts": [{"text": "Say hello in one word"}]}]
}).encode()

req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})

try:
    resp = urllib.request.urlopen(req)
    body = resp.read().decode()
    print("SUCCESS:", body[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}: {e.reason}")
    print(e.read().decode()[:500])
except Exception as e:
    print(f"ERROR: {e}")
