import React from 'react';
import { motion } from 'framer-motion';
import { Plant, PlantCategoryMap } from '../types/plant';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

interface PlantCardProps {
  plant: Plant;
  onClick?: (plant: Plant) => void;
  className?: string;
  showFavorite?: boolean;
  isFavorite?: boolean;
  onToggleFavorite?: (plantId: string) => void;
}

const PlantCard: React.FC<PlantCardProps> = ({ 
  plant, 
  onClick, 
  className,
  showFavorite = false,
  isFavorite = false,
  onToggleFavorite
}) => {
  const navigate = useNavigate();
  
  const handleCardClick = () => {
    if (onClick) {
      onClick(plant);
    } else {
      navigate(`/plant/${plant.id}`);
    }
  };

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onToggleFavorite) {
      onToggleFavorite(plant.id);
    }
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        y: -5, 
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' 
      }}
      transition={{ duration: 0.3 }}
      onClick={handleCardClick}
      className={cn(
        'bg-white dark:bg-gray-800 rounded-xl overflow-hidden shadow-lg cursor-pointer border border-gray-100 dark:border-gray-700 flex flex-col h-full',
        className
      )}
    >
      <div className="relative h-48 overflow-hidden">
        <img 
          src={plant.imageUrl} 
          alt={plant.name}
          className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
        />
        <div className="absolute top-3 right-3 flex gap-2">
          {showFavorite && (
            <button
              onClick={handleFavoriteClick}
              className={`p-1.5 rounded-full transition-colors ${
                isFavorite 
                  ? 'bg-red-500 text-white' 
                  : 'bg-white/80 dark:bg-gray-800/80 text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-800'
              }`}
              aria-label={isFavorite ? '取消收藏' : '收藏'}
            >
              <i className={`fas ${isFavorite ? 'fa-heart' : 'fa-heart'}`} />
            </button>
          )}
          <span className="bg-white/80 dark:bg-gray-800/80 text-xs font-medium px-2 py-1 rounded-full text-gray-700 dark:text-gray-300 backdrop-blur-sm">
            {PlantCategoryMap[plant.category]}
          </span>
        </div>
      </div>
      
      <div className="p-5 flex flex-col flex-grow">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{plant.name}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 italic mb-3">{plant.scientificName}</p>
        <p className="text-gray-600 dark:text-gray-300 text-sm line-clamp-2 flex-grow">
          {plant.description}
        </p>
        
        {plant.bloomingSeason && (
          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
              <i className="fas fa-calendar-alt mr-2 text-emerald-500" />
              <span>花期: {plant.bloomingSeason}</span>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default PlantCard;