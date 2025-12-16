import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { Plant, PlantCategoryMap } from '../types/plant';
import { plants } from '../mock/plants';
import { useTheme } from '../hooks/useTheme';
import { toast } from 'sonner';

const PlantDetail: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [plant, setPlant] = useState<Plant | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [isFavorite, setIsFavorite] = useState(false);

  useEffect(() => {
    // 模拟加载植物详情
    setIsLoading(true);
    
    // 在实际应用中，这里会从API获取植物详情
    setTimeout(() => {
      const foundPlant = plants.find(p => p.id === id);
      setPlant(foundPlant || null);
      setIsLoading(false);
      
      // 检查是否在收藏夹中
      const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
      setIsFavorite(favorites.includes(id));
    }, 500);
  }, [id]);

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
              <i className="fas fa-leaf text-emerald-500 text-2xl animate-pulse" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">加载植物信息中...</h2>
          </div>
        </div>
      </div>
    );
  }

  if (!plant) {
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
          </div></header>

        {/* 主要内容区域 */}
        <div className="container mx-auto px-4 py-8 flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
              <i className="fas fa-exclamation-triangle text-red-500 text-2xl" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">未找到该植物</h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2 mb-6">您查找的植物信息不存在或已被移除</p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/explore')}
              className="px-6 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
            >
              返回植物浏览
            </motion.button>
          </div>
        </div>
      </div>
    );
  }

  const toggleFavorite = () => {
    let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    if (isFavorite) {
      favorites = favorites.filter((favId: string) => favId !== id);
      toast.success('已从收藏夹移除');
    } else {
      favorites.push(id);
      toast.success('已添加到收藏夹');
    }
    
    localStorage.setItem('favorites', JSON.stringify(favorites));
    setIsFavorite(!isFavorite);
  };

  const tabs = [
    { id: 'overview', label: '概述', icon: 'fas fa-info-circle' },
    { id: 'care', label: '养护指南', icon: 'fas fa-trowel' },
    { id: 'propagation', label: '繁殖方法', icon: 'fas fa-seedling' },
    { id: 'problems', label: '病虫害防治', icon: 'fas fa-bug' }
  ];

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-300 ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-900'}`}>
      {/* 顶部导航 */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => navigate(-1)}
              className="p-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              aria-label="返回"
            >
              <i className="fas fa-arrow-left" />
            </motion.button>
            
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-500 to-teal-600 bg-clip-text text-transparent">
              植物详情
            </h1>
          </div>
          
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={toggleFavorite}
              className={`p-2 rounded-full transition-colors ${
                isFavorite 
                  ? 'bg-red-500 text-white' 
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
              aria-label={isFavorite ? '取消收藏' : '收藏'}
            >
              <i className={`fas ${isFavorite ? 'fa-heart' : 'fa-heart'}`} />
            </motion.button>
            
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
          {/* 植物基本信息 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className={`bg-white dark:bg-gray-800 rounded-2xl shadow-md overflow-hidden border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            <div className="md:flex">
              {/* 植物图片 */}
              <div className="md:w-2/5">
                <img 
                  src={plant.imageUrl} 
                  alt={plant.name}
                  className="w-full h-full object-cover"
                />
              </div>
              
              {/* 植物信息 */}
              <div className="md:w-3/5 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{plant.name}</h2>
                    <p className="text-lg text-gray-600 dark:text-gray-400 italic">{plant.scientificName}</p>
                  </div>
                  <span className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 text-xs font-medium px-3 py-1 rounded-full">
                    {PlantCategoryMap[plant.category]}
                  </span>
                </div>
                
                <p className="mt-4 text-gray-700 dark:text-gray-300">{plant.description}</p>
                
                <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {plant.bloomingSeason && (
                    <div className="flex items-center text-gray-700 dark:text-gray-300">
                      <i className="fas fa-calendar-alt text-emerald-500 mr-2" />
                      <span>花期: {plant.bloomingSeason}</span>
                    </div>
                  )}
                  
                  {plant.sunlightRequirements && (
                    <div className="flex items-center text-gray-700 dark:text-gray-300">
                      <i className="fas fa-sun text-yellow-500 mr-2" />
                      <span>光照: {plant.sunlightRequirements}</span>
                    </div>
                  )}
                  
                  {plant.waterNeeds && (
                    <div className="flex items-center text-gray-700 dark:text-gray-300">
                      <i className="fas fa-tint text-blue-500 mr-2" />
                      <span>浇水: {plant.waterNeeds}</span>
                    </div>
                  )}
                  
                  {plant.origin && (
                    <div className="flex items-center text-gray-700 dark:text-gray-300">
                      <i className="fas fa-map-marker-alt text-red-500 mr-2" />
                      <span>原产地: {plant.origin}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* 标签导航 */}
          <div className="mt-6 overflow-x-auto">
            <div className="flex space-x-1 min-w-max">
              {tabs.map((tab) => (
                <motion.button
                  key={tab.id}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2.5 rounded-lg flex items-center gap-2 transition-all ${
                    activeTab === tab.id 
                      ? 'bg-emerald-500 text-white shadow-md' 
                      : `${theme === 'light' 
                          ? 'bg-white text-gray-700 hover:bg-gray-50' 
                          : 'bg-gray-800 text-gray-300 hover:bg-gray-750'} border border-gray-200 dark:border-gray-700`
                  }`}
                >
                  <i className={tab.icon} />
                  <span>{tab.label}</span>
                </motion.button>
              ))}
            </div>
          </div>
          
          {/* 标签内容 */}
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`mt-6 bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">植物概述</h3>
                  <p className="text-gray-700 dark:text-gray-300">{plant.description}</p>
                </div>
                
                {plant.otherNames && plant.otherNames.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">别名</h3>
                    <div className="flex flex-wrap gap-2">
                      {plant.otherNames.map((name, index) => (
                        <span 
                          key={index}
                          className={`px-3 py-1 rounded-full text-sm ${
                            theme === 'light' 
                              ? 'bg-gray-100 text-gray-700' 
                              : 'bg-gray-750 text-gray-300'
                          }`}
                        >
                          {name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {plant.benefits && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">主要价值</h3>
                    <p className="text-gray-700 dark:text-gray-300">{plant.benefits}</p>
                  </div>
                )}
                
                {plant.toxicity && (
                  <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-4 border border-amber-100 dark:border-amber-800/30">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 flex items-center">
                      <i className="fas fa-exclamation-triangle text-amber-500 mr-2" />
                      毒性信息
                    </h3>
                    <p className="text-gray-700 dark:text-gray-300">{plant.toxicity}</p>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'care' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">基础养护</h3>
                  {plant.careTips && <p className="text-gray-700 dark:text-gray-300 mb-4">{plant.careTips}</p>}
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    <div className={`p-4 rounded-xl ${
                      theme === 'light' ? 'bg-blue-50' : 'bg-blue-900/20'
                    } border border-blue-100 dark:border-blue-800/30`}>
                      <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center mb-3">
                        <i className="fas fa-sun text-blue-500" />
                      </div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-1">光照需求</h4>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{plant.sunlightRequirements || '适中光照'}</p>
                    </div>
                    
                    <div className={`p-4 rounded-xl ${
                      theme === 'light' ? 'bg-blue-50' : 'bg-blue-900/20'
                    } border border-blue-100 dark:border-blue-800/30`}>
                      <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center mb-3">
                        <i className="fas fa-tint text-blue-500" />
                      </div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-1">浇水频率</h4>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{plant.waterNeeds || '保持土壤湿润'}</p>
                    </div>
                    
                    <div className={`p-4 rounded-xl ${
                      theme === 'light' ? 'bg-blue-50' : 'bg-blue-900/20'
                    } border border-blue-100 dark:border-blue-800/30`}>
                      <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center mb-3">
                        <i className="fas fa-temperature-low text-blue-500" />
                      </div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-1">温度偏好</h4>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {plant.category === 'SUCCULENT' 
                          ? '温暖干燥（15-28°C）' 
                          : plant.category === 'FERN' 
                            ? '凉爽湿润（15-22°C）' 
                            : '温和（18-25°C）'}
                      </p>
                    </div>
                  </div>
                </div>
                
                {plant.plantingInstructions && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">种植指南</h3>
                    <p className="text-gray-700 dark:text-gray-300">{plant.plantingInstructions}</p>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'propagation' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">繁殖方法</h3>
                  {plant.propagationMethods ? (
                    <p className="text-gray-700 dark:text-gray-300">{plant.propagationMethods}</p>
                  ) : (
                    <p className="text-gray-700 dark:text-gray-300">
                      根据植物类型不同，常见的繁殖方法包括播种、扦插、分株、嫁接等。
                      请选择适合该植物的繁殖方式进行尝试。
                    </p>
                  )}
                </div>
                
                <div className={`p-4 rounded-xl ${
                  theme === 'light' ? 'bg-emerald-50' : 'bg-emerald-900/20'
                } border border-emerald-100 dark:border-emerald-800/30`}>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center">
                    <i className="fas fa-lightbulb text-emerald-500 mr-2" />
                    繁殖小贴士
                  </h4>
                  <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>选择健康的母株进行繁殖，提高成功率</span>
                    </li>
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>繁殖过程中保持适当的湿度和温度</span>
                    </li>
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>使用干净的工具和新鲜的介质，防止感染</span>
                    </li>
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>耐心等待，不同植物的生根时间各不相同</span>
                    </li>
                  </ul>
                </div>
              </div>
            )}
            
            {activeTab === 'problems' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">常见病虫害</h3>
                  {plant.pestsAndDiseases ? (
                    <p className="text-gray-700 dark:text-gray-300">{plant.pestsAndDiseases}</p>
                  ) : (
                    <p className="text-gray-700 dark:text-gray-300">
                      该植物的常见病虫害信息正在整理中。一般来说，保持良好的生长环境、
                      定期检查植株和适当的养护措施可以有效预防大多数病虫害。
                    </p>
                  )}
                </div>
                
                <div className={`p-4 rounded-xl ${
                  theme === 'light' ? 'bg-red-50' : 'bg-red-900/20'
                } border border-red-100 dark:border-red-800/30`}>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center">
                    <i className="fas fa-exclamation-triangle text-red-500 mr-2" />
                    防治建议
                  </h4>
                  <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>定期检查植物的叶片背面和茎部，早发现早处理</span>
                    </li>
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>保持通风良好，避免过度浇水导致的真菌病害</span>
                    </li>
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>发现病虫害时，及时隔离感染的植株</span>
                    </li>
                    <li className="flex items-start">
                      <i className="fas fa-check-circle text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span>可以使用有机杀虫剂或自制防治液（如肥皂水）进行处理</span>
                    </li>
                  </ul>
                </div>
              </div>
            )}
          </motion.div>
          
          {/* 相关植物推荐 */}
          <div className="mt-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">相关植物推荐</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {plants
                .filter(p => p.category === plant.category && p.id !== plant.id)
                .slice(0, 3)
                .map(relatedPlant => (
                  <motion.div
                    key={relatedPlant.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ y: -5 }}
                    transition={{ duration: 0.3 }}
                    onClick={() => navigate(`/plant/${relatedPlant.id}`)}
                    className={`bg-white dark:bg-gray-800 rounded-xl overflow-hidden shadow-md cursor-pointer border border-gray-100 dark:border-gray-700`}
                  >
                    <div className="h-40 overflow-hidden">
                      <img 
                        src={relatedPlant.imageUrl} 
                        alt={relatedPlant.name}
                        className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
                      />
                    </div>
                    <div className="p-4">
                      <h4 className="font-bold text-gray-900 dark:text-white mb-1">{relatedPlant.name}</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400 italic">{relatedPlant.scientificName}</p>
                    </div>
                  </motion.div>
                ))}
            </div>
          </div>
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

export default PlantDetail;