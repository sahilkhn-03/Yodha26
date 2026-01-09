"""
Simple test script for facial stress detection with maximized window visibility
"""

import cv2
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from facial_stress_inference_v2 import FacialStressInference, StressConfig, get_stress_level_label
import time

def main():
    print("\n" + "=" * 70)
    print(" " * 15 + "🎭 FACIAL STRESS DETECTION - LIVE TEST")
    print("=" * 70)
    print("\nInitializing system...")
    
    # Create configuration
    config = StressConfig(
        show_landmarks=True,
        show_connections=True,
        landmark_size=2,
        connection_thickness=2
    )
    
    # Initialize engine
    engine = FacialStressInference(config)
    print("✅ Facial stress engine initialized")
    
    # Open webcam
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow on Windows
    if not cap.isOpened():
        print("❌ ERROR: Could not open webcam!")
        print("   Check if your camera is connected and not in use by another app.")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    print(f"✅ Webcam opened: {int(actual_width)}x{int(actual_height)}")
    
    # Create window with explicit properties
    window_name = 'Facial Stress Detection - Press Q to Quit'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow(window_name, 1280, 720)
    
    # Try to move window to front
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    
    print("\n" + "=" * 70)
    print("🎥 LIVE FEED STARTING...")
    print("=" * 70)
    print("\n📌 CONTROLS:")
    print("   Q - Quit")
    print("   L - Toggle landmarks")
    print("   C - Toggle connections")
    print("   F - Toggle fullscreen")
    print("\n⚡ Look at the window that just opened!")
    print("   (It should be on top of other windows)\n")
    
    frame_count = 0
    fps_start = time.time()
    fps = 0
    fullscreen = False
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break
            
            # Process frame
            result, processed_frame = engine.process_frame_with_visualization(frame)
            
            # Create info overlay
            if result['face_detected']:
                stress = result['facial_stress']
                level = get_stress_level_label(stress)
                
                # Background for text
                overlay = processed_frame.copy()
                cv2.rectangle(overlay, (10, 10), (500, 180), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, processed_frame, 0.4, 0, processed_frame)
                
                # Stress info - larger text
                color = (0, 255, 0) if stress < 30 else (0, 255, 255) if stress < 60 else (0, 0, 255)
                cv2.putText(processed_frame, f"STRESS: {stress:.1f}/100 - {level}", 
                           (20, 45), cv2.FONT_HERSHEY_DUPLEX, 1.0, color, 2)
                
                # Component features
                cv2.putText(processed_frame, f"Eye Closure:    {result['eye_closure']:.2f}", 
                           (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                cv2.putText(processed_frame, f"Eyebrow Tension: {result['eyebrow_tension']:.2f}", 
                           (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                cv2.putText(processed_frame, f"Jaw Tension:    {result['jaw_tension']:.2f}", 
                           (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                # Border indicator
                border_color = color
                cv2.rectangle(processed_frame, (5, 5), 
                            (processed_frame.shape[1]-5, processed_frame.shape[0]-5), 
                            border_color, 8)
            else:
                # No face detected
                cv2.putText(processed_frame, "NO FACE DETECTED", 
                           (50, 100), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 255), 3)
                cv2.putText(processed_frame, "Position your face in the camera", 
                           (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # FPS counter
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                fps = 30 / elapsed if elapsed > 0 else 0
                fps_start = time.time()
            
            cv2.putText(processed_frame, f"FPS: {fps:.1f}", 
                       (processed_frame.shape[1] - 150, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow(window_name, processed_frame)
            
            # Keep window on top every 30 frames
            if frame_count % 30 == 0:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
            
            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q') or key == 27:  # Q or ESC
                print("\n👋 Quitting...")
                break
            elif key == ord('l') or key == ord('L'):
                config.show_landmarks = not config.show_landmarks
                print(f"Landmarks: {'✅ ON' if config.show_landmarks else '❌ OFF'}")
            elif key == ord('c') or key == ord('C'):
                config.show_connections = not config.show_connections
                print(f"Connections: {'✅ ON' if config.show_connections else '❌ OFF'}")
            elif key == ord('f') or key == ord('F'):
                fullscreen = not fullscreen
                if fullscreen:
                    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    print("Fullscreen: ✅ ON")
                else:
                    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                    print("Fullscreen: ❌ OFF")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🔧 Cleaning up...")
        cap.release()
        cv2.destroyAllWindows()
        engine.close()
        print("✅ Done!\n")

if __name__ == "__main__":
    main()
