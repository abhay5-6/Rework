import api from "./client";

export async function getJoinRequests() {

  const response =
    await api.get(
      "/workspaces/join-requests"
    );

  return response.data;
}

export async function approveJoinRequest(
  requestId: number
) {

  const response =
    await api.post(

      `/workspaces/join-requests/${requestId}/approve`,

      {}
    );

  return response.data;
}

export async function rejectJoinRequest(
  requestId: number
) {

  const response =
    await api.post(

      `/workspaces/join-requests/${requestId}/reject`,

      {}
    );

  return response.data;
}