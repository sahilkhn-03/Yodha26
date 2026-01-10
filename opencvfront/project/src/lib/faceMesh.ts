/**
 * MediaPipe Face Mesh visualization utilities
 * Runs face detection in the browser and draws mesh overlay
 */

// Face mesh connections for drawing
export const FACE_MESH_CONNECTIONS = [
  // Lips outer
  [61, 146], [146, 91], [91, 181], [181, 84], [84, 17], [17, 314], [314, 405], [405, 321], [321, 375], [375, 291],
  [61, 185], [185, 40], [40, 39], [39, 37], [37, 0], [0, 267], [267, 269], [269, 270], [270, 409], [409, 291],
  // Lips inner
  [78, 95], [95, 88], [88, 178], [178, 87], [87, 14], [14, 317], [317, 402], [402, 318], [318, 324], [324, 308],
  [78, 191], [191, 80], [80, 81], [81, 82], [82, 13], [13, 312], [312, 311], [311, 310], [310, 415], [415, 308],
  // Left eye
  [33, 7], [7, 163], [163, 144], [144, 145], [145, 153], [153, 154], [154, 155], [155, 133],
  [33, 246], [246, 161], [161, 160], [160, 159], [159, 158], [158, 157], [157, 173], [173, 133],
  // Right eye
  [362, 382], [382, 381], [381, 380], [380, 374], [374, 373], [373, 390], [390, 249], [249, 263],
  [362, 466], [466, 388], [388, 387], [387, 386], [386, 385], [385, 384], [384, 398], [398, 263],
  // Face oval
  [10, 338], [338, 297], [297, 332], [332, 284], [284, 251], [251, 389], [389, 356], [356, 454], [454, 323], [323, 361],
  [361, 288], [288, 397], [397, 365], [365, 379], [379, 378], [378, 400], [400, 377], [377, 152], [152, 148], [148, 176],
  [176, 149], [149, 150], [150, 136], [136, 172], [172, 58], [58, 132], [132, 93], [93, 234], [234, 127], [127, 162],
  [162, 21], [21, 54], [54, 103], [103, 67], [67, 109], [109, 10],
];

export function drawFaceMesh(
  ctx: CanvasRenderingContext2D,
  landmarks: Array<{ x: number; y: number; z: number }>,
  width: number,
  height: number,
  features?: { avg_eye_aspect_ratio?: number; avg_eyebrow_tension?: number; jaw_drop?: number }
) {
  // Draw connections with visible but transparent lines
  ctx.strokeStyle = 'rgba(0, 255, 0, 0.45)'; // 45% opacity - clearly visible
  ctx.lineWidth = 1;

  for (const [start, end] of FACE_MESH_CONNECTIONS) {
    const startPoint = landmarks[start];
    const endPoint = landmarks[end];
    
    if (startPoint && endPoint) {
      ctx.beginPath();
      ctx.moveTo(startPoint.x * width, startPoint.y * height);
      ctx.lineTo(endPoint.x * width, endPoint.y * height);
      ctx.stroke();
    }
  }

  // Draw key landmark points
  ctx.fillStyle = 'rgba(0, 255, 0, 0.7)'; // 70% opacity
  const keyPoints = [33, 133, 362, 263, 1, 61, 291]; // Eyes, nose, mouth corners
  for (const idx of keyPoints) {
    const landmark = landmarks[idx];
    if (landmark) {
      ctx.beginPath();
      ctx.arc(landmark.x * width, landmark.y * height, 2, 0, 2 * Math.PI);
      ctx.fill();
    }
  }

  // If feature estimates are provided, display compact labels near relevant regions
  if (features) {
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.font = '12px Inter, Arial, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';

    // Eye openness near left eye (use landmark 33)
    const leftEye = landmarks[33];
    if (leftEye && typeof features.avg_eye_aspect_ratio === 'number') {
      const txt = `Eye: ${Math.round(features.avg_eye_aspect_ratio * 100) / 100}`;
      ctx.fillText(txt, leftEye.x * width + 6, leftEye.y * height - 10);
    }

    // Brow tension near left eyebrow (use landmark 70)
    const leftBrow = landmarks[70];
    if (leftBrow && typeof features.avg_eyebrow_tension === 'number') {
      const txt = `Brow: ${Math.round(features.avg_eyebrow_tension * 1000) / 100}`;
      ctx.fillText(txt, leftBrow.x * width + 6, leftBrow.y * height - 10);
    }

    // Jaw drop near chin (use landmark 152)
    const chin = landmarks[152];
    if (chin && typeof features.jaw_drop === 'number') {
      const txt = `Jaw: ${Math.round(features.jaw_drop * 1000) / 100}`;
      ctx.fillText(txt, chin.x * width + 6, chin.y * height - 10);
    }
  }
}
