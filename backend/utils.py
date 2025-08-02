import re
import os
import numpy as np

from dotenv import load_dotenv
from aiohue.v2.models.light import LightPut
from aiohue.v2.models.feature import (
    DimmingFeaturePut,
    GradientFeatureBase,
    GradientPoint,
    ColorFeaturePut,
    ColorPoint,
    DynamicsFeaturePut
)

load_dotenv()
APPKEY = os.getenv("APPKEY")
BRIDGE_IP = os.getenv("BRIDGE_IP")


def rgb_to_xy(color_input: tuple | str) -> tuple[float, float]:
    """
    RGB 튜플이나 hex 코드를 CIE XY 좌표로 변환합니다.
    
    Args:
        color_input: RGB 튜플 (r, g, b) 또는 hex 문자열 ("#RRGGBB" 또는 "RRGGBB")
        
    Returns:
        tuple: (x, y) CIE 좌표
    """
    def hex_to_rgb(hex_color):
        """
        hex 색상 코드를 RGB 튜플로 변환합니다.
        
        Args:
            hex_color: hex 문자열 ("#RRGGBB" 또는 "RRGGBB")
            
        Returns:
            tuple: (r, g, b) RGB 값
        """
        # # 제거하고 대문자로 변환
        hex_color = hex_color.lstrip('#').upper()
        
        # 유효한 hex 코드인지 확인
        if not re.match(r'^[0-9A-F]{6}$', hex_color):
            raise ValueError("유효하지 않은 hex 색상 코드입니다.")
        
        # hex를 RGB로 변환
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    
        return r, g, b
    
    # 입력값이 문자열인 경우 (hex 코드)
    if isinstance(color_input, str):
        rgb = hex_to_rgb(color_input)
    # 입력값이 튜플/리스트인 경우
    elif isinstance(color_input, (tuple, list)) and len(color_input) == 3:
        rgb = color_input
    else:
        raise ValueError("입력값은 RGB 튜플 (r, g, b) 또는 hex 문자열이어야 합니다.")
    
    # RGB 값을 0-1 범위로 정규화
    r, g, b = [val / 255.0 for val in rgb]
    
    # 감마 보정 (sRGB → Linear RGB)
    def gamma_correction(val):
        if val <= 0.04045:
            return val / 12.92
        else:
            return ((val + 0.055) / 1.055) ** 2.4
    
    r_linear = gamma_correction(r)
    g_linear = gamma_correction(g)
    b_linear = gamma_correction(b)
    
    # sRGB to XYZ 변환 행렬 (D65 illuminant)
    # 행렬은 ITU-R BT.709 표준 기반
    transform_matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])
    
    # Linear RGB를 XYZ로 변환
    rgb_linear = np.array([r_linear, g_linear, b_linear])
    xyz = np.dot(transform_matrix, rgb_linear)
    
    X, Y, Z = xyz
    
    # XYZ를 xy 좌표로 변환
    # 분모가 0인 경우를 방지
    denominator = X + Y + Z
    if denominator == 0:
        # 검은색인 경우, 검은색 좌표 반환 (색상 없음)
        x, y = 0.0, 0.0
    else:
        x = X / denominator
        y = Y / denominator
    
    return round(x, 4), round(y, 4)


def create_gradient_lightput(gradient_points: list[str],
                  duration: int,
                  brightness: int) -> LightPut:
    cie_points = [rgb_to_xy(point) for point in gradient_points]
    gradint_arr = []
    for x, y in cie_points:
        gradint_arr.append(GradientPoint(color=ColorFeaturePut(xy=ColorPoint(x, y))))
    return LightPut(
        gradient=GradientFeatureBase(points=gradint_arr),
        dynamics=DynamicsFeaturePut(duration=duration),
        dimming=DimmingFeaturePut(brightness=brightness)
    )