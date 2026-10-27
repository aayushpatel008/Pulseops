from app.schemas.server import ServerUpdate
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import engine, SessionLocal
from app.database.base import Base
from app.models.incident import Incident
from app.models.server import Server
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
from app.schemas.server import (
    ServerCreate,
    ServerResponse,
)

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="PulseOps API",
    description="Backend API for the PulseOps monitoring platform",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to PulseOps",
        "status": "running"
    }




@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
@app.get("/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except SQLAlchemyError:
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }


@app.post("/incidents", response_model=IncidentResponse, status_code=201)
def create_incident(incident_data: IncidentCreate):
    db = SessionLocal()

    try:
        incident = Incident(
            title=incident_data.title,
            description=incident_data.description,
            priority=incident_data.priority,
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        return incident

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create incident",
        )

    finally:
        db.close()


@app.get("/incidents", response_model=list[IncidentResponse])
def get_incidents(
    status: str | None = None,
    priority: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    db = SessionLocal()

    try:
        allowed_statuses = ["open", "in_progress", "resolved"]
        allowed_priorities = ["low", "medium", "high"]

        # Validate status
        if status is not None and status not in allowed_statuses:
            raise HTTPException(
                status_code=422,
                detail="Invalid status",
            )

        # Validate priority
        if priority is not None and priority not in allowed_priorities:
            raise HTTPException(
                status_code=422,
                detail="Invalid priority",
            )

        # Start with all incidents
        query = db.query(Incident)

        # Apply status filter
        if status is not None:
            query = query.filter(Incident.status == status)

        # Apply priority filter
        if priority is not None:
            query = query.filter(Incident.priority == priority)

        # Apply pagination and return results
        incidents = (
            query
            .order_by(Incident.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return incidents

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve incidents",
        )

    finally:
        db.close()


@app.post("/servers", response_model=ServerResponse, status_code=201)
def create_server(server_data: ServerCreate):
    db = SessionLocal()

    try:
        existing_server = (
            db.query(Server)
            .filter(Server.hostname == server_data.hostname)
            .first()
        )

        if existing_server:
            raise HTTPException(
                status_code=409,
                detail="A server with this hostname already exists",
            )

        server = Server(
            name=server_data.name,
            hostname=server_data.hostname,
            ip_address=server_data.ip_address,
            environment=server_data.environment,
        )

        db.add(server)
        db.commit()
        db.refresh(server)

        return server

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to register server",
        )

    finally:
        db.close()

@app.delete("/servers/{server_id}")
def delete_server(server_id: int):
    db = SessionLocal()

    try:
        server = (
            db.query(Server)
            .filter(Server.id == server_id)
            .first()
        )

        if server is None:
            raise HTTPException(
                status_code=404,
                detail="Server not found",
            )

        db.delete(server)
        db.commit()

        return {
            "message": "Server deleted successfully",
            "id": server_id,
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete server",
        )

    finally:
        db.close()

@app.get("/servers", response_model=list[ServerResponse])
def get_servers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    db = SessionLocal()

    try:
        servers = (
            db.query(Server)
            .order_by(Server.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return servers

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve servers",
        )

    finally:
        db.close()


@app.patch("/servers/{server_id}", response_model=ServerResponse)
def update_server(server_id: int, server_data: ServerUpdate):
    db = SessionLocal()

    try:
        server = (
            db.query(Server)
            .filter(Server.id == server_id)
            .first()
        )

        if server is None:
            raise HTTPException(
                status_code=404,
                detail="Server not found",
            )

        update_data = server_data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=422,
                detail="Provide at least one field to update",
            )

        for field, value in update_data.items():
            if value is None and field != "ip_address":
                raise HTTPException(
                    status_code=422,
                    detail=f"{field} cannot be null",
                )

        if "hostname" in update_data and update_data["hostname"] != server.hostname:
            existing_server = (
                db.query(Server)
                .filter(Server.hostname == update_data["hostname"])
                .first()
            )

            if existing_server:
                raise HTTPException(
                    status_code=409,
                    detail="A server with this hostname already exists",
                )

        for field, value in update_data.items():
            setattr(server, field, value)

        db.commit()
        db.refresh(server)

        return server

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update server",
        )

    finally:
        db.close()

@app.get("/servers/{server_id}", response_model=ServerResponse)
def get_server(server_id: int):
    db = SessionLocal()

    try:
        server = (
            db.query(Server)
            .filter(Server.id == server_id)
            .first()
        )

        if server is None:
            raise HTTPException(
                status_code=404,
                detail="Server not found",
            )

        return server

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve server",
        )

    finally:
        db.close()



@app.patch("/incidents/{incident_id}/status")
def update_incident_status(incident_id: int, status: str):
    db = SessionLocal()

    try:
        incident = db.query(Incident).filter(
            Incident.id == incident_id
        ).first()

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        allowed_statuses = ["open", "in_progress", "resolved"]

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status"
            )

        incident.status = status
        db.commit()
        db.refresh(incident)

        return {
            "message": "Incident status updated successfully",
            "id": incident.id,
            "status": incident.status
        }

    finally:
        db.close()

@app.patch("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: int, data: IncidentUpdate):
    db = SessionLocal()

    try:
        incident = db.query(Incident).filter(
            Incident.id == incident_id
        ).first()

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=422,
                detail="Provide at least one field to update",
            )

        # Required fields cannot be null.
        for field in ("title", "status", "priority"):
            if field in update_data and update_data[field] is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"{field} cannot be null",
                )

        allowed_statuses = ["open", "in_progress", "resolved"]
        allowed_priorities = ["low", "medium", "high"]

        if (
            "status" in update_data
            and update_data["status"] not in allowed_statuses
        ):
            raise HTTPException(
                status_code=422,
                detail="Invalid status",
            )

        if (
            "priority" in update_data
            and update_data["priority"] not in allowed_priorities
        ):
            raise HTTPException(
                status_code=422,
                detail="Invalid priority",
            )

        for field, value in update_data.items():
            setattr(incident, field, value)

        db.commit()
        db.refresh(incident)

        return incident

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update incident",
        )

    finally:
        db.close()

    
@app.delete("/incidents/{incident_id}")
def delete_incident(incident_id: int):
    db = SessionLocal()

    try:
        incident = db.query(Incident).filter(
            Incident.id == incident_id
        ).first()

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        db.delete(incident)
        db.commit()

        return {
            "message": "Incident deleted successfully",
            "id": incident_id
        }

    finally:
        db.close()
