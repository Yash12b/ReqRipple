import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../lib/api';

interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
}

interface Project {
  id: string;
  name: string;
  description: string;
  domain: string;
  owner_user_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  projects: Project[];
  activeProject: Project | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  selectProject: (projectId: string) => void;
  refreshProjects: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('reqripple_token'));
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProjects = async () => {
    try {
      const list = await api.getProjects();
      setProjects(list);
      if (list.length > 0) {
        const savedId = localStorage.getItem('reqripple_active_project_id');
        const matched = list.find((p: Project) => p.id === savedId) || list[0];
        setActiveProject(matched);
        localStorage.setItem('reqripple_active_project_id', matched.id);
      }
    } catch (err) {
      console.error('Failed to load projects', err);
    }
  };

  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem('reqripple_token');
      if (storedToken) {
        try {
          const me = await api.getMe();
          setUser(me);
          await refreshProjects();
        } catch (err) {
          console.error('Session expired or invalid', err);
          logout();
        }
      }
      setLoading(false);
    }
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.login({ email, password });
    localStorage.setItem('reqripple_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    await refreshProjects();
  };

  const logout = () => {
    localStorage.removeItem('reqripple_token');
    localStorage.removeItem('reqripple_active_project_id');
    setToken(null);
    setUser(null);
    setProjects([]);
    setActiveProject(null);
  };

  const selectProject = (projectId: string) => {
    const found = projects.find((p) => p.id === projectId);
    if (found) {
      setActiveProject(found);
      localStorage.setItem('reqripple_active_project_id', found.id);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        projects,
        activeProject,
        loading,
        login,
        logout,
        selectProject,
        refreshProjects,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
