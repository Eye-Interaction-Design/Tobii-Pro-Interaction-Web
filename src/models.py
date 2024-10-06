from pydantic import BaseModel

from typing import Dict, Optional
from math import isnan


def _nan_to_none(value):
    return None if isnan(value) else value


class EyePosition(BaseModel):
    x: float
    y: float
    z: float

    @property
    def is_valid(self) -> bool:
        return not (isnan(self.x) or isnan(self.y) or isnan(self.z))

    def to_dict(self) -> Dict[str, Optional[float]]:
        return {"x": _nan_to_none(self.x), "y": _nan_to_none(self.y), "z": _nan_to_none(self.z)}


class GazePoint(BaseModel):
    x: float
    y: float

    @property
    def is_valid(self) -> bool:
        return not (isnan(self.x) or isnan(self.y))

    def to_dict(self) -> Dict[str, Optional[float]]:
        return {"x": _nan_to_none(self.x), "y": _nan_to_none(self.y)}

