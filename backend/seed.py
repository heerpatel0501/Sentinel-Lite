from datetime import datetime, timedelta
import json
import database
import models


def seed_database_if_empty():
    db = database.SessionLocal()
    try:
        # Check if cameras already seeded
        if db.query(models.Camera).count() > 0:
            return

        print("[DB Seed] Seeding initial canonical Gujarat surveillance data...")
        now = datetime.now()

        # 1. Departments
        departments = [
            models.Department(name="Police", contact_email="controlroom@gujaratpolice.gov.in"),
            models.Department(name="RTO", contact_email="helpdesk-rto@gujarat.gov.in"),
            models.Department(name="GSRTC", contact_email="centraltransit@gsrtc.in"),
            models.Department(name="Municipal", contact_email="smartcity@ahmedabadcity.gov.in"),
            models.Department(name="Panchayat", contact_email="panchayat-sec@gujarat.gov.in"),
        ]
        db.add_all(departments)
        db.commit()

        # 2. Cameras
        cameras = [
            # Ahmedabad
            models.Camera(name="AHM-Junction-01", latitude=23.0225, longitude=72.5714, department="Police", vms_vendor="Milestone", status="online", resolution="1080p"),
            models.Camera(name="AHM-Traffic-02", latitude=23.0250, longitude=72.5740, department="RTO", vms_vendor="Hikvision", status="online", resolution="4K"),
            models.Camera(name="AHM-BusStop-03", latitude=23.0200, longitude=72.5700, department="GSRTC", vms_vendor="Genetec", status="online", resolution="1080p"),
            models.Camera(name="AHM-Park-04", latitude=23.0300, longitude=72.5800, department="Municipal", vms_vendor="Dahua", status="offline", resolution="720p"),
            # Rajkot
            models.Camera(name="RJK-MainRoad-01", latitude=22.3039, longitude=70.8022, department="Police", vms_vendor="Genetec", status="online", resolution="1080p"),
            models.Camera(name="RJK-Crossroad-02", latitude=22.3050, longitude=70.8050, department="RTO", vms_vendor="Milestone", status="online", resolution="4K"),
            models.Camera(name="RJK-Station-03", latitude=22.3000, longitude=70.8000, department="GSRTC", vms_vendor="Hikvision", status="offline", resolution="1080p"),
            models.Camera(name="RJK-Square-04", latitude=22.3100, longitude=70.8100, department="Municipal", vms_vendor="Milestone", status="online", resolution="720p"),
            # Surat
            models.Camera(name="SRT-Highway-01", latitude=21.1702, longitude=72.8311, department="Police", vms_vendor="Hikvision", status="online", resolution="4K"),
            models.Camera(name="SRT-Toll-02", latitude=21.1750, longitude=72.8350, department="RTO", vms_vendor="Dahua", status="online", resolution="1080p"),
            models.Camera(name="SRT-Depot-03", latitude=21.1650, longitude=72.8250, department="GSRTC", vms_vendor="Genetec", status="online", resolution="1080p"),
            models.Camera(name="SRT-Market-04", latitude=21.1800, longitude=72.8400, department="Municipal", vms_vendor="Milestone", status="online", resolution="1080p"),
            # Vadodara
            models.Camera(name="VAD-Entry-01", latitude=22.3072, longitude=73.1812, department="Police", vms_vendor="Milestone", status="online", resolution="1080p"),
            models.Camera(name="VAD-Bridge-02", latitude=22.3100, longitude=73.1850, department="RTO", vms_vendor="Genetec", status="offline", resolution="4K"),
            models.Camera(name="VAD-Terminal-03", latitude=22.3000, longitude=73.1750, department="GSRTC", vms_vendor="Hikvision", status="online", resolution="1080p"),
            models.Camera(name="VAD-Plaza-04", latitude=22.3150, longitude=73.1900, department="Municipal", vms_vendor="Dahua", status="online", resolution="720p"),
            # Gandhinagar
            models.Camera(name="GND-Secretariat-01", latitude=23.2156, longitude=72.6369, department="Police", vms_vendor="Genetec", status="online", resolution="4K"),
            models.Camera(name="GND-Circle-02", latitude=23.2200, longitude=72.6400, department="RTO", vms_vendor="Milestone", status="online", resolution="1080p"),
            models.Camera(name="GND-BusStand-03", latitude=23.2100, longitude=72.6300, department="GSRTC", vms_vendor="Dahua", status="online", resolution="1080p"),
            models.Camera(name="GND-Sector-04", latitude=23.2250, longitude=72.6450, department="Municipal", vms_vendor="Hikvision", status="offline", resolution="1080p"),
            # Mock ONVIF Camera
            models.Camera(name="TEST-ONVIF-01", latitude=23.0000, longitude=72.0000, department="Police", vms_vendor="ONVIF", status="online", resolution="1080p", onvif_host="192.168.1.64", onvif_port=80, onvif_username="admin", onvif_password="vault_demo_key"),
        ]
        db.add_all(cameras)
        db.commit()

        # 3. VMS Systems
        vms_systems = [
            models.VMSSystem(name="Police-Milestone-XProtect", vendor="Milestone", host="10.0.1.10", port=80, protocol="RTSP", department_id=1, status="active", last_sync=now),
            models.VMSSystem(name="RTO-Hikvision-iVMS", vendor="Hikvision", host="10.0.2.10", port=8000, protocol="RTSP", department_id=2, status="active", last_sync=now),
            models.VMSSystem(name="GSRTC-Genetec-Center", vendor="Genetec", host="10.0.3.10", port=443, protocol="RTSP", department_id=3, status="active", last_sync=now),
            models.VMSSystem(name="Municipal-Dahua-DSS", vendor="Dahua", host="10.0.4.10", port=37777, protocol="RTSP", department_id=4, status="active", last_sync=now),
            models.VMSSystem(name="SmartCity-ONVIF-Gateway", vendor="ONVIF", host="192.168.1.64", port=80, protocol="ONVIF", department_id=4, status="active", last_sync=now),
            models.VMSSystem(name="Sentinel-Official-RTSP-Grid", vendor="Sentinel", host="cctv.corp8.cloud", port=554, protocol="RTSP", department_id=1, status="active", last_sync=now),
        ]
        db.add_all(vms_systems)
        db.commit()

        # 4. Users
        users = [
            models.User(email="admin@gujaratpolice.gov.in", department_id=1, role="admin"),
            models.User(email="analyst@rto.gujarat.gov.in", department_id=2, role="analyst"),
            models.User(email="monitor@gsrtc.in", department_id=3, role="viewer"),
            models.User(email="civic@ahmedabadcity.gov.in", department_id=4, role="analyst"),
        ]
        db.add_all(users)
        db.commit()

        # 5. Watchlist
        watchlist = [
            models.Watchlist(plate_text="GJ01AB1234", reason="stolen", added_by_department="Police", active=True),
            models.Watchlist(plate_text="GJ05XX9999", reason="wanted", added_by_department="Police", active=True),
            models.Watchlist(plate_text="GJ03MC4567", reason="flagged", added_by_department="RTO", active=True),
            models.Watchlist(plate_text="GJ18ZZ0001", reason="flagged", added_by_department="Police", active=True),
            models.Watchlist(plate_text="GJ06CD5555", reason="stolen", added_by_department="Police", active=False),
        ]
        db.add_all(watchlist)
        db.commit()

        # 6. Detections & Plates
        det1 = models.VehicleDetection(
            camera_id=1, timestamp=now - timedelta(minutes=45), vehicle_type="car", confidence_score=0.92,
            bounding_box=[0.22, 0.55, 0.51, 0.76], frame_snapshot_path="/snapshots/det_ahm_01.jpg"
        )
        det2 = models.VehicleDetection(
            camera_id=11, timestamp=now - timedelta(minutes=20), vehicle_type="bus", confidence_score=0.89,
            bounding_box=[0.15, 0.30, 0.60, 0.85], frame_snapshot_path="/snapshots/det_srt_02.jpg"
        )
        db.add_all([det1, det2])
        db.commit()

        p1 = models.Plate(detection_id=det1.id, plate_text="GJ01-AB-1234", normalized_plate="GJ01AB1234", ocr_confidence=0.94, plate_bounding_box=[0.35, 0.65, 0.45, 0.72])
        p2 = models.Plate(detection_id=det2.id, plate_text="GJ05-XX-9999", normalized_plate="GJ05XX9999", ocr_confidence=0.91, plate_bounding_box=[0.28, 0.68, 0.40, 0.76])
        db.add_all([p1, p2])
        db.commit()

        # 7. Vehicle Movements
        movements = [
            models.VehicleMovement(plate_text="GJ01-AB-1234", camera_id=1, department_id=1, detection_id=det1.id, timestamp=now - timedelta(minutes=45)),
            models.VehicleMovement(plate_text="GJ01-AB-1234", camera_id=2, department_id=2, detection_id=None, timestamp=now - timedelta(minutes=30)),
            models.VehicleMovement(plate_text="GJ01-AB-1234", camera_id=4, department_id=4, detection_id=None, timestamp=now - timedelta(minutes=10)),
            models.VehicleMovement(plate_text="GJ05-XX-9999", camera_id=9, department_id=1, detection_id=None, timestamp=now - timedelta(minutes=60)),
            models.VehicleMovement(plate_text="GJ05-XX-9999", camera_id=11, department_id=3, detection_id=det2.id, timestamp=now - timedelta(minutes=20)),
            models.VehicleMovement(plate_text="GJ03-MC-4567", camera_id=6, department_id=2, detection_id=None, timestamp=now - timedelta(minutes=75)),
            models.VehicleMovement(plate_text="GJ03-MC-4567", camera_id=8, department_id=4, detection_id=None, timestamp=now - timedelta(minutes=35)),
            models.VehicleMovement(plate_text="GJ18-ZZ-0001", camera_id=17, department_id=1, detection_id=None, timestamp=now - timedelta(minutes=80)),
            models.VehicleMovement(plate_text="GJ18-ZZ-0001", camera_id=18, department_id=2, detection_id=None, timestamp=now - timedelta(minutes=40)),
            models.VehicleMovement(plate_text="GJ06-CD-5555", camera_id=13, department_id=1, detection_id=None, timestamp=now - timedelta(minutes=95)),
            models.VehicleMovement(plate_text="GJ06-CD-5555", camera_id=15, department_id=3, detection_id=None, timestamp=now - timedelta(minutes=50)),
        ]
        db.add_all(movements)
        db.commit()

        # 8. Evidence Records
        ev1 = models.EvidenceRecord(
            detection_id=det1.id, plate_text="GJ01-AB-1234", file_path="evidence/snapshots/GJ01-AB-1234_cam1.jpg",
            uri_reference="/evidence/snapshots/GJ01-AB-1234_cam1.jpg", pts_timestamp=15.2, file_size_bytes=42100
        )
        ev2 = models.EvidenceRecord(
            detection_id=det2.id, plate_text="GJ05-XX-9999", file_path="evidence/snapshots/GJ05-XX-9999_cam11.jpg",
            uri_reference="/evidence/snapshots/GJ05-XX-9999_cam11.jpg", pts_timestamp=32.8, file_size_bytes=51400
        )
        db.add_all([ev1, ev2])
        db.commit()

        # 9. Alerts
        alerts = [
            models.Alert(
                plate_text="GJ01-AB-1234", alert_type="cross_department",
                camera_ids_involved=["AHM-Junction-01", "AHM-Traffic-02"],
                departments_involved=["Police", "RTO"], timestamp=now - timedelta(minutes=15),
                status="new", description="Vehicle tracked across Police and RTO cameras."
            ),
            models.Alert(
                plate_text="GJ05-XX-9999", alert_type="watchlist_match",
                camera_ids_involved=["SRT-Highway-01", "SRT-Depot-03"],
                departments_involved=["Police", "GSRTC"], timestamp=now - timedelta(minutes=25),
                status="new", description="Suspicious vehicle near GSRTC depot."
            ),
            models.Alert(
                plate_text="GJ03-MC-4567", alert_type="speeding",
                camera_ids_involved=["RJK-Crossroad-02", "RJK-Square-04"],
                departments_involved=["RTO", "Municipal"], timestamp=now - timedelta(minutes=40),
                status="reviewed", description="Speeding violation in municipal zone."
            ),
            models.Alert(
                plate_text="GJ18-ZZ-0001", alert_type="watchlist_match",
                camera_ids_involved=["GND-Secretariat-01", "GND-Circle-02"],
                departments_involved=["Police", "RTO"], timestamp=now - timedelta(minutes=55),
                status="new", description="VIP convoy route clearance check."
            ),
        ]
        db.add_all(alerts)
        db.commit()

        # 10. Stream Health
        stream_healths = [
            models.StreamHealth(camera_id=1, status="active", codec="H.264", resolution="1080p", fps_actual=25.0, last_pts=150.2, reconnect_attempts=0),
            models.StreamHealth(camera_id=2, status="active", codec="H.265", resolution="4K", fps_actual=30.0, last_pts=220.4, reconnect_attempts=0),
            models.StreamHealth(camera_id=3, status="active", codec="H.264", resolution="1080p", fps_actual=24.0, last_pts=95.1, reconnect_attempts=0),
            models.StreamHealth(camera_id=5, status="active", codec="H.264", resolution="1080p", fps_actual=25.0, last_pts=310.0, reconnect_attempts=0),
        ]
        db.add_all(stream_healths)
        db.commit()

        # 11. Audit Logs
        audits = [
            models.AuditLog(user_id=1, action="VIEW_ALERT_FEED", target_type="alert", target_id="ALL", timestamp=now - timedelta(hours=2)),
            models.AuditLog(user_id=2, action="WATCHLIST_QUERY", target_type="watchlist", target_id="GJ01AB1234", timestamp=now - timedelta(hours=1)),
            models.AuditLog(user_id=1, action="EXPORT_CROSS_DEPT_TRAIL", target_type="vehicle_movement", target_id="GJ05-XX-9999", timestamp=now - timedelta(minutes=30)),
        ]
        db.add_all(audits)
        db.commit()

        # 12. Investigation
        inv = models.Investigation(
            title="Investigation: Cross-Agency Interception of Stolen Vehicle GJ01-AB-1234",
            case_number="CASE-2026-GUJ-0842",
            target_plate="GJ01-AB-1234",
            lead_investigator_id=1,
            status="active",
            priority="critical",
            notes="Target vehicle flagged in state stolen vehicle registry. Reconstructed path across Ahmedabad and Gandhinagar.",
            created_at=now - timedelta(hours=3),
            updated_at=now - timedelta(minutes=10)
        )
        db.add(inv)
        db.commit()

        inv_ev = models.InvestigationEvidence(
            investigation_id=inv.id,
            evidence_record_id=ev1.id,
            title="AHM-Junction-01 Forensic ANPR Snapshot",
            evidence_type="snapshot",
            uri="/evidence/snapshots/GJ01-AB-1234_cam1.jpg",
            notes="Captured at junction with 0.94 OCR confidence.",
            created_at=now - timedelta(hours=2)
        )
        db.add(inv_ev)
        db.commit()

        print("[DB Seed] Successfully populated canonical Gujarat surveillance data!")
    except Exception as e:
        db.rollback()
        print(f"[DB Seed Error] Failed to seed database: {e}")
    finally:
        db.close()
