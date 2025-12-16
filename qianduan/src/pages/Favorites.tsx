import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { Plant } from '../types/plant';
import { plants } from '../mock/plants';
import PlantCard from '../components/PlantCard';
import { toast } from 'sonner';

const Favorites: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState<Plant[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 从localStorage加载收藏的植物ID
    const favoriteIds = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    // 如果没有收藏记录，使用一些默认的收藏数据
    if (favoriteIds.length === 0) {
      // 默认收藏前两个植物
      const defaultFavorites = plants.slice(0, 2);
      setFavorites(defaultFavorites);
      
      // 将默认收藏保存到localStorage
      const defaultIds = defaultFavorites.map(plant => plant.id);
      localStorage.setItem('favorites', JSON.stringify(defaultIds));
    } else {
      // 根据ID获取植物对象
      const favoritePlants = plants.filter(plant => favoriteIds.includes(plant.id));
      setFavorites(favoritePlants);
    }
    
    setIsLoading(false);
  }, []);

  // 切换收藏状态
  const toggleFavorite = (plantId: string) => {
    // 获取当前收藏列表
    const currentFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    // 检查植物是否已在收藏中
    const isCurrentlyFavorite = currentFavorites.includes(plantId);
    
    let updatedFavorites: string[];
    
    if (isCurrentlyFavorite) {
      // 从收藏中移除
      updatedFavorites = currentFavorites.filter((id: string) => id !== plantId);
      toast.success('已从收藏夹移除');
    } else {
      // 添加到收藏
      updatedFavorites = [...currentFavorites, plantId];
      toast.success('已添加到收藏夹');
    }
    
    // 更新localStorage
    localStorage.setItem('favorites', JSON.stringify(updatedFavorites));
    
    // 更新UI
    setFavorites(prev => 
      isCurrentlyFavorite 
        ? prev.filter(plant => plant.id !== plantId)
        : [...prev, plants.find(plant => plant.id === plantId)!]
    );
  };

  // 检查植物是否在收藏中
  const isPlantFavorite = (plantId: string): boolean => {
    return favorites.some(plant => plant.id === plantId);
  };

  if (isLoading) {
    return (
      <div className={`min-h-screen flex flex-col ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-900'}`}>
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
            </div>
          </div>
        </header>

        {/* 主要内容区域 */}
        <div className="container mx-auto px-4 py-8 flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mb-4">
              <i className="fas fa-heart text-emerald-500 text-2xl animate-pulse" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">加载收藏的植物中...</h2>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-300 ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-900'}`}>
      {/* 顶部导航 */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => navigate('/')}
              className="p-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              aria-label="返回"
            >
              <i className="fas fa-arrow-left" />
            </motion.button>
            
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-500 to-teal-600 bg-clip-text text-transparent">
              我的收藏
            </h1>
          </div>
          
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
          </div>
        </div>
      </header>

      {/* 主要内容区域 */}
      <div className="container mx-auto px-4 py-8 flex-1">
        <div className="max-w-6xl mx-auto">
          {/* 页面标题 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">我的收藏植物</h2>
            <p className="text-gray-600 dark:text-gray-400">
              您已收藏 {favorites.length} 种植物
            </p>
          </motion.div>
          
          {/* 收藏的植物列表 */}
          {favorites.length > 0 ? (
            <motion.div
              layout
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            >
              <AnimatePresence>
                {favorites.map((plant) => (
                  <motion.div
                    key={plant.id}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.3 }}
                  >
                    <PlantCard 
                      plant={plant}
                      showFavorite={true}
                      isFavorite={isPlantFavorite(plant.id)}
                      onToggleFavorite={toggleFavorite}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 text-center border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
            >
              <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
                <i className="fas fa-heart text-gray-400 dark:text-gray-500 text-2xl" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">暂无收藏的植物</h3>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                浏览植物并点击心形图标将喜欢的植物添加到收藏夹中
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/explore')}
                className="mt-6 px-6 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
              >
                <i className="fas fa-search mr-2" />
                浏览植物
              </motion.button>
            </motion.div>
          )}
          
          {/* 收藏统计卡片 */}
          {favorites.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className={`mt-8 bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">收藏统计</h3>
              
              {/* 按分类统计 */}
              <div className="space-y-4">
                {(() => {
                  // 计算各类别植物数量
                  const categoryCount: Record<string, number> = {};
                  favorites.forEach(plant => {
                    categoryCount[plant.category] = (categoryCount[plant.category] || 0) + 1;
                  });
                  
                  // 转换为数组并排序
                  const categoryStats = Object.entries(categoryCount)
                    .map(([category, count]) => ({ category, count }))
                    .sort((a, b) => b.count - a.count);
                  
                  // 映射类别ID到名称
                  const categoryNames: Record<string, string> = {
                    'flower': '花卉',
                    'tree': '树木',
                    'bush': '灌木',
                    'herb': '草本',
                    'vine': '藤蔓',
                    'succulent': '多肉',
                    'fern': '蕨类',
                    'grass': '草类'
                  };
                  
                  return (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      {categoryStats.map(({ category, count }) => (
                        <div 
                          key={category}
                          className={`p-4 rounded-lg ${
                            theme === 'light' ? 'bg-gray-50' : 'bg-gray-750'
                          } border border-gray-200 dark:border-gray-700`}
                        >
                          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                            {categoryNames[category] || category}
                          </h4>
                          <div className="flex items-center justify-between">
                            <span className="text-2xl font-bold text-gray-900 dark:text-white">{count}</span>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              {Math.round((count / favorites.length) * 100)}%
                            </span>
                          </div>
                          <div 
                            className="h-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full mt-2"
                            style={{ 
                              backgroundColor: theme === 'light' ? '#e5e7eb' : '#374151' 
                            }}
                          >
                            <div 
                              className="h-1.5 rounded-full bg-emerald-500" 
                              style={{ 
                                width: `${(count / favorites.length) * 100}%` 
                              }} 
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                })()}
              </div>
              
              {/* 导出/管理选项 */}
              <div className="mt-6 flex justify-center gap-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => toast.info('导出功能即将上线')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    theme === 'light' 
                      ? 'bg-gray-100 text-gray-700 hover:bg-gray-200' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <i className="fas fa-download mr-2" />
                  导出收藏
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    if (window.confirm('确定要清空所有收藏吗？')) {
                      localStorage.removeItem('favorites');
                      setFavorites([]);
                      toast.success('已清空所有收藏');
                    }
                  }}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    theme === 'light' 
                      ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                      : 'bg-red-900/30 text-red-400 hover:bg-red-900/50'
                  }`}
                >
                  <i className="fas fa-trash-alt mr-2" />
                  清空收藏
                </motion.button>
              </div>
            </motion.div>
          )}
        </div>
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

export default Favorites;