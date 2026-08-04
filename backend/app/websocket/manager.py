from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.active_connections: dict[
            int,
            list[WebSocket]
        ] = {}

        self.online_users: dict[
            int,
            set[str]
        ] = {}

        self.user_connections: dict[
            int,
            dict[str, WebSocket]
        ] = {}

        self.message_timestamps: dict[
            str,
            list[float]
        ] = {}

    async def connect(
        self,
        workspace_id: int,
        username: str,
        websocket: WebSocket
    ):

        await websocket.accept()

        if workspace_id not in (
            self.active_connections
        ):
            self.active_connections[
                workspace_id
            ] = []

        if workspace_id not in (
            self.online_users
        ):
            self.online_users[
                workspace_id
            ] = set()

        if workspace_id not in (
            self.user_connections
        ):
            self.user_connections[
                workspace_id
            ] = {}

        existing_connection = (
            self.user_connections[
                workspace_id
            ].get(username)
        )

        if existing_connection:
            try:
                await existing_connection.close(
                    code=4000
                )
            except Exception:
                pass

            if existing_connection in (
                self.active_connections[
                    workspace_id
                ]
            ):
                self.active_connections[
                    workspace_id
                ].remove(existing_connection)

        self.active_connections[
            workspace_id
        ].append(websocket)

        self.user_connections[
            workspace_id
        ][username] = websocket

        self.online_users[
            workspace_id
        ].add(username)

    def disconnect(
        self,
        workspace_id: int,
        username: str,
        websocket: WebSocket
    ):

        if workspace_id in (
            self.active_connections
        ):

            if websocket in (
                self.active_connections[
                    workspace_id
                ]
            ):

                self.active_connections[
                    workspace_id
                ].remove(websocket)

            if not self.active_connections[
                workspace_id
            ]:

                del self.active_connections[
                    workspace_id
                ]

        if workspace_id in (
            self.user_connections
        ):

            if (
                self.user_connections[
                    workspace_id
                ].get(username)
                is websocket
            ):
                del self.user_connections[
                    workspace_id
                ][username]

            if not self.user_connections[
                workspace_id
            ]:

                del self.user_connections[
                    workspace_id
                ]

        if workspace_id in (
            self.online_users
        ):

            has_current_connection = (
                workspace_id in self.user_connections
                and username in self.user_connections[
                    workspace_id
                ]
            )

            if not has_current_connection:
                self.online_users[
                    workspace_id
                ].discard(username)

            if not self.online_users[
                workspace_id
            ]:

                del self.online_users[
                    workspace_id
                ]

    def get_online_users(
        self,
        workspace_id: int
    ):

        return list(
            self.online_users.get(
                workspace_id,
                set()
            )
        )

    async def broadcast_local(
        self,
        workspace_id: int,
        message: dict
    ):
        """Send message only to locally connected WebSockets. Called by Redis listener."""
        if workspace_id not in (
            self.active_connections
        ):
            return

        disconnected = []

        for connection in (
            self.active_connections[
                workspace_id
            ]
        ):

            try:

                await connection.send_json(
                    message
                )

            except Exception:

                disconnected.append(
                    connection
                )

        for connection in disconnected:

            self.active_connections[
                workspace_id
            ].remove(connection)

            if not self.active_connections[
                workspace_id
            ]:

                del self.active_connections[
                    workspace_id
                ]

    async def broadcast(
        self,
        workspace_id: int,
        message: dict
    ):
        """Publish message to Redis to be distributed across all nodes."""
        from app.websocket.redis_pubsub import redis_manager
        
        # Publish to Redis instead of sending locally
        if redis_manager.redis:
            await redis_manager.publish(workspace_id, message)
        else:
            # Fallback to local broadcast if Redis is not available
            await self.broadcast_local(workspace_id, message)

manager = ConnectionManager()
