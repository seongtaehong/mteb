"""Required python >=3.9 and that the `google-generativeai` package is installed. Additionally the GOOGLE_API_KEY environment variable must be set."""

from __future__ import annotations

from functools import partial
from typing import Any, List, Optional

import numpy as np

from mteb.encoder_interface import Encoder
from mteb.model_meta import ModelMeta


class GoogleTextEmbeddingModel(Encoder):
    def __init__(self, model_name: str, sep: str = " ", **kwargs) -> None:
        self.model_name = model_name

    def _embed(
        self,
        texts: List[str],
        google_task_type: str = None,
        titles: List[str] | None = None,
        dimensionality: Optional[int] = 768,
    ) -> List[List[float]]:
        """
        Embeds texts with a pre-trained, foundational model.
        From https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings#generative-ai-get-text-embedding-python_vertex_ai_sdk
        """
        try:
            from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
        except:
            raise ImportError(
                "The `vertexai` package is required to run the google API, please install it using `pip install vertexai`"
            )
        model = TextEmbeddingModel.from_pretrained(self.model_name)
        if titles:
            # Allow title-only embeddings by replacing text with a space
            # Else Google throws google.api_core.exceptions.InvalidArgument: 400 The text content is empty.
            inputs = [TextEmbeddingInput(text if text else " ", task_type=google_task_type, title=title) for text, title in zip(texts, titles)]
        else:
            inputs = [TextEmbeddingInput(text, task_type=google_task_type) for text in texts]
        kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
        try:
            embeddings = model.get_embeddings(inputs, **kwargs)
        # Except google.api_core.exceptions.InternalServerError
        except Exception as e:
            print("Retrying once after error:", e)
            embeddings = model.get_embeddings(inputs, **kwargs)
        return np.asarray([embedding.values for embedding in embeddings])

    def _embed_genai(
        self, sentences: list[str], *, google_task_type: str = None, titles: list[str] | None = None
    ) -> np.ndarray:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "`google-generativeai` is required to run the google API, pleae install it using `pip install google-generativeai`"
            )

        if titles:
            result = genai.embed_content(  # type: ignore
                model=self.model_name,
                content=sentences,
                task_type=google_task_type,
                title=titles,
            )
        else:
            result = genai.embed_content(  # type: ignore
                model=self.model_name,
                content=sentences,
                task_type=google_task_type,
            )

        return np.asarray(result["embedding"])

    def encode(
        self,
        sentences: list[str],
        prompt_name: str | None = None,
        google_task_type: str | None = None, # Optional
        **kwargs: Any,
    ) -> np.ndarray:
        if prompt_name and google_task_type is None:
            task = mteb.get_task(prompt_name)
            task_type = task.metadata.type
            if task_type in ["Classification", "MultilabelClassification"]:
                google_task_type = "CLASSIFICATION"
            elif task_type == "Clustering":
                google_task_type = "CLUSTERING"
            elif task_type == "STS":
                google_task_type = "SIMILARITY"
        return self._embed(sentences, google_task_type=google_task_type)

    def encode_queries(self, queries: list[str], **kwargs: Any) -> np.ndarray:
        return self._embed(queries, google_task_type="RETRIEVAL_QUERY")

    def encode_corpus(self, corpus: list[dict[str, str]], **kwargs: Any) -> np.ndarray:
        if isinstance(corpus, dict):
            sentences, titles = [], []

            for i in range(len(corpus["text"])):  # type: ignore
                titles.append(corpus["title"][i])  # type: ignore
                sentences.append(corpus["text"][i])  # type: ignore
        else:
            sentences, titles = [], []
            for doc in corpus:
                titles.append(doc["title"])
                sentences.append(doc["text"])
        return self._embed(sentences, google_task_type="RETRIEVAL_DOCUMENT", titles=titles)


name = "text-embedding-004"
google_emb_004 = ModelMeta(
    loader=partial(GoogleTextEmbeddingModel, model_name=name),
    name=name,
    languages=["eng-Latn"],
    open_source=False,
    revision="1",
    release_date=None,  # couldnt figure this out
    n_parameters=None,
    memory_usage=None,
    max_tokens=3072,
    embed_dim=768,
    license=None,
    similarity_fn_name="cosine",  # assumed
    framework=[],
)


if __name__ == "__main__":
    import mteb

    mdl = mteb.get_model(google_emb_004.name, google_emb_004.revision)
    emb = mdl.encode(["Hello, world!"])