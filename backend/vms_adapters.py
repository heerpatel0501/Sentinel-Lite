"""
VMS Federation Adapter Layer (Model 3)

This demonstrates the adapter pattern to normalize video streams from disparate VMS vendors across
different government departments into a single standardized API for the frontend.
"""
import asyncio
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class VMSProvider(ABC):
    """
    Abstract Base Class for all VMS Integrations.

    In a real-world scenario, implementations would use vendor-specific SDKs/APIs 
    (like Milestone MIP SDK or Hikvision ISAPI) to fetch live RTSP streams and convert 
    them via WebRTC or HLS.
    """
    @abstractmethod
    async def get_stream(self, camera: Any) -> Dict[str, Any]:
        """
        Fetch stream URL.
        Note: We accept a `camera` object (which should contain connection info)
        instead of just camera_id so the DB doesn't have to be queried inside the adapter.
        """

    async def check_status(self, camera: Any) -> str:
        """
        Check the connectivity status of the camera.
        """
        # default fallback; real adapters override this
        # pylint: disable=unused-argument
        return "unknown"


class MilestoneMockProvider(VMSProvider):
    """
    Simulated Milestone XProtect provider.
    """
    async def get_stream(self, camera: Any) -> Dict[str, Any]:
        return {
            "stream_url": "https://commondatastorage.googleapis.com"
                          "/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "status": "active",
            "resolution": "1080p"
        }


class HikvisionMockProvider(VMSProvider):
    """
    Simulated Hikvision NVR provider.
    """
    async def get_stream(self, camera: Any) -> Dict[str, Any]:
        return {
            "stream_url": "https://commondatastorage.googleapis.com"
                          "/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "status": "active",
            "resolution": "4K"
        }


class GenetecMockProvider(VMSProvider):
    """
    Simulated Genetec Security Center provider.
    """
    async def get_stream(self, camera: Any) -> Dict[str, Any]:
        return {
            "stream_url": "https://commondatastorage.googleapis.com"
                          "/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "status": "active",
            "resolution": "1080p"
        }


class DahuaMockProvider(VMSProvider):
    """
    Simulated Dahua provider.
    """
    async def get_stream(self, camera: Any) -> Dict[str, Any]:
        return {
            "stream_url": "https://commondatastorage.googleapis.com"
                          "/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "status": "active",
            "resolution": "720p"
        }


class LiveGridProvider(VMSProvider):
    """
    Provider for externally configured Live Grid cameras.
    """
    async def get_stream(self, camera: Any) -> Dict[str, Any]:
        camera_id = getattr(camera, "id", camera)
        return {
            "stream_url": f"https://cctv.corp8.cloud/{camera_id}/index.m3u8",
            "status": "active",
            "resolution": "1080p"
        }


class ONVIFProvider(VMSProvider):
    """
    Real protocol translation: discovers an ONVIF-compliant camera,
    fetches its RTSP stream URI via the ONVIF device/media service,
    and maps it to an HLS URL served by an RTSP->HLS relay
    (e.g. ffmpeg or MediaMTX) running alongside the backend.
    """

    DEVICE_REGISTRY: Dict[str, Dict[str, Any]] = {
        # "cam-onvif-01": {"host": "192.168.1.64", "port": 80, "user": "admin", "password": "abc"},
    }
    RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8888")

    def _get_device_info(self, camera: Any) -> Optional[Dict[str, Any]]:
        camera_id = str(getattr(camera, "id", camera))
        if hasattr(camera, "onvif_host") and camera.onvif_host:
            return {
                "host": camera.onvif_host,
                "port": getattr(camera, "onvif_port", 80),
                "user": getattr(camera, "onvif_username", ""),
                "password": getattr(camera, "onvif_password", "")
            }
        return self.DEVICE_REGISTRY.get(camera_id)

    def _sync_fetch_rtsp_uri(self, device_info: Dict[str, Any]) -> Optional[str]:
        # pylint: disable=import-outside-toplevel
        try:
            from onvif import ONVIFCamera
            cam = ONVIFCamera(
                device_info["host"],
                device_info["port"],
                device_info["user"],
                device_info["password"]
            )
            media_service = cam.create_media_service()
            profiles = media_service.GetProfiles()
            if not profiles:
                return None

            stream_setup = {
                "StreamSetup": {
                    "Stream": "RTP-Unicast",
                    "Transport": {"Protocol": "RTSP"},
                },
                "ProfileToken": profiles[0].token,
            }
            uri_response = media_service.GetStreamUri(stream_setup)
            return uri_response.Uri
        except RuntimeError as e:
            print(f"ONVIF Connection Error: {e}")
            return None
        except ImportError as e:
            print(f"ONVIF library missing: {e}")
            return None
        # pylint: disable=broad-exception-caught
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    async def _fetch_rtsp_uri(self, camera: Any) -> Optional[str]:
        device_info = self._get_device_info(camera)
        if not device_info:
            return None
        return await asyncio.to_thread(self._sync_fetch_rtsp_uri, device_info)

    async def get_stream(self, camera: Any) -> Dict[str, Any]:
        rtsp_uri = await self._fetch_rtsp_uri(camera)
        camera_id = getattr(camera, "id", camera)

        if not rtsp_uri:
            return {
                "stream_url": None,
                "status": "offline",
                "resolution": "unknown"
            }

        return {
            "stream_url": f"{self.RELAY_BASE_URL}/{camera_id}/index.m3u8",
            "status": await self.check_status(camera),
            "resolution": "unknown"
        }

    def _sync_check_status(self, device_info: Dict[str, Any]) -> str:
        # pylint: disable=import-outside-toplevel
        try:
            from onvif import ONVIFCamera
            cam = ONVIFCamera(
                device_info["host"],
                device_info["port"],
                device_info["user"],
                device_info["password"]
            )
            cam.devicemgmt.GetSystemDateAndTime()
            return "active"
        except RuntimeError:
            return "offline"
        except ImportError:
            return "offline"
        # pylint: disable=broad-exception-caught
        except Exception:
            return "offline"

    async def check_status(self, camera: Any) -> str:
        device_info = self._get_device_info(camera)
        if not device_info:
            return "offline"
        return await asyncio.to_thread(self._sync_check_status, device_info)


def get_vms_provider(vendor_name: str) -> VMSProvider:
    """Factory function to get the correct VMS provider."""
    vendors = {
        "Milestone": MilestoneMockProvider(),
        "Hikvision": HikvisionMockProvider(),
        "Genetec": GenetecMockProvider(),
        "Dahua": DahuaMockProvider(),
        "LiveGrid": LiveGridProvider(),
        "ONVIF": ONVIFProvider()
    }
    return vendors.get(vendor_name, MilestoneMockProvider())
