import { create } from "zustand";
import { persist } from "zustand/middleware";

/** Represents an Organization root tenant */
export interface Organization {
  id: number;
  name: string;
  created_at: string;
}

/** Represents a User's membership inside an Organization */
export interface OrgMembership {
  user_id: number;
  org_id: number;
  role: string;
  joined_at: string;
  organization?: Organization;
}

interface OrgState {
  organizations: Organization[];
  activeOrgId: number | null;
  setOrganizations: (orgs: Organization[]) => void;
  setActiveOrgId: (id: number | null) => void;
}

/**
 * Zustand store for multi-tenant Organization context.
 * Persists the selected activeOrgId in localStorage across sessions.
 */
export const useOrgStore = create<OrgState>()(
  persist(
    (set) => ({
      organizations: [],
      activeOrgId: null,
      setOrganizations: (orgs) => set({ organizations: orgs }),
      setActiveOrgId: (id) => set({ activeOrgId: id }),
    }),
    {
      name: "org-storage",
    }
  )
);
