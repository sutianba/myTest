import React, { useState } from 'react';
import { motion } from 'framer-motion';
import ImageUpload from '../components/ImageUpload';
import PlantRecognition, { PlantClassificationRules } from './PlantRecognition';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';
import { AuthContext } from '../contexts/authContext';

type TabType = 'upload' | 'explore';

const Home: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { isAuthenticated, logout, currentUser } = React.useContext(AuthContext);
  const [activeTab, setActiveTab] = useState<TabType>('upload');

  const tabs = [
    { id: 'upload', label: '图片识别', icon: 'fas fa-upload' },
    { id: 'explore', label: '植物探索', icon: 'fas fa-leaf' }
  ];

  // 额外功能项
  // 管理功能
  const adminFeatures = [
    { id: 'account', label: '账号管理', icon: 'fas fa-user-cog', description: '管理您的个人信息' },
    { id: 'users', label: '用户管理', icon: 'fas fa-users-cog', description: '管理系统用户' },
    { id: 'permissions', label: '权限管理', icon: 'fas fa-shield-alt', description: '管理用户权限' }
  ];

  // 额外功能项
  const extraFeatures = [
    { id: 'favorites', label: '我的收藏', icon: 'fas fa-heart', description: '查看您收藏的植物', route: '/favorites' },
    { id: 'history', label: '识别历史', icon: 'fas fa-history', description: '查看您的识别记录', route: '/history' },
    { id: 'community', label: '花卉社区', icon: 'fas fa-comments', description: '分享您的花卉识别经验', route: '/community' },
    { id: 'encyclopedia', label: '植物百科', icon: 'fas fa-book', description: '浏览植物知识库', route: '/explore' },
    { id: 'care-guide', label: '养护建议', icon: 'fas fa-trowel', description: '获取植物养护指南', route: '/other' }
  ];

  // 处理额外功能点击
  const handleFeatureClick = (feature: { id: string, label: string, route?: string }) => {
    if (feature.route) {
      window.location.href = feature.route;
    } else {
      toast.info(`${feature.label}功能即将上线，敬请期待！`);
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
            
            {isAuthenticated && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  logout();
                  window.location.href = '/login';
                }}
                className="px-4 py-2 bg-red-500 text-white rounded-full text-sm font-medium hover:bg-red-600 transition-colors flex items-center"
              >
                <i className="fas fa-sign-out-alt mr-2" />
                退出登录
              </motion.button>
            )}
          </div>
        </div>
      </header>

      {/* 主要内容区域 */}
      <div className="container mx-auto px-4 py-8 flex flex-col md:flex-row gap-8">
        {/* 左侧标签导航 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="md:w-64 shrink-0"
        >
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md border border-gray-100 dark:border-gray-700 overflow-hidden sticky top-24">
            <div className="p-4 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-850">
              <h2 className="font-semibold text-gray-900 dark:text-white">功能导航</h2>
            </div>
            <nav className="p-2">
              {tabs.map((tab) => (
                <motion.button
                  key={tab.id}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all
                    ${activeTab === tab.id 
                      ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 font-medium' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-750'
                    }
                  `}
                >
                  <i className={tab.icon} />
                  <span>{tab.label}</span>
                </motion.button>
              ))}
              
              {/* 功能分隔线 */}
              <div className="my-2 border-t border-gray-100 dark:border-gray-700" />
              
              {/* 管理功能标题 */}
              <div className="px-4 py-2">
                <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  管理功能
                </h3>
              </div>
              
              {/* 管理功能项 */}
              {adminFeatures.map((feature) => (
                <motion.button
                  key={feature.id}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    window.location.href = `/${feature.id}`;
                  }}
                  className="w-full flex flex-col items-start gap-1 px-4 py-3 rounded-xl transition-all text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-750 group"
                >
                  <div className="flex items-center gap-3">
                    <i className={`${feature.icon} text-gray-500 dark:text-gray-400 group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors`} />
                    <span className="font-medium">{feature.label}</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 ml-8 opacity-0 group-hover:opacity-100 transition-opacity">
                    {feature.description}
                  </p>
                </motion.button>
              ))}
              
              {/* 功能分隔线 */}
              <div className="my-2 border-t border-gray-100 dark:border-gray-700" />
              
              {/* 额外功能标题 */}
              <div className="px-4 py-2">
                <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  更多工具
                </h3>
              </div>
              
               {/* 额外功能项 */}
               {extraFeatures.map((feature) => (
                 <motion.button
                   key={feature.id}
                   whileHover={{ x: 4 }}
                   whileTap={{ scale: 0.98 }}
                   onClick={() => handleFeatureClick(feature)}
                   className={`w-full flex flex-col items-start gap-1 px-4 py-3 rounded-xl transition-all ${
                     (window.location.pathname === feature.route || 
                      (feature.id === 'encyclopedia' && window.location.pathname === '/explore'))
                       ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 font-medium' 
                       : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-750'
                   } group`}
                 >
                   <div className="flex items-center gap-3">
                     <i className={`${feature.icon} text-gray-500 dark:text-gray-400 group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors`} />
                     <span className="font-medium">{feature.label}</span>
                   </div>
                   <p className="text-xs text-gray-500 dark:text-gray-400 ml-8 opacity-0 group-hover:opacity-100 transition-opacity">
                     {feature.description}
                   </p>
                 </motion.button>
               ))}
            </nav>
          </div>
          
          {/* 植物识别统计卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mt-6 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl shadow-lg p-5 text-white"
          >
            <h3 className="font-semibold mb-3 flex items-center">
              <i className="fas fa-chart-line mr-2" />
              识别统计
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm">植物种类</span>
                <span className="font-bold text-lg">10,000+</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">准确率</span>
                <span className="font-bold text-lg">98.7%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">全球用户</span>
                <span className="font-bold text-lg">500万+</span>
              </div>
            </div>
          </motion.div>
        </motion.div>
        
        {/* 右侧主内容 */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="flex-1"
        >
          {activeTab === 'upload' ? (
            <ImageUpload />
          ) : (
            <PlantRecognition />
          )}
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

export default Home;