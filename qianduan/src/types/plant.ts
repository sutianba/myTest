// 植物数据类型定义

// 植物分类枚举
export enum PlantCategory {
  FLOWER = 'flower',
  TREE = 'tree',
  BUSH = 'bush',
  HERB = 'herb',
  VINE = 'vine',
  SUCCULENT = 'succulent',
  FERN = 'fern',
  GRASS = 'grass',
}

// 植物分类中文映射
export const PlantCategoryMap: Record<PlantCategory, string> = {
  [PlantCategory.FLOWER]: '花卉',
  [PlantCategory.TREE]: '树木',
  [PlantCategory.BUSH]: '灌木',
  [PlantCategory.HERB]: '草本',
  [PlantCategory.VINE]: '藤蔓',
  [PlantCategory.SUCCULENT]: '多肉',
  [PlantCategory.FERN]: '蕨类',
  [PlantCategory.GRASS]: '草类',
};

// 植物数据接口
export interface Plant {
  id: string;
  name: string;
  scientificName: string;
  category: PlantCategory;
  description: string;
  imageUrl: string;
  bloomingSeason?: string;
  sunlightRequirements?: string;
  waterNeeds?: string;
  origin?: string;
  toxicity?: string;
  careTips?: string;
  plantingInstructions?: string;
  propagationMethods?: string;
  pestsAndDiseases?: string;
  benefits?: string;
  otherNames?: string[];
}

// 识别历史记录接口
export interface RecognitionHistory {
  id: string;
  plantId: string | null;
  plantName?: string;
  imageUrl: string;
  recognizedAt: string;
  confidence: number;
  isFavorite: boolean;
}

// 收藏的植物接口
export interface FavoritePlant {
  id: string;
  plantId: string;
  addedAt: string;
}

// 识别结果接口
export interface RecognitionResult {
  plant: Plant | null;
  confidence: number;
  similarPlants: Plant[];
  imageUrl: string;
  recognizedAt: string;
}