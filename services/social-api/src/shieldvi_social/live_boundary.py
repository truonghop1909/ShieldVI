"""Route-specific upload/message budgets for the opt-in factory only."""
from .middleware import RequestBoundary
class LiveRequestBoundary(RequestBoundary):
    async def __call__(self,scope,receive,send):
        path=scope.get('path','')
        if path=='/api/studio/datasets':return await RequestBoundary(self.app,max_bytes=2097152)(scope,receive,send)
        if path=='/api/live/moderator/test-conversations':return await RequestBoundary(self.app,max_bytes=131072)(scope,receive,send)
        if path.startswith('/api/live/threads/') and path.endswith('/messages'):return await RequestBoundary(self.app,max_bytes=131072)(scope,receive,send)
        return await super().__call__(scope,receive,send)
