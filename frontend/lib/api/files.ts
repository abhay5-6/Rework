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
 * Constructs an authenticated URL for accessing or downloading a workspace file.
 *
 * @param fileUrl - The relative file path returned by the server (e.g. /workspaces/1/files/uuid.png).
 * @param token - Optional JWT access token to attach as a query parameter for media tags.
 * @returns Formatted absolute or relative URL with authentication token attached.
 */
export function getAuthenticatedFileUrl(fileUrl: string, token?: string): string {
  if (!token) return fileUrl;
  const separator = fileUrl.includes("?") ? "&" : "?";
  return `${fileUrl}${separator}token=${encodeURIComponent(token)}`;
}
