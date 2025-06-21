import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext'; // Make sure this import is correct

interface Team {
  id: number;
  name: string;
}

interface TeamContextType {
  teamId: number | null;
  setTeamId: (id: number) => void;
  teams: Team[];
  setTeams: React.Dispatch<React.SetStateAction<Team[]>>;
}

export const TeamContext = createContext<TeamContextType>({
  teamId: null,
  setTeamId: () => {},
  teams: [],
  setTeams: () => {},
});

export const TeamProvider = ({ children }: { children: React.ReactNode }) => {
  const { token } = useAuth(); // get token to fetch teams
  const [teamId, setTeamId] = useState<number | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);

  useEffect(() => {
    if (!token) return;

    fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/teams`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => (res.ok ? res.json() : []))
      .then(setTeams)
      .catch(console.error);
  }, [token]);

  return (
    <TeamContext.Provider value={{ teamId, setTeamId, teams, setTeams }}>
      {children}
    </TeamContext.Provider>
  );
};

export const useTeam = () => useContext(TeamContext);
