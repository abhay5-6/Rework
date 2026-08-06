import type { AxiosProgressEvent } from "axios";
import api from "./client";

export interface FileUploadResponse {
  file_url: string;
  file_name: string;
  file_type: string;
}

/**
 * Uploads a file to a specific workspace.
 * Requires active workspace membership.
 *
 * @param roomId - The target workspace ID.
 * @param file - The file object to upload.
 * @param onProgress - Optional callback to track upload progress.
 * @returns Promise resolving to the file upload response containing file_url, file_name, and file_type.
 */
export async function uploadRoomFile(
  roomId: number,
  file: File,
  onProgress?: (progressEvent: AxiosProgressEvent) => void
): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<FileUploadResponse>(
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

/**
 * Retrieves a protected workspace file using the authenticated API client.
 *
 * @param fileUrl - The relative file URL returned by the upload endpoint.
 * @returns The protected file contents as a Blob.
 */
export async function downloadWorkspaceFile(fileUrl: string): Promise<Blob> {
  const response = await api.get<Blob>(fileUrl, {
    responseType: "blob",
  });

  return response.data;
}
