import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useParams, useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

interface Comment {
  id: number;
  user_id: number;
  username: string;
  content: string;
  created_at: string;
}

interface PostDetail {
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
  comments: Comment[];
}

const PostDetail: React.FC = () => {
  const { theme } = useTheme();
  const { postId } = useParams<{ postId: string }>();
  const navigate = useNavigate();
  const [post, setPost] = useState<PostDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [commentContent, setCommentContent] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [liked, setLiked] = useState(false);

  const fetchPostDetail = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/community/posts/${postId}`);
      const data = await response.json();
      
      if (data.success) {
        setPost(data.post);
      } else {
        toast.error(data.error || '获取帖子详情失败');
      }
    } catch (error) {
      console.error('获取帖子详情失败:', error);
      toast.error('获取帖子详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPostDetail();
  }, [postId]);

  const handleLike = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/community/like', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',  // 包含cookie以支持会话
        body: JSON.stringify({
          target_type: 'post',
          target_id: postId
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setLiked(data.liked);
        toast.success(data.message);
        fetchPostDetail();
      } else {
        toast.error(data.error || '操作失败');
      }
    } catch (error) {
      console.error('点赞操作失败:', error);
      toast.error('操作失败');
    }
  };

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!commentContent.trim()) {
      toast.warning('评论内容不能为空');
      return;
    }

    setSubmittingComment(true);
    
    try {
      const response = await fetch(`http://localhost:5000/api/community/posts/${postId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',  // 包含cookie以支持会话
        body: JSON.stringify({ content: commentContent })
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast.success('评论成功');
        setCommentContent('');
        fetchPostDetail();
      } else {
        toast.error(data.error || '评论失败');
      }
    } catch (error) {
      console.error('评论失败:', error);
      toast.error('评论失败');
    } finally {
      setSubmittingComment(false);
    }
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

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <i className="fas fa-spinner fa-spin text-4xl text-emerald-500" />
      </div>
    );
  }

  if (!post) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <i className="fas fa-exclamation-circle text-6xl text-gray-300 dark:text-gray-700 mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-lg">帖子不存在</p>
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
      <div className="max-w-4xl mx-auto px-4 py-8">
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
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden"
        >
          {post.image_data && (
            <div className="relative h-96">
              <img
                src={post.image_data}
                alt={post.title}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <div className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center">
                  <i className="fas fa-user text-emerald-500 text-xl" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white text-lg">
                    {post.username}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatTime(post.created_at)}
                  </p>
                </div>
              </div>
              
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleLike}
                className={`flex items-center gap-2 px-4 py-2 rounded-full transition-colors ${
                  liked
                    ? 'bg-red-100 text-red-500'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}
              >
                <i className={`fas fa-heart ${liked ? 'text-red-500' : ''}`} />
                <span>{post.like_count}</span>
              </motion.button>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              {post.title}
            </h1>

            <div className="prose dark:prose-invert max-w-none mb-6">
              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {post.content}
              </p>
            </div>

            {post.recognition_result && (
              <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                <h3 className="font-semibold text-emerald-700 dark:text-emerald-400 mb-2">
                  <i className="fas fa-leaf mr-2" />
                  识别结果
                </h3>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {post.recognition_result}
                </p>
              </div>
            )}

            <div className="flex items-center gap-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <i className="fas fa-eye" />
                <span>{post.views} 次浏览</span>
              </div>
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <i className="fas fa-comment" />
                <span>{post.comment_count} 条评论</span>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mt-8"
        >
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            评论 ({post.comments.length})
          </h2>

          <form onSubmit={handleCommentSubmit} className="mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
              <textarea
                value={commentContent}
                onChange={(e) => setCommentContent(e.target.value)}
                placeholder="写下您的评论..."
                className="w-full h-24 p-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-none bg-transparent text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <div className="flex justify-end mt-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  type="submit"
                  disabled={submittingComment || !commentContent.trim()}
                  className="px-6 py-2 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {submittingComment ? (
                    <>
                      <i className="fas fa-spinner fa-spin" />
                      发布中...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-paper-plane" />
                      发布评论
                    </>
                  )}
                </motion.button>
              </div>
            </div>
          </form>

          <div className="space-y-4">
            {post.comments.map((comment, index) => (
              <motion.div
                key={comment.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center flex-shrink-0">
                    <i className="fas fa-user text-emerald-500" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {comment.username}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {formatTime(comment.created_at)}
                      </p>
                    </div>
                    <p className="text-gray-700 dark:text-gray-300">
                      {comment.content}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {post.comments.length === 0 && (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl">
              <i className="fas fa-comment-slash text-6xl text-gray-300 dark:text-gray-700 mb-4" />
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                暂无评论，快来发表第一条评论吧！
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default PostDetail;