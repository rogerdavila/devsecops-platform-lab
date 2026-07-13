import asyncio
import signal

import uvicorn

from src.apps.internal import app as internal_app
from src.apps.public import app as public_app


async def serve() -> None:
    public_config = uvicorn.Config(
        public_app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True,
    )
    internal_config = uvicorn.Config(
        internal_app,
        host="0.0.0.0",
        port=9090,
        log_level="info",
        access_log=True,
    )

    public_server = uvicorn.Server(public_config)
    internal_server = uvicorn.Server(internal_config)

    # Disable uvicorn's per-server signal handlers; coordinate shutdown here
    # so SIGTERM stops both servers and triggers lifespan shutdown events.
    public_server.install_signal_handlers = lambda: None  # type: ignore[method-assign]
    internal_server.install_signal_handlers = lambda: None  # type: ignore[method-assign]

    loop = asyncio.get_event_loop()

    def _handle_shutdown() -> None:
        public_server.should_exit = True
        internal_server.should_exit = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_shutdown)

    await asyncio.gather(public_server.serve(), internal_server.serve())


if __name__ == "__main__":
    asyncio.run(serve())
