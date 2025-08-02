import time
import requests

# Test file for pytest
URL = "http://localhost:8000"

def test_fade_in_out():
    requests.post(f"{URL}/on/1")
    requests.post(f"{URL}/template/base_light_transition", json={
        "light_idx": 1,
        "duration": 2000,
        "gradient_points": ["0000ff"] * 5,
        "brightness": 100
    })
    time.sleep(1)
    requests.post(f"{URL}/template/base_light_transition", json={
        "light_idx": 1,
        "duration": 1000,
        "gradient_points": ["0000ff"] * 5,
        "brightness": 0
    })
    
def test_blink():
    requests.post(f"{URL}/on/1")
    requests.post(f"{URL}/template/blink", json={
        "light_idx": 1,
        "duration": int(1/2/16*1000*16),
        "gradient_points": ["ff0000"] * 5,
        "interval": int(1/2/16*1000)
    })
    time.sleep(1)
    requests.post(f"{URL}/off/1")