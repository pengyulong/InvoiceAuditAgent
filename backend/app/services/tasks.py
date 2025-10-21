"""
Celery任务定义
"""

from celery import current_task
from app.services.celery_app import celery_app
from app.services.audit_service import AuditService
from app.core.database import SessionLocal


@celery_app.task(bind=True)
def process_audit_task(self, task_id: str):
    """处理审计任务的Celery任务"""
    db = SessionLocal()
    try:
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': '开始处理...'}
        )

        # 创建审计服务
        audit_service = AuditService(db)

        # 开始审计
        import asyncio
        success = asyncio.run(audit_service.start_audit(task_id))

        if success:
            return {'status': 'SUCCESS', 'result': '审计完成'}
        else:
            return {'status': 'FAILURE', 'result': '审计失败'}

    except Exception as e:
        return {'status': 'FAILURE', 'result': str(e)}
    finally:
        db.close()