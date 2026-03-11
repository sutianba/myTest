import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useParams, useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

interface Post {
  id: number;
  title: string;
  content: string;
  image_data: string | null;
  like_count: number;
  comment_count: number;
  created_at: string;
}

interface UserProfile {
  id: number;
  username: string;
  bio: string;
  avatar_url: string;
  followers: number;
  following: number;
  posts: Post[];
}

const UserProfile: React.FC = () => {
  const { theme } = useTheme();
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);

  const fetchUserProfile = async () => {
    try {
      // 这里可以从API获取用户资料，现在返回模拟数据
      const mockProfile: UserProfile = {
        id: 1,
        username: username || 'testuser',
        bio: '花卉爱好者，喜欢分享花卉识别和养护经验',
        avatar_url: 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=User%20avatar%20portrait&sign=test',
        followers: 123,
        following: 45,
        posts: [
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
          }
        ]
      };
      setProfile(mockProfile);
    } catch (error) {
      console.error('获取用户资料失败:', error);
      toast.error('获取用户资料失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserProfile();
  }, [username]);

  const handleFollow = async () => {
    try {
      // 这里可以处理关注逻辑
      setIsFollowing(!isFollowing);
      toast.success(isFollowing ? '已取消关注' : '关注成功');
    } catch (error) {
      console.error('关注操作失败:', error);
      toast.error('操作失败');
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

  if (!profile) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <i className="fas fa-user-slash text-6xl text-gray-300 dark:text-gray-700 mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-lg">用户不存在</p>
          <button
            onClick={() => navigate('/community')}
            className="mt-4 px-6 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600"
          >
            返回社区
          </button>
        </div>
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
        <button
          onClick={() => navigate('/community')}
          className="mb-6 flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-emerald-500"
        >
          <i className="fas fa-arrow-left" />
          返回社区
        </button>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden mb-8"
        >
          <div className="p-6">
            <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
              <div className="w-32 h-32 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center overflow-hidden">
                <img
                  src={profile.avatar_url}
                  alt={profile.username}
                  className="w-full h-full object-cover"
                />
              </div>
              
              <div className="flex-1">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                      {profile.username}
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      {profile.bio}
                    </p>
                  </div>
                  
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleFollow}
                    className={`px-6 py-2 rounded-lg font-medium transition-colors ${isFollowing
                      ? 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      : 'bg-emerald-500 text-white hover:bg-emerald-600'
                    }`}
                  >
                    {isFollowing ? '已关注' : '关注'}
                  </motion.button>
                </div>

                <div className="flex gap-8 mt-4">
                  <div className="text-center">
                    <p className="text-xl font-bold text-gray-900 dark:text-white">
                      {profile.posts.length}
                    </p>
                    <p className="text-gray-600 dark:text-gray-400">帖子</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-gray-900 dark:text-white">
                      {profile.followers}
                    </p>
                    <p className="text-gray-600 dark:text-gray-400">粉丝</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-gray-900 dark:text-white">
                      {profile.following}
                    </p>
                    <p className="text-gray-600 dark:text-gray-400">关注</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            发布的帖子
          </h2>

          {profile.posts.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl">
              <i className="fas fa-file-alt text-6xl text-gray-300 dark:text-gray-700 mb-4" />
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                暂无发布内容
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {profile.posts.map((post, index) => (
                <motion.div
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handlePostClick(post.id)}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
                >
                  {post.image_data && (
                    <div className="relative h-48 overflow-hidden">
                      <img
                        src={post.image_data}
                        alt={post.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 line-clamp-2">
                      {post.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                      {post.content}
                    </p>
                    <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                      <span>{formatTime(post.created_at)}</span>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1">
                          <i className="fas fa-heart text-red-500" />
                          <span>{post.like_count}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <i className="fas fa-comment" />
                          <span>{post.comment_count}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default UserProfile;