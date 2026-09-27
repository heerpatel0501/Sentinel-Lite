import React, { useState, useRef, useEffect } from 'react';
import Hls from 'hls.js';

function VideoModal({ streamInfo, onClose, cameraName }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detectionData, setDetectionData] = useState([]);
  const [customVideoUrl, setCustomVideoUrl] = useState(null);
  const [currentVehicleCount, setCurrentVehicleCount] = useState(0);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);

  const originalSrc = streamInfo?.stream_url;
  const isLiveGrid = originalSrc && originalSrc.includes('.m3u8');
  const videoSrc = customVideoUrl || originalSrc;

  // HLS setup
  useEffect(() => {
    if (!videoSrc) return;

    let hls = null;
    const video = videoRef.current;

    if (videoSrc.includes('.m3u8')) {
      if (Hls.isSupported()) {
        hls = new Hls();
        hls.loadSource(videoSrc);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          video.play().catch(e => console.log('Autoplay blocked:', e));
        });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native support (Safari)
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', () => {
          video.play().catch(e => console.log('Autoplay blocked:', e));
        });
      }
    } else {
      // Normal MP4
      video.src = videoSrc;
      video.play().catch(e => console.log('Autoplay blocked:', e));
    }

    return () => {
      if (hls) hls.destroy();
    };
  }, [videoSrc]);

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const objectUrl = URL.createObjectURL(file);
    setCustomVideoUrl(objectUrl);
    setDetectionData([]);
    setCurrentVehicleCount(0);
    clearCanvas();

    setIsAnalyzing(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/detect', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.status === 'success') {
        setDetectionData(data.results);
      }
    } catch (err) {
      console.error("Analysis failed:", err);
      alert("Failed to analyze video.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLiveAnalyze = async () => {
    if (!originalSrc) return;

    setDetectionData([]);
    setCurrentVehicleCount(0);
    clearCanvas();
    setIsAnalyzing(true);

    const formData = new FormData();
    formData.append('stream_url', originalSrc);

    try {
      const response = await fetch('http://localhost:8000/detect', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.status === 'success') {
        // We get ~10 seconds of future detections. 
        // We need to map these to the video's current time. 
        // In a real live stream with a buffer, mapping is tricky, but for a demo,
        // we can just offset the timestamps so they play out over the next 10 seconds.
        const videoCurrentTime = videoRef.current ? videoRef.current.currentTime : 0;
        const adjustedDetections = data.results.map(det => ({
          ...det,
          timestamp: videoCurrentTime + det.timestamp
        }));
        setDetectionData(adjustedDetections);
      }
    } catch (err) {
      console.error("Analysis failed:", err);
      alert("Failed to analyze live stream.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current || !canvasRef.current || detectionData.length === 0) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const currentTime = video.currentTime;
    
    const closestFrame = detectionData.reduce((prev, curr) => {
      return (Math.abs(curr.timestamp - currentTime) < Math.abs(prev.timestamp - currentTime) ? curr : prev);
    });

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (Math.abs(closestFrame.timestamp - currentTime) <= 1.0) {
      setCurrentVehicleCount(closestFrame.detections.length);
      
      closestFrame.detections.forEach(det => {
        const [x1_rel, y1_rel, x2_rel, y2_rel] = det.bounding_box;
        
        const x = x1_rel * canvas.width;
        const y = y1_rel * canvas.height;
        const width = (x2_rel - x1_rel) * canvas.width;
        const height = (y2_rel - y1_rel) * canvas.height;
        
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, width, height);
        
        const label = `${det.object_type} ${Math.round(det.confidence * 100)}%`;
        ctx.fillStyle = '#00ff00';
        ctx.font = '16px Arial';
        ctx.fillText(label, x, y > 20 ? y - 5 : y + 20);
      });
    } else {
      setCurrentVehicleCount(0);
    }
  };

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    if (!video || !canvas) return;

    const syncSize = () => {
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
    };

    video.addEventListener('loadedmetadata', syncSize);
    window.addEventListener('resize', syncSize);
    
    return () => {
      video.removeEventListener('loadedmetadata', syncSize);
      window.removeEventListener('resize', syncSize);
    };
  }, [videoSrc]);

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h3 style={{ margin: 0 }}>Live Feed: {cameraName}</h3>
          <div>
            {!customVideoUrl && isLiveGrid && (
              <button 
                onClick={handleLiveAnalyze}
                style={styles.actionBtn}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? 'Analyzing Live...' : 'Analyze Live Stream'}
              </button>
            )}
            
            <input 
              type="file" 
              accept="video/*" 
              style={{ display: 'none' }} 
              ref={fileInputRef}
              onChange={handleFileUpload}
            />
            <button 
              onClick={() => fileInputRef.current.click()}
              style={{ ...styles.actionBtn, backgroundColor: '#10b981' }}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? 'Analyzing...' : 'Upload MP4 (YOLOv8)'}
            </button>
            <button onClick={onClose} style={styles.closeBtn}>×</button>
          </div>
        </div>
        
        <div style={styles.videoContainer}>
          <video 
            ref={videoRef}
            controls 
            style={styles.video}
            onTimeUpdate={handleTimeUpdate}
          />
          <canvas 
            ref={canvasRef}
            style={styles.canvas}
          />
        </div>
        
        <div style={styles.footer}>
          <span><strong>Status:</strong> {customVideoUrl ? 'Local Upload' : streamInfo?.status}</span>
          <span><strong>Vehicles detected:</strong> <span style={{ color: '#ef4444', fontWeight: 'bold' }}>{currentVehicleCount}</span></span>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000
  },
  modal: {
    backgroundColor: 'white',
    width: '900px',
    maxWidth: '95%',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 10px 25px rgba(0,0,0,0.2)'
  },
  header: {
    padding: '15px 20px',
    backgroundColor: '#1e293b',
    color: 'white',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  actionBtn: {
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '4px',
    cursor: 'pointer',
    marginRight: '15px'
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: 'white',
    fontSize: '24px',
    cursor: 'pointer',
    verticalAlign: 'middle'
  },
  videoContainer: {
    backgroundColor: '#000',
    width: '100%',
    aspectRatio: '16/9',
    position: 'relative',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  video: {
    width: '100%',
    height: '100%',
    objectFit: 'fill'
  },
  canvas: {
    position: 'absolute',
    top: 0,
    left: 0,
    pointerEvents: 'none'
  },
  footer: {
    padding: '15px 20px',
    backgroundColor: '#f8fafc',
    display: 'flex',
    justifyContent: 'space-between',
    borderTop: '1px solid #e2e8f0'
  }
};

export default VideoModal;
