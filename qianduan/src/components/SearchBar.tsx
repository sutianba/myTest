import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface SearchBarProps {
  onSearch: (query: string) => void;
  className?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, className }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch(value);
  };

  const handleClear = () => {
    setSearchQuery('');
    onSearch('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative w-full max-w-2xl',
        className
      )}
    >
      <input
        type="text"
        placeholder="搜索植物名称、学名或描述..."
        value={searchQuery}
        onChange={handleInputChange}
        className="w-full pl-10 pr-10 py-3 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 text-gray-800 dark:text-gray-200 transition-all duration-300 shadow-sm"
      />
      <i className="fas fa-search absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" />
      
      {searchQuery && (
        <motion.button
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleClear}
          className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
          aria-label="清除搜索"
        >
          <i className="fas fa-times-circle" />
        </motion.button>
      )}
    </motion.div>
  );
};

export default SearchBar;