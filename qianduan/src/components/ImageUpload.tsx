import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useTheme } from '../hooks/useTheme';
import { useNavigate } from 'react-router-dom';

interface ImageUploadProps {
  onImageUpload?: (file: File) => void;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ onImageUpload }) => {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      toast.error('请选择图片文件');
      return;
    }
    
    // 保存选中的文件
    setSelectedFile(file);
    
    // 显示预览
    const reader = new FileReader();
    reader.onload = (event) => {
      setSelectedImage(event.target?.result as string);
    };
    reader.readAsDataURL(file);
    
    // 通知父组件
    if (onImageUpload) {
      onImageUpload(file);
    }
  };
  
  const handleUpload = async () => {
    if (!selectedImage || !selectedFile) {
      toast.warning('请先选择一张图片');
      return;
    }
    
    setLoading(true);
    
    try {
      toast.success('图片上传成功，正在识别中...');
      
      // 将图片转换为Base64格式发送给后端
      const reader = new FileReader();
      
      reader.onload = async (event) => {
        const base64Image = event.target?.result as string;
        
        try {
          // 调用后端识别API
          const response = await fetch('http://localhost:5000/api/detect', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: base64Image })
          });
          
          const data = await response.json();
          
          if (data.success) {
            // 存储识别结果和图片到localStorage
            localStorage.setItem('lastRecognitionImage', selectedImage);
            localStorage.setItem('lastRecognitionResult', JSON.stringify(data.results));
            
            // 跳转到识别结果页面
            navigate('/recognition-result');
          } else {
            toast.error(`识别失败: ${data.error || '未知错误'}`);
          }
        } catch (apiError) {
          console.error('API调用失败:', apiError);
          toast.error('识别服务不可用，请稍后重试');
        } finally {
          setLoading(false);
        }
      };
      
      reader.onerror = () => {
        toast.error('图片处理失败，请重试');
        setLoading(false);
      };
      
      // 读取文件为Base64
      reader.readAsDataURL(selectedFile);
      
    } catch (error) {
      console.error('上传过程中发生错误:', error);
      toast.error('识别失败，请重试');
      setLoading(false);
    }
  };
  
  const handleRemoveImage = () => {
    setSelectedImage(null);
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    
    // 创建一个新的事件来触发文件变化处理
    const event = new Event('change') as any;
    event.target = { files: [file] };
    
    if (fileInputRef.current) {
      fileInputRef.current.files = e.dataTransfer.files;
      handleFileChange(event);
    }
  };
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="text-center">
        <motion.h2 
          initial={{ y: -20 }}
          animate={{ y: 0 }}
          className="text-2xl font-bold text-gray-900 dark:text-white mb-2"
        >
          植物图片识别
        </motion.h2>
        <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          上传植物或花卉的图片，我们将帮助您识别其种类并提供详细信息
        </p>
      </div>
      
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        className="w-full max-w-2xl mx-auto"
      >
        {!selectedImage ? (
          <div 
            className={`
              border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
              ${theme === 'light' ? 'border-gray-300 hover:border-emerald-500' : 'border-gray-700 hover:border-emerald-500'}
              transition-colors duration-300
            `}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input 
              type="file" 
              ref={fileInputRef}
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
            
            <div className="w-16 h-16 rounded-full bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-4">
              <i className="fas fa-cloud-upload-alt text-emerald-500 text-xl" />
            </div>
            
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
              拖放图片到此处或点击上传
            </h3>
            
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              支持 JPG、PNG、WEBP 格式
            </p>
            
            <button 
              type="button"
              className="px-6 py-2.5 bg-emerald-500 text-white rounded-full text-sm font-medium hover:bg-emerald-600 transition-colors"
            >
              选择图片
            </button>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden border border-gray-200 dark:border-gray-700">
            <div className="relative">
              <img 
                src={selectedImage} 
                alt="预览图"
                className="w-full h-64 object-contain bg-gray-50 dark:bg-gray-900"
              />
              <button
                onClick={handleRemoveImage}
                className="absolute top-3 right-3 bg-white/80 dark:bg-gray-800/80 p-2 rounded-full text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-800 transition-colors"
                aria-label="移除图片"
              >
                <i className="fas fa-times" />
              </button>
            </div>
            
            <div className="p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-left">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">图片已选择</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  点击"开始识别"按钮进行植物识别
                </p>
              </div>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleUpload}
                disabled={loading}
                className="px-6 py-2.5 bg-emerald-500 text-white rounded-full text-sm font-medium hover:bg-emerald-600 transition-colors flex items-center"
              >
                {loading ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-2" />
                    识别中...
                  </>
                ) : (
                  <>
                    <i className="fas fa-leaf mr-2" />
                    开始识别
                  </>
                )}
              </motion.button>
            </div>
          </div>
        )}
      </motion.div>
      
      <div className="w-full max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <i className="fas fa-lightbulb text-yellow-500 mr-2" />
          识别提示
        </h3>
        
        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li className="flex items-start">
            <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
            <span>确保图片清晰，植物主体占据大部分画面</span>
          </li>
          <li className="flex items-start">
            <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
            <span>光线充足，避免过度曝光或模糊的照片</span>
          </li>
          <li className="flex items-start">
            <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
            <span>对于花卉，尽量拍摄花朵的正面</span>
          </li>
          <li className="flex items-start">
            <i className="fas fa-check-circle text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
            <span>对于叶子，确保叶脉清晰可见</span>
          </li>
        </ul>
      </div>
    </motion.div>
  );
};

export default ImageUpload;