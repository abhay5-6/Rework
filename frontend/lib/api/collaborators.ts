import api from "./client";


export async function sendCollaborationRequest(
  userId: number
) {

  const response =
    await api.post(

      `/collaborators/request/${userId}`,

      {}
    );

  return response.data;
}


export async function getCollaborationRequests() {

  const response =
    await api.get(

      "/collaborators/requests"
    );

  return response.data;
}


export async function acceptCollaborationRequest(
  requestId: number
) {

  const response =
    await api.post(

      `/collaborators/requests/${requestId}/accept`,

      {}
    );

  return response.data;
}


export async function rejectCollaborationRequest(
  requestId: number
) {

  const response =
    await api.post(

      `/collaborators/requests/${requestId}/reject`,

      {}
    );

  return response.data;
}


export async function getCollaborators() {

  const response =
    await api.get(

      "/collaborators/"
    );

  return response.data;
}