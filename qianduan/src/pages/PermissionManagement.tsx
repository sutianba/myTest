import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { AuthContext } from '../contexts/authContext';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// 模拟角色权限数据
const mockRoles = [
  { 
    id: '1', 
    name: '管理员', 
    key: 'admin', 
    description: '系统管理员，拥有所有权限',
    permissions: {
      viewDashboard: true,
      manageUsers: true,
      managePermissions: true,
      uploadImages: true,
      recognizePlants: true,
      viewHistory: true,
      manageCollection: true,
      accessAPI: true
    }
  },
  { 
    id: '2', 
    name: '普通用户', 
    key: 'user', 
    description: '标准用户权限',
    permissions: {
      viewDashboard: true,
      manageUsers: false,
      managePermissions: false,
      uploadImages: true,
      recognizePlants: true,
      viewHistory: true,
      manageCollection: true,
      accessAPI: false
    }
  },
  { 
    id: '3', 
    name: '访客', 
    key: 'guest', 
    description: '只读权限，限制功能访问',
    permissions: {
      viewDashboard: true,
      manageUsers: false,
      managePermissions: false,
      uploadImages: false,
      recognizePlants: false,
      viewHistory: false,
      manageCollection: false,
      accessAPI: false
    }
  }
];

// 权限定义
const permissionsDefinition = [
  { key: 'viewDashboard', name: '查看仪表盘', category: '基础功能' },
  { key: 'manageUsers', name: '管理用户', category: '管理功能' },
  { key: 'managePermissions', name: '管理权限', category: '管理功能' },
  { key: 'uploadImages', name: '上传图片', category: '识别功能' },
  { key: 'recognizePlants', name: '识别植物', category: '识别功能' },
  { key: 'viewHistory', name: '查看历史记录', category: '历史功能' },
  { key: 'manageCollection', name: '管理收藏', category: '收藏功能' },
  { key: 'accessAPI', name: '访问API', category: '高级功能' }
];

// 角色使用统计数据
const roleUsageData = [
  { name: '管理员', count: 1, fill: '#3b82f6' },
  { name: '普通用户', count: 125, fill: '#10b981' },
  { name: '访客', count: 42, fill: '#f59e0b' }
];

const PermissionManagement: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { currentUser } = useContext(AuthContext);
  const [roles, setRoles] = useState(mockRoles);
  const [selectedRole, setSelectedRole] = useState(mockRoles[0]);
  const [newRole, setNewRole] = useState({ name: '', key: '', description: '' });
  const [isAddingRole, setIsAddingRole] = useState(false);
  const [editingRole, setEditingRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 处理权限变更
  const handlePermissionChange = (permissionKey: string) => {
    // 不允许取消管理员自己的管理员权限
    if (selectedRole.key === 'admin' && permissionKey === 'managePermissions' && currentUser.role === 'admin') {
      toast.error('您不能取消管理员的管理权限');
      return;
    }

    setRoles(prevRoles => 
      prevRoles.map(role => {
        if (role.id === selectedRole.id) {
          return {
            ...role,
            permissions: {
              ...role.permissions,
              [permissionKey]: !role.permissions[permissionKey as keyof typeof role.permissions]
            }
          };
        }
        return role;
      })
    );
    
    // 更新当前选中的角色
    setSelectedRole(prev => ({
      ...prev,
      permissions: {
        ...prev.permissions,
        [permissionKey]: !prev.permissions[permissionKey as keyof typeof prev.permissions]
      }
    }));
    
    toast.success('权限已更新');
  };

  // 保存角色信息
  const handleSaveRole = () => {
    // 验证表单
    if (!newRole.name.trim() || !newRole.key.trim()) {
      toast.error('角色名称和角色标识不能为空');
      return;
    }

    // 检查角色标识是否已存在
    const existingRole = roles.find(role => role.key === newRole.key);
    if (existingRole && editingRole !== newRole.key) {
      toast.error('角色标识已存在，请使用其他标识');
      return;
    }

    setLoading(true);

    // 模拟保存操作
    setTimeout(() => {
      if (editingRole) {
        // 更新现有角色
        setRoles(prevRoles => 
          prevRoles.map(role => 
            role.key === editingRole 
              ? { 
                  ...role, 
                  name: newRole.name, 
                  key: newRole.key, 
                  description: newRole.description 
                } 
              : role
          )
        );
        
        // 如果当前选中的是正在编辑的角色，更新选中的角色
        if (selectedRole.key === editingRole) {
          setSelectedRole(prev => ({
            ...prev,
            name: newRole.name,
            key: newRole.key,
            description: newRole.description
          }));
        }
        
        toast.success('角色信息已更新');
      } else {
        // 添加新角色
        const newRoleObj = {
          id: Date.now().toString(),
          ...newRole,
          permissions: {
            viewDashboard: true,
            manageUsers: false,
            managePermissions: false,
            uploadImages: true,
            recognizePlants: true,
            viewHistory: true,
            manageCollection: true,
            accessAPI: false
          }
        };
        
        setRoles(prevRoles => [...prevRoles, newRoleObj]);
        setSelectedRole(newRoleObj);
        toast.success('新角色已添加');
      }
      
      // 重置表单
      setNewRole({ name: '', key: '', description: '' });
      setIsAddingRole(false);
      setEditingRole(null);
      setLoading(false);
    }, 500);
  };

  // 删除角色
  const handleDeleteRole = (roleKey: string) => {
    // 不允许删除管理员角色
    if (roleKey === 'admin') {
      toast.error('不能删除管理员角色');
      return;
    }

    // 如果当前选中的是要删除的角色，选择默认角色
    if (selectedRole.key === roleKey) {
      const defaultRole = roles.find(role => role.key === 'admin') || roles[0];
      setSelectedRole(defaultRole);
    }

    setLoading(true);

    // 模拟删除操作
    setTimeout(() => {
      setRoles(prevRoles => prevRoles.filter(role => role.key !== roleKey));
      toast.success('角色已删除');
      setLoading(false);
    }, 500);
  };

  // 开始编辑角色
  const handleEditRole = (role: any) => {
    setNewRole({
      name: role.name,
      key: role.key,
      description: role.description || ''
    });
    setEditingRole(role.key);
    setIsAddingRole(true);
  };

  // 取消添加/编辑角色
  const handleCancelAddRole = () => {
    setNewRole({ name: '', key: '', description: '' });
    setIsAddingRole(false);
    setEditingRole(null);
  };

  // 渲染权限类别
  const renderPermissionCategories = () => {
    const categories: { [key: string]: typeof permissionsDefinition } = {};
    
    permissionsDefinition.forEach(permission => {
      if (!categories[permission.category]) {
        categories[permission.category] = [];
      }
      categories[permission.category].push(permission);
    });
    
    return Object.entries(categories).map(([category, permissions]) => (
      <div key={category} className="mb-6">
        <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
          {category}
        </h4>
        <div className="space-y-2">
          {permissions.map(permission => {
            const isChecked = selectedRole.permissions[permission.key as keyof typeof selectedRole.permissions];
            const isDisabled = permission.key === 'managePermissions' && selectedRole.key === 'admin' && currentUser.role === 'admin';
            
            return (
              <div key={permission.key} className={`flex items-center justify-between p-3 rounded-lg border ${
                theme === 'light' 
                  ? 'border-gray-200 hover:border-gray-300' 
                  : 'border-gray-700 hover:border-gray-600'
              } transition-colors`}>
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <input
                      id={permission.key}
                      name={permission.key}
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handlePermissionChange(permission.key)}
                      disabled={isDisabled}
                      className="h-5 w-5 text-emerald-500 focus:ring-emerald-500 border-gray-300 rounded dark:border-gray-600 dark:bg-gray-800"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor={permission.key} className={`font-medium ${
                      isDisabled ? 'text-gray-400 cursor-not-allowed' : 'text-gray-900 dark:text-white'
                    }`}>
                      {permission.name}
                    </label>
                  </div>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {permission.key}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    ));
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
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">权限管理</h2>
            <p className="text-gray-600 dark:text-gray-400">管理系统角色和权限配置</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧角色列表 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className={`bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
            >
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-850 flex items-center justify-between">
                <h3 className="font-semibold text-gray-900 dark:text-white">角色列表</h3>
                <button
                  onClick={() => {
                    setIsAddingRole(!isAddingRole);
                    setEditingRole(null);
                    setNewRole({ name: '', key: '', description: '' });
                  }}
                  className="p-2 rounded-lg text-emerald-500 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
                  aria-label={isAddingRole ? "取消添加角色" : "添加新角色"}
                >
                  {isAddingRole ? (
                    <i className="fas fa-times" />
                  ) : (
                    <i className="fas fa-plus" />
                  )}
                </button>
              </div>
              
              {/* 添加/编辑角色表单 */}
              {isAddingRole && (
                <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-850">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                    {editingRole ? '编辑角色' : '添加新角色'}
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        角色名称
                      </label>
                      <input
                        type="text"
                        placeholder="输入角色名称"
                        value={newRole.name}
                        onChange={(e) => setNewRole({ ...newRole, name: e.target.value })}
                        className={`w-full px-3 py-2 rounded-lg border ${
                          theme === 'light' 
                            ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                            : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                        } transition-all duration-300 text-sm`}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        角色标识
                      </label>
                      <input
                        type="text"
                        placeholder="输入角色标识 (英文/数字/下划线)"
                        value={newRole.key}
                        onChange={(e) => setNewRole({ ...newRole, key: e.target.value.replace(/[^a-zA-Z0-9_]/g, '') })}
                        disabled={editingRole === 'admin'}
                        className={`w-full px-3 py-2 rounded-lg border ${
                          editingRole === 'admin'
                            ? (theme === 'light' ? 'border-gray-200 bg-gray-100 text-gray-500' : 'border-gray-700 bg-gray-850 text-gray-400')
                            : (theme === 'light' 
                              ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                              : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500')
                        } transition-all duration-300 text-sm`}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        角色描述
                      </label>
                      <textarea
                        placeholder="输入角色描述（可选）"
                        value={newRole.description}
                        onChange={(e) => setNewRole({ ...newRole, description: e.target.value })}
                        rows={2}
                        className={`w-full px-3 py-2 rounded-lg border ${
                          theme === 'light' 
                            ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                            : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                        } transition-all duration-300 text-sm resize-none`}
                      />
                    </div>
                    
                    <div className="flex gap-2 mt-4">
                      <button
                        onClick={handleSaveRole}
                        disabled={loading}
                        className="flex-1 px-3 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-colors flex items-center justify-center"
                      >
                        {loading ? (
                          <>
                            <i className="fas fa-spinner fa-spin mr-1" />
                            保存中...
                          </>
                        ) : (
                          '保存'
                        )}
                      </button>
                      <button
                        onClick={handleCancelAddRole}
                        className="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {/* 角色列表 */}
              <div className="max-h-[calc(100vh-360px)] overflow-y-auto">
                {roles.map((role) => (
                  <div
                    key={role.id}
                    onClick={() => {
                      setSelectedRole(role);
                      setEditingRole(null);
                      setIsAddingRole(false);
                    }}
                    className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors border-b border-gray-100 dark:border-gray-700 last:border-b-0 ${
                      selectedRole.id === role.id 
                        ? 'bg-emerald-50 dark:bg-emerald-900/20 border-l-4 border-l-emerald-500' 
                        : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">{role.name}</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{role.key}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditRole(role);
                          }}
                          disabled={role.key === 'admin'}
                          className={`p-1.5 rounded-lg text-sm ${
                            role.key === 'admin' 
                              ? 'text-gray-400 cursor-not-allowed' 
                              : 'text-blue-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors'
                          }`}
                          aria-label="编辑角色"
                        >
                          <i className="fas fa-edit" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm(`确定要删除角色"${role.name}"吗？`)) {
                              handleDeleteRole(role.key);
                            }
                          }}
                          disabled={role.key === 'admin'}
                          className={`p-1.5 rounded-lg text-sm ${
                            role.key === 'admin' 
                              ? 'text-gray-400 cursor-not-allowed' 
                              : 'text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors'
                          }`}
                          aria-label="删除角色"
                        >
                          <i className="fas fa-trash-alt" />
                        </button>
                      </div>
                    </div>
                    {role.description && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{role.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>

            {/* 右侧权限配置和统计 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 当前角色权限配置 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className={`bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
              >
                <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-850">
                  <h3 className="font-semibold text-gray-900 dark:text-white">权限配置</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    配置 <span className="font-medium">{selectedRole.name}</span> 角色的权限
                  </p>
                </div>
                
                <div className="p-4">
                  {renderPermissionCategories()}
                </div>
              </motion.div>

              {/* 角色使用统计 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className={`bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
              >
                <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-850">
                  <h3 className="font-semibold text-gray-900 dark:text-white">角色使用统计</h3>
                </div>
                
                <div className="p-4">
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={roleUsageData}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke={theme === 'light' ? '#e5e7eb' : '#374151'} />
                        <XAxis 
                          dataKey="name" 
                          tick={{ fill: theme === 'light' ? '#4b5563' : '#d1d5db' }} 
                        />
                        <YAxis 
                          tick={{ fill: theme === 'light' ? '#4b5563' : '#d1d5db' }} 
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: theme === 'light' ? '#ffffff' : '#1f2937',
                            border: `1px solid ${theme === 'light' ? '#e5e7eb' : '#374151'}`,
                            borderRadius: '0.5rem',
                            color: theme === 'light' ? '#111827' : '#f9fafb'
                          }} 
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  <div className="mt-4 grid grid-cols-3 gap-4">
                    {roleUsageData.map((item) => (
                      <div 
                        key={item.name} 
                        className={`p-4 rounded-lg border ${
                          theme === 'light' 
                            ? 'border-gray-200 bg-gray-50' 
                            : 'border-gray-700 bg-gray-850'
                        }`}
                      >
                        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">{item.name}</h4>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{item.count}</p>
                        <div 
                          className="h-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full mt-2"
                          style={{ 
                            backgroundColor: theme === 'light' ? '#e5e7eb' : '#374151' 
                          }}
                        >
                          <div 
                            className="h-1 rounded-full" 
                            style={{ 
                              width: `${(item.count / Math.max(...roleUsageData.map(d => d.count))) * 100}%`,
                              backgroundColor: item.fill
                            }} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* 权限管理提示 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-5 border border-purple-100 dark:border-purple-800/30"
              >
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                  <i className="fas fa-info-circle text-purple-500 mr-2" />
                  权限管理说明
                </h3>
                
                <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                  <li className="flex items-start">
                    <i className="fas fa-check-circle text-purple-500 mt-0.5 mr-2 flex-shrink-0" />
                    <span>系统使用角色-权限模型来控制用户对功能的访问</span>
                  </li>
                  <li className="flex items-start">
                    <i className="fas fa-check-circle text-purple-500 mt-0.5 mr-2 flex-shrink-0" />
                    <span>管理员角色拥有系统的所有权限，包括管理其他用户和权限</span>
                  </li>
                  <li className="flex items-start">
                    <i className="fas fa-check-circle text-purple-500 mt-0.5 mr-2 flex-shrink-0" />
                    <span>普通用户角色拥有基本的识别和收藏功能</span>
                  </li>
                  <li className="flex items-start">
                    <i className="fas fa-check-circle text-purple-500 mt-0.5 mr-2 flex-shrink-0" />
                    <span>您可以创建自定义角色并配置特定的权限组合</span>
                  </li>
                </ul>
              </motion.div>
            </div>
          </div>
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

export default PermissionManagement;