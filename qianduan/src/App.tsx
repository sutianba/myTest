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
import Community from "@/pages/Community";
import PostDetail from "@/pages/PostDetail";
import CreatePost from "@/pages/CreatePost";
import AdminDashboard from "@/pages/AdminDashboard";
import AlbumManagement from "@/pages/AlbumManagement";
import ErrorBoundary from "@/components/ErrorBoundary";
import { AuthProvider } from '@/contexts/authContext';

export default function App() {
  return (
    <AuthProvider>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/explore" element={<PlantRecognition />} />
          <Route path="/account" element={<AccountManagement />} />
          <Route path="/users" element={<UserManagement />} />
          <Route path="/permissions" element={<PermissionManagement />} />
          <Route path="/plant/:id" element={<PlantDetail />} />
          <Route path="/recognition-result" element={<RecognitionResult />} />
          <Route path="/history" element={<RecognitionHistory />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="/community" element={<Community />} />
          <Route path="/community/post/:postId" element={<PostDetail />} />
          <Route path="/community/create" element={<CreatePost />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/albums" element={<AlbumManagement />} />
          {/* 添加访客路线，方便用户直接访问主要功能 */}
          <Route path="/guest" element={<Home />} />
        </Routes>
      </ErrorBoundary>
    </AuthProvider>
  );
}
