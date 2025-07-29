import os
import asyncio

import uvicorn
from fastapi import FastAPI, HTTPException

from dotenv import load_dotenv
from aiohue import HueBridgeV2
from aiohue.v2.models.light import LightPut
from aiohue.v2.models.feature import (
    GradientFeatureBase,
    GradientPoint,
    ColorFeaturePut,
    ColorPoint,
    DynamicsFeaturePut
)
from model import BaseLightTransition, Blink
from utils import rgb_to_xy


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
    
    cie_points = [rgb_to_xy(point) for point in transition.gradient_points]
    
    async with HueBridgeV2(BRIDGE_IP, APPKEY) as bridge:
        gradient_points = []
        for x, y in cie_points:
            gradient_points.append(GradientPoint(color=ColorFeaturePut(xy=ColorPoint(x, y))))
        light_update = LightPut(
            gradient=GradientFeatureBase(points=gradient_points),
            dynamics=DynamicsFeaturePut(duration=transition.duration)
        )
        await bridge.lights.update(light_ids[transition.light_idx], light_update)
        
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