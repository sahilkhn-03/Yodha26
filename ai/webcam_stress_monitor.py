"""
Real-time Webcam Stress Monitoring
===================================
Monitor stress levels from webcam feed in real-time.
Press 'q' to quit.
"""

import cv2
import numpy as np
from inference_stress_model import StressPredictor

# Initialize predictor
print("Loading stress predictor...")
predictor = StressPredictor()
print("✓ Ready!\n")
print("Press 'q' to quit")

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam")
    exit()

frame_count = 0
stress_score = None
stress_level = "Unknown"

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Error: Could not read frame")
        break
    
    # Predict every 30 frames (about once per second at 30fps)
    if frame_count % 30 == 0:
        result = predictor.predict_from_frame(frame)
        
        if result['success']:
            stress_score = result['stress_score']
            stress_level = result['stress_level']
            
            # Print to console
            print(f"Stress: {stress_score:.1f}/100 ({stress_level})")
    
    # Display stress info on frame
    if stress_score is not None:
        # Determine color based on stress level
        if stress_score < 30:
            color = (0, 255, 0)  # Green
        elif stress_score < 55:
            color = (0, 255, 255)  # Yellow
        elif stress_score < 75:
            color = (0, 165, 255)  # Orange
        else:
            color = (0, 0, 255)  # Red
        
        # Draw stress info
        cv2.putText(frame, f"Stress: {stress_score:.1f}/100", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, f"Level: {stress_level}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # Draw stress bar
        bar_width = int(stress_score * 6)  # Max 600 pixels
        cv2.rectangle(frame, (10, 90), (10 + bar_width, 110), color, -1)
        cv2.rectangle(frame, (10, 90), (610, 110), (255, 255, 255), 2)
    
    # Show frame
    cv2.imshow('Real-time Stress Monitor', frame)
    
    frame_count += 1
    
    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\n✓ Monitoring stopped")
