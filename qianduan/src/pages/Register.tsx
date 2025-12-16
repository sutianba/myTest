import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/authContext';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';

const Register: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 表单验证
    if (!formData.username || !formData.password) {
      toast.error('请填写所有必填字段');
      return;
    }
    
    if (formData.password.length < 6) {
      toast.error('密码长度至少为6位');
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);

    // 真实注册请求
    try {
      const response = await fetch('http://localhost:5000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 注册成功后跳转到登录页面
        toast.success('注册成功，请登录！');
        navigate('/login');
      } else {
        // 注册失败
        toast.error(data.error || '注册失败，请稍后重试');
      }
    } catch (error) {
      console.error('注册错误:', error);
      toast.error('注册失败，请检查网络连接或稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = () => {
    navigate('/login');
  };



  return (
    <div className={`min-h-screen flex items-center justify-center p-4 transition-colors duration-300 ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-900'}`}>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* 注册卡片 */}
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">创建账号</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">加入植物花卉识别系统</p>
          </div>

          {/* 注册表单 */}
          <form onSubmit={handleSubmit} className="space-y-5">
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
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                密码
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="请设置密码"
                  className={`w-full px-4 py-3 pr-10 rounded-lg border ${
                    theme === 'light' 
                      ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                      : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                  } transition-all duration-300`}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  {showPassword ? (
                    <i className="fas fa-eye-slash" />
                  ) : (
                    <i className="fas fa-eye" />
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">密码长度至少为6位</p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                确认密码
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="请再次输入密码"
                  className={`w-full px-4 py-3 pr-10 rounded-lg border ${
                    theme === 'light' 
                      ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                      : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                  } transition-all duration-300`}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  {showConfirmPassword ? (
                    <i className="fas fa-eye-slash" />
                  ) : (
                    <i className="fas fa-eye" />
                  )}
                </button>
              </div>
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
                  注册中...
                </>
              ) : (
                <>
                  <i className="fas fa-user-plus" />
                  注册
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
             跳过注册，直接体验
           </motion.button>

           {/* 登录链接 */}
           <div className="mt-6 text-center">
             <p className="text-gray-600 dark:text-gray-400 text-sm">
               已有账号？{' '}
               <button
                 onClick={handleLogin}
                 className="text-emerald-500 hover:text-emerald-600 font-medium transition-colors duration-300"
               >
                 立即登录
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

export default Register;