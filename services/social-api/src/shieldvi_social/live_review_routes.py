"""Staff clarification is an audited note, never an automatic visibility change."""
import time
from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,Request,HTTPException
from .dependencies import get_content_write_db
from .moderation_routes import ReviewInput,staff_writer
from .review_routes import find
from .review_store import check_claim,decision_audit
from .content_store import require_versions,rate_limit,output

router=APIRouter(prefix='/api/live/moderator',tags=['live-review'])

@router.post('/content/{kind}/{entity_id}/clarification')
def clarify(kind:Literal['post','comment'],entity_id:UUID,payload:ReviewInput,request:Request,
            who=Depends(staff_writer),db=Depends(get_content_write_db)):
    rate_limit(db,request.app.state.settings,who.user)
    row=find(db,kind,entity_id,True);require_versions(row,payload);check_claim(db,row,who.user)
    if row.visibility_status=='DELETED_BY_AUTHOR':raise HTTPException(409,'Deleted content')
    before=row.visibility_status;row.decision_version+=1;row.updated_at=int(time.time())
    decision_audit(db,row,who.user,'REQUEST_CLARIFICATION',before,payload.reason)
    db.commit()
    return output(row,who.user)
