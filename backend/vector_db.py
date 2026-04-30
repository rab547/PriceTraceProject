from __future__ import annotations # type: ignore

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure model downloads go to a writable project directory (avoids ~/.cache permission issues).
os.environ.setdefault("HF_HOME", os.path.join(_BACKEND_DIR, ".hf"))
os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(_BACKEND_DIR, ".hf", "transformers"))
os.environ.setdefault("HF_HUB_CACHE", os.path.join(_BACKEND_DIR, ".hf", "hub"))

import chromadb
import torch
from PIL import Image
from transformers import (
    AutoModelForZeroShotObjectDetection,
    AutoProcessor as DinoAutoProcessor,
    CLIPImageProcessor,
    CLIPVisionModelWithProjection,
)

_DEFAULT_CLIP_MODEL_ID = "openai/clip-vit-base-patch32"
_DEFAULT_DINO_MODEL_ID = "IDEA-Research/grounding-dino-tiny"


def crop_image(image: Image.Image, box_xyxy: Sequence[float]) -> Optional[Image.Image]:
    x1, y1, x2, y2 = [float(v) for v in box_xyxy]
    x1_i = max(0, int(round(x1)))
    y1_i = max(0, int(round(y1)))
    x2_i = min(image.width, int(round(x2)))
    y2_i = min(image.height, int(round(y2)))

    if x2_i <= x1_i or y2_i <= y1_i:
        return None

    return image.crop((x1_i, y1_i, x2_i, y2_i))


@dataclass(frozen=True)
class Detection:
    box_xyxy: Tuple[float, float, float, float]
    score: float
    label: str


class GroundingDinoDetector:
    def __init__(
        self,
        model_id: str = _DEFAULT_DINO_MODEL_ID,
        device: Optional[str] = None,
    ) -> None:
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        cache_dir = os.environ.get("HF_HOME")
        self._processor = DinoAutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
        self._model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, cache_dir=cache_dir).to(
            self.device
        )
        self._model.eval()

    @torch.inference_mode()
    def detect(
        self,
        image: Image.Image,
        text_prompt: str,
        *,
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
    ) -> List[Detection]:
        rgb = image.convert("RGB")
        inputs = self._processor(images=rgb, text=text_prompt, return_tensors="pt").to(self.device)
        outputs = self._model(**inputs)

        results = self._processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=box_threshold,
            text_threshold=text_threshold,
            target_sizes=[rgb.size[::-1]],  # (h, w)
        )[0]

        boxes = results["boxes"].detach().cpu().tolist()
        scores = results["scores"].detach().cpu().tolist()
        labels = list(results["text_labels"])

        detections: List[Detection] = []
        for box, score, label in zip(boxes, scores, labels):
            x1, y1, x2, y2 = [float(v) for v in box]
            detections.append(Detection((x1, y1, x2, y2), float(score), str(label)))
        return detections


class ClipEmbedder:
    def __init__(
        self,
        model_id: str = _DEFAULT_CLIP_MODEL_ID,
        device: Optional[str] = None,
    ) -> None:
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        cache_dir = os.environ.get("HF_HOME")
        self._processor = CLIPImageProcessor.from_pretrained(model_id, cache_dir=cache_dir)
        self._model = CLIPVisionModelWithProjection.from_pretrained(model_id, cache_dir=cache_dir).to(self.device)
        self._model.eval()

    @torch.inference_mode()
    def embed_images(self, images: Sequence[Image.Image]) -> List[List[float]]:
        rgb_images = [im.convert("RGB") for im in images]
        inputs = self._processor(images=rgb_images, return_tensors="pt").to(self.device)
        outputs = self._model(pixel_values=inputs["pixel_values"])
        feats = outputs.image_embeds
        feats = torch.nn.functional.normalize(feats, p=2, dim=-1)
        return feats.detach().cpu().tolist()


class VectorDB:
    def __init__(
        self,
        *,
        persist_dir: Optional[str] = None,
        collection_name: str = "pricetrace_images",
        image_root: Optional[str] = None,
    ) -> None:
        self.persist_dir = persist_dir or os.path.join(_BACKEND_DIR, "chroma_data")
        self.image_root = os.path.abspath(image_root) if image_root else None
        os.makedirs(self.persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self._embedder: Optional[ClipEmbedder] = None
        self._detector: Optional[GroundingDinoDetector] = None

    def _get_embedder(self) -> ClipEmbedder:
        if self._embedder is None:
            self._embedder = ClipEmbedder()
        return self._embedder

    def _get_detector(self) -> GroundingDinoDetector:
        if self._detector is None:
            self._detector = GroundingDinoDetector()
        return self._detector

    def index_image(
        self,
        image_path: str,
        *,
        use_grounding_dino: bool = True,
        text_prompt: str = "",
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
    ) -> Dict[str, Any]:
        image = Image.open(image_path).convert("RGB")

        items: List[Tuple[Image.Image, Dict[str, Any]]] = []

        if use_grounding_dino:
            if not text_prompt.strip():
                raise ValueError("text_prompt is required when use_grounding_dino=True")

            detections = self._get_detector().detect(
                image,
                text_prompt=text_prompt,
                box_threshold=box_threshold,
                text_threshold=text_threshold,
            )

            for det in detections:
                crop = crop_image(image, det.box_xyxy)
                if crop is None:
                    continue
                items.append(
                    (
                        crop,
                        {
                            "source": "crop",
                            "label": det.label,
                            "score": det.score,
                            "box_xyxy": ",".join(str(v) for v in det.box_xyxy),
                        },
                    )
                )
        else:
            items.append((image, {"source": "full_image"}))

        if not items:
            return {"indexed": 0, "ids": []}

        images = [im for im, _ in items]
        embeddings = self._get_embedder().embed_images(images)

        ids: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        documents: List[str] = []

        for _, meta in items:
            _id = uuid.uuid4().hex
            ids.append(_id)
            abs_path = os.path.abspath(image_path)
            stored_path = (
                os.path.relpath(abs_path, self.image_root)
                if self.image_root
                else abs_path
            )
            meta_full = {
                "image_path": stored_path,
                **meta,
            }
            metadatas.append(meta_full)
            documents.append(meta_full.get("label", meta_full.get("source", "image")))

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

        return {"indexed": len(ids), "ids": ids}

    def search_by_image(
        self,
        image_path: str,
        *,
        k: int = 5,
    ) -> Dict[str, Any]:
        image = Image.open(image_path).convert("RGB")
        query_vec = self._get_embedder().embed_images([image])[0]

        res = self._collection.query(
            query_embeddings=[query_vec],
            n_results=k,
            include=["metadatas", "documents", "distances"],
        )

        out: List[Dict[str, Any]] = []
        for _id, dist, meta, doc in zip(
            res.get("ids", [[]])[0],
            res.get("distances", [[]])[0],
            res.get("metadatas", [[]])[0],
            res.get("documents", [[]])[0],
        ):
            if self.image_root and "image_path" in meta:
                meta = {**meta, "image_path": os.path.join(self.image_root, meta["image_path"])}
            out.append(
                {
                    "id": _id,
                    "distance": dist,
                    "document": doc,
                    "metadata": meta,
                }
            )
            
        return {"results": out}

    def search(
        self,
        image_path: str,
        max_k: int = 5,
        min_similarity: float = 0.0,
    ) -> List[Tuple[str, float]]:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        raw = self.search_by_image(image_path, k=max_k)
        results: List[Tuple[str, float]] = []
        for r in raw["results"]:
            similarity = 1.0 - r["distance"]
            if similarity >= min_similarity:
                path = r["metadata"]["image_path"]
                results.append((path, round(similarity, 4)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results