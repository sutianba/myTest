import React, { useState, useEffect, useContext } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { AuthContext } from '../contexts/authContext';

interface Post {
  id: number;
  title: string;
  content: string;
  image_data: string | null;
  like_count: number;
  comment_count: number;
  created_at: string;
}

const MyPosts: React.FC = () => {
  const { theme } = useTheme();
  const { isAuthenticated, currentUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  // 检查登录状态
  React.useEffect(() => {
    if (!isAuthenticated) {
      toast.warning('请先登录');
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  const fetchMyPosts = async () => {
    try {
      // 这里可以从API获取用户自己的帖子，现在返回模拟数据
      const mockPosts: Post[] = [
        {
          id: 1,
          title: '如何识别常见花卉',
          content: '分享一些识别常见花卉的小技巧...',
          image_data: 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Flower%20identification&sign=test',
          like_count: 25,
          comment_count: 8,
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          title: '玫瑰养护指南',
          content: '玫瑰的养护方法和注意事项...',
          image_data: 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Rose%20care&sign=test',
          like_count: 42,
          comment_count: 15,
          created_at: new Date(Date.now() - 86400000).toISOString()
        },
        {
          id: 3,
          title: '多肉植物养护',
          content: '多肉植物的养护要点和常见问题...',
          image_data: 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Succulent%20plants&sign=test',
          like_count: 18,
          comment_count: 5,
          created_at: new Date(Date.now() - 172800000).toISOString()
        }
      ];
      setPosts(mockPosts);
    } catch (error) {
      console.error('获取我的帖子失败:', error);
      toast.error('获取失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchMyPosts();
    }
  }, [isAuthenticated]);

  const handleEditPost = (postId: number) => {
    // 编辑帖子逻辑
    toast.info('编辑功能开发中');
  };

  const handleDeletePost = async (postId: number) => {
    try {
      // 这里可以处理删除帖子的逻辑
      setPosts(posts.filter(post => post.id !== postId));
      toast.success('帖子已删除');
    } catch (error) {
      console.error('删除帖子失败:', error);
      toast.error('删除失败');
    }
  };

  const handlePostClick = (postId: number) => {
    navigate(`/community/post/${postId}`);
  };

  const formatTime = (timeString: string) => {
    const date = new Date(timeString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / 86400000);
    
    if (days < 1) return '今天';
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <i className="fas fa-spinner fa-spin text-4xl text-emerald-500" />
      </div>
    );
  }

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
              我的发布
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              管理您发布的所有帖子
            </p>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/community/create')}
            className="px-6 py-3 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors flex items-center gap-2"
          >
            <i className="fas fa-plus" />
            发布新帖子
          </motion.button>
        </div>

        {posts.length === 0 ? (
          <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-xl">
            <i className="fas fa-file-alt text-6xl text-gray-300 dark:text-gray-700 mb-4" />
            <p className="text-gray-500 dark:text-gray-400 text-lg mb-6">
              您还没有发布任何帖子
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/community/create')}
              className="px-6 py-3 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
            >
              发布第一个帖子
            </motion.button>
          </div>
        ) : (
          <div className="space-y-6">
            {posts.map((post, index) => (
              <motion.div
                key={post.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden"
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white line-clamp-2">
                      {post.title}
                    </h3>
                    <div className="flex gap-2">
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleEditPost(post.id)}
                        className="p-2 text-gray-500 dark:text-gray-400 hover:text-emerald-500 transition-colors"
                      >
                        <i className="fas fa-edit" />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleDeletePost(post.id)}
                        className="p-2 text-gray-500 dark:text-gray-400 hover:text-red-500 transition-colors"
                      >
                        <i className="fas fa-trash" />
                      </motion.button>
                    </div>
                  </div>
                  
                  <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
                    {post.content}
                  </p>
                  
                  {post.image_data && (
                    <div className="mb-4 rounded-lg overflow-hidden">
                      <img
                        src={post.image_data}
                        alt={post.title}
                        className="w-full h-48 object-cover"
                      />
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <span>{formatTime(post.created_at)}</span>
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-2">
                        <i className="fas fa-heart text-red-500" />
                        <span>{post.like_count}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <i className="fas fa-comment" />
                        <span>{post.comment_count}</span>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handlePostClick(post.id)}
                        className="text-emerald-500 hover:text-emerald-600 transition-colors"
                      >
                        查看详情
                      </motion.button>
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

export default MyPosts;