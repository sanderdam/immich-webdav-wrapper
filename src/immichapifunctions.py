import requests
import logging
import time

def fetch_with_retries(url, api_key, max_retries=3):
        """Helper function to fetch data with retries."""
        headers = {'x-api-key': api_key}
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                #_logger.error(f"Error fetching {url} (attempt {attempt}/{max_retries}): {e}")
                time.sleep(2)
        return None  # Return None if all retries fail