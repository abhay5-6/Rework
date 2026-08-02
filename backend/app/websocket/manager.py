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
        room_id: int,
        username: str,
        websocket: WebSocket
    ):

        await websocket.accept()

        if room_id not in (
            self.active_connections
        ):
            self.active_connections[
                room_id
            ] = []

        if room_id not in (
            self.online_users
        ):
            self.online_users[
                room_id
            ] = set()

        if room_id not in (
            self.user_connections
        ):
            self.user_connections[
                room_id
            ] = {}

        existing_connection = (
            self.user_connections[
                room_id
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
                    room_id
                ]
            ):
                self.active_connections[
                    room_id
                ].remove(existing_connection)

        self.active_connections[
            room_id
        ].append(websocket)

        self.user_connections[
            room_id
        ][username] = websocket

        self.online_users[
            room_id
        ].add(username)

    def disconnect(
        self,
        room_id: int,
        username: str,
        websocket: WebSocket
    ):

        if room_id in (
            self.active_connections
        ):

            if websocket in (
                self.active_connections[
                    room_id
                ]
            ):

                self.active_connections[
                    room_id
                ].remove(websocket)

            if not self.active_connections[
                room_id
            ]:

                del self.active_connections[
                    room_id
                ]

        if room_id in (
            self.user_connections
        ):

            if (
                self.user_connections[
                    room_id
                ].get(username)
                is websocket
            ):
                del self.user_connections[
                    room_id
                ][username]

            if not self.user_connections[
                room_id
            ]:

                del self.user_connections[
                    room_id
                ]

        if room_id in (
            self.online_users
        ):

            has_current_connection = (
                room_id in self.user_connections
                and username in self.user_connections[
                    room_id
                ]
            )

            if not has_current_connection:
                self.online_users[
                    room_id
                ].discard(username)

            if not self.online_users[
                room_id
            ]:

                del self.online_users[
                    room_id
                ]

    def get_online_users(
        self,
        room_id: int
    ):

        return list(
            self.online_users.get(
                room_id,
                set()
            )
        )

    async def broadcast(
        self,
        room_id: int,
        message: dict
    ):

        if room_id not in (
            self.active_connections
        ):
            return

        disconnected = []

        for connection in (
            self.active_connections[
                room_id
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
                room_id
            ].remove(connection)

            if not self.active_connections[
                room_id
            ]:

                del self.active_connections[
                    room_id
                ]

manager = ConnectionManager()
