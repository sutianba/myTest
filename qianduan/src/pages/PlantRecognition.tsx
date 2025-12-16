import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plant, PlantCategory, PlantCategoryMap } from '../types/plant';
import { plants } from '../mock/plants';
import PlantCard from '../components/PlantCard';
import CategoryFilter from '../components/CategoryFilter';
import SearchBar from '../components/SearchBar';
import { Empty } from '../components/Empty';

// 获取分类描述
const getCategoryDescription = (category: PlantCategory): string => {
  const descriptions: Record<PlantCategory, string> = {
    [PlantCategory.FLOWER]: '开花植物，通常具有鲜艳的花朵和观赏价值。',
    [PlantCategory.TREE]: '高大的木本植物，具有明显的主干和树冠。',
    [PlantCategory.BUSH]: '低矮的木本植物，多分枝但没有明显的主干。',
    [PlantCategory.HERB]: '一年生或多年生草本植物，通常具有药用或调味价值。',
    [PlantCategory.VINE]: '需要依附其他物体生长的攀缘植物。',
    [PlantCategory.SUCCULENT]: '茎叶肉质化，能够储存大量水分的耐旱植物。',
    [PlantCategory.FERN]: '没有种子的维管植物，通过孢子繁殖，通常生长在阴湿环境。',
    [PlantCategory.GRASS]: '单子叶植物，叶片细长，多为绿色。'
  };
  
  return descriptions[category];
};

// 植物分类规则说明组件
export const PlantClassificationRules: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700 mb-8"
    >
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center">
        <i className="fas fa-info-circle text-emerald-500 mr-2" />
        植物花卉分类规则
      </h2>
      
      <div className="space-y-4">
        {Object.entries(PlantCategoryMap).map(([category, name]) => (
          <div key={category} className="flex items-start">
            <div className="w-3 h-3 rounded-full bg-emerald-500 mt-1.5 mr-3" />
            <div>
              <h3 className="font-semibold text-gray-800 dark:text-gray-200">{name}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {getCategoryDescription(category as PlantCategory)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

const PlantRecognition: React.FC = () => {
  const [selectedCategories, setSelectedCategories] = useState<PlantCategory[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  
  const handleCategoryToggle = (category: PlantCategory) => {
    setSelectedCategories(prev => 
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  // 过滤植物列表
  const filteredPlants = plants.filter(plant => {
    const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(plant.category);
    const matchesSearch = searchQuery === '' || 
      plant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plant.scientificName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plant.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesCategory && matchesSearch;
  });

  return (
    <div>
      {/* 主内容 */}
      <main className="container mx-auto px-4 py-8">
        {/* 植物分类规则说明 */}
        <PlantClassificationRules />
        
        {/* 分类筛选 */}
        {/* 搜索栏 */}
        <SearchBar 
          onSearch={setSearchQuery}
          className="mb-6 mx-auto"
        />

        {/* 分类筛选 */}
        <CategoryFilter 
          selectedCategories={selectedCategories}
          onCategoryToggle={handleCategoryToggle}
        />

        {/* 植物卡片网格 */}
        {filteredPlants.length > 0 ? (
          <motion.div
            layout
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          >
            <AnimatePresence>
              {filteredPlants.map((plant) => (
                <motion.div
                  key={plant.id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3 }}
                >
                  <PlantCard plant={plant} />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        ) : (
          <Empty 
            title="未找到植物" 
            description="尝试更改搜索条件或清除筛选器以查看更多植物" 
          />
        )}
      </main>
    </div>
  );
};

export default PlantRecognition;