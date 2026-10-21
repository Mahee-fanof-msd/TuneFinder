
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("CYANITE_API_TOKEN")

if not token:
    raise ValueError("CYANITE_API_TOKEN not found in .env")

url = "https://api.cyanite.ai/graphql"

query = """
query LibraryTracksQuery {
  libraryTracks(first: 10) {
    edges {
      node {
        id
      }
    }
  }
}
"""

response = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={"query": query},
    timeout=30
)

print("HTTP Status:", response.status_code)
print("Cyanite Response:", response.text)
