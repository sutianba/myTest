import { createContext } from "react";

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  currentUser: User;
  login: (userData: User) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  currentUser: {
    id: '',
    username: '',
    email: '',
    role: 'user'
  },
  login: () => {},
  logout: () => {},
});