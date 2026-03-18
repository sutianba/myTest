import { createContext, useState, useEffect, ReactNode, useContext } from "react";

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  currentUser: User;
  token: string | null;
  login: (userData: User, token: string) => void;
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
  token: null,
  login: () => {},
  logout: () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User>({
    id: '',
    username: '',
    email: '',
    role: 'user'
  });
  const [token, setToken] = useState<string | null>(null);

  // 从本地存储加载认证状态
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setIsAuthenticated(true);
        setCurrentUser(userData);
        setToken(storedToken);
      } catch (error) {
        console.error('Failed to parse stored user data:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const login = (userData: User, token: string) => {
    setIsAuthenticated(true);
    setCurrentUser(userData);
    setToken(token);
    
    // 保存到本地存储
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = () => {
    setIsAuthenticated(false);
    setCurrentUser({
      id: '',
      username: '',
      email: '',
      role: 'user'
    });
    setToken(null);
    
    // 从本地存储移除
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, currentUser, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// 添加 useAuth 钩子
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
