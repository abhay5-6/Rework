from datetime import datetime

from pydantic import BaseModel

from app.schemas.workspace import RoomResponse


class MessageOnlyResponse(BaseModel):
    message: str


class SuccessMessageResponse(BaseModel):
    success: bool
    message: str


class RoomListResponse(BaseModel):
    items: list[RoomResponse]
    total: int
    skip: int
    limit: int


class RoomJoinRequestResponse(BaseModel):
    request_id: int
    workspace_id: int
    workspace_name: str
    user_id: int
    username: str
    status: str


class RoomUpdateResponse(BaseModel):
    message: str
    ai_enabled: bool


class CollaboratorRequestResponse(BaseModel):
    request_id: int
    sender_id: int
    username: str


class CollaboratorResponse(BaseModel):
    id: int
    username: str


class FileUploadResponse(BaseModel):
    file_url: str
    file_name: str | None = None
    file_type: str | None = None


class AuthProvidersResponse(BaseModel):
    google: bool
    github: bool


class GraphNodeData(BaseModel):
    label: str
    domain: str
    importance: int


class GraphNodePosition(BaseModel):
    x: int
    y: int


class GraphNode(BaseModel):
    id: str
    type: str
    data: GraphNodeData
    position: GraphNodePosition


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class RoomGraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class MemorySummaryDetailsResponse(BaseModel):
    summary: str
    stored_memory_id: int


class MemorySummaryResponse(BaseModel):
    summary: MemorySummaryDetailsResponse | None = None


class RoomAiAnswerResponse(BaseModel):
    answer: str


class MemoryReinforceResponse(BaseModel):
    message: str
    confidence_score: float


class WorkspaceTaskResponse(BaseModel):
    id: int
    description: str
    assignee_username: str | None = None
    status: str
    created_at: datetime
    completed_at: datetime | None = None
