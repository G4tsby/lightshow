import os
import asyncio

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.logger import logger

from dotenv import load_dotenv
from aiohue import HueBridgeV2
from model import BaseLightTransition, Blink
from utils import create_gradient_lightput


# Load env
load_dotenv()

APPKEY = os.getenv("APPKEY")
BRIDGE_IP = os.getenv("BRIDGE_IP")
light_ids = [os.getenv("LEFT_LIGHT_ID"), os.getenv("RIGHT_LIGHT_ID")]

app = FastAPI()


@app.post("/template/base_light_transition")
async def base_light_transition(transition: BaseLightTransition):
    if len(transition.gradient_points) != 5:
        raise HTTPException(status_code=400, detail="Gradient points must be 5")

    async with HueBridgeV2(BRIDGE_IP, APPKEY) as bridge:
        light_update = create_gradient_lightput(
            transition.gradient_points, transition.duration, transition.brightness
        )
        await bridge.lights.update(light_ids[transition.light_idx], light_update)


@app.post("/template/blink")
async def blink(transition: Blink):
    async with HueBridgeV2(BRIDGE_IP, APPKEY) as bridge:
        bright_state = create_gradient_lightput(
            transition.gradient_points, duration=0, brightness=transition.brightness
        )
        dim_state = create_gradient_lightput(
            transition.gradient_points, duration=0, brightness=0
        )

        for i in range(transition.duration // transition.interval):
            await bridge.lights.update(light_ids[transition.light_idx], bright_state)
            logger.info(f"on {i}")
            await asyncio.sleep(transition.interval / 1000)
            await bridge.lights.update(light_ids[transition.light_idx], dim_state)
            logger.info(f"off {i}")
            await asyncio.sleep(transition.interval / 1000)


@app.post("/off/{light_idx}")
async def off(light_idx: int):
    if light_idx < 0 or light_idx > len(light_ids):
        raise HTTPException(status_code=400, detail="Light index out of range")

    async with HueBridgeV2(BRIDGE_IP, APPKEY) as bridge:
        await bridge.lights.turn_off(light_ids[light_idx])


@app.post("/on/{light_idx}")
async def on(light_idx: int):
    if light_idx < 0 or light_idx > len(light_ids):
        raise HTTPException(status_code=400, detail="Light index out of range")

    async with HueBridgeV2(BRIDGE_IP, APPKEY) as bridge:
        await bridge.lights.turn_on(light_ids[light_idx])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
