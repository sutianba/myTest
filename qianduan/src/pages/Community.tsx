import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

interface Post {
  id: number;
  user_id: number;
  username: string;
  title: string;
  content: string;
  image_data: string | null;
  recognition_result: string | null;
  category: string;
  views: number;
  comment_count: number;
  like_count: number;
  created_at: string;
}

const Community: React.FC = () => {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [page, setPage] = useState(1);

  const categories = [
    { id: 'all', name: '全部' },
    { id: 'general', name: '综合讨论' },
    { id: 'flower', name: '花卉识别' },
    { id: 'plant', name: '植物养护' },
    { id: 'share', name: '经验分享' }
  ];

  const fetchPosts = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/community/posts?page=${page}&per_page=10&category=${selectedCategory}`);
      const data = await response.json();
      
      if (data.success) {
        setPosts(data.posts);
      } else {
        toast.error(data.error || '获取帖子列表失败');
      }
    } catch (error) {
      console.error('获取帖子列表失败:', error);
      toast.error('获取帖子列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchPosts();
  }, [selectedCategory, page]);

  const handlePostClick = (postId: number) => {
    navigate(`/community/post/${postId}`);
  };

  const handleCreatePost = () => {
    navigate('/community/create');
  };

  const formatTime = (timeString: string) => {
    const date = new Date(timeString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen bg-gray-50 dark:bg-gray-900"
    >
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              花卉社区
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              分享您的花卉识别经验和养护心得
            </p>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCreatePost}
            className="px-6 py-3 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors flex items-center gap-2"
          >
            <i className="fas fa-plus" />
            发布帖子
          </motion.button>
        </div>

        <div className="mb-6">
          <div className="flex gap-2 overflow-x-auto pb-2">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => {
                  setSelectedCategory(category.id);
                  setPage(1);
                }}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                  selectedCategory === category.id
                    ? 'bg-emerald-500 text-white'
                    : theme === 'light'
                    ? 'bg-white text-gray-700 hover:bg-gray-100'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <i className="fas fa-spinner fa-spin text-4xl text-emerald-500" />
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-12">
            <i className="fas fa-comments text-6xl text-gray-300 dark:text-gray-700 mb-4" />
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              暂无帖子，快来发布第一个帖子吧！
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {posts.map((post, index) => (
              <motion.div
                key={post.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => handlePostClick(post.id)}
                className={`
                  bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden
                  cursor-pointer hover:shadow-lg transition-shadow
                  border border-gray-200 dark:border-gray-700
                `}
              >
                {post.image_data && (
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={post.image_data}
                      alt={post.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-3 left-3">
                      <span className="px-3 py-1 bg-emerald-500 text-white text-xs font-medium rounded-full">
                        {categories.find(c => c.id === post.category)?.name || post.category}
                      </span>
                    </div>
                  </div>
                )}
                
                <div className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center">
                        <i className="fas fa-user text-emerald-500" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {post.username}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {formatTime(post.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    {post.title}
                  </h3>
                  
                  <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                    {post.content}
                  </p>

                  <div className="flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
                    <div className="flex items-center gap-2">
                      <i className="fas fa-eye" />
                      <span>{post.views}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <i className="fas fa-heart text-red-500" />
                      <span>{post.like_count}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <i className="fas fa-comment" />
                      <span>{post.comment_count}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default Community;