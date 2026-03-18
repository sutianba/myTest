import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/authContext';
import ImageUpload from '../components/ImageUpload';

interface Album {
  id: number;
  name: string;
  description: string;
  cover_image: string;
  created_at: string;
  updated_at: string;
  photos?: Photo[];
}

interface Photo {
  id: number;
  album_id: number;
  image_path: string;
  thumbnail_path: string;
  filename: string;
  plant_name: string;
  confidence: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

const AlbumManagement: React.FC = () => {
  const { token } = useAuth();
  const [albums, setAlbums] = useState<Album[]>([]);
  const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newAlbum, setNewAlbum] = useState({ name: '', description: '' });
  const [isUploading, setIsUploading] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const [feedback, setFeedback] = useState({
    isCorrect: true,
    correctedPlantName: '',
    feedback: ''
  });

  // 获取相册列表
  const fetchAlbums = async () => {
    if (!token) return;

    try {
      const response = await fetch('http://localhost:5000/api/albums', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setAlbums(data.data);
        }
      }
    } catch (error) {
      console.error('获取相册列表失败:', error);
      toast.error('获取相册列表失败');
    }
  };

  // 创建相册
  const handleCreateAlbum = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const response = await fetch('http://localhost:5000/api/albums', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newAlbum)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          toast.success('相册创建成功');
          setIsCreating(false);
          setNewAlbum({ name: '', description: '' });
          fetchAlbums();
        }
      }
    } catch (error) {
      console.error('创建相册失败:', error);
      toast.error('创建相册失败');
    }
  };

  // 获取相册详情
  const fetchAlbumDetails = async (albumId: number) => {
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:5000/api/albums/${albumId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setSelectedAlbum(data.data);
        }
      }
    } catch (error) {
      console.error('获取相册详情失败:', error);
      toast.error('获取相册详情失败');
    }
  };

  // 上传图片
  const handleUpload = async (files: File[]) => {
    if (!token || !selectedAlbum) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('album_id', selectedAlbum.id.toString());

    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch('http://localhost:5000/api/photos/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          toast.success(data.message);
          fetchAlbumDetails(selectedAlbum.id);
        }
      }
    } catch (error) {
      console.error('上传图片失败:', error);
      toast.error('上传图片失败');
    } finally {
      setIsUploading(false);
    }
  };

  // 删除相册
  const handleDeleteAlbum = async (albumId: number) => {
    if (!token) return;

    if (window.confirm('确定要删除这个相册吗？')) {
      try {
        const response = await fetch(`http://localhost:5000/api/albums/${albumId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.code === 200) {
            toast.success('相册删除成功');
            setSelectedAlbum(null);
            fetchAlbums();
          }
        }
      } catch (error) {
        console.error('删除相册失败:', error);
        toast.error('删除相册失败');
      }
    }
  };

  // 删除图片
  const handleDeletePhoto = async (photoId: number) => {
    if (!token || !selectedAlbum) return;

    if (window.confirm('确定要删除这张图片吗？')) {
      try {
        const response = await fetch(`http://localhost:5000/api/photos/${photoId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.code === 200) {
            toast.success('图片删除成功');
            fetchAlbumDetails(selectedAlbum.id);
          }
        }
      } catch (error) {
        console.error('删除图片失败:', error);
        toast.error('删除图片失败');
      }
    }
  };

  // 打开反馈模态框
  const handleFeedback = (photo: Photo) => {
    setSelectedPhoto(photo);
    setFeedback({
      isCorrect: true,
      correctedPlantName: photo.plant_name || '',
      feedback: ''
    });
    setShowFeedbackModal(true);
  };

  // 提交反馈
  const handleSubmitFeedback = async () => {
    if (!token || !selectedPhoto) return;

    try {
      const response = await fetch('http://localhost:5000/api/feedback', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          photo_id: selectedPhoto.id,
          original_plant_name: selectedPhoto.plant_name,
          corrected_plant_name: feedback.correctedPlantName,
          confidence: selectedPhoto.confidence,
          feedback: feedback.feedback,
          is_correct: feedback.isCorrect ? 1 : 0
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          toast.success('反馈提交成功');
          setShowFeedbackModal(false);
          if (selectedAlbum) {
            fetchAlbumDetails(selectedAlbum.id);
          }
        }
      }
    } catch (error) {
      console.error('提交反馈失败:', error);
      toast.error('提交反馈失败');
    }
  };

  // 批量分类图片
  const handleClassifyPhotos = async () => {
    if (!token || !selectedAlbum) return;

    const photoIds = selectedAlbum.photos?.map(photo => photo.id) || [];
    if (photoIds.length === 0) {
      toast.warning('请先上传图片');
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/api/classify', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ photo_ids: photoIds })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          toast.success(data.message);
          fetchAlbumDetails(selectedAlbum.id);
        }
      }
    } catch (error) {
      console.error('分类图片失败:', error);
      toast.error('分类图片失败');
    }
  };

  useEffect(() => {
    fetchAlbums();
  }, [token]);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-green-800">相册管理</h1>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
        >
          {isCreating ? '取消' : '创建相册'}
        </button>
      </div>

      {/* 创建相册表单 */}
      {isCreating && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">创建新相册</h2>
          <form onSubmit={handleCreateAlbum}>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">相册名称</label>
              <input
                type="text"
                value={newAlbum.name}
                onChange={(e) => setNewAlbum({ ...newAlbum, name: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">相册描述</label>
              <textarea
                value={newAlbum.description}
                onChange={(e) => setNewAlbum({ ...newAlbum, description: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                rows={3}
              ></textarea>
            </div>
            <button
              type="submit"
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
            >
              创建
            </button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {albums.map(album => (
          <div
            key={album.id}
            className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition"
          >
            <div className="h-48 bg-gray-200">
              {album.cover_image ? (
                <img
                  src={`http://localhost:5000/${album.cover_image}`}
                  alt={album.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  无封面
                </div>
              )}
            </div>
            <div className="p-4">
              <h3 className="text-lg font-semibold mb-2">{album.name}</h3>
              <p className="text-gray-600 text-sm mb-4">{album.description}</p>
              <div className="flex justify-between">
                <button
                  onClick={() => fetchAlbumDetails(album.id)}
                  className="text-green-600 hover:text-green-800"
                >
                  查看
                </button>
                <button
                  onClick={() => handleDeleteAlbum(album.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 相册详情 */}
      {selectedAlbum && (
        <>
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold">{selectedAlbum.name}</h2>
              <button
                onClick={() => setSelectedAlbum(null)}
                className="text-gray-600 hover:text-gray-800"
              >
                返回
              </button>
            </div>

            <p className="text-gray-600 mb-6">{selectedAlbum.description}</p>

            {/* 图片上传 */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4">上传图片</h3>
              <ImageUpload onUpload={handleUpload} isUploading={isUploading} />
            </div>

            {/* 批量操作 */}
            <div className="mb-6">
              <button
                onClick={handleClassifyPhotos}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition mr-2"
              >
                批量分类
              </button>
            </div>

            {/* 图片列表 */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {selectedAlbum.photos?.map(photo => (
                <div key={photo.id} className="relative">
                  <div className="h-48 bg-gray-200 rounded-lg overflow-hidden">
                    <img
                      src={`http://localhost:5000/${photo.image_path}`}
                      alt={photo.filename}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="mt-2">
                    <p className="text-sm font-medium">{photo.filename}</p>
                    {photo.plant_name && (
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-green-600">
                          {photo.plant_name} ({(photo.confidence * 100).toFixed(1)}%)
                        </p>
                        <button
                          onClick={() => handleFeedback(photo)}
                          className="text-blue-600 hover:text-blue-800 text-xs"
                        >
                          反馈
                        </button>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeletePhoto(photo.id)}
                    className="absolute top-2 right-2 bg-red-600 text-white w-8 h-8 rounded-full flex items-center justify-center hover:bg-red-700"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* 反馈模态框 */}
          {showFeedbackModal && selectedPhoto && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 max-w-md w-full">
                <h3 className="text-xl font-semibold mb-4">反馈识别结果</h3>
                <div className="mb-4">
                  <img
                    src={`http://localhost:5000/${selectedPhoto.image_path}`}
                    alt={selectedPhoto.filename}
                    className="w-full h-48 object-cover rounded-lg mb-4"
                  />
                  <p className="text-sm font-medium">{selectedPhoto.filename}</p>
                  <p className="text-sm text-green-600">
                    当前识别: {selectedPhoto.plant_name} ({(selectedPhoto.confidence * 100).toFixed(1)}%)
                  </p>
                </div>
                <div className="mb-4">
                  <label className="block text-gray-700 mb-2">
                    <input
                      type="checkbox"
                      checked={feedback.isCorrect}
                      onChange={(e) => setFeedback({ ...feedback, isCorrect: e.target.checked })}
                      className="mr-2"
                    />
                    识别结果正确
                  </label>
                </div>
                {!feedback.isCorrect && (
                  <div className="mb-4">
                    <label className="block text-gray-700 mb-2">正确的植物名称</label>
                    <input
                      type="text"
                      value={feedback.correctedPlantName}
                      onChange={(e) => setFeedback({ ...feedback, correctedPlantName: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                )}
                <div className="mb-4">
                  <label className="block text-gray-700 mb-2">其他反馈</label>
                  <textarea
                    value={feedback.feedback}
                    onChange={(e) => setFeedback({ ...feedback, feedback: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    rows={3}
                  ></textarea>
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowFeedbackModal(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleSubmitFeedback}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                  >
                    提交反馈
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AlbumManagement;