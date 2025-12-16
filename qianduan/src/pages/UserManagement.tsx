import React, { useState, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthContext } from '../contexts/authContext';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';

// 模拟用户数据
const mockUsers = [
  { id: '1', username: 'admin', email: 'admin@example.com', role: 'admin', status: 'active', registeredAt: '2023-01-15' },
  { id: '2', username: 'user1', email: 'user1@example.com', role: 'user', status: 'active', registeredAt: '2023-02-20' },
  { id: '3', username: 'user2', email: 'user2@example.com', role: 'user', status: 'active', registeredAt: '2023-03-10' },{ id: '4', username: 'user3', email: 'user3@example.com', role: 'user', status: 'inactive', registeredAt: '2023-04-05' },
  { id: '5', username: 'user4', email: 'user4@example.com', role: 'user', status: 'active', registeredAt: '2023-05-12' },
];

const UserManagement: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { currentUser } = useContext(AuthContext);
  const [users, setUsers] = useState(mockUsers);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [editingUser, setEditingUser] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // 过滤用户列表
  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesRole = selectedRole === 'all' || user.role === selectedRole;
    const matchesStatus = selectedStatus === 'all' || user.status === selectedStatus;
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  // 处理用户角色变更
  const handleRoleChange = (userId: string, newRole: string) => {
    if (userId === currentUser.id && newRole !== 'admin') {
      toast.error('您不能更改自己的管理员角色');
      return;
    }
    
    setUsers(prevUsers => 
      prevUsers.map(user => 
        user.id === userId ? { ...user, role: newRole } : user
      )
    );
    toast.success(`用户 ${users.find(u => u.id === userId)?.username} 的角色已更新`);
  };

  // 处理用户状态变更
  const handleStatusChange = (userId: string, newStatus: string) => {
    if (userId === currentUser.id) {
      toast.error('您不能更改自己的账户状态');
      return;
    }
    
    setUsers(prevUsers => 
      prevUsers.map(user => 
        user.id === userId ? { ...user, status: newStatus } : user
      )
    );
    toast.success(`用户 ${users.find(u => u.id === userId)?.username} 的状态已更新`);
  };

  // 删除用户
  const handleDeleteUser = (userId: string) => {
    if (userId === currentUser.id) {
      toast.error('您不能删除自己的账户');
      return;
    }
    
    if (window.confirm('确定要删除此用户吗？此操作不可撤销。')) {
      setLoading(true);
      
      // 模拟删除操作
      setTimeout(() => {
        setUsers(prevUsers => prevUsers.filter(user => user.id !== userId));
        toast.success('用户已成功删除');
        setLoading(false);
      }, 500);
    }
  };

  // 编辑用户
  const handleEditUser = (user: any) => {
    setEditingUser({ ...user });
  };

  // 保存编辑后的用户信息
  const handleSaveUser = () => {
    if (!editingUser) return;
    
    // 验证邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(editingUser.email)) {
      toast.error('请输入有效的邮箱地址');
      return;
    }
    
    setLoading(true);
    
    // 模拟保存操作
    setTimeout(() => {
      setUsers(prevUsers => 
        prevUsers.map(user => 
          user.id === editingUser.id ? editingUser : user
        )
      );
      toast.success('用户信息已更新');
      setEditingUser(null);
      setLoading(false);
    }, 500);
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setEditingUser(null);
  };

  // 渲染状态标签
  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">活跃</span>;
      case 'inactive':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">非活跃</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">未知</span>;
    }
  };

  // 渲染角色标签
  const renderRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">管理员</span>;
      case 'user':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300">普通用户</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">未知</span>;
    }
  };

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
            <i className="fas fa-leaf text-emerald-500 text-3xl mr-3" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-500 to-teal-600 bg-clip-text text-transparent">
              植物花卉识别系统
            </h1>
          </motion.div>
          
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.3 }}
              onClick={toggleTheme}
              className="p-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              aria-label="切换主题"
            >
              {theme === 'light' ? (
                <i className="fas fa-moon" />
              ) : (
                <i className="fas fa-sun" />
              )}
            </motion.button>
            
            <div className="flex items-center gap-2">
              <img 
                src={`https://ui-avatars.com/api/?name=${currentUser.username}&background=random&color=fff`} 
                alt="用户头像"
                className="w-8 h-8 rounded-full object-cover border-2 border-emerald-500"
              />
              <span className="text-gray-700 dark:text-gray-300 font-medium">
                {currentUser.username}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* 主要内容 */}
      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-6xl mx-auto"
        >
          {/* 页面标题 */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">用户管理</h2>
            <p className="text-gray-600 dark:text-gray-400">查看和管理系统中的所有用户</p>
          </div>

          {/* 筛选和搜索区域 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-5 mb-6 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* 搜索框 */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="搜索用户名或邮箱..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`w-full pl-10 pr-4 py-2.5 rounded-lg border ${
                    theme === 'light' 
                      ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                      : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                  } transition-all duration-300`}
                />
                <i className="fas fa-search absolute left-3.5 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" />
              </div>

              {/* 角色筛选 */}
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className={`w-full px-4 py-2.5 rounded-lg border ${
                  theme === 'light' 
                    ? 'border-gray-300 bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                    : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                } transition-all duration-300`}
              >
                <option value="all">所有角色</option>
                <option value="admin">管理员</option>
                <option value="user">普通用户</option>
              </select>

              {/* 状态筛选 */}
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className={`w-full px-4 py-2.5 rounded-lg border ${
                  theme === 'light' 
                    ? 'border-gray-300 bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                    : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                } transition-all duration-300`}
              >
                <option value="all">所有状态</option>
                <option value="active">活跃</option>
                <option value="inactive">非活跃</option>
              </select>
            </div>
          </motion.div>

          {/* 用户列表 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className={`bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-850">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      用户名
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      邮箱
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      角色
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      状态
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      注册日期
                    </th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  <AnimatePresence>
                    {filteredUsers.length > 0 ? (
                      filteredUsers.map((user) => (
                        <motion.tr
                          key={user.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ duration: 0.3 }}
                          className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-10 w-10">
                                <img 
                                  className="h-10 w-10 rounded-full object-cover" 
                                  src={`https://ui-avatars.com/api/?name=${user.username}&background=random&color=fff`} 
                                  alt={user.username}
                                />
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900 dark:text-white">{user.username}</div>
                                {user.id === currentUser.id && (
                                  <div className="text-xs text-blue-500">（当前用户）</div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900 dark:text-gray-300">{user.email}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {editingUser?.id === user.id ? (
                              <select
                                value={editingUser.role}
                                onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                                disabled={user.id === currentUser.id}
                                className={`px-2 py-1 rounded border text-sm ${
                                  user.id === currentUser.id 
                                    ? (theme === 'light' ? 'border-gray-200 bg-gray-100 text-gray-500' : 'border-gray-700 bg-gray-850 text-gray-400')
                                    : (theme === 'light' ? 'border-gray-300' : 'border-gray-700 bg-gray-900 text-gray-100')
                                }`}
                              >
                                <option value="admin">管理员</option>
                                <option value="user">普通用户</option>
                              </select>
                            ) : (
                              renderRoleBadge(user.role)
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {editingUser?.id === user.id ? (
                              <select
                                value={editingUser.status}
                                onChange={(e) => setEditingUser({ ...editingUser, status: e.target.value })}
                                disabled={user.id === currentUser.id}
                                className={`px-2 py-1 rounded border text-sm ${
                                  user.id === currentUser.id 
                                    ? (theme === 'light' ? 'border-gray-200 bg-gray-100 text-gray-500' : 'border-gray-700 bg-gray-850 text-gray-400')
                                    : (theme === 'light' ? 'border-gray-300' : 'border-gray-700 bg-gray-900 text-gray-100')
                                }`}
                              >
                                <option value="active">活跃</option>
                                <option value="inactive">非活跃</option>
                              </select>
                            ) : (
                              renderStatusBadge(user.status)
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {user.registeredAt}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            {editingUser?.id === user.id ? (
                              <div className="flex justify-end gap-2">
                                <button
                                  onClick={handleCancelEdit}
                                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                >
                                  <i className="fas fa-times mr-1" /> 取消
                                </button>
                                <button
                                  onClick={handleSaveUser}
                                  disabled={loading}
                                  className="text-emerald-500 hover:text-emerald-600 dark:text-emerald-400 dark:hover:text-emerald-300"
                                >
                                  {loading ? (
                                    <i className="fas fa-spinner fa-spin mr-1" />
                                  ) : (
                                    <i className="fas fa-check mr-1" />
                                  )}
                                  保存
                                </button>
                              </div>
                            ) : (
                              <div className="flex justify-end gap-2">
                                <button
                                  onClick={() => handleEditUser(user)}
                                  className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
                                >
                                  <i className="fas fa-edit mr-1" /> 编辑
                                </button>
                                <button
                                  onClick={() => {
                                    if (user.id !== currentUser.id) {
                                      handleRoleChange(user.id, user.role === 'admin' ? 'user' : 'admin');
                                    }
                                  }}
                                  disabled={user.id === currentUser.id}
                                  className={`${
                                    user.role === 'admin' 
                                      ? 'text-yellow-500 hover:text-yellow-600 dark:text-yellow-400 dark:hover:text-yellow-300' 
                                      : 'text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300'
                                  } ${user.id === currentUser.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                  {user.role === 'admin' ? (
                                    <>
                                      <i className="fas fa-user-slash mr-1" /> 撤销管理
                                    </>
                                  ) : (
                                    <>
                                      <i className="fas fa-user-shield mr-1" /> 设为管理
                                    </>
                                  )}
                                </button>
                                <button
                                  onClick={() => handleStatusChange(user.id, user.status === 'active' ? 'inactive' : 'active')}
                                  disabled={user.id === currentUser.id}
                                  className={`${
                                    user.status === 'active' 
                                      ? 'text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300' 
                                      : 'text-green-500 hover:text-green-600 dark:text-green-400 dark:hover:text-green-300'
                                  } ${user.id === currentUser.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                  {user.status === 'active' ? (
                                    <>
                                      <i className="fas fa-ban mr-1" /> 禁用
                                    </>
                                  ) : (
                                    <>
                                      <i className="fas fa-check-circle mr-1" /> 启用
                                    </>
                                  )}
                                </button>
                                <button
                                  onClick={() => handleDeleteUser(user.id)}
                                  disabled={user.id === currentUser.id || loading}
                                  className={`text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 ${
                                    user.id === currentUser.id || loading ? 'opacity-50 cursor-not-allowed' : ''
                                  }`}
                                >
                                  {loading ? (
                                    <i className="fas fa-spinner fa-spin mr-1" />
                                  ) : (
                                    <i className="fas fa-trash-alt mr-1" />
                                  )}
                                  删除
                                </button>
                              </div>
                            )}
                          </td>
                        </motion.tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-6 py-10 text-center">
                          <div className="flex flex-col items-center">
                            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-750 rounded-full flex items-center justify-center mb-4">
                              <i className="fas fa-users text-gray-400 text-2xl" />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">未找到用户</h3>
                            <p className="text-gray-500 dark:text-gray-400 max-w-md">
                              尝试更改搜索条件或筛选器以查看更多用户
                            </p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>

            {/* 分页信息 */}
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-850 border-t border-gray-200 dark:border-gray-700 sm:px-6 flex items-center justify-between">
              <div className="flex-1 flex justify-between sm:hidden">
                <button className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:bg-gray-800 dark:hover:bg-gray-750">
                  上一页
                </button>
                <button className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:bg-gray-800 dark:hover:bg-gray-750">
                  下一页
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    显示 <span className="font-medium">{filteredUsers.length > 0 ? 1 : 0}</span> 到 <span className="font-medium">{filteredUsers.length}</span> 条，共 <span className="font-medium">{filteredUsers.length}</span> 条记录
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                    <button className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-750">
                      <span className="sr-only">上一页</span>
                      <i className="fas fa-chevron-left"></i>
                    </button>
                    <button className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-emerald-50 text-sm font-medium text-emerald-600 dark:border-gray-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                      1
                    </button>
                    <button className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-750">
                      <span className="sr-only">下一页</span>
                      <i className="fas fa-chevron-right"></i>
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </motion.div>

          {/* 管理提示 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl p-5 border border-blue-100 dark:border-blue-800/30"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              <i className="fas fa-info-circle text-blue-500 mr-2" />
              管理员提示
            </h3>
            
            <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
              <li className="flex items-start">
                <i className="fas fa-check-circle text-blue-500 mt-0.5 mr-2 flex-shrink-0" />
                <span>作为管理员，您可以管理所有用户的角色和状态</span>
              </li>
              <li className="flex items-start">
                <i className="fas fa-check-circle text-blue-500 mt-0.5 mr-2 flex-shrink-0" />
                <span>请谨慎操作，某些更改可能会影响用户的使用体验</span>
              </li>
              <li className="flex items-start">
                <i className="fas fa-check-circle text-blue-500 mt-0.5 mr-2 flex-shrink-0" />
                <span>您不能修改或删除自己的管理员账户</span>
              </li>
            </ul>
          </motion.div>
        </motion.div>
      </div>

      {/* 页脚 */}
      <footer className={`mt-12 py-6 border-t ${theme === 'light' ? 'border-gray-200' : 'border-gray-800'}`}>
        <div className="container mx-auto px-4 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>© 2025 植物花卉识别系统 | 探索自然之美</p>
        </div>
      </footer>
    </div>
  );
};

export default UserManagement;