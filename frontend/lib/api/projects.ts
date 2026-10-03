import { Project, ProjectCreateInput } from "../types/project";
import { apiRequest } from "./client";

export async function getProjects(): Promise<Project[]> {
  return apiRequest<Project[]>("/projects");
}

export async function createProject(data: ProjectCreateInput): Promise<Project> {
  return apiRequest<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
