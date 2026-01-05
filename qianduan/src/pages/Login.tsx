import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/authContext';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';

const Login: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      toast.error('请填写所有字段');
      return;
    }

    setLoading(true);

    // 真实登录请求
    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',  // 包含cookie以支持会话
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 登录成功
        const userData = {
          id: '1', // 后端可能没有返回id，暂时使用固定值
          username: formData.username,
          email: `${formData.username}@example.com`,
          role: data.role || 'user'
        };
        
        login(userData);
        toast.success('登录成功！');
        navigate('/');
      } else {
        // 登录失败
        toast.error(data.error || '登录失败，请检查用户名和密码');
      }
    } catch (error) {
      console.error('登录错误:', error);
      toast.error('登录失败，请检查网络连接或稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = () => {
    navigate('/register');
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 transition-colors duration-300 ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-900'}`}>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* 登录卡片 */}
        <div className={`bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}>
          {/* Logo和标题 */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-4"
            >
              <i className="fas fa-leaf text-emerald-500 text-2xl" />
            </motion.div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">植物花卉识别系统</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">登录您的账号</p>
          </div>

          {/* 登录表单 */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                用户名
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="请输入用户名"
                className={`w-full px-4 py-3 rounded-lg border ${
                  theme === 'light' 
                    ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                    : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                } transition-all duration-300`}
                required
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  密码
                </label>
              </div>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="请输入密码"
                className={`w-full px-4 py-3 rounded-lg border ${
                  theme === 'light' 
                    ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                    : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                } transition-all duration-300`}
                required
              />
            </div>

            <motion.button
              type="submit"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={loading}
              className="w-full px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-lg transition-colors duration-300 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin" />
                  登录中...
                </>
              ) : (
                <>
                  <i className="fas fa-sign-in-alt" />
                  登录
                </>
              )}
            </motion.button>
           </form>

           {/* 跳过登录按钮 */}
           <motion.button
             whileHover={{ scale: 1.02 }}
             whileTap={{ scale: 0.98 }}
             onClick={() => {
               const guestUser = {
                 id: 'guest',
                 username: '访客',
                 email: 'guest@example.com',
                 role: 'user'
               };
               login(guestUser);
               toast.success('已以访客身份进入系统');
               navigate('/');
             }}
             className="w-full mt-4 px-6 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-850 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-300"
           >
             <i className="fas fa-arrow-right mr-2" />
             跳过登录，直接体验
           </motion.button>

           {/* 注册链接 */}
           <div className="mt-6 text-center">
             <p className="text-gray-600 dark:text-gray-400 text-sm">
               还没有账号？{' '}
               <button
                 onClick={handleRegister}
                 className="text-emerald-500 hover:text-emerald-600 font-medium transition-colors duration-300"
               >
                 立即注册
               </button>
             </p>
           </div>
        </div>

        {/* 主题切换按钮 */}
        <motion.button
          whileHover={{ rotate: 180 }}
          transition={{ duration: 0.3 }}
          onClick={toggleTheme}
          className={`absolute top-4 right-4 p-2 rounded-full ${
            theme === 'light' ? 'bg-white text-gray-800' : 'bg-gray-800 text-gray-200'
          } shadow-md`}
          aria-label="切换主题"
        >
          {theme === 'light' ? (
            <i className="fas fa-moon" />
          ) : (
            <i className="fas fa-sun" />
          )}
        </motion.button>
      </motion.div>
    </div>
  );
};

export default Login;