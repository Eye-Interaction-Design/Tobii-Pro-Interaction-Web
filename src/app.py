import uvicorn
from fastapi import FastAPI, WebSocket
from starlette.middleware.cors import CORSMiddleware

import json
import asyncio

from .eye_tracker import EyeTracker, GazePoint, tr

eyetracker = EyeTracker()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


async def send_gaze_point(websocket: WebSocket):
    while True:
        await asyncio.sleep(1 / 60)
        await websocket.send_text(json.dumps({ "x": eyetracker.gaze_point.x, "y": eyetracker.gaze_point.y }))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    asyncio.create_task(send_gaze_point(websocket))

    try:
        while True:
            data = await websocket.receive_text()
            print("Received:", data)
            await websocket.send_text('{"status": "ok"}')
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


@app.post("/calibration:start")
async def calibration_start():
    if not eyetracker.calibration:
        return { "message": "eyetracker not found" }

    try:
        eyetracker.calibration.enter_calibration_mode()

        return { "message": "ok" }
    except tr.EyeTrackerInvalidOperationError:
        print("Already calibration? leaved.")
        eyetracker.calibration.leave_calibration_mode()
        eyetracker.calibration.enter_calibration_mode()

        return { "message": "ok" }


@app.post("/calibration:collect")
async def calibration_collect(point: GazePoint):
    if not eyetracker.calibration:
        return { "message": "eyetracker not found" }

    print("Collect:", point.x, point.y)

    if eyetracker.calibration.collect_data(point.x, point.y) == tr.CALIBRATION_STATUS_SUCCESS:
        return { "message": "ok" }
    else:
        return { "message": "failed" }


@app.post("/calibration:result")
async def calibration_result(force: bool = False):
    if not eyetracker.calibration:
        return { "message": "eyetracker not found" }

    calibration_result = eyetracker.calibration.compute_and_apply()

    # print calibration result
    print(calibration_result.status, len(calibration_result.calibration_points))
    for point in calibration_result.calibration_points:
        print(point.position_on_display_area, ":")
        for sample in point.calibration_samples:
            print(sample.left_eye.position_on_display_area, sample.right_eye.position_on_display_area)

    if force or calibration_result.status == tr.CALIBRATION_STATUS_SUCCESS:
        eyetracker.calibration.leave_calibration_mode()

        return { "message": "ok" }
    else:
        recalibration_points = []
        for recalibrate_point in recalibration_points:
            eyetracker.calibration.discard_data(recalibrate_point[0], recalibrate_point[1])

        return { "message": "failed", "recalibrate": recalibration_points }


@app.on_event("startup")
async def startup():
    eyetracker.subscribe()


@app.on_event("shutdown")
async def shutdown():
    eyetracker.unsubscribe()


def start():
    uvicorn.run("src.app:app", port=8000, reload=True)
