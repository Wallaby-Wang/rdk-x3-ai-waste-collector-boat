from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from time import sleep
from typing import Iterator

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse

from .config import AppConfig, load_config
from .runtime import BoatRuntime


def create_app(config: AppConfig | None = None, autostart: bool = True) -> FastAPI:
    config = config or load_config()
    runtime = BoatRuntime(config)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if autostart:
            runtime.start()
        try:
            yield
        finally:
            runtime.stop()

    app = FastAPI(
        title="Laker RDK X3 AI Waste Collector Boat",
        description="RDK X3 vision, YOLO detection, visual servo control and ESP32-S3 motor bridge.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.runtime = runtime
    app.state.config = config

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        ui_path = Path(config.server.ui_path)
        html = ui_path.read_text(encoding="utf-8")
        injected = (
            '<script>window.LeftDashboard&&window.LeftDashboard.configure({'
            'statusUrl:"/api/status",streamUrl:"/stream.mjpg",logoSrc:"/Logo.png",'
            f"pollMs:{int(config.server.poll_ms)}"
            "});</script>"
        )
        if "</body>" in html:
            html = html.replace("</body>", injected + "\n</body>")
        else:
            html += injected
        return HTMLResponse(html)

    @app.get("/Logo.png")
    def logo() -> FileResponse:
        return FileResponse(Path(config.server.logo_path), media_type="image/png")

    @app.get("/api/status")
    def status() -> JSONResponse:
        return JSONResponse(runtime.get_status())

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "state": runtime.get_status()["navigation"]["state"]}

    @app.post("/api/control/stop")
    def stop_boat() -> dict[str, str]:
        runtime.emergency_stop()
        return {"status": "stopped"}

    @app.get("/stream.mjpg")
    def stream() -> StreamingResponse:
        return StreamingResponse(_mjpeg(runtime), media_type="multipart/x-mixed-replace; boundary=frame")

    return app


def _mjpeg(runtime: BoatRuntime) -> Iterator[bytes]:
    while True:
        frame = runtime.get_latest_jpeg()
        yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(frame)).encode("ascii")
        yield b"\r\n\r\n" + frame + b"\r\n"
        sleep(0.05)


def app_from_config_path(path: str | None = None) -> FastAPI:
    return create_app(load_config(path))
