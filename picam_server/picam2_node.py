import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from std_msgs.msg import String
from vision_msgs.msg import Detection2DArray, Detection2D
import requests
import onnxruntime as ort
import os
from app_detect import COCO_CLASSES, get_camera, MODEL_PATH

class PiCam2Node(Node):
    def __init__(self):
        super().__init__("picam2_node")
        
        self.declare_parameter("server_url", "http://localhost:5000/api/upload")
        self.server_url = self.get_parameter("server_url").value
        
        # Load YOLOv8 model
        self.model = self.load_model()
        self.camera = get_camera()
        
        # Publisher for detections (to navThread)
        self.pub_detections = self.create_publisher(
            Detection2DArray,
            "/camera/detections",
            10
        )
        
        # Subscriber for shutdown
        self.create_subscription(
            String,
            "/rover/system_shutdown",
            self.shutdown_callback,
            10
        )
        
        # capture and detect every 100ms
        self.timer = self.create_timer(0.1, self.capture_and_detect)
        self.get_logger().info(f"PiCam2 node started. Server URL: {self.server_url}")
    
    def load_model(self):
        """Load YOLOv8 ONNX model"""
        if not os.path.exists(MODEL_PATH):
            self.get_logger().error(f"Model not found at {MODEL_PATH}")
            return None
        try:
            session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
            self.get_logger().info("YOLOv8n ONNX model loaded")
            return session
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {e}")
            return None
    
    def capture_and_detect(self):
        """Capture frame, run YOLOv8, publish detections + send to server"""
        try:
            if self.model is None:
                return
            
            # Capture frame
            frame = self.camera.capture_array()
            orig_h, orig_w = frame.shape[:2]
            
            # Run detection
            detections = self.detect_objects(frame, orig_h, orig_w)
            
            # Publish detections to navThread
            self.publish_detections(detections)
            
            # Send frame + detections to external server
            self.send_to_server(frame, detections)
            
        except Exception as e:
            self.get_logger().error(f"Capture/detection error: {e}")
    
    def detect_objects(self, frame, orig_h, orig_w, conf_threshold=0.4):
        """Run YOLOv8 on frame"""
        input_size = 640
        img_resized = cv2.resize(frame, (input_size, input_size))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_norm = img_rgb.astype(np.float32) / 255.0
        img_input = np.transpose(img_norm, (2, 0, 1))[np.newaxis, ...]
        
        # Inference
        input_name = self.model.get_inputs()[0].name
        outputs = self.model.run(None, {input_name: img_input})
        predictions = outputs[0][0].T
        
        # Decode
        boxes_xywh = predictions[:, :4]
        class_scores = predictions[:, 4:]
        class_ids = np.argmax(class_scores, axis=1)
        confidences = class_scores[np.arange(len(class_ids)), class_ids]
        
        mask = confidences >= conf_threshold
        boxes_xywh = boxes_xywh[mask]
        confidences = confidences[mask]
        class_ids = class_ids[mask]
        
        scale_x = orig_w / input_size
        scale_y = orig_h / input_size
        
        boxes_xyxy = []
        for box in boxes_xywh:
            cx, cy, w, h = box
            x1 = int((cx - w / 2) * scale_x)
            y1 = int((cy - h / 2) * scale_y)
            x2 = int((cx + w / 2) * scale_x)
            y2 = int((cy + h / 2) * scale_y)
            boxes_xyxy.append([x1, y1, x2, y2])
        
        # NMS
        detections = []
        if boxes_xyxy:
            boxes_for_nms = [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in boxes_xyxy]
            indices = cv2.dnn.NMSBoxes(
                boxes_for_nms,
                confidences.tolist(),
                conf_threshold,
                0.45
            )
            if len(indices) > 0:
                for i in indices.flatten():
                    x1, y1, x2, y2 = boxes_xyxy[i]
                    cls_id = int(class_ids[i])
                    conf = float(confidences[i])
                    label = COCO_CLASSES[cls_id] if cls_id < len(COCO_CLASSES) else f"cls{cls_id}"
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "box": [x1, y1, x2, y2],
                        "class_id": cls_id
                    })
        
        return detections
    
    def publish_detections(self, detections):
        """Publish detections to ROS topic for navThread"""
        detection_array = Detection2DArray()
        detection_array.header.stamp = self.get_clock().now().to_msg()
        detection_array.header.frame_id = "camera"
        
        for det in detections:
            detection_2d = Detection2D()
            detection_2d.header.stamp = detection_array.header.stamp
            
            x1, y1, x2, y2 = det["box"]
            detection_2d.bbox.center.x = float((x1 + x2) / 2)
            detection_2d.bbox.center.y = float((y1 + y2) / 2)
            detection_2d.bbox.size_x = float(x2 - x1)
            detection_2d.bbox.size_y = float(y2 - y1)
            
            result = Detection2D()
            result.hypothesis.class_name = det["label"]
            result.hypothesis.likelihood = det["confidence"]
            detection_2d.results.append(result)
            
            detection_array.detections.append(detection_2d)
        
        self.pub_detections.publish(detection_array)
    
    def send_to_server(self, frame, detections):
        """Send frame + detections to external web server"""
        try:
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            
            # Prepare detection data
            detection_data = [
                {
                    "label": det["label"],
                    "confidence": det["confidence"],
                    "box": det["box"]
                }
                for det in detections
            ]
            
            # Send to server
            files = {'image': ('frame.jpg', buffer.tobytes())}
            data = {'detections': str(detection_data)}
            
            response = requests.post(self.server_url, files=files, data=data, timeout=2)
            
            if response.status_code != 200:
                self.get_logger().warn(f"Server returned {response.status_code}")
        
        except requests.exceptions.Timeout:
            self.get_logger().warn("Server request timeout")
        except Exception as e:
            self.get_logger().warn(f"Server send error: {e}")
    
    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received")
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = PiCam2Node()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()