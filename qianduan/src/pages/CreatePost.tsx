import React, { useState, useContext, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { AuthContext } from '../contexts/authContext';

interface Topic {
  name: string;
  display_name: string;
  post_count: number;
}

const CreatePost: React.FC = () => {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const { isAuthenticated, currentUser } = useContext(AuthContext);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [imageData, setImageData] = useState<string | null>(null);
  const [recognitionResult, setRecognitionResult] = useState<string | null>(null);
  const [category, setCategory] = useState('general');
  const [loading, setLoading] = useState(false);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [suggestedTopics, setSuggestedTopics] = useState<Topic[]>([]);
  const [showTopicSuggestions, setShowTopicSuggestions] = useState(false);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  // 检查登录状态
  React.useEffect(() => {
    if (!isAuthenticated) {
      toast.warning('请先登录');
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // 加载话题列表
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/community/topics');
        const data = await response.json();
        if (data.success) {
          setTopics(data.topics);
        }
      } catch (error) {
        console.error('获取话题列表失败:', error);
      }
    };
    fetchTopics();
  }, []);

  // 处理内容变化，显示话题建议
  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setContent(newContent);

    // 检查是否正在输入话题（以#开头）
    const lastHashIndex = newContent.lastIndexOf('#');
    if (lastHashIndex !== -1) {
      const partialTopic = newContent.substring(lastHashIndex + 1).trim();
      if (partialTopic && !partialTopic.includes('#')) {
        // 过滤匹配的话题
        const filteredTopics = topics.filter(topic => 
          topic.name.toLowerCase().includes(partialTopic.toLowerCase())
        );
        setSuggestedTopics(filteredTopics);
        setShowTopicSuggestions(true);
        return;
      }
    }
    setShowTopicSuggestions(false);
  };

  // 选择话题
  const selectTopic = (topic: Topic) => {
    // 找到内容中最后一个#的位置
    const lastHashIndex = content.lastIndexOf('#');
    if (lastHashIndex !== -1) {
      // 替换部分输入为完整话题
      const beforeHash = content.substring(0, lastHashIndex);
      const newContent = `${beforeHash}#${topic.name}# `;
      setContent(newContent);
      
      // 记录已选话题
      if (!selectedTopics.includes(topic.name)) {
        setSelectedTopics([...selectedTopics, topic.name]);
      }
    }
    setShowTopicSuggestions(false);
  };

  // 移除已选话题
  const removeTopic = (topicName: string) => {
    setSelectedTopics(selectedTopics.filter(topic => topic !== topicName));
    // 也可以从内容中移除该话题，但这需要更复杂的处理
  };

  const categories = [
    { id: 'general', name: '综合讨论' },
    { id: 'flower', name: '花卉识别' },
    { id: 'plant', name: '植物养护' },
    { id: 'share', name: '经验分享' }
  ];

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('请选择图片文件');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64Image = event.target?.result as string;
      setImageData(base64Image);
      
      if (category === 'flower') {
        handleRecognition(base64Image);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleRecognition = async (base64Image: string) => {
    try {
      toast.info('正在识别花卉...');
      
      const response = await fetch('http://localhost:5000/api/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Image })
      });
      
      const data = await response.json();
      
      if (data.success && data.results.detections.length > 0) {
        const detection = data.results.detections[0];
        setRecognitionResult(
          `识别结果: ${detection.name} (置信度: ${(detection.confidence * 100).toFixed(1)}%)`
        );
        toast.success('识别成功！');
      } else {
        toast.warning('未能识别出花卉，您可以手动输入识别结果');
      }
    } catch (error) {
      console.error('识别失败:', error);
      toast.error('识别失败，请重试');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !content.trim()) {
      toast.warning('标题和内容不能为空');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:5000/api/community/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',  // 包含cookie以支持会话
        body: JSON.stringify({
          username: currentUser.username,  // 添加用户名
          title: title.trim(),
          content: content.trim(),
          image_data: imageData,
          recognition_result: recognitionResult,
          category
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast.success('帖子发布成功！');
        navigate('/community');
      } else {
        toast.error(data.error || '发布失败');
      }
    } catch (error) {
      console.error('发布失败:', error);
      toast.error('发布失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveImage = () => {
    setImageData(null);
    setRecognitionResult(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen bg-gray-50 dark:bg-gray-900"
    >
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-6">
          <button
            onClick={() => navigate('/community')}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-emerald-500"
          >
            <i className="fas fa-arrow-left" />
            返回社区
          </button>
        </div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
            发布新帖子
          </h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                标题 *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="请输入帖子标题"
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                maxLength={200}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                分类
              </label>
              <div className="flex gap-3 flex-wrap">
                {categories.map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setCategory(cat.id)}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      category === cat.id
                        ? 'bg-emerald-500 text-white'
                        : theme === 'light'
                        ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                图片
              </label>
              {!imageData ? (
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center cursor-pointer hover:border-emerald-500 transition-colors">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                    id="image-upload"
                  />
                  <label
                    htmlFor="image-upload"
                    className="cursor-pointer"
                  >
                    <div className="w-16 h-16 rounded-full bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-4">
                      <i className="fas fa-cloud-upload-alt text-emerald-500 text-2xl" />
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 mb-2">
                      点击上传图片
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-500">
                      支持 JPG、PNG、WEBP 格式
                    </p>
                  </label>
                </div>
              ) : (
                <div className="relative">
                  <img
                    src={imageData}
                    alt="预览"
                    className="w-full h-64 object-cover rounded-lg"
                  />
                  <button
                    type="button"
                    onClick={handleRemoveImage}
                    className="absolute top-2 right-2 bg-white/80 dark:bg-gray-800/80 p-2 rounded-full text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-800 transition-colors"
                  >
                    <i className="fas fa-times" />
                  </button>
                </div>
              )}
            </div>

            {recognitionResult && (
              <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 font-medium">
                  <i className="fas fa-check-circle" />
                  {recognitionResult}
                </div>
              </div>
            )}

            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                内容 *
              </label>
              <textarea
                value={content}
                onChange={handleContentChange}
                placeholder="请输入帖子内容...支持使用#话题#格式添加话题"
                rows={8}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-none bg-transparent text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              
              {/* 已选话题 */}
              {selectedTopics.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedTopics.map(topic => (
                    <span
                      key={topic}
                      className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded-full text-sm flex items-center gap-1"
                    >
                      #{topic}#
                      <button
                        type="button"
                        onClick={() => removeTopic(topic)}
                        className="text-emerald-500 hover:text-emerald-700 dark:hover:text-emerald-300"
                      >
                        <i className="fas fa-times text-xs" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              
              {/* 话题建议 */}
              {showTopicSuggestions && suggestedTopics.length > 0 && (
                <div className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {suggestedTopics.map((topic, index) => (
                    <div
                      key={index}
                      className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors flex justify-between items-center"
                      onClick={() => selectTopic(topic)}
                    >
                      <span className="text-gray-900 dark:text-white">#{topic.name}#</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{topic.post_count} posts</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="button"
                onClick={() => navigate('/community')}
                className="flex-1 px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                取消
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                className="flex-1 px-6 py-3 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <i className="fas fa-spinner fa-spin" />
                    发布中...
                  </>
                ) : (
                  <>
                    <i className="fas fa-paper-plane" />
                    发布帖子
                  </>
                )}
              </motion.button>
            </div>
          </form>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default CreatePost;