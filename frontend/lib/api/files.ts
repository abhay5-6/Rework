import type { AxiosProgressEvent } from "axios";

import api from "./client";

export async function uploadRoomFile(
  roomId: number,
  file: File,
  onProgress?: (progressEvent: AxiosProgressEvent) => void
) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(
    `/workspaces/${roomId}/files`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: onProgress,
    }
  );

  return response.data;
}
