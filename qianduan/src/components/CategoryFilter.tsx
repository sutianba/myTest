import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PlantCategory, PlantCategoryMap } from '../types/plant';
import { cn } from '@/lib/utils';

interface CategoryFilterProps {
  selectedCategories: PlantCategory[];
  onCategoryToggle: (category: PlantCategory) => void;
  className?: string;
}

const CategoryFilter: React.FC<CategoryFilterProps> = ({ 
  selectedCategories, 
  onCategoryToggle,
  className
}) => {
  const categories = Object.entries(PlantCategoryMap);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn(
        'w-full overflow-x-auto py-2 mb-6 scrollbar-hide',
        className
      )}
    >
      <div className="flex space-x-2 min-w-max">
        <AnimatePresence>
          {categories.map(([key, value]) => {
            const category = key as PlantCategory;
            const isSelected = selectedCategories.includes(category);
            
            return (
              <motion.button
                key={category}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => onCategoryToggle(category)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                  isSelected 
                    ? 'bg-emerald-500 text-white shadow-md' 
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750'
                }`}
              >
                {value}
              </motion.button>
            );
          })}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default CategoryFilter;