from starlette.responses import JSONResponse


class RequestBoundary:
    """Cap streamed request bodies and prevent caching auth/PII responses."""

    def __init__(self, app, max_bytes=16384):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        messages = []
        size = 0
        limit = 131072 if scope["path"].startswith(("/api/v1/posts", "/api/v1/comments")) else self.max_bytes
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > limit:
                response = JSONResponse({"detail": "Request body too large"}, status_code=413,
                                        headers={"Cache-Control": "no-store"})
                return await response(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            return messages.pop(0) if messages else await receive()

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")])
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, replay, secure_send)
