import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { AuthContext } from '../contexts/authContext';
import { useContext } from 'react';

const CommunityManagement: React.FC = () => {
  const { theme } = useTheme();
  const { isAuthenticated, currentUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('reports');
  const [reports, setReports] = useState<any[]>([]);
  const [posts, setPosts] = useState<any[]>([]);
  const [comments, setComments] = useState<any[]>([]);
  const [sensitiveWords, setSensitiveWords] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // 检查登录状态和权限
  useEffect(() => {
    if (!isAuthenticated) {
      toast.warning('请先登录');
      navigate('/login');
    } else if (currentUser?.role !== 'admin') {
      toast.warning('您没有权限访问此页面');
      navigate('/community');
    }
  }, [isAuthenticated, currentUser, navigate]);

  // 加载数据
  useEffect(() => {
    if (isAuthenticated && currentUser?.role === 'admin') {
      loadData();
    }
  }, [isAuthenticated, currentUser]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // 加载举报列表
      const reportsResponse = await fetch('http://localhost:5000/api/community/reports');
      const reportsData = await reportsResponse.json();
      if (reportsData.success) {
        setReports(reportsData.reports);
      }

      // 加载敏感词列表
      const wordsResponse = await fetch('http://localhost:5000/api/community/sensitive-words');
      const wordsData = await wordsResponse.json();
      if (wordsData.success) {
        setSensitiveWords(wordsData.words);
      }

      // 加载公告列表
      const announcementsResponse = await fetch('http://localhost:5000/api/community/announcements');
      const announcementsData = await announcementsResponse.json();
      if (announcementsData.success) {
        setAnnouncements(announcementsData.announcements);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      toast.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessReport = async (reportId: number, status: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/community/reports/${reportId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      const data = await response.json();
      if (data.success) {
        toast.success('举报处理成功');
        loadData();
      } else {
        toast.error(data.error || '处理失败');
      }
    } catch (error) {
      console.error('处理举报失败:', error);
      toast.error('处理失败');
    }
  };

  const handleUpdatePostStatus = async (postId: number, status: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/community/posts/${postId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      const data = await response.json();
      if (data.success) {
        toast.success('帖子状态更新成功');
        loadData();
      } else {
        toast.error(data.error || '更新失败');
      }
    } catch (error) {
      console.error('更新帖子状态失败:', error);
      toast.error('更新失败');
    }
  };

  const handleUpdateCommentStatus = async (commentId: number, status: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/community/comments/${commentId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      const data = await response.json();
      if (data.success) {
        toast.success('评论状态更新成功');
        loadData();
      } else {
        toast.error(data.error || '更新失败');
      }
    } catch (error) {
      console.error('更新评论状态失败:', error);
      toast.error('更新失败');
    }
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
              社区管理
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              管理社区内容、举报和公告
            </p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/community')}
            className="px-4 py-2 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors flex items-center gap-2"
          >
            <i className="fas fa-arrow-left" />
            返回社区
          </motion.button>
        </div>

        {/* 标签页导航 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 mb-6">
          <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('reports')}
              className={`px-4 py-2 font-medium transition-colors ${activeTab === 'reports'
                ? 'text-emerald-500 border-b-2 border-emerald-500'
                : 'text-gray-600 dark:text-gray-400 hover:text-emerald-500'
                }`}
            >
              举报管理
            </button>
            <button
              onClick={() => setActiveTab('content')}
              className={`px-4 py-2 font-medium transition-colors ${activeTab === 'content'
                ? 'text-emerald-500 border-b-2 border-emerald-500'
                : 'text-gray-600 dark:text-gray-400 hover:text-emerald-500'
                }`}
            >
              内容审核
            </button>
            <button
              onClick={() => setActiveTab('sensitive')}
              className={`px-4 py-2 font-medium transition-colors ${activeTab === 'sensitive'
                ? 'text-emerald-500 border-b-2 border-emerald-500'
                : 'text-gray-600 dark:text-gray-400 hover:text-emerald-500'
                }`}
            >
              敏感词管理
            </button>
            <button
              onClick={() => setActiveTab('announcements')}
              className={`px-4 py-2 font-medium transition-colors ${activeTab === 'announcements'
                ? 'text-emerald-500 border-b-2 border-emerald-500'
                : 'text-gray-600 dark:text-gray-400 hover:text-emerald-500'
                }`}
            >
              公告管理
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`px-4 py-2 font-medium transition-colors ${activeTab === 'users'
                ? 'text-emerald-500 border-b-2 border-emerald-500'
                : 'text-gray-600 dark:text-gray-400 hover:text-emerald-500'
                }`}
            >
              用户管理
            </button>
          </div>
        </div>

        {/* 标签页内容 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          {activeTab === 'reports' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                举报管理
              </h2>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                        举报ID
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                        举报者
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                        举报对象
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                        举报原因
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                        状态
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.map((report) => (
                      <tr key={report.id} className="border-b border-gray-200 dark:border-gray-700">
                        <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                          {report.id}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                          {report.reporter_name}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                          {report.target_type === 'post' ? '帖子' : report.target_type === 'comment' ? '评论' : '用户'} #{report.target_id}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                          {report.reason}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            report.status === 'pending' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            : report.status === 'processed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                          }`}>
                            {report.status === 'pending' ? '待处理' : report.status === 'processed' ? '已处理' : '已驳回'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {report.status === 'pending' && (
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleProcessReport(report.id, 'processed')}
                                className="px-2 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600 transition-colors"
                              >
                                处理
                              </button>
                              <button
                                onClick={() => handleProcessReport(report.id, 'dismissed')}
                                className="px-2 py-1 bg-gray-500 text-white rounded text-xs hover:bg-gray-600 transition-colors"
                              >
                                驳回
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {reports.length === 0 && (
                <div className="text-center py-12">
                  <i className="fas fa-flag text-6xl text-gray-300 dark:text-gray-700 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 text-lg">
                    暂无举报记录
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'content' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                内容审核
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                审核待处理的帖子和评论
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    帖子审核
                  </h3>
                  <div className="space-y-4">
                    {posts.length === 0 && (
                      <div className="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <i className="fas fa-file-alt text-4xl text-gray-300 dark:text-gray-600 mb-2" />
                        <p className="text-gray-500 dark:text-gray-400">
                          暂无待审核的帖子
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    评论审核
                  </h3>
                  <div className="space-y-4">
                    {comments.length === 0 && (
                      <div className="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <i className="fas fa-comment text-4xl text-gray-300 dark:text-gray-600 mb-2" />
                        <p className="text-gray-500 dark:text-gray-400">
                          暂无待审核的评论
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sensitive' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                敏感词管理
              </h2>
              <div className="space-y-6">
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    添加敏感词
                  </h3>
                  <form className="flex gap-3">
                    <input
                      type="text"
                      placeholder="输入敏感词"
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <input
                      type="text"
                      placeholder="替换为"
                      defaultValue="***"
                      className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      type="button"
                      className="px-4 py-2 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
                    >
                      添加
                    </motion.button>
                  </form>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    敏感词列表
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                            ID
                          </th>
                          <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                            敏感词
                          </th>
                          <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                            替换为
                          </th>
                          <th className="py-3 px-4 text-left text-sm font-semibold text-gray-600 dark:text-gray-400">
                            操作
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {sensitiveWords.map((word) => (
                          <tr key={word.id} className="border-b border-gray-200 dark:border-gray-700">
                            <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                              {word.id}
                            </td>
                            <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                              {word.word}
                            </td>
                            <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                              {word.replacement}
                            </td>
                            <td className="py-3 px-4 text-sm">
                              <button className="text-red-500 hover:text-red-700 transition-colors">
                                <i className="fas fa-trash" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'announcements' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                公告管理
              </h2>
              <div className="space-y-6">
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    添加公告
                  </h3>
                  <form className="space-y-4">
                    <input
                      type="text"
                      placeholder="公告标题"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <textarea
                      placeholder="公告内容"
                      rows={4}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      type="button"
                      className="px-4 py-2 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors"
                    >
                      添加公告
                    </motion.button>
                  </form>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    公告列表
                  </h3>
                  <div className="space-y-4">
                    {announcements.map((announcement) => (
                      <div key={announcement.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-semibold text-gray-900 dark:text-white">
                            {announcement.title}
                          </h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            announcement.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                          }`}>
                            {announcement.is_active ? '激活' : '未激活'}
                          </span>
                        </div>
                        <p className="text-gray-600 dark:text-gray-400 mb-3">
                          {announcement.content}
                        </p>
                        <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
                          <span>创建于: {new Date(announcement.created_at).toLocaleString()}</span>
                          <div className="flex gap-2">
                            <button className="text-emerald-500 hover:text-emerald-700 transition-colors">
                              <i className="fas fa-edit" />
                            </button>
                            <button className="text-red-500 hover:text-red-700 transition-colors">
                              <i className="fas fa-trash" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'users' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                用户管理
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                管理用户账号和权限
              </p>
              <div className="space-y-4">
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    封禁用户
                  </h3>
                  <form className="space-y-4">
                    <input
                      type="text"
                      placeholder="用户ID或用户名"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <textarea
                      placeholder="封禁原因"
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <input
                      type="datetime-local"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      type="button"
                      className="px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors"
                    >
                      封禁用户
                    </motion.button>
                  </form>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    已封禁用户
                  </h3>
                  <div className="space-y-4">
                    <div className="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <i className="fas fa-user-slash text-4xl text-gray-300 dark:text-gray-600 mb-2" />
                      <p className="text-gray-500 dark:text-gray-400">
                        暂无封禁用户
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default CommunityManagement;