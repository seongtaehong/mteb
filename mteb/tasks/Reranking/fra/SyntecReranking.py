from __future__ import annotations

import datasets

from mteb.abstasks.TaskMetadata import TaskMetadata

from ....abstasks.AbsTaskReranking import AbsTaskReranking


class SyntecReranking(AbsTaskReranking):
    metadata = TaskMetadata(
        name="SyntecReranking",
        description="This dataset has been built from the Syntec Collective bargaining agreement.",
        reference="https://huggingface.co/datasets/lyon-nlp/mteb-fr-reranking-syntec-s2p",
        dataset={
            "path": "lyon-nlp/mteb-fr-reranking-syntec-s2p",
            "revision": "daf0863838cd9e3ba50544cdce3ac2b338a1b0ad",
        },
        type="Reranking",
        category="s2p",
        modalities=["text"],
        eval_splits=["test"],
        eval_langs=["fra-Latn"],
        main_score="map_at_1000",
        date=("2022-12-01", "2022-12-02"),
        domains=["Legal", "Written"],
        task_subtypes=None,
        license="cc-by-nc-sa-4.0",
        annotations_creators="human-annotated",
        dialect=None,
        sample_creation="found",
        bibtex_citation="""@misc{ciancone2024extending,
      title={Extending the Massive Text Embedding Benchmark to French}, 
      author={Mathieu Ciancone and Imene Kerboua and Marion Schaeffer and Wissam Siblini},
      year={2024},
      eprint={2405.20468},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}""",
        descriptive_stats={
            "n_samples": {"test": 100},
            "test": {
                "average_document_length": 1716.897738446411,
                "average_query_length": 72.82,
                "num_documents": 1017,
                "num_queries": 100,
                "average_relevant_docs_per_query": 1.0,
                "average_instruction_length": 0,
                "num_instructions": 0,
                "average_top_ranked_per_query": 10.17,
            },
        },
    )

    def load_data(self, **kwargs):
        if self.data_loaded:
            return

        self.dataset = datasets.load_dataset(
            name="queries",
            **self.metadata_dict["dataset"],
            split=self.metadata.eval_splits[0],
        )
        documents = datasets.load_dataset(
            name="documents", **self.metadata_dict["dataset"], split="test"
        )
        # replace documents ids in positive and negative column by their respective texts
        doc_id2txt = dict(list(zip(documents["doc_id"], documents["text"])))

        self.dataset = self.dataset.map(
            lambda x: {
                "positive": [doc_id2txt[docid] for docid in x["positive"]],
                "negative": [doc_id2txt[docid] for docid in x["negative"]],
            }
        )
        self.dataset = datasets.DatasetDict({"test": self.dataset})

        self.dataset_transform()

        # now convert to the new format
        self.transform_old_dataset_format(self.dataset)

        self.data_loaded = True
