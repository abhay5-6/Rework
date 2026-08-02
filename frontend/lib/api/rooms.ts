import api from "./client";

export async function getRooms(organizationId?: number) {

  try {
    const url = organizationId ? `/rooms/?organization_id=${organizationId}` : "/rooms/";
    const response =
      await api.get(
        url
      );

    const payload = response.data;

    // Backend may return either a plain list
    // or a paginated object with `items`.
    if (Array.isArray(payload)) {
      return payload;
    }

    if (
      payload
      && Array.isArray(payload.items)
    ) {
      return payload.items;
    }

    return [];

  } catch (error) {

    console.error(
      "Failed to fetch rooms:",
      error
    );

    return [];
  }
}

export async function getRoom(
  roomId: number
) {
  const response = await api.get(
    `/rooms/${roomId}`
  );

  return response.data;
}

export async function joinRoom(
  roomId: number
) {

  const response =
    await api.post(

      `/rooms/${roomId}/join`,

      {}
    );

  return response.data;
}

export async function createRoom(
  name: string,
  description: string,
  is_private: boolean,
  organization_id?: number
) {

  const response =
    await api.post(

      "/rooms/",

      {
        name,
        description,
        is_private,
        organization_id,
      }
    );

  return response.data;
}

export async function leaveRoom(
  roomId: number
) {

  const response =
    await api.post(

      `/rooms/${roomId}/leave`,

      {}
    );

  return response.data;
}

export async function deleteRoom(
  roomId: number
) {

  const response =
    await api.delete(

      `/rooms/${roomId}`
    );

  return response.data;
}

//
// =========================
// MEMBERS / HIERARCHY
// =========================
//

export async function getRoomMembers(
  roomId: number
) {

  const response =
    await api.get(

      `/rooms/${roomId}/members`
    );

  return response.data;
}

export async function promoteMember(
  roomId: number,
  userId: number
) {

  const response =
    await api.post(

      `/rooms/${roomId}/promote/${userId}`,

      {}
    );

  return response.data;
}

export async function demoteMember(
  roomId: number,
  userId: number
) {

  const response =
    await api.post(

      `/rooms/${roomId}/demote/${userId}`,

      {}
    );

  return response.data;
}

export async function removeMember(
  roomId: number,
  userId: number
) {

  const response =
    await api.post(

      `/rooms/${roomId}/remove/${userId}`,

      {}
    );

  return response.data;
}

export async function toggleRoomAI(
  roomId: number,
  ai_enabled: boolean
) {
  const response = await api.patch(
    `/rooms/${roomId}`,
    { ai_enabled }
  );

  return response.data;
}