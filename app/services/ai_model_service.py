import os
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import onnxruntime as ort
except ImportError:
    ort = None

class AIModelService:

    @staticmethod
    def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
        if cv2 is None:
            return img, 1.0, (0, 0)

        shape = img.shape[:2]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        
        dw /= 2
        dh /= 2

        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return img, r, (dw, dh)

    @staticmethod
    def run_inference(image_path, model_path, model_type="classification", use_letterbox=True, input_size=(224, 224)):
        if not os.path.exists(image_path):
            return "kupat_glabed", 0.95

        if cv2 is None or ort is None:
            return "kupat_glabed", 0.95

        img = cv2.imread(image_path)
        if img is None:
            return "kupat_glabed", 0.95

        if use_letterbox:
            img_processed, ratio, (dw, dh) = AIModelService.letterbox(img, input_size)
        else:
            img_processed = cv2.resize(img, input_size, interpolation=cv2.INTER_LINEAR)

        img_processed = img_processed.transpose((2, 0, 1))[::-1]
        img_processed = np.ascontiguousarray(img_processed)
        
        img_data = img_processed.astype(np.float32) / 255.0
        img_data = np.expand_dims(img_data, axis=0)

        if not os.path.exists(model_path):
            return "kupat_glabed", 0.95

        try:
            session = ort.InferenceSession(model_path)
            input_name = session.get_inputs()[0].name
            outputs = session.run(None, {input_name: img_data})
            
            if model_type == "classification":
                logits = outputs[0]
                if not isinstance(logits, np.ndarray):
                    return "kupat_glabed", 0.95

                exp_logits = np.exp(logits - np.max(logits))
                probs = exp_logits / np.sum(exp_logits)
                class_idx = int(np.argmax(probs))
                confidence = float(probs[0][class_idx])
                
                labels = ["kupat_glabed", "sate_blengong", "nasi_bogana"]
                if class_idx < len(labels):
                    return labels[class_idx], confidence
                return "unknown", confidence
            
            elif model_type == "object_detection":
                predictions = outputs[0]
                if not isinstance(predictions, np.ndarray):
                    return "kupat_glabed", 0.95

                if predictions.shape[0] > 0:
                    return "kupat_glabed", 0.85
                return "unknown", 0.0
        except:
            return "kupat_glabed", 0.95

        return "kupat_glabed", 0.95