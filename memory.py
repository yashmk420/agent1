
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import uuid

load_dotenv()


_model = None
_index = None



def get_resources():
    global _model, _index
    
    if _model is None:
        _model = SentenceTransformer("all-mpnet-base-v2")

    if _index is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in .env")
        pc = Pinecone(api_key=api_key)
        _index = pc.Index("agent-memory")

    return _index, _model





def remember_note(project, note):

    index, model = get_resources()
    vector = model.encode(note).tolist()


    index.upsert(
        vectors=[{
            "id": str(uuid.uuid4()),
            "values": vector,
            "metadata": {"text": note}
        }],
        namespace=project
    )

    print(f"Note stored under project: {project}")



def recall_notes(project, question):
    
    index, model = get_resources()
    query_vector = model.encode(question).tolist()

    results = index.query(
        vector=query_vector,
        top_k=5,
        include_metadata=True,
        namespace=project
    )

    return results["matches"]


def cleanup_duplicate_notes(project, dry_run=True):
    # Get the Pinecone index. We don't need the embedding model
    # because we compare the original text, not vector similarity.
    index, _ = get_resources()

    # Maps normalized note text to the first ID we find.
    seen = {}
    duplicate_ids = []

    # index.list() returns pages of IDs and handles pagination.
    # This operation requires a supported serverless index.
    for page in index.list(namespace=project, limit=100):
        # Listing returns IDs only, so fetch the records to get text.
        vector_ids = page

        # Fetch records in batches of at most 100.
        for start in range(0, len(vector_ids), 100):
            batch_ids = vector_ids[start:start + 100]

            records = index.fetch(
                ids=batch_ids,
                namespace=project
            )

            # Compare the readable text of each record.
            for vector_id, record in records.vectors.items():
                metadata = record.metadata or {}
                note = metadata.get("text", "")

                # Skip notes with no useful text.
                if not note.strip():
                    continue

                # Ignore capitalization and repeated whitespace.
                normalized = " ".join(note.split()).casefold()

                if normalized in seen:
                    # We've already kept one copy of this note.
                    duplicate_ids.append(vector_id)
                else:
                    # Keep the first ID for this note.
                    seen[normalized] = vector_id


    # Preview the duplicates without deleting them.
    print(f"Project: {project}")
    print(f"Duplicate records found: {len(duplicate_ids)}")

    for duplicate_id in duplicate_ids:
        print(f"Duplicate ID: {duplicate_id}")

    # True means preview only; False means actually delete.
    if dry_run:
        print("Preview only. No records were deleted.")
        return duplicate_ids

    # Delete only the extra copies in this project.
    if duplicate_ids:
        index.delete(
            ids=duplicate_ids,
            namespace=project
        )

    print(f"Deleted {len(duplicate_ids)} duplicate records.")
    return duplicate_ids