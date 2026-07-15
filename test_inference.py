import os
from typing import Tuple, List
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class YOLO26Tester:
    """Utility class to run type-safe end-to-end inference using YOLO26."""

    LABELS: List[str] = ["kupat_glabed", "olos", "sate", "sega_ponggol", "soto_tauco", "tahu_aci"]
    COLOR_PALETTE: List[Tuple[int, int, int]] = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (0, 255, 255),  # Yellow
        (255, 0, 255),  # Magenta
        (255, 255, 0)   # Cyan
    ]

    @staticmethod
    def letterbox(
        img: np.ndarray, 
        new_shape: Tuple[int, int] = (640, 640), 
        color: Tuple[int, int, int] = (114, 114, 114)
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """Resizes and pads image to fit model constraints while preserving ratio."""
        if cv2 is None:
            return img, 1.0, (0.0, 0.0)

        shape: Tuple[int, int] = (img.shape[0], img.shape[1])
        r: float = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        new_unpad: Tuple[int, int] = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        dw: float = (new_shape[1] - new_unpad[0]) / 2.0
        dh: float = (new_shape[0] - new_unpad[1]) / 2.0

        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        
        top: int = int(round(dh - 0.1))
        bottom: int = int(round(dh + 0.1))
        left: int = int(round(dw - 0.1))
        right: int = int(round(dw + 0.1))
        
        img = cv2.copyMakeBorder(
            img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )
        return img, r, (dw, dh)

    @classmethod
    def test_image_inference(
        cls, 
        image_path: str, 
        model_path: str, 
        output_path: str = "output_detected.png", 
        conf_threshold: float = 0.25
    ) -> None:
        if cv2 is None or ort is None:
            print("[Error] OpenCV or ONNX Runtime is not installed.")
            return

        if not os.path.exists(image_path):
            print(f"[Error] Source image '{image_path}' not found.")
            return

        if not os.path.exists(model_path):
            print(f"[Error] ONNX Model '{model_path}' not found.")
            return

        orig_img = cv2.imread(image_path)
        if orig_img is None:
            print("[Error] Failed to read the image.")
            return
        assert isinstance(orig_img, np.ndarray)

        orig_h: int = orig_img.shape[0]
        orig_w: int = orig_img.shape[1]
        input_size: Tuple[int, int] = (640, 640)

        img_processed, ratio, (dw, dh) = cls.letterbox(orig_img, input_size)
        
        img_input = img_processed.transpose((2, 0, 1))[::-1]
        img_input = np.ascontiguousarray(img_input)
        img_data = img_input.astype(np.float32) / 255.0
        img_data = np.expand_dims(img_data, axis=0)

        session = ort.InferenceSession(model_path)
        input_name: str = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: img_data})

        if not isinstance(outputs, list) or len(outputs) == 0:
            print("[Error] Expected list output from ONNX session.")
            return
        
        predictions = outputs[0]
        if not isinstance(predictions, np.ndarray):
            print("[Error] First output node must be a numpy array.")
            return

        if len(predictions.shape) != 3 or predictions.shape[2] != 6:
            print(f"[Error] Expected shape (1, 300, 6), got {predictions.shape}.")
            return

        detections: np.ndarray = predictions[0]

        for i in range(detections.shape[0]):
            detection = detections[i]
            x1, y1, x2, y2, confidence, class_id_val = detection

            if confidence >= conf_threshold:
                orig_x1 = int(round((x1 - dw) / ratio))
                orig_y1 = int(round((y1 - dh) / ratio))
                orig_x2 = int(round((x2 - dw) / ratio))
                orig_y2 = int(round((y2 - dh) / ratio))

                orig_x1 = max(0, min(orig_x1, orig_w - 1))
                orig_y1 = max(0, min(orig_y1, orig_h - 1))
                orig_x2 = max(0, min(orig_x2, orig_w - 1))
                orig_y2 = max(0, min(orig_y2, orig_h - 1))

                class_id: int = int(class_id_val)
                label: str = cls.LABELS[class_id] if class_id < len(cls.LABELS) else f"ID: {class_id}"
                color: Tuple[int, int, int] = cls.COLOR_PALETTE[class_id % len(cls.COLOR_PALETTE)]

                cv2.rectangle(orig_img, (orig_x1, orig_y1), (orig_x2, orig_y2), color, 3)

                text: str = f"{label} {confidence:.2f}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale: float = 0.6
                thickness: int = 2
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                
                text_bg_y1 = max(0, orig_y1 - text_size[1] - 10)
                cv2.rectangle(
                    orig_img, 
                    (orig_x1, text_bg_y1), 
                    (orig_x1 + text_size[0] + 10, orig_y1), 
                    color, 
                    -1
                )
                
                cv2.putText(
                    orig_img, 
                    text, 
                    (orig_x1 + 5, orig_y1 - 5), 
                    font, 
                    font_scale, 
                    (255, 255, 255), 
                    thickness, 
                    cv2.LINE_AA
                )

        cv2.imwrite(output_path, orig_img)
        print(f"[Success] YOLO26 Inference complete. Result saved at '{output_path}'.")


if __name__ == "__main__":
    IMAGE_FILE = "image.png"
    MODEL_FILE = os.path.join("app", "model_ai", "food_detector.onnx")
    
    if not os.path.exists(MODEL_FILE):
        MODEL_FILE = os.path.join("model_ai", "food_detector.onnx")

    YOLO26Tester.test_image_inference(IMAGE_FILE, MODEL_FILE)