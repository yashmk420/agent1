from pathlib import Path

def chunk_text(text, chunk_size=100, overlap=21):
     chunks = []

     for i in range(0,len(text), chunk_size - overlap):
         chunk = text[i:i+chunk_size]
         chunks.append(chunk)

     return chunks

## reads all the text from folders and breaks them to chunk, adds ina. dictonary typoe data and push in to chunks

def read_folder(folder):

     documents = []

     for item in folder.rglob("*"):
         if item.is_file() and item.suffix in [".md", ".py", ".txt"]:
             text = item.read_text()

             documents.append({
                 "file": item.name,
                 "text": text
             })     
     return documents 


## we check relevant words from chunks wich is related to users question   


def get_relevant_chunks(chunks, question):
    words = question.split()

    stop_words = ["and", "or", "but", "the", "is", "are", "was", "were", "in", "on", "at", "to", "of"]

    scored_chunks = []

    for chunk in chunks:
        score = 0
        text = chunk["chunk"].lower()

        for word in words:
            word = word.lower().strip(".,!?;:\"'()[]{}<>")

            if word in stop_words:
                continue
            if len(word) < 3:
                continue

            if word in text:
                score += 1

        if score > 0:
            scored_chunks.append({
                "text": chunk["chunk"],
                "score": score
            })

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)

    top_chunks = scored_chunks[:20]

    print("Relevant chunks:", len(scored_chunks))
    print("Selected chunks:", len(top_chunks))

    return "\n".join(item["text"] for item in top_chunks)
