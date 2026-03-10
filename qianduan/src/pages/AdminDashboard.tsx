import React, { useState, useEffect, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthContext } from '../contexts/authContext';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

interface User {
  id: number;
  username: string;
  email: string;
  status: string;
  role: string;
  created_at: string;
}

interface Report {
  id: number;
  reporter_username: string;
  reported_type: string;
  reason: string;
  status: string;
  created_at: string;
}

const AdminDashboard: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { currentUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState<User[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // 检查是否为管理员
  useEffect(() => {
    if (currentUser?.role !== 'admin') {
      toast.error('您没有管理员权限');
      navigate('/account');
    }
  }, [currentUser, navigate]);

  // 获取用户列表
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users?search=${searchQuery}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setUsers(data.data.users);
      }
    } catch (error) {
      toast.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取举报列表
  const fetchReports = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/reports', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setReports(data.data.reports);
      }
    } catch (error) {
      toast.error('获取举报列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'reports') {
      fetchReports();
    }
  }, [activeTab]);

  // 封禁用户
  const handleBanUser = async (userId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/ban', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: userId,
          reason: '违反社区规定',
          duration: 24 * 60 // 24小时
        })
      });
      const data = await response.json();
      if (data.success) {
        toast.success('用户已封禁');
        fetchUsers();
      }
    } catch (error) {
      toast.error('封禁用户失败');
    }
  };

  // 解封用户
  const handleUnbanUser = async (userId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/unban', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: userId,
          reason: '解封'
        })
      });
      const data = await response.json();
      if (data.success) {
        toast.success('用户已解封');
        fetchUsers();
      }
    } catch (error) {
      toast.error('解封用户失败');
    }
  };

  // 处理举报
  const handleReport = async (reportId: number, status: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/reports/${reportId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          status,
          admin_action: status === 'resolved' ? '已处理' : '已驳回'
        })
      });
      const data = await response.json();
      if (data.success) {
        toast.success('举报处理成功');
        fetchReports();
      }
    } catch (error) {
      toast.error('处理举报失败');
    }
  };

  if (currentUser?.role !== 'admin') {
    return null;
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-900'}`}>
      {/* 顶部导航 */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center"
          >
            <i className="fas fa-crown text-purple-500 text-3xl mr-3" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-500 to-indigo-600 bg-clip-text text-transparent">
              管理后台
            </h1>
          </motion.div>
          
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.3 }}
              onClick={toggleTheme}
              className="p-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              {theme === 'light' ? (
                <i className="fas fa-moon" />
              ) : (
                <i className="fas fa-sun" />
              )}
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/account')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              <i className="fas fa-arrow-left mr-2" />
              返回个人中心
            </motion.button>
          </div>
        </div>
      </header>

      {/* 主要内容 */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* 欢迎信息 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              欢迎回来，{currentUser?.username}
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              这里是管理后台，您可以管理用户、处理举报、审核内容等
            </p>
          </motion.div>

          {/* 标签页 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex gap-2 mb-6"
          >
            {[
              { id: 'users', label: '用户管理', icon: 'users' },
              { id: 'reports', label: '举报处理', icon: 'flag' },
              { id: 'reviews', label: '内容审核', icon: 'clipboard-check' },
              { id: 'logs', label: '操作日志', icon: 'history' }
            ].map((tab) => (
              <motion.button
                key={tab.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 rounded-lg font-medium transition-all duration-300 flex items-center ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-md'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <i className={`fas fa-${tab.icon} mr-2`} />
                {tab.label}
              </motion.button>
            ))}
          </motion.div>

          {/* 内容区域 */}
          <AnimatePresence mode="wait">
            {activeTab === 'users' && (
              <motion.div
                key="users"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-md overflow-hidden"
              >
                {/* 搜索栏 */}
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex gap-4">
                    <div className="flex-1 relative">
                      <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        placeholder="搜索用户名或邮箱..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className={`w-full pl-10 pr-4 py-3 rounded-lg border ${
                          theme === 'light'
                            ? 'border-gray-300 focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                            : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                        } transition-all duration-300`}
                      />
                    </div>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={fetchUsers}
                      className="px-6 py-3 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors"
                    >
                      <i className="fas fa-search mr-2" />
                      搜索
                    </motion.button>
                  </div>
                </div>

                {/* 用户列表 */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700/50">
                      <tr>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">用户</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">邮箱</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">状态</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">角色</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">注册时间</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {loading ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-8 text-center">
                            <i className="fas fa-spinner fa-spin text-2xl text-purple-500" />
                          </td>
                        </tr>
                      ) : users.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                            暂无用户数据
                          </td>
                        </tr>
                      ) : (
                        users.map((user) => (
                          <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                            <td className="px-6 py-4">
                              <div className="flex items-center">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 flex items-center justify-center text-white font-bold mr-3">
                                  {user.username.charAt(0).toUpperCase()}
                                </div>
                                <span className="font-medium text-gray-900 dark:text-white">{user.username}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-gray-600 dark:text-gray-400">{user.email}</td>
                            <td className="px-6 py-4">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                user.status === 'active'
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                              }`}>
                                {user.status === 'active' ? '正常' : '已封禁'}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                user.role === 'admin'
                                  ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                              }`}>
                                {user.role === 'admin' ? '管理员' : '普通用户'}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                              {new Date(user.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex gap-2">
                                {user.status === 'active' ? (
                                  <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => handleBanUser(user.id)}
                                    className="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
                                  >
                                    <i className="fas fa-ban mr-1" />
                                    封禁
                                  </motion.button>
                                ) : (
                                  <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => handleUnbanUser(user.id)}
                                    className="px-3 py-1.5 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
                                  >
                                    <i className="fas fa-check mr-1" />
                                    解封
                                  </motion.button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {activeTab === 'reports' && (
              <motion.div
                key="reports"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-md overflow-hidden"
              >
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">举报列表</h3>
                </div>
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {loading ? (
                    <div className="p-8 text-center">
                      <i className="fas fa-spinner fa-spin text-2xl text-purple-500" />
                    </div>
                  ) : reports.length === 0 ? (
                    <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                      暂无举报数据
                    </div>
                  ) : (
                    reports.map((report) => (
                      <motion.div
                        key={report.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                                {report.reported_type === 'post' ? '帖子' : report.reported_type === 'comment' ? '评论' : '用户'}
                              </span>
                              <span className="text-sm text-gray-500 dark:text-gray-400">
                                举报者: {report.reporter_username}
                              </span>
                              <span className="text-sm text-gray-500 dark:text-gray-400">
                                {new Date(report.created_at).toLocaleDateString()}
                              </span>
                            </div>
                            <p className="text-gray-700 dark:text-gray-300 mb-3">{report.reason}</p>
                            {report.status === 'pending' && (
                              <div className="flex gap-2">
                                <motion.button
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.95 }}
                                  onClick={() => handleReport(report.id, 'resolved')}
                                  className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
                                >
                                  <i className="fas fa-check mr-1" />
                                  处理
                                </motion.button>
                                <motion.button
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.95 }}
                                  onClick={() => handleReport(report.id, 'rejected')}
                                  className="px-4 py-2 bg-gray-500 text-white rounded-lg text-sm hover:bg-gray-600 transition-colors"
                                >
                                  <i className="fas fa-times mr-1" />
                                  驳回
                                </motion.button>
                              </div>
                            )}
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            report.status === 'pending'
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                              : report.status === 'resolved'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                          }`}>
                            {report.status === 'pending' ? '待处理' : report.status === 'resolved' ? '已处理' : '已驳回'}
                          </span>
                        </div>
                      </motion.div>
                    ))
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'reviews' && (
              <motion.div
                key="reviews"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-8 text-center"
              >
                <i className="fas fa-clipboard-check text-6xl text-gray-300 dark:text-gray-600 mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">内容审核</h3>
                <p className="text-gray-600 dark:text-gray-400">此功能正在开发中...</p>
              </motion.div>
            )}

            {activeTab === 'logs' && (
              <motion.div
                key="logs"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-8 text-center"
              >
                <i className="fas fa-history text-6xl text-gray-300 dark:text-gray-600 mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">操作日志</h3>
                <p className="text-gray-600 dark:text-gray-400">此功能正在开发中...</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
