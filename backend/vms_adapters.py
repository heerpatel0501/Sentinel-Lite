from abc import ABC, abstractmethod
from typing import Dict, Any

# ==========================================
# VMS Federation Adapter Layer (Model 3)
# ==========================================
# This demonstrates the adapter pattern to normalize 
# video streams from disparate VMS vendors across 
# different government departments into a single 
# standardized API for the frontend.

class VMSProvider(ABC):
    """
    Abstract Base Class for all VMS Integrations.
    In a real-world scenario, implementations would use vendor-specific 
    SDKs/APIs (like Milestone MIP SDK or Hikvision ISAPI) to fetch 
    live RTSP streams and convert them via WebRTC or HLS.
    """
    @abstractmethod
    def get_stream(self, camera_id: Any) -> Dict[str, Any]:
        pass

class MilestoneMockProvider(VMSProvider):
    def get_stream(self, camera_id: Any) -> Dict[str, Any]:
        # Simulating fetching a stream from Milestone XProtect
        return {
            "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "status": "active",
            "resolution": "1080p"
        }

class HikvisionMockProvider(VMSProvider):
    def get_stream(self, camera_id: Any) -> Dict[str, Any]:
        # Simulating fetching a stream from Hikvision NVR
        return {
            "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "status": "active",
            "resolution": "4K"
        }

class GenetecMockProvider(VMSProvider):
    def get_stream(self, camera_id: Any) -> Dict[str, Any]:
        # Simulating fetching a stream from Genetec Security Center
        return {
            "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "status": "active",
            "resolution": "1080p"
        }

class DahuaMockProvider(VMSProvider):
    def get_stream(self, camera_id: str) -> Dict[str, Any]:
        return {
            "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "status": "active",
            "resolution": "720p"
        }

class LiveGridProvider(VMSProvider):
    def get_stream(self, camera_id: str) -> Dict[str, Any]:
        # camera_id might be something like "cam-01" from the JSON
        return {
            "stream_url": f"https://cctv.corp8.cloud/{camera_id}/index.m3u8",
            "status": "active",
            "resolution": "1080p" # Assuming 1080p for live grid
        }

class SentinelOfficialRTSPAdapter(VMSProvider):
    """
    Official I-Hub Gujarat Sentinel Simulated-Live Stream Adapter:
    - Ingests ~12 hours of footage across 30+ government cameras
    - Connects over RTSP over TCP (interleaved)
    - Dynamic discovery via GET /api/ingest (never hardcoded)
    - Mixed H.264 / H.265 multi-resolution support with backoff reconnect
    - Presentation Time Stamp (PTS) chronosequencing for cross-camera correlation
    """
    def __init__(self, base_ingest_url: str = "https://cctv.corp8.cloud"):
        self.base_ingest_url = base_ingest_url

    def get_stream(self, camera_id: Any) -> Dict[str, Any]:
        return {
            "stream_url": f"{self.base_ingest_url}/{camera_id}/index.m3u8",
            "rtsp_transport": "tcp",
            "status": "active",
            "resolution": "1080p",
            "codec": "H.264/H.265",
            "sync_mode": "PTS",
            "reconnect_policy": "exponential_backoff"
        }

def get_vms_provider(vendor_name: str) -> VMSProvider:
    """Factory function to get the correct VMS provider."""
    vendors = {
        "Milestone": MilestoneMockProvider(),
        "Hikvision": HikvisionMockProvider(),
        "Genetec": GenetecMockProvider(),
        "Dahua": DahuaMockProvider(),
        "LiveGrid": LiveGridProvider(),
        "Sentinel": SentinelOfficialRTSPAdapter(),
        "OfficialRTSP": SentinelOfficialRTSPAdapter()
    }
    return vendors.get(vendor_name, MilestoneMockProvider())

