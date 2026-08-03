import api from "./client";

export interface Task {
  id: number;
  description: string;
  assignee_username: string | null;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export async function getWorkspaceTasks(roomId: number): Promise<Task[]> {
  const response = await api.get(`/workspaces/${roomId}/tasks`);
  return response.data;
}

export async function updateTask(roomId: number, taskId: number, updates: Partial<Pick<Task, "status" | "completed_at">> & { completed?: boolean }): Promise<Task> {
  const response = await api.patch(`/workspaces/${roomId}/tasks/${taskId}`, updates);
  return response.data;
}
