from typing import Optional, List
import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException
from starlette.middleware.cors import CORSMiddleware

import json
import asyncio
from time import sleep

from .tobii_pro_eye_tracker import TobiiProEyeTracker, GazePoint, tr

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


eyetracker: Optional[TobiiProEyeTracker] = None
connected_clients: List[WebSocket] = []
main_loop = None


def handle_gaze_data(gaze_point: GazePoint):
    broadcast_gaze_data(gaze_point)


def wait_for_device():
    global eyetracker

    while True:
        if eyetracker:
            break

        devices = tr.find_all_eyetrackers()
        if devices:
            eyetracker = TobiiProEyeTracker(devices[0])
            eyetracker.on_gaze_data = handle_gaze_data
            eyetracker.subscribe()

        sleep(1)


def broadcast_gaze_data(gaze_point: GazePoint):
    if not connected_clients or not main_loop:
        return

    message = json.dumps({"x": gaze_point.x, "y": gaze_point.y})
    disconnected_clients = []

    for client in connected_clients:
        try:
            print("Sending message to client:", message)
            asyncio.run_coroutine_threadsafe(client.send_text(message), main_loop)
        except Exception as e:
            print(f"Error sending to client: {e}")
            disconnected_clients.append(client)

    # Remove disconnected clients
    for client in disconnected_clients:
        connected_clients.remove(client)


@app.websocket("/eye_tracking")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print("Received:", data)
            await websocket.send_text('{"status": "ok"}')
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        await websocket.close()


@app.post("/calibration:start")
async def calibration_start():
    if not eyetracker:
        raise HTTPException(status_code=400, detail="CONNECT EYETRACKER FIRST")

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
    if not eyetracker:
        raise HTTPException(status_code=400, detail="CONNECT EYETRACKER FIRST")

    print("Collect:", point.x, point.y)

    if eyetracker.calibration.collect_data(point.x, point.y) == tr.CALIBRATION_STATUS_SUCCESS:
        return { "message": "ok" }
    else:
        return { "message": "failed" }


@app.post("/calibration:result")
async def calibration_result(force: bool = False):
    if not eyetracker:
        raise HTTPException(status_code=400, detail="CONNECT EYETRACKER FIRST")

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
    global main_loop
    main_loop = asyncio.get_event_loop()
    asyncio.create_task(asyncio.to_thread(wait_for_device))


@app.on_event("shutdown")
async def shutdown():
    if eyetracker:
        eyetracker.unsubscribe()


def start():
    uvicorn.run("src.app:app", port=8000, reload=True)
