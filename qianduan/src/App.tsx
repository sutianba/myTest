import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import PlantRecognition from "@/pages/PlantRecognition";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import AccountManagement from "@/pages/AccountManagement";
import UserManagement from "@/pages/UserManagement";
import PermissionManagement from "@/pages/PermissionManagement";
import PlantDetail from "@/pages/PlantDetail";
import RecognitionResult from "@/pages/RecognitionResult";
import RecognitionHistory from "@/pages/RecognitionHistory";
import Favorites from "@/pages/Favorites";
import { useState } from "react";
import { AuthContext } from '@/contexts/authContext';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState({
    id: '1',
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin'
  });

  const login = (userData: any) => {
    setIsAuthenticated(true);
    setCurrentUser(userData);
  };

  const logout = () => {
    setIsAuthenticated(false);
    setCurrentUser({
      id: '',
      username: '',
      email: '',
      role: 'user'
    });
  };

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, currentUser, login, logout }}
    >
       <Routes>
         <Route path="/" element={isAuthenticated ? <Home /> : <Login />} />
         <Route path="/login" element={<Login />} />
         <Route path="/register" element={<Register />} />
         <Route path="/explore" element={<PlantRecognition />} />
         <Route path="/account" element={isAuthenticated ? <AccountManagement /> : <Login />} />
         <Route path="/users" element={isAuthenticated ? <UserManagement /> : <Login />} />
         <Route path="/permissions" element={isAuthenticated ? <PermissionManagement /> : <Login />} />
         <Route path="/plant/:id" element={isAuthenticated ? <PlantDetail /> : <Login />} />
         <Route path="/recognition-result" element={isAuthenticated ? <RecognitionResult /> : <Login />} />
         <Route path="/history" element={isAuthenticated ? <RecognitionHistory /> : <Login />} />
         <Route path="/favorites" element={isAuthenticated ? <Favorites /> : <Login />} />
         {/* 添加访客路线，方便用户直接访问主要功能 */}
         <Route path="/guest" element={<Home />} />
       </Routes>
    </AuthContext.Provider>
  );
}
