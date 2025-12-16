import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { AuthContext } from '../contexts/authContext';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';

const AccountManagement: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { currentUser } = useContext(AuthContext);
  const [formData, setFormData] = useState({
    username: currentUser.username,
    email: currentUser.email,
    avatar: `https://ui-avatars.com/api/?name=${currentUser.username}&background=random&color=fff`
  });
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
  };

  const handleUpdateProfile = async () => {
    setLoading(true);
    
    try {
      // 模拟API请求
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('个人资料更新成功！');
      setIsEditing(false);
    } catch (error) {
      toast.error('更新失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    // 验证密码
    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmNewPassword) {
      toast.error('请填写所有密码字段');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      toast.error('新密码长度至少为6位');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmNewPassword) {
      toast.error('两次输入的新密码不一致');
      return;
    }

    setLoading(true);
    
    try {
      // 模拟API请求
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('密码修改成功！');
      // 重置密码表单
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmNewPassword: ''
      });
    } catch (error) {
      toast.error('密码修改失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // 模拟图片上传
      const reader = new FileReader();
      reader.onload = (event) => {
        setFormData(prev => ({ ...prev, avatar: event.target?.result as string }));
        toast.success('头像上传成功！');
      };
      reader.readAsDataURL(file);
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
                src={formData.avatar} 
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
          className="max-w-3xl mx-auto"
        >
          {/* 页面标题 */}
          <div className="mb-8 text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">账号管理</h2>
            <p className="text-gray-600 dark:text-gray-400">管理您的个人资料和账号设置</p>
          </div>

          {/* 账户信息卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={`bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 mb-6 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            <div className="flex flex-col items-center mb-6">
              <div className="relative mb-4">
                <img 
                  src={formData.avatar} 
                  alt="用户头像"
                  className="w-24 h-24 rounded-full object-cover border-4 border-emerald-100 dark:border-emerald-900/30"
                />
                <label className="absolute bottom-0 right-0 bg-emerald-500 text-white rounded-full p-2 cursor-pointer shadow-md hover:bg-emerald-600 transition-colors">
                  <i className="fas fa-camera"></i>
                  <input 
                    type="file" 
                    accept="image/*" 
                    className="hidden" 
                    onChange={handleAvatarUpload}
                  />
                </label>
              </div>
              
              <div className="text-center">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{formData.username}</h3>
                <p className="text-gray-600 dark:text-gray-400">{formData.email}</p>
                <p className="text-sm text-emerald-500 mt-1">{currentUser.role === 'admin' ? '管理员' : '普通用户'}</p>
              </div>
            </div>

            {/* 个人资料表单 */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    用户名
                  </label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className={`w-full px-4 py-3 rounded-lg border ${
                      isEditing 
                        ? (theme === 'light' 
                          ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                          : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500')
                        : (theme === 'light' 
                          ? 'border-gray-200 bg-gray-50' 
                          : 'border-gray-700 bg-gray-850 text-gray-400')
                    } transition-all duration-300`}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    邮箱
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className={`w-full px-4 py-3 rounded-lg border ${
                      isEditing 
                        ? (theme === 'light' 
                          ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                          : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500')
                        : (theme === 'light' 
                          ? 'border-gray-200 bg-gray-50' 
                          : 'border-gray-700 bg-gray-850 text-gray-400')
                    } transition-all duration-300`}
                  />
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex justify-center gap-4 mt-6">
                {isEditing ? (
                  <>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        setIsEditing(false);
                        // 重置表单数据
                        setFormData({
                          username: currentUser.username,
                          email: currentUser.email,
                          avatar: formData.avatar
                        });
                      }}
                      className="px-6 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                    >
                      取消
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleUpdateProfile}
                      disabled={loading}
                      className="px-6 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
                    >
                      {loading ? (
                        <>
                          <i className="fas fa-spinner fa-spin mr-2" />
                          保存中...
                        </>
                      ) : (
                        <>
                          <i className="fas fa-save mr-2" />
                          保存
                        </>
                      )}
                    </motion.button>
                  </>
                ) : (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setIsEditing(true)}
                    className="px-6 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
                  >
                    <i className="fas fa-edit mr-2" />
                    编辑资料
                  </motion.button>
                )}
              </div>
            </div>
          </motion.div>

          {/* 密码修改卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className={`bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 mb-6 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center">
              <i className="fas fa-lock text-emerald-500 mr-2" />
              修改密码
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  当前密码
                </label>
                <input
                  type="password"
                  name="currentPassword"
                  value={passwordData.currentPassword}
                  onChange={handlePasswordChange}
                  placeholder="请输入当前密码"
                  className={`w-full px-4 py-3 rounded-lg border ${
                    theme === 'light' 
                      ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                      : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                  } transition-all duration-300`}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  新密码
                </label>
                <input
                  type="password"
                  name="newPassword"
                  value={passwordData.newPassword}
                  onChange={handlePasswordChange}
                  placeholder="请输入新密码"
                  className={`w-full px-4 py-3 rounded-lg border ${
                    theme === 'light' 
                      ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                      : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                  } transition-all duration-300`}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">密码长度至少为6位</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  确认新密码
                </label>
                <input
                  type="password"
                  name="confirmNewPassword"
                  value={passwordData.confirmNewPassword}
                  onChange={handlePasswordChange}
                  placeholder="请再次输入新密码"
                  className={`w-full px-4 py-3 rounded-lg border ${
                    theme === 'light' 
                      ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                      : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                  } transition-all duration-300`}
                />
              </div>

              {/* 修改密码按钮 */}
              <div className="flex justify-center mt-6">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleChangePassword}
                  disabled={loading}
                  className="px-6 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
                >
                  {loading ? (
                    <>
                      <i className="fas fa-spinner fa-spin mr-2" />
                      修改中...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-key mr-2" />
                      修改密码
                    </>
                  )}
                </motion.button>
              </div>
            </div>
          </motion.div>

          {/* 账号安全提示 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-5 border border-emerald-100 dark:border-emerald-800/30"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              <i className="fas fa-shield-alt text-emerald-500 mr-2" />
              账号安全提示
            </h3>
            
            <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
              <li className="flex items-start">
                <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                <span>定期修改密码，使用强密码保护您的账号</span>
              </li>
              <li className="flex items-start">
                <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                <span>不要与他人共享您的账号信息</span>
              </li>
              <li className="flex items-start">
                <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                <span>确保您的邮箱地址是有效的，以便找回密码</span>
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

export default AccountManagement;