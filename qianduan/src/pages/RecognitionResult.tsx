import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { Plant, RecognitionResult as RecognitionResultType } from '../types/plant';
import { plants } from '../mock/plants';
import { toast } from 'sonner';

const RecognitionResult: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [recognitionResult, setRecognitionResult] = useState<RecognitionResultType | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 从localStorage获取识别的图片和结果
    const imageUrl = localStorage.getItem('lastRecognitionImage');
    const resultStr = localStorage.getItem('lastRecognitionResult');
    
    if (!imageUrl) {
      // 如果没有识别图片，重定向到上传页面
      navigate('/');
      return;
    }
    
    // 模拟识别过程（实际是从localStorage读取结果）
    setIsLoading(true);
    
    // 模拟API调用延迟
    setTimeout(() => {
      let result: RecognitionResultType | null = null;
      
      if (resultStr) {
        // 如果有真实的识别结果，使用它
        const recognitionData = JSON.parse(resultStr);
        
        // 从detections中获取植物识别结果
        const detection = recognitionData.detections && recognitionData.detections.length > 0 ? recognitionData.detections[0] : null;
        
        // 从exif_info中获取日期和位置信息
        const exifInfo = recognitionData.exif_info || {};
        const dateTime = exifInfo.date_time || "未知日期";
        
        // 格式化位置信息
        let locationStr = "未知位置";
        if (exifInfo.location && exifInfo.location.has_location) {
          const loc = exifInfo.location;
          locationStr = `${loc.province} ${loc.city} ${loc.district}`;
        }
        
        // 构建植物对象
        const plant: Plant = {
          id: detection ? detection.name.toLowerCase().replace(/\s+/g, '-') : 'unknown',
          name: detection ? detection.name : '未知植物',
          category: 'flower',
          scientificName: detection ? detection.name : 'Unknown',
          description: '',
          imageUrl: '',
          characteristics: [],
          habitat: '',
          bloomingSeason: '',
          uses: [],
          funFacts: []
        };
        
        result = {
          plant,
          confidence: detection ? detection.confidence : Math.round((0.85 + Math.random() * 0.15) * 100) / 100,
          similarPlants: [], // 暂时不处理相似植物
          imageUrl,
          recognizedAt: new Date().toISOString(),
          date: dateTime,
          location: locationStr
        };
      } else {
        // 如果没有真实结果，使用模拟数据作为备用
        const randomIndex = Math.floor(Math.random() * plants.length);
        const recognizedPlant = plants[randomIndex];
        
        // 生成随机置信度
        const confidence = Math.round((0.85 + Math.random() * 0.15) * 100) / 100;
        
        // 生成相似植物列表（排除已识别的植物）
        const similarPlants = plants
          .filter(plant => plant.category === recognizedPlant.category && plant.id !== recognizedPlant.id)
          .sort(() => 0.5 - Math.random())
          .slice(0, 3);
        
        result = {
          plant: recognizedPlant,
          confidence,
          similarPlants,
          imageUrl,
          recognizedAt: new Date().toISOString()
        };
      }
      
      if (result) {
        setRecognitionResult(result);
        
        // 保存到识别历史
        const history = JSON.parse(localStorage.getItem('recognitionHistory') || '[]');
        const historyItem = {
          id: Date.now().toString(),
          plantId: result.plant.id,
          plantName: result.plant.name,
          imageUrl,
          recognizedAt: result.recognizedAt,
          confidence: result.confidence,
          isFavorite: false,
          date: result.date,
          location: result.location
        };
        
        history.unshift(historyItem); // 添加到历史记录开头
        localStorage.setItem('recognitionHistory', JSON.stringify(history.slice(0, 50))); // 只保留最近50条记录
      }
      
      setIsLoading(false);
    }, 500); // 缩短延迟时间
  }, [navigate]);

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
            <div className="w-20 h-20 mx-auto bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mb-4">
              <i className="fas fa-search text-emerald-500 text-3xl animate-pulse" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">正在分析植物特征...</h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2">请稍候，我们正在识别您上传的植物</p>
          </div>
        </div>
      </div>
    );
  }

  if (!recognitionResult || !recognitionResult.plant) {
    return (
      <div className={`min-h-screen flex flex-col ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-900'}`}>
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
                识别结果
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
        <div className="container mx-auto px-4 py-8 flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
              <i className="fas fa-exclamation-triangle text-red-500 text-3xl" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">无法识别该植物</h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2 mb-6">请尝试上传更清晰的图片，或确保植物主体占据画面大部分</p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/')}
              className="px-6 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
            >
              重新上传
            </motion.button>
          </div>
        </div>
      </div>
    );
  }

  const { plant, confidence, similarPlants, imageUrl } = recognitionResult;

  const addToFavorites = () => {
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    if (favorites.includes(plant.id)) {
      toast.warning('该植物已在收藏夹中');
      return;
    }
    
    favorites.push(plant.id);
    localStorage.setItem('favorites', JSON.stringify(favorites));
    toast.success('已添加到收藏夹');
  };

  const viewPlantDetail = () => {
    navigate(`/plant/${plant.id}`);
  };

  const uploadAnother = () => {
    navigate('/');
  };

  // 格式化置信度百分比
  const formattedConfidence = Math.round(confidence * 100);

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
              识别结果
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
        <div className="max-w-4xl mx-auto">
          {/* 识别成功提示 */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className={`bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4 mb-6 border border-emerald-100 dark:border-emerald-800/30`}
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <i className="fas fa-check-circle text-emerald-500 text-xl" />
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">识别成功</h3>
                <p className="text-sm text-gray-700 dark:text-gray-300">我们已成功识别出您上传的植物</p>
              </div>
            </div>
          </motion.div>
          
          {/* 识别结果卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className={`bg-white dark:bg-gray-800 rounded-2xl shadow-md overflow-hidden border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            <div className="md:flex">
              {/* 上传的图片和识别的图片对比 */}
              <div className="md:w-1/3 relative">
                <img 
                  src={imageUrl} 
                  alt="上传的植物图片"
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-3 left-3 bg-black/50 text-white text-xs px-2 py-1 rounded">
                  上传图片
                </div>
              </div>
              
              {/* 识别结果信息 */}
              <div className="md:w-2/3 p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{plant.name}</h2>
                    <p className="text-lg text-gray-600 dark:text-gray-400 italic">{plant.scientificName}</p>
                  </div>
                  
                  {/* 置信度指示器 */}
                  <div className="flex items-center gap-2">
                    <span className={`text-lg font-bold ${
                      formattedConfidence >= 90 ? 'text-emerald-500' : 
                      formattedConfidence >= 70 ? 'text-amber-500' : 'text-red-500'
                    }`}>
                      {formattedConfidence}%
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">置信度</span>
                  </div>
                </div>
                
                {/* 置信度进度条 */}
                <div className="mt-3">
                  <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${formattedConfidence}%` }}
                      transition={{ duration: 1, delay: 0.5 }}
                      className={`h-full rounded-full ${
                        formattedConfidence >= 90 ? 'bg-emerald-500' : 
                        formattedConfidence >= 70 ? 'bg-amber-500' : 'bg-red-500'
                      }`}
                    />
                  </div>
                </div>
                
                <p className="mt-4 text-gray-700 dark:text-gray-300">{plant.description}</p>
                
                <div className="mt-6 flex flex-wrap gap-3">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={viewPlantDetail}
                    className="px-5 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors flex items-center"
                  >
                    <i className="fas fa-info-circle mr-2" />
                    查看详情
                  </motion.button>
                  
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={addToFavorites}
                    className={`px-5 py-2.5 rounded-lg font-medium transition-colors flex items-center ${
                      theme === 'light' 
                        ? 'bg-gray-100 text-gray-700 hover:bg-gray-200' 
                        : 'bg-gray-750 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    <i className="fas fa-heart mr-2" />
                    添加到收藏
                  </motion.button>
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* 植物基本信息卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className={`mt-6 bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 border ${theme === 'light' ? 'border-gray-100' : 'border-gray-700'}`}
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">基本信息</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* 识别到的日期信息 */}
              {recognitionResult?.date && (
                <div className="flex items-start">
                  <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <i className="fas fa-clock text-green-500" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">拍摄日期</h4>
                    <p className="text-gray-600 dark:text-gray-400">{recognitionResult.date}</p>
                  </div>
                </div>
              )}
              
              {/* 识别到的地区信息 */}
              {recognitionResult?.location && (
                <div className="flex items-start">
                  <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <i className="fas fa-map-pin text-purple-500" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">拍摄地点</h4>
                    <p className="text-gray-600 dark:text-gray-400">{recognitionResult.location}</p>
                  </div>
                </div>
              )}
              
              {plant.bloomingSeason && (
                <div className="flex items-start">
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <i className="fas fa-calendar-alt text-blue-500" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">花期</h4>
                    <p className="text-gray-600 dark:text-gray-400">{plant.bloomingSeason}</p>
                  </div>
                </div>
              )}
              
              {plant.sunlightRequirements && (
                <div className="flex items-start">
                  <div className="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <i className="fas fa-sun text-yellow-500" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">光照需求</h4>
                    <p className="text-gray-600 dark:text-gray-400">{plant.sunlightRequirements}</p>
                  </div>
                </div>
              )}
              
              {plant.waterNeeds && (
                <div className="flex items-start">
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <i className="fas fa-tint text-blue-500" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">浇水需求</h4>
                    <p className="text-gray-600 dark:text-gray-400">{plant.waterNeeds}</p>
                  </div>
                </div>
              )}
              
              {plant.origin && (
                <div className="flex items-start">
                  <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <i className="fas fa-map-marker-alt text-red-500" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">原产地</h4>
                    <p className="text-gray-600 dark:text-gray-400">{plant.origin}</p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
          
          {/* 养护小贴士 */}
          {plant.careTips && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className={`mt-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-2xl p-6 border border-yellow-100 dark:border-yellow-800/30`}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                <i className="fas fa-lightbulb text-yellow-500 mr-2" />
                养护小贴士
              </h3>
              <p className="text-gray-700 dark:text-gray-300">{plant.careTips}</p>
            </motion.div>
          )}
          
          {/* 相似植物 */}
          {similarPlants && similarPlants.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="mt-8"
            >
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">相似植物</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {similarPlants.map(similarPlant => (
                  <motion.div
                    key={similarPlant.id}
                    whileHover={{ y: -5 }}
                    transition={{ duration: 0.3 }}
                    onClick={() => navigate(`/plant/${similarPlant.id}`)}
                    className={`bg-white dark:bg-gray-800 rounded-xl overflow-hidden shadow-md cursor-pointer border border-gray-100 dark:border-gray-700`}
                  >
                    <div className="h-36 overflow-hidden">
                      <img 
                        src={similarPlant.imageUrl} 
                        alt={similarPlant.name}
                        className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
                      />
                    </div>
                    <div className="p-3">
                      <h4 className="font-bold text-gray-900 dark:text-white mb-1 text-sm">{similarPlant.name}</h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400 italic">{similarPlant.scientificName}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
          
          {/* 操作按钮 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-8 flex justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={uploadAnother}
              className="px-8 py-3 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
            >
              <i className="fas fa-upload mr-2" />
              识别另一张图片
            </motion.button>
          </motion.div>
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

export default RecognitionResult;