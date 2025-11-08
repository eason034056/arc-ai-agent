"""
FastAPI Main Application

This is the entry point for the FastAPI web server.
It defines all HTTP endpoints and integrates:
- Slack webhooks
- Admin API
- Expense system webhooks
- Health checks
- Metrics

API Documentation available at: http://localhost:8080/docs
"""

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
import asyncio 

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.connection import get_db, init_db
from app.db.schema import BatchCreateRequest, BatchResponse
from app.agent.graph import run_payroll_workflow
from app.agent.policies import PayrollPolicy
from app.onchain.service import OnchainService

# Setup logging first
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# ========================================
# CREATE FASTAPI APP
# ========================================
app = FastAPI(
    title="Arc Payroll AI Agent",
    description="Automated payroll processing with AI and blockchain",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ========================================
# CORS MIDDLEWARE
# ========================================
# Allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# STARTUP / SHUTDOWN
# ========================================

@app.on_event("startup")
async def startup_event():
    """
    Run when application starts
    
    Initialize:
    - Database tables
    - Log startup message
    """
    logger.info("Application starting up")
    
    # Initialize database (create tables if needed)
    # In production, use Alembic migrations instead
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Run when application shuts down
    """
    logger.info("Application shutting down")


# ========================================
# HEALTH CHECK
# ========================================

@app.get("/healthz")
async def health_check():
    """
    Health check endpoint
    
    Used by:
    - Docker healthcheck
    - Load balancers
    - Monitoring systems
    
    Returns:
        {"status": "ok"}
    """
    return {"status": "ok"}


@app.get("/")
async def root():
    """
    Root endpoint
    
    Returns basic information about the API
    """
    return {
        "name": "Arc Payroll AI Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/healthz"
    }


# ========================================
# ADMIN ENDPOINTS
# ========================================

@app.post("/admin/trigger")
async def trigger_payroll_batch(month: str) -> dict:
    """
    Trigger the payroll workflow for a given month.
    
    This endpoint manually starts the payroll process for the given month.
    It runs the full LangGraph workflow and returns the summarized result.

    Args:
        month: Payroll month (format: "YYYY-MM")

    Returns:
        dict: Final workflow summary (batch_id, month, status, etc.)
    """
    from uuid import uuid4
    from app.agent.graph import run_payroll_workflow
    from app.agent.policies import PayrollPolicy
    from app.db.schema import AgentState

    batch_id = f"batch_{month.replace('-', '')}_{uuid4().hex[:8]}"

    logger.info(
        "Manual trigger requested",
        extra={"month": month, "batch_id": batch_id},
    )

    try:
        # Get Slack client for approval workflow
        # If Slack is not configured, slack_client will be None and workflow will continue without Slack
        slack_client = None
        try:
            from app.slack.app import slack_app
            if slack_app and slack_app.client:
                slack_client = slack_app.client
                logger.debug("Slack client available for approval workflow")
            else:
                logger.debug("Slack app not configured, continuing without Slack integration")
        except Exception as e:
            logger.warning(
                "Slack not configured or unavailable, continuing without Slack integration",
                extra={"error": str(e)}
            )
        
        # Run full workflow
        final_state = run_payroll_workflow(
            batch_id=batch_id,
            month=month,
            policy=PayrollPolicy(),
            slack_client=slack_client,
        )

        # Handle both AgentState objects and dicts (LangGraph may return dict)
        if isinstance(final_state, dict):
            final_state = AgentState(**final_state)

        # 🧩 Extract status safely (with fallback to default)
        status = "unknown"
        if hasattr(final_state, "metadata") and isinstance(final_state.metadata, dict):
            # Try normal metadata
            status = final_state.metadata.get("final_status", "unknown")
            # Fallback: look for legacy status key
            if status == "unknown" and "status" in final_state.metadata:
                status = final_state.metadata["status"]

        # 🧩 Fallback 2: look for implicit clues
        if status == "unknown" and len(final_state.errors) == 0:
            status = "completed"
        elif status == "unknown" and len(final_state.errors) > 0:
            status = "completed_with_warnings"

        # ✅ Build clean API response
        response = {
            "batch_id": final_state.batch_id,
            "month": final_state.month,
            "status": status,
            "line_count": len(final_state.lines),
            "tx_hashes": final_state.tx_hashes,
            "errors": final_state.errors,
        }

        logger.info(
            "Payroll batch completed",
            extra={"batch_id": batch_id, "status": status},
        )

        # Print concise terminal summary
        print(f"\n🧾 Batch {batch_id} Summary:")
        print(f"   Month: {month}")
        print(f"   Status: {status.upper()}")
        print(f"   Lines: {len(final_state.lines)}")
        print(f"   Tx Hashes: {len(final_state.tx_hashes)}")
        print(f"   Errors: {len(final_state.errors)}\n")

        return response

    except Exception as e:
        logger.error(
            "Failed to trigger batch",
            extra={"month": month, "error": str(e)},
            exc_info=True,
        )
        return {"detail": f"Failed to trigger batch: {str(e)}"}


@app.get("/batches/{batch_id}")
async def get_batch(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Get batch details by ID
    
    Returns information about a specific payroll batch.
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Batch details including lines and transactions
        
    Example:
        GET /batches/batch_abc123
        
        Response:
        {
            "id": "batch_abc123",
            "month": "2025-11",
            "status": "completed",
            "total_amount": "27500.00",
            "line_count": 5,
            ...
        }
    """
    # TODO: Query database for batch
    # from app.db.models import PayrollBatch
    # batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    # if not batch:
    #     raise HTTPException(status_code=404, detail="Batch not found")
    # return BatchResponse.from_orm(batch)
    
    # Placeholder response
    return {
        "id": batch_id,
        "status": "not_implemented",
        "message": "Database query not implemented yet"
    }


@app.get("/batches")
async def list_batches(
    month: str = Query(None, description="Filter by month (YYYY-MM)"),
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Max results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List payroll batches
    
    Returns a paginated list of payroll batches.
    Can filter by month and status.
    
    Args:
        month: Optional month filter
        status: Optional status filter
        limit: Maximum results per page
        offset: Offset for pagination
        
    Returns:
        List of batches
        
    Example:
        GET /batches?month=2025-11&status=completed&limit=10
    """
    # TODO: Query database
    # from app.db.models import PayrollBatch
    # query = db.query(PayrollBatch)
    # if month:
    #     query = query.filter(PayrollBatch.month == month)
    # if status:
    #     query = query.filter(PayrollBatch.status == status)
    # batches = query.offset(offset).limit(limit).all()
    # return {"batches": [BatchResponse.from_orm(b) for b in batches]}
    
    return {
        "batches": [],
        "total": 0,
        "message": "Database query not implemented yet"
    }


# ========================================
# SLACK ENDPOINTS (Production Safe)
# ========================================

@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Slack events endpoint (Production safe)
    Handles:
      - interactive button clicks
      - slash commands
      - url_verification handshake
    """

    from app.slack.app import slack_handler

    if not slack_handler:
        logger.warning("⚠️ Slack events received but Slack integration is not configured")
        return JSONResponse(status_code=503, content={"error": "Slack integration not configured"})

    logger.info("📥 Received Slack event request", extra={
        "method": request.method,
        "url": str(request.url),
    })

    # Step 1️⃣ Handle URL verification handshake instantly
    try:
        body = await request.json()
        if body.get("type") == "url_verification":
            logger.info("🔐 Slack URL verification challenge received")
            return JSONResponse(content={"challenge": body.get("challenge")})
    except Exception:
        # ignore if not json (interactive payload is form-data)
        pass

    # Step 2️⃣ Run Slack Bolt in background to avoid blocking the 3s window
    async def process_in_background(req: Request):
        try:
            await slack_handler.handle(req)
            logger.info("✅ Slack handler completed successfully")
        except Exception as e:
            logger.exception(f"❌ Slack handler error (background): {e}")

    # 🚀 Launch background task — does not block Slack 3s timeout
    asyncio.create_task(process_in_background(request))

    # Step 3️⃣ Immediately return HTTP 200 OK to Slack
    logger.debug("⚡ Fast ack returned to Slack to prevent retries")
    return JSONResponse(status_code=200, content={"ok": True})



@app.post("/slack/commands")
async def slack_commands(request: Request):
    """
    Slack slash commands endpoint
    
    Handles commands like:
    - /payroll status <batch_id>
    - /payroll trigger <month>
    
    Args:
        request: FastAPI Request object containing Slack command data
        
    Returns:
        Response from Slack Bolt handler
    """
    from app.slack.app import slack_handler
    
    if not slack_handler:
        logger.warning("Slack command received but Slack integration is not configured")
        return JSONResponse(
            status_code=503,
            content={"error": "Slack integration not configured"}
        )
    
    logger.debug("Received Slack command")
    
    return await slack_handler.handle(request)


# ========================================
# EXPENSE SYSTEM WEBHOOK
# ========================================

@app.post("/expense/webhook")
async def expense_webhook(payload: dict):
    """
    Receive callbacks from expense system
    
    After we send transaction results to the expense system,
    they might send callbacks with status updates.
    
    Args:
        payload: Callback data from expense system
        
    Returns:
        Acknowledgment
    """
    logger.info("Expense webhook received", extra={"payload": payload})
    
    # TODO: Process expense system callback
    # Update database with expense record status
    
    return {"status": "received"}


# ========================================
# REPORTS ENDPOINTS
# ========================================

@app.get("/reports/{month}/reconcile")
async def get_reconciliation_report(
    month: str,
    format: str = Query("json", description="Response format: json or csv")
):
    """
    Get reconciliation report for a specific month
    
    Args:
        month: Payroll month (YYYY-MM)
        format: Response format (json or csv)
        
    Returns:
        Reconciliation report
    """
    # TODO: Generate reconciliation report from database
    
    if format == "csv":
        # Return CSV file
        from fastapi.responses import Response
        csv_content = "employee_id,wallet,amount,tx_hash,status\n"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=payroll_{month}.csv"
            }
        )
    
    return {
        "month": month,
        "status": "not_implemented",
        "message": "Report generation not implemented yet"
    }


# ========================================
# METRICS ENDPOINT
# ========================================

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format.
    Scraped by Prometheus server for monitoring.
    """
    from prometheus_client import generate_latest
    
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )


if __name__ == "__main__":
    # For development only
    # In production, use uvicorn command:
    # uvicorn app.api.main:app --host 0.0.0.0 --port 8080
    
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_dev
    )

