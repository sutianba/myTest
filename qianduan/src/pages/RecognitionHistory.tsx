import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { RecognitionHistory as RecognitionHistoryType, Plant } from '../types/plant';
import { mockRecognitionHistory } from '../mock/plants';
import { plants } from '../mock/plants';
import { toast } from 'sonner';

const RecognitionHistory: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [history, setHistory] = useState<RecognitionHistoryType[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 从localStorage加载历史记录，如果没有则使用模拟数据
    const savedHistory = localStorage.getItem('recognitionHistory');
    
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    } else {
      // 使用模拟数据并保存到localStorage
      setHistory(mockRecognitionHistory);
      localStorage.setItem('recognitionHistory', JSON.stringify(mockRecognitionHistory));
    }
    
    setIsLoading(false);
  }, []);

  // 过滤历史记录
  const filteredHistory = history.filter(item => {
    if (!searchQuery) return true;
    
    const searchLower = searchQuery.toLowerCase();
    return (
      item.plantName?.toLowerCase().includes(searchLower) || 
      item.id.toLowerCase().includes(searchLower)
    );
  });

  // 切换收藏状态
  const toggleFavorite = (historyId: string) => {
    setHistory(prev => 
      prev.map(item => 
        item.id === historyId ? { ...item, isFavorite: !item.isFavorite } : item
      )
    );
    
    // 更新localStorage
    const updatedHistory = history.map(item => 
      item.id === historyId ? { ...item, isFavorite: !item.isFavorite } : item
    );
    localStorage.setItem('recognitionHistory', JSON.stringify(updatedHistory));
    
    toast.success('已更新收藏状态');
  };

  // 查看植物详情
  const viewPlantDetail = (plantId: string | null) => {
    if (plantId) {
      navigate(`/plant/${plantId}`);
    }
  };

  // 删除历史记录
  const deleteHistoryItem = (historyId: string) => {
    if (window.confirm('确定要删除这条识别记录吗？')) {
      setHistory(prev => prev.filter(item => item.id !== historyId));
      
      // 更新localStorage
      const updatedHistory = history.filter(item => item.id !== historyId);
      localStorage.setItem('recognitionHistory', JSON.stringify(updatedHistory));
      
      toast.success('已删除识别记录');
    }
  };

  // 清空历史记录
  const clearAllHistory = () => {
    if (window.confirm('确定要清空所有识别记录吗？此操作不可恢复。')) {
      setHistory([]);
      localStorage.removeItem('recognitionHistory');
      toast.success('已清空所有识别记录');
    }
  };

  // 获取植物对象
  const getPlantById = (plantId: string | null): Plant | null => {
    if (!plantId) return null;
    return plants.find(p => p.id === plantId) || null;
  };

  // 格式化日期时间
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
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
              <i className="fas fa-history text-emerald-500 text-2xl animate-pulse" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">加载识别历史中...</h2>
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
              识别历史
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
        <div className="max-w-5xl mx-auto">
          {/* 页面标题和操作 */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">识别历史记录</h2>
              <p className="text-gray-600 dark:text-gray-400">查看您之前识别过的所有植物</p>
            </div>
            
            {history.length > 0 && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={clearAllHistory}
                className={`mt-4 sm:mt-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  theme === 'light' 
                    ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                    : 'bg-red-900/30 text-red-400 hover:bg-red-900/50'
                }`}
              >
                <i className="fas fa-trash-alt mr-1" />
                清空历史
              </motion.button>
            )}
          </div>
          
          {/* 搜索框 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <div className="relative">
              <input
                type="text"
                placeholder="搜索识别记录..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`w-full pl-10 pr-4 py-3 rounded-lg border ${
                  theme === 'light' 
                    ? 'border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500' 
                    : 'border-gray-700 bg-gray-900 text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
                } transition-all duration-300`}
              />
              <i className="fas fa-search absolute left-3.5 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" />
              
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3.5 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                  aria-label="清除搜索"
                >
                  <i className="fas fa-times-circle" />
                </button>
              )}
            </div>
          </motion.div>
          
          {/* 历史记录列表 */}
          {filteredHistory.length > 0 ? (
            <motion.div
              layout
              className="space-y-4"
            >
              <AnimatePresence>
                {filteredHistory.map((item) => {
                  const plant = getPlantById(item.plantId);
                  const isRecognized = !!item.plantId;
                  
                  return (
                    <motion.div
                      key={item.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className={`bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border ${
                        theme === 'light' ? 'border-gray-100' : 'border-gray-700'
                      }`}
                    >
                      <div className="md:flex">
                        {/* 图片 */}
                        <div className="md:w-1/4">
                          <img 
                            src={item.imageUrl} 
                            alt={item.plantName || '识别图片'}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        
                        {/* 信息 */}
                        <div className="md:w-3/4 p-5">
                          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                            <div>
                              <div className="flex items-center">
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                  {item.plantName || '未识别的植物'}
                                </h3>
                                
                                {item.isFavorite && (
                                  <span className="ml-2 text-red-500">
                                    <i className="fas fa-heart" />
                                  </span>
                                )}
                              </div>
                              
                              {plant && (
                                <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                                  {plant.scientificName}
                                </p>
                              )}
                              
                              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                                识别时间: {formatDate(item.recognizedAt)}
                              </p>
                            </div>
                            
                            <div className="flex flex-col items-start sm:items-end gap-2">
                              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                                item.confidence >= 0.9 
                                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' 
                                  : item.confidence >= 0.7 
                                    ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' 
                                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                              }`}>
                                置信度: {Math.round(item.confidence * 100)}%
                              </div>
                              
                              <div className="flex gap-2">
                                <motion.button
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                  onClick={() => toggleFavorite(item.id)}
                                  className={`p-2 rounded-lg transition-colors ${
                                    item.isFavorite 
                                      ? 'bg-red-100 text-red-500 hover:bg-red-200 dark:bg-red-900/20 dark:hover:bg-red-900/40' 
                                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600'
                                  }`}
                                  aria-label={item.isFavorite ? '取消收藏' : '收藏'}
                                >
                                  <i className={`fas ${item.isFavorite ? 'fa-heart' : 'fa-heart'}`} />
                                </motion.button>
                                
                                {isRecognized && (
                                  <motion.button
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    onClick={() => viewPlantDetail(item.plantId)}
                                    className={`p-2 rounded-lg transition-colors ${
                                      theme === 'light' 
                                        ? 'bg-gray-100 text-gray-500 hover:bg-gray-200' 
                                        : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                                    }`}
                                    aria-label="查看详情"
                                  >
                                    <i className="fas fa-info-circle" />
                                  </motion.button>
                                )}
                                
                                <motion.button
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                  onClick={() => deleteHistoryItem(item.id)}
                                  className={`p-2 rounded-lg transition-colors ${
                                    theme === 'light' 
                                      ? 'bg-gray-100 text-gray-500 hover:bg-red-100 hover:text-red-500' 
                                      : 'bg-gray-700 text-gray-400 hover:bg-red-900/20 hover:text-red-400'
                                  }`}
                                  aria-label="删除"
                                >
                                  <i className="fas fa-trash-alt" />
                                </motion.button>
                              </div>
                            </div>
                          </div>
                          
                          {isRecognized && plant && (
                            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                              <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                                {plant.description}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </motion.div>
          ) : (
            <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 text-center border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}>
              <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
                <i className="fas fa-history text-gray-400 dark:text-gray-500 text-2xl" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {searchQuery ? '未找到匹配的记录' : '暂无识别历史'}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                {searchQuery 
                  ? '尝试使用不同的关键词搜索，或清除搜索条件' 
                  : '上传植物图片进行识别，识别记录将保存在这里'}
              </p>
              
              {!searchQuery && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => navigate('/')}
                  className="mt-6 px-6 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
                >
                  <i className="fas fa-upload mr-2" />
                  开始识别
                </motion.button>
              )}
            </div>
          )}
          
          {/* 历史记录统计 */}
          {history.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className={`mt-8 bg-white dark:bg-gray-800 rounded-xl shadow-md p-5 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">历史记录统计</h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className={`p-4 rounded-lg ${
                  theme === 'light' ? 'bg-blue-50' : 'bg-blue-900/20'
                } border border-blue-100 dark:border-blue-800/30`}>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-1">总识别次数</h4>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{history.length}</p>
                </div>
                
                <div className={`p-4 rounded-lg ${
                  theme === 'light' ? 'bg-green-50' : 'bg-green-900/20'} border border-green-100 dark:border-green-800/30`}>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-1">成功识别</h4>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {history.filter(item => item.plantId).length}
                  </p>
                </div>
                
                <div className={`p-4 rounded-lg ${
                  theme === 'light' ? 'bg-red-50' : 'bg-red-900/20'
                } border border-red-100 dark:border-red-800/30`}>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-1">收藏数量</h4>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {history.filter(item => item.isFavorite).length}
                  </p>
                </div>
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

export default RecognitionHistory;