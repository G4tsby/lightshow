from pydantic import BaseModel


class BaseLightTransition(BaseModel):
    light_idx: int
    gradient_points: list[str] # Hex color code
    duration: int
    brightness: int = 100
    
class Blink(BaseLightTransition):
    interval: int